#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline owner-backup extraction of the Android OSIP template only.

Never reads or writes a device. The resulting private template preserves the
original Android payload, including its old ramdisk; it is NOT a public ROM.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib
from pack_boot import template_prefix

HEADER_BYTES = 40 * 512
RESERVED_BYTES = 234881024
LAYOUT = ((36050, (0, 1)), (100050, (13,)), (4050, (14,)))


def records(header, reserved_bytes):
    # The inspected original disk has three pointers but num_images == 1;
    # these are distinct fields, not interchangeable descriptor counts.
    if len(header) != HEADER_BYTES or header[:4] != b'$OS$' or header[8:10] != b'\x03\x01':
        raise ValueError('unsupported owner disk header')
    size = struct.unpack_from('<H', header, 10)[0]
    checksum = 0
    for value in header[:104]:
        checksum ^= value
    if size != 104 or checksum or reserved_bytes != RESERVED_BYTES:
        raise ValueError('invalid header or reserved backup size')
    entries, intervals = [], []
    for index, (expected_lba, attributes) in enumerate(LAYOUT):
        minor, major, lba, load, entry, sectors, attribute = struct.unpack_from('<HHIIIIB', header, 32 + index * 24)
        if (lba, load, entry) != (expected_lba, 0x1100000, 0x1101000) or attribute not in attributes:
            raise ValueError('different OSIP layout')
        start, length = (lba - 40) * 512, sectors * 512
        if not 0 < length <= 32000 * 512 or start < 0 or start + length > reserved_bytes:
            raise ValueError('OSIP range out of bounds')
        if any(start < end and begin < start + length for begin, end in intervals):
            raise ValueError('overlapping OSIP images')
        if any(header[53 + index * 24:56 + index * 24]):
            raise ValueError('unknown descriptor reserved fields')
        intervals.append((start, start + length))
        entries.append((minor, major, lba, load, entry, sectors, attribute, start, length))
    return entries


def extract(header_path, reserved_path, output):
    for path, size in ((header_path, HEADER_BYTES), (reserved_path, RESERVED_BYTES)):
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
            raise ValueError('missing or wrong-size owner backup')
    if output.exists() or output.is_symlink():
        raise ValueError('output must be new')
    header = header_path.read_bytes()
    android = records(header, reserved_path.stat().st_size)[0]
    with reserved_path.open('rb') as stream:
        stream.seek(android[-2])
        payload = stream.read(android[-1])
    if len(payload) != android[-1]:
        raise ValueError('short backup read')
    container = bytearray(512)
    container[:32] = header[:32]
    container[7] = 0
    container[8:10] = b'\x01\x01'
    struct.pack_into('<H', container, 10, 56)
    struct.pack_into('<HHIIIIB3x', container, 32, *android[:7])
    for value in container[:56]:
        container[7] ^= value
    result = bytes(container) + payload
    # Validate actual ducati2fhd bootstub, kernel and gzip/newc ramdisk ranges.
    # No old ramdisk approvals or stock signatures are silently removed.
    template_prefix(result)
    with output.open('xb') as stream:
        stream.write(result)
    output.chmod(0o600)
    return {'template_bytes': len(result), 'template_sha256': hashlib.sha256(result).hexdigest(),
            'android_payload_preserved': True, 'old_ramdisk_preserved': True,
            'only_android_descriptor_exported': True, 'device_io': False,
            'backup_modified': False, 'whole_backup_integrity_verified': False,
            'bootability_verified': False, 'publication_approved': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disk-header', required=True, type=Path)
    parser.add_argument('--reserved-backup', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(extract(args.disk_header, args.reserved_backup, args.output), indent=2))
        return 0
    except (ValueError, OSError, EOFError, struct.error, zlib.error):
        print(json.dumps({'error': 'owner template extraction refused', 'device_io': False, 'publication_approved': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
