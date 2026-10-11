#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stage an owner-selected raw image in recovery cache, never flash it.

Dry-run default. Apply creates a unique private directory, verifies the upload,
then hard-links to the checksum-named installation path without overwriting.
Failures preserve partial files for inspection; no automatic retry or reboot.
"""
import argparse
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import uuid
from backup_acer import preflight, SYSTEM_BYTES
from flash_system import require_cache_staging, require_unmounted
from inspect_system import inspect
from recovery_adb import RecoveryADB

RESERVE_BYTES = 16 * 1024 * 1024


def inspect_source(source, expected):
    if not re.fullmatch(r'[0-9a-f]{64}', expected):
        raise ValueError('explicit raw SHA-256 required')
    if source.is_symlink() or not source.is_file() or source.stat().st_size != SYSTEM_BYTES:
        raise ValueError('full regular raw system image required')
    with source.open('rb') as stream:
        checked = inspect(stream, SYSTEM_BYTES)
    if checked['format'] != 'raw' or checked['expanded_zero_holes_sha256'] != expected:
        raise ValueError('raw format/checksum mismatch')


def available_cache(adb):
    value = adb.read('stat -f -c "%a:%S" /cache')
    if not re.fullmatch(r'[0-9]{1,20}:[0-9]{1,10}', value):
        raise ValueError('supported filesystem capacity query required')
    blocks, block_bytes = map(int, value.split(':'))
    if block_bytes not in (1024, 2048, 4096, 8192):
        raise ValueError('unsupported cache filesystem block size')
    if blocks * block_bytes < SYSTEM_BYTES + RESERVE_BYTES:
        raise ValueError('cache lacks raw-image space plus reserve')


def stage(adb, source, expected, apply=False):
    inspect_source(source, expected)
    header, _ = preflight(adb)
    if adb.read('getprop ro.bootmode') != 'recovery' or adb.read('test -f /tmp/recovery.log && echo RECOVERY') != 'RECOVERY':
        raise ValueError('supported root recovery required')
    require_unmounted(adb)
    require_cache_staging(adb)
    available_cache(adb)
    remote = '/cache/acer-system-' + expected + '.raw.img'
    if adb.read('test ! -e ' + remote + ' && test ! -L ' + remote + ' && echo ABSENT') != 'ABSENT':
        raise ValueError('existing destination must not be overwritten')
    report = {'device': 'acer-a1-840fhd', 'applied': False,
              'cache_space_checked': True, 'remote_checksum_verified': False,
              'partition_written': False, 'reboot': False,
              'publication_approved': False,
              'temporary_header_staging_enabled': bool(getattr(adb, 'legacy_header_staging', False))}
    if not apply:
        return report
    if adb.header() != header:
        raise ValueError('header changed before staging')
    require_cache_staging(adb)
    available_cache(adb)
    folder = '/cache/acer-stage-' + uuid.uuid4().hex
    temporary = folder + '/system.raw.img'
    adb.run(['shell', adb.root('umask 077; mkdir ' + folder)])
    # Never delete on failure: partial uploads and completed destinations are
    # distinguishable evidence, and no recursive cleanup is appropriate.
    adb.run(['push', str(source.resolve()), temporary], timeout=1200)
    stat = adb.read('stat -t ' + temporary).split()
    digest = adb.read('sha256sum ' + temporary).split()
    if len(stat) < 2 or stat[0] != temporary or stat[1] != str(SYSTEM_BYTES) or digest != [expected, temporary]:
        raise ValueError('uploaded image size/checksum mismatch')
    require_cache_staging(adb)
    # ln, unlike adb push or mv, fails if the final destination already exists.
    adb.run(['shell', adb.root('ln ' + temporary + ' ' + remote)])
    require_cache_staging(adb, remote)
    if adb.read('sha256sum ' + remote).split() != [expected, remote]:
        raise ValueError('final staged image checksum mismatch')
    adb.run(['shell', adb.root('rm ' + temporary + '; rmdir ' + folder)])
    report['applied'] = report['remote_checksum_verified'] = True
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', required=True, type=Path)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--raw-sha256', required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--legacy-header-staging', action='store_true')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(stage(RecoveryADB(args.adb, args.serial, args.legacy_header_staging),
                               args.input, args.raw_sha256, args.apply), indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, struct.error, subprocess.SubprocessError):
        print(json.dumps({'error': 'staging refused or incomplete; preserve partial cache files',
                          'cache_files_may_have_been_created': args.apply,
                          'temporary_header_staging_enabled': args.legacy_header_staging,
                          'partition_written': False, 'reboot': False, 'automatic_retry': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
