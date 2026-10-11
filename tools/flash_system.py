#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Guarded raw system write from a pre-staged recovery file; dry-run default.

Default Android exec-out header read; explicit legacy mode stages a temporary
20KiB header. Never enters recovery, uploads system images, unmounts, formats,
changes boot/GPT, deletes staged system images or reboots.
"""
import argparse
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
from backup_acer import preflight, SYSTEM_BYTES
from verify_owner_backup import verify
from recovery_adb import RecoveryADB


def require_unmounted(adb):
    for line in adb.read('cat /proc/mounts').splitlines():
        fields = line.split()
        if len(fields) != 6:
            raise ValueError('unsupported mount inventory')
        source = fields[0]
        if fields[1] == '/system' or source == '/dev/block/mmcblk0p9':
            raise ValueError('system must be unmounted, including read-only mounts')
        if source.startswith('/dev/'):
            if not re.fullmatch(r'[A-Za-z0-9_./:-]+', source):
                raise ValueError('unsupported block alias')
            if adb.read('readlink -f ' + source) == '/dev/block/mmcblk0p9':
                raise ValueError('system block alias is mounted')


def require_cache_staging(adb, remote_image=None):
    """Reject redirected cache paths and RAM/userdata/system staging."""
    if adb.read('readlink -f /cache') != '/cache':
        raise ValueError('cache staging path is redirected')
    if remote_image is not None and adb.read('readlink -f ' + remote_image) != remote_image:
        raise ValueError('cache image path is redirected')
    cache_mounts = []
    for line in adb.read('cat /proc/mounts').splitlines():
        fields = line.split()
        if len(fields) != 6:
            raise ValueError('unsupported mount inventory')
        if fields[1].startswith('/cache/'):
            raise ValueError('nested cache mount is unsupported')
        if fields[1] == '/cache':
            cache_mounts.append(fields)
    if len(cache_mounts) != 1:
        raise ValueError('one explicit cache mount required')
    source, _, filesystem, options, _, _ = cache_mounts[0]
    if filesystem != 'ext4' or 'rw' not in options.split(','):
        raise ValueError('writable ext4 cache required')
    if not re.fullmatch(r'/dev/[A-Za-z0-9_./:-]+', source):
        raise ValueError('unsupported cache block alias')
    if adb.read('readlink -f ' + source) != '/dev/block/mmcblk0p7':
        raise ValueError('cache differs from reviewed partition')


def install(adb, serial, backup_dir, expected_sha256, remote_image, apply=False):
    if not re.fullmatch(r'[0-9a-f]{64}', expected_sha256):
        raise ValueError('explicit raw-image SHA-256 required')
    if remote_image != '/cache/acer-system-' + expected_sha256 + '.raw.img':
        raise ValueError('exact checksum-named cache image required')
    receipt_path = backup_dir / 'private-backup-receipt.json'
    if receipt_path.is_symlink() or not receipt_path.is_file() or receipt_path.stat().st_size > 65536:
        raise ValueError('private complete-scope receipt required')
    receipt = json.loads(receipt_path.read_text())
    if not isinstance(receipt, dict):
        raise ValueError('unsupported private receipt structure')
    if receipt.get('serial') != serial or receipt.get('includes_system') is not True:
        raise ValueError('same selected serial and system rollback backup required')
    checked = verify(backup_dir / 'acer-disk-header.bin', backup_dir / 'acer-reserved.img',
                     backup_dir / 'acer-system.img', receipt_path)
    if not checked['saved_receipt_checksums_matched']:
        raise ValueError('owner backup checksum mismatch')
    header, current_layout = preflight(adb)
    if current_layout != receipt['layout']:
        raise ValueError('current layout differs from backed-up layout')
    if adb.read('getprop ro.bootmode') != 'recovery' or adb.read('test -f /tmp/recovery.log && echo RECOVERY') != 'RECOVERY':
        raise ValueError('supported recovery context not confirmed')
    if adb.read('readlink -f /dev/block/platform/intel/by-label/system') != '/dev/block/mmcblk0p9':
        raise ValueError('system alias differs from reviewed partition')
    require_unmounted(adb)
    require_cache_staging(adb, remote_image)
    if adb.read('test -f ' + remote_image + ' && test ! -L ' + remote_image + ' && echo REGULAR') != 'REGULAR':
        raise ValueError('regular pre-staged file required')
    stat = adb.read('stat -t ' + remote_image).split()
    if len(stat) < 2 or stat[0] != remote_image or stat[1] != str(SYSTEM_BYTES):
        raise ValueError('remote raw image size differs from full partition')
    remote_hash = adb.read('sha256sum ' + remote_image).split()
    if not remote_hash or remote_hash[0] != expected_sha256:
        raise ValueError('pre-staged raw image checksum differs')
    report = {'device': 'acer-a1-840fhd', 'backup_checksums_matched': True,
              'current_layout_checked': True, 'recovery_context_checked': True,
              'system_unmounted_checked': True, 'remote_raw_checksum_checked': True,
              'cache_staging_mount_checked': True,
              'applied': False, 'system_readback_verified': False, 'boot_written': False,
              'gpt_written': False, 'userdata_erased': False, 'reboot': False,
              'installation_boot_verified': False, 'publication_approved': False}
    report['temporary_header_staging_enabled'] = bool(getattr(adb, 'legacy_header_staging', False))
    if not apply:
        return report
    if adb.header() != header:
        raise ValueError('disk header changed before write')
    require_unmounted(adb)
    require_cache_staging(adb, remote_image)
    # No unchecked adb push, implicit mount change, erase or retry. Caller
    # must prevent concurrent staging/partition changes throughout operation.
    result = adb.run(['shell', adb.root('set -e; dd if=' + remote_image +
                     ' of=/dev/block/mmcblk0p9 bs=1048576; sync; sha256sum /dev/block/mmcblk0p9')], timeout=1200)
    output = re.findall(r'(?m)^([0-9a-f]{64})\s+/dev/block/mmcblk0p9\s*$', result.decode('utf-8', 'strict'))
    if output != [expected_sha256]:
        raise ValueError('system write/readback incomplete; do not reboot')
    if adb.header() != header:
        raise ValueError('disk header changed; do not reboot')
    report['applied'] = report['system_readback_verified'] = True
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', required=True, type=Path)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--owner-backup', required=True, type=Path)
    parser.add_argument('--raw-sha256', required=True)
    parser.add_argument('--remote-image', required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--legacy-header-staging', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = install(RecoveryADB(args.adb, args.serial, args.legacy_header_staging), args.serial, args.owner_backup,
                         args.raw_sha256, args.remote_image, args.apply)
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, struct.error, subprocess.SubprocessError):
        print(json.dumps({'error': 'preflight refused or system write/readback incomplete',
                          'partition_write_may_have_started': args.apply,
                          'temporary_header_staging_enabled': args.legacy_header_staging,
                          'reboot': False, 'automatic_retry': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
