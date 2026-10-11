#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Offline OSIP/GPT layout checks for owner backup acquisition.

Independent parser of format facts checked against the official source's GPT
structure definition. No disk GUIDs, partition GUIDs or personal values output.
No device I/O or writes; this is not a complete backup or recovery program.
"""
import argparse
import json
from pathlib import Path
import struct
import sys
import zlib
from extract_boot_template import HEADER_BYTES, RESERVED_BYTES, records


def layout(header):
    records(header, RESERVED_BYTES)
    gpt = header[512:1024]
    if gpt[:8] != b'EFI PART':
        raise ValueError('missing primary GPT')
    revision, size, checksum, reserved = struct.unpack_from('<4I', gpt, 8)
    current, alternate, first, last = struct.unpack_from('<4Q', gpt, 24)
    table_lba, count, entry_size, table_crc = struct.unpack_from('<Q3I', gpt, 72)
    if revision != 0x10000 or size != 92 or reserved or current != 1 or not 2 <= first <= 40 <= last < alternate:
        raise ValueError('unsupported GPT header geometry')
    checked = bytearray(gpt[:size])
    checked[16:20] = bytes(4)
    if zlib.crc32(checked) != checksum or any(gpt[size:]):
        raise ValueError('GPT header checksum or reserved bytes invalid')
    begin, end = table_lba * 512, table_lba * 512 + count * entry_size
    if not 2 <= table_lba < 40 or not 1 <= count <= 128 or entry_size != 128 or end > len(header) or end > first * 512:
        raise ValueError('unsupported GPT table bounds')
    table = header[begin:end]
    if zlib.crc32(table) != table_crc:
        raise ValueError('GPT table checksum invalid')
    partitions, intervals = {}, []
    for index in range(count):
        row = table[index * entry_size:(index + 1) * entry_size]
        if row[:16] == bytes(16):
            continue
        start, finish = struct.unpack_from('<2Q', row, 32)
        name = row[56:128].decode('utf-16-le', 'strict').split('\0', 1)[0]
        if not name or name in partitions or not first <= start <= finish <= last:
            raise ValueError('invalid GPT partition')
        if any(start <= stop and other <= finish for other, stop in intervals):
            raise ValueError('overlapping GPT partitions')
        intervals.append((start, finish))
        partitions[name] = {'index': index + 1, 'start_sector': start, 'sectors': finish - start + 1}
    boot = partitions.get('reserved')
    system = partitions.get('system')
    if boot != {'index': 1, 'start_sector': 40, 'sectors': 458752}:
        raise ValueError('reserved partition does not match supported Acer layout')
    if not system or system['index'] != 9 or system['sectors'] != 3686400:
        raise ValueError('system partition does not match supported Acer layout')
    return {'device': 'acer-a1-840fhd', 'osip_layout_verified': True,
            'primary_gpt_header_crc_verified': True, 'primary_gpt_table_crc_verified': True,
            'reserved': boot, 'system': system,
            'disk_sectors_from_primary_gpt': alternate + 1,
            'backup_gpt_independently_checked': False, 'complete_backup_verified': False,
            'device_identity_verified': False, 'device_io': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('disk_header', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.disk_header.is_symlink() or not args.disk_header.is_file() or args.disk_header.stat().st_size != HEADER_BYTES:
            raise ValueError('supported regular header backup required')
        print(json.dumps(layout(args.disk_header.read_bytes()), indent=2))
        return 0
    except (OSError, ValueError, struct.error):
        print(json.dumps({'error': 'Acer OSIP/GPT layout check refused', 'device_io': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
