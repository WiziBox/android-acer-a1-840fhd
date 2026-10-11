#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Owner backup via authenticated root ADB; dry-run preflight by default.

Android 9 exec-out backend. No device writes, reboot, flash, remount or root
enable command. Full userdata/factory/config backups are outside this scope.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
from acer_layout import HEADER_BYTES, RESERVED_BYTES, layout

SYSTEM_BYTES = 1887436800


class ADB:
    def __init__(self, executable, serial):
        if not executable.is_file() or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,255}', serial):
            raise ValueError('explicit adb binary and serial required')
        self.command = [str(executable.resolve()), '-s', serial]
        self.root_prefix = None

    def run(self, arguments, timeout=30, stdout=subprocess.PIPE):
        result = subprocess.run(self.command + arguments, stdout=stdout, stderr=subprocess.PIPE, timeout=timeout)
        if result.returncode:
            raise ValueError('ADB operation failed')
        return result.stdout

    def root(self, command):
        if self.root_prefix is None:
            raise ValueError('root preflight missing')
        if "'" in command or '\n' in command:
            raise ValueError('unsafe remote command')
        return self.root_prefix + command + ("'" if self.root_prefix else '')

    def read(self, command):
        return self.run(['shell', self.root(command)]).decode('utf-8', 'strict').strip()

    def get_root(self):
        if b'uid=0(' in self.run(['shell', 'id']):
            self.root_prefix = ''
        elif b'uid=0(' in self.run(['shell', "su -c 'id'"]):
            self.root_prefix = "su -c '"
        else:
            raise ValueError('existing authorized root required; no automatic root enable')

    def header(self):
        return self.run(['exec-out', self.root('dd if=/dev/block/mmcblk0 bs=512 count=40 2>/dev/null')])


def preflight(adb, include_system=False):
    props = {}
    for key in ('ro.product.manufacturer', 'ro.product.model', 'ro.hardware'):
        props[key] = adb.run(['shell', 'getprop ' + key]).decode('utf-8', 'strict').strip()
    if props != {'ro.product.manufacturer': 'Acer', 'ro.product.model': 'A1-840FHD', 'ro.hardware': 'ducati2fhd'}:
        raise ValueError('exact supported model/hardware not confirmed')
    adb.get_root()
    header = adb.header()
    verified = layout(header)
    for name, block in (('reserved', 'mmcblk0p1'), ('system', 'mmcblk0p9')):
        for field, sysfs in (('start_sector', 'start'), ('sectors', 'size')):
            value = adb.read('cat /sys/class/block/' + block + '/' + sysfs)
            if not value.isdigit() or int(value) != verified[name][field]:
                raise ValueError('live sysfs partition differs from GPT')
    media = adb.read('cat /sys/class/block/mmcblk0/size')
    if not media.isdigit() or int(media) != verified['disk_sectors_from_primary_gpt']:
        raise ValueError('GPT/media capacity mismatch')
    if include_system:
        mounted = adb.read('cat /proc/mounts')
        for line in mounted.splitlines():
            fields = line.split()
            if len(fields) != 6:
                raise ValueError('unsupported mount inventory')
            source = fields[0]
            target_system = fields[1] == '/system' or source == '/dev/block/mmcblk0p9'
            if source.startswith('/dev/') and re.fullmatch(r'[A-Za-z0-9_./:-]+', source):
                target_system |= adb.read('readlink -f ' + source) == '/dev/block/mmcblk0p9'
            if target_system:
                if 'ro' not in fields[3].split(','):
                    raise ValueError('system is mounted writable; no live block backup')
    return header, verified


def transfer(adb, source, output, expected):
    command = 'dd if=' + source + ' bs=1048576'
    command += ' 2>/dev/null'
    with output.open('xb') as stream:
        adb.run(['exec-out', adb.root(command)], timeout=1200, stdout=stream)
    output.chmod(0o600)
    if output.stat().st_size != expected:
        raise ValueError('short/contaminated backup; preserve partial file')
    digest = hashlib.sha256()
    with output.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    remote = adb.read('sha256sum ' + source).split()
    if not remote or not re.fullmatch(r'[0-9a-fA-F]{64}', remote[0]) or remote[0].lower() != digest.hexdigest():
        raise ValueError('live source/backup hash mismatch; do not trust partial backup')
    return {'file': output.name, 'bytes': expected, 'sha256': digest.hexdigest(), 'live_source_hash_matched': True}


def backup(adb, serial, output, include_system=False, apply=False):
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(Path(__file__).parents[1].resolve()):
        raise ValueError('new private output outside this public repository required')
    header, verified = preflight(adb, include_system)
    report = {'model_checked': True, 'live_layout_checked': True, 'applied': False,
              'includes_system': include_system, 'includes_userdata_factory_config': False,
              'device_reads': True, 'device_writes': False, 'reboot': False,
              'complete_device_recovery_verified': False, 'publication_approved': False}
    if not apply:
        return report
    if not output.parent.is_dir() or output.parent.is_symlink() or shutil.disk_usage(output.parent).free < HEADER_BYTES + RESERVED_BYTES + (SYSTEM_BYTES if include_system else 0):
        raise ValueError('private parent or backup free space missing')
    output.mkdir(mode=0o700)
    header_path = output / 'acer-disk-header.bin'
    with header_path.open('xb') as stream:
        stream.write(header)
    header_path.chmod(0o600)
    files = [{'file': header_path.name, 'bytes': len(header), 'sha256': hashlib.sha256(header).hexdigest()}]
    files.append(transfer(adb, '/dev/block/mmcblk0p1', output / 'acer-reserved.img', RESERVED_BYTES))
    if include_system:
        files.append(transfer(adb, '/dev/block/mmcblk0p9', output / 'acer-system.img', SYSTEM_BYTES))
    second_header, second_layout = preflight(adb, include_system)
    if second_header != header or second_layout != verified:
        raise ValueError('device layout changed during backup; preserve but do not use it')
    report['applied'] = True
    # Serial and hashes belong ONLY to the private receipt. Do not print them.
    receipt = dict(report, serial=serial, layout=verified, files=files)
    with (output / 'private-backup-receipt.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adb', required=True, type=Path)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--include-system', action='store_true')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(backup(ADB(args.adb, args.serial), args.serial, args.output, args.include_system, args.apply), indent=2))
        return 0
    except (OSError, ValueError, struct.error, subprocess.SubprocessError):
        print(json.dumps({'error': 'backup refused or incomplete; keep partial private files, do not flash', 'device_writes': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
