#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Read-only owner backup structure/checksum checks, not restoration proof.

No device access, extraction, repair or publication approval. Hashes are kept
only in an optional new private report; console summaries omit identifiers.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import struct
import sys
import zlib
from acer_layout import layout
from extract_boot_template import HEADER_BYTES, RESERVED_BYTES, records
from audit_boot import cpio_entries, ramdisk_from_boot, align
from inspect_system import inspect, PARTITIONS

ROOT = Path(__file__).resolve().parents[1]


def legacy_recovery_inventory(raw):
    """Check private legacy archive bounds without extracting/overlaying it.

    Duplicate paths are counted, never interpreted as a final filesystem.
    This intentionally does not change the strict new-ROM cpio parser.
    """
    position, count, duplicates, seen = 0, 0, 0, set()
    while True:
        header = raw[position:position + 110]
        if len(header) != 110 or header[:6] not in (b'070701', b'070702'):
            raise ValueError('invalid/truncated newc header')
        fields = [int(header[6 + i * 8:14 + i * 8], 16) for i in range(13)]
        size, namesize, crc = fields[6], fields[11], fields[12]
        if not 1 <= namesize <= 4096:
            raise ValueError('invalid newc name size')
        encoded = raw[position + 110:position + 110 + namesize]
        if len(encoded) != namesize or not encoded.endswith(b'\0') or b'\0' in encoded[:-1]:
            raise ValueError('invalid newc name')
        path = PurePosixPath(encoded[:-1].decode('utf-8', 'strict'))
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('unsafe archive path')
        name = str(path)
        start = align(position + 110 + namesize, 4)
        end = start + size
        following = align(end, 4)
        if following > len(raw):
            raise ValueError('truncated newc member')
        if header[:6] == b'070702' and sum(raw[start:end]) & 0xffffffff != crc:
            raise ValueError('newc CRC mismatch')
        if name == 'TRAILER!!!':
            if size or any(raw[following:]):
                raise ValueError('unexpected data after newc trailer')
            return count, duplicates
        duplicates += name in seen
        seen.add(name)
        count += 1
        position = following


def regular(path, size):
    if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
        raise ValueError('wrong size or unsupported backup file')


def digest(path, size):
    regular(path, size)
    hashed, total = hashlib.sha256(), 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            hashed.update(block)
            total += len(block)
            if total > size:
                raise ValueError('backup changed while reading')
    if total != size:
        raise ValueError('short backup')
    return hashed.hexdigest()


def payload_check(payload, attribute):
    # Signed stock payloads have the existing wrapper before the bootstub.
    offset = 0 if attribute & 1 else 0x400
    if offset and payload[:4] != b'$OSM':
        raise ValueError('missing signed wrapper')
    if len(payload) < offset + 0x3206:
        raise ValueError('short boot payload')
    kernel, ramdisk = struct.unpack_from('<II', payload, offset + 0x400)
    start = offset + 0x3000
    end = start + kernel + ramdisk
    if not kernel or kernel % 4096 or not ramdisk or end > len(payload):
        raise ValueError('boot payload bounds invalid')
    tail = payload[end:]
    # The real owner stock unsigned recovery uses 225 bytes of erased-FF
    # sector padding. Accept only that role's homogeneous partial last sector,
    # not arbitrary trailers or padding in a newly built Android boot image.
    erased = attribute == 13 and 0 < len(tail) < 512 and all(value == 255 for value in tail)
    if any(tail) and not erased:
        raise ValueError('unknown boot payload trailer')
    if payload[start + 0x202:start + 0x206] != b'HdrS':
        raise ValueError('missing x86 kernel header')
    # Normalize only an in-memory inspection container. Preserve source bytes.
    body = payload[offset:end]
    image = bytearray(512) + body
    image += bytes((-len(image)) % 512)
    image[:4] = b'$OS$'
    struct.pack_into('<I', image, 0x30, (len(image) - 512) // 512)
    for value in image[:56]:
        image[7] ^= value
    _, raw = ramdisk_from_boot(bytes(image), 'acer-a1-840fhd')
    if attribute == 13:
        entries, duplicates = legacy_recovery_inventory(raw)
    else:
        entries, duplicates = sum(1 for _ in cpio_entries(raw)), 0
    return {'structure_checked': True, 'ramdisk_entries': entries,
            'duplicate_ramdisk_paths': duplicates,
            'ramdisk_final_filesystem_verified': False,
            'last_sector_padding': 'erased_ff' if erased else 'zero_or_none',
            'oem_signature_cryptographically_verified': False}


def verify(header_path, reserved_path, system_path=None, receipt_path=None):
    regular(header_path, HEADER_BYTES)
    regular(reserved_path, RESERVED_BYTES)
    header = header_path.read_bytes()
    verified_layout = layout(header)
    descriptions = []
    with reserved_path.open('rb') as stream:
        for role, entry in zip(('android', 'recovery', 'droidboot'), records(header, RESERVED_BYTES)):
            stream.seek(entry[-2])
            payload = stream.read(entry[-1])
            if len(payload) != entry[-1]:
                raise ValueError('short OSIP payload')
            try:
                descriptions.append(dict(payload_check(payload, entry[6]), role=role))
            except ValueError as error:
                raise ValueError(role + ': ' + str(error)) from error
    files = [{'file': header_path.name, 'bytes': HEADER_BYTES, 'sha256': digest(header_path, HEADER_BYTES)},
             {'file': reserved_path.name, 'bytes': RESERVED_BYTES, 'sha256': digest(reserved_path, RESERVED_BYTES)}]
    system_report = None
    if system_path is not None:
        size = PARTITIONS['acer-a1-840fhd']
        regular(system_path, size)
        with system_path.open('rb') as stream:
            system_report = inspect(stream, size)
        if system_report['format'] != 'raw':
            raise ValueError('raw owner system backup required')
        files.append({'file': system_path.name, 'bytes': size, 'sha256': system_report['expanded_zero_holes_sha256']})
    comparison = False
    if receipt_path is not None:
        if receipt_path.is_symlink() or not receipt_path.is_file() or receipt_path.stat().st_size > 65536:
            raise ValueError('invalid private receipt')
        receipt = json.loads(receipt_path.read_text())
        if not isinstance(receipt, dict) or not isinstance(receipt.get('files'), list) or not all(isinstance(item, dict) for item in receipt['files']):
            raise ValueError('unsupported private receipt structure')
        if any(receipt.get(key) is not True for key in ('applied', 'model_checked', 'live_layout_checked')):
            raise ValueError('not a completed owner backup receipt')
        if receipt.get('layout') != verified_layout:
            raise ValueError('receipt layout differs')
        expected = {entry['file']: entry for entry in receipt['files']}
        if len(expected) != len(receipt['files']):
            raise ValueError('duplicate receipt file')
        for actual in files:
            other = expected.get(actual['file'])
            if not other or any(other.get(key) != actual[key] for key in ('bytes', 'sha256')):
                raise ValueError('backup differs from saved receipt')
        comparison = True
    return {'device': 'acer-a1-840fhd', 'backup_structure_checked': True,
            'osip_payloads': descriptions, 'primary_gpt_checked': True,
            'system_format_checked': system_report is not None,
            'saved_receipt_checksums_matched': comparison, 'files': files,
            'device_identity_independently_verified': False,
            'filesystem_integrity_verified': False, 'contents_privacy_audited': False,
            'complete_device_backup_verified': False, 'restoration_verified': False,
            'device_io': False, 'publication_approved': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disk-header', required=True, type=Path)
    parser.add_argument('--reserved-backup', required=True, type=Path)
    parser.add_argument('--system-backup', type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--private-report', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.private_report is not None and (args.private_report.exists() or args.private_report.is_symlink() or args.private_report.resolve().is_relative_to(ROOT)):
            raise ValueError('new private report outside public repo required')
        report = verify(args.disk_header, args.reserved_backup, args.system_backup, args.receipt)
        if args.private_report is not None:
            descriptor = os.open(args.private_report, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                json.dump(report, stream, indent=2)
                stream.write('\n')
            args.private_report.chmod(0o600)
        # Never print owner file hashes, serial, GUID, command line or contents.
        summary = {key: value for key, value in report.items() if key not in ('files', 'osip_payloads')}
        summary['osip_payloads_checked'] = len(report['osip_payloads'])
        print(json.dumps(summary, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, EOFError, struct.error, zlib.error):
        print(json.dumps({'error': 'owner backup verification refused', 'device_io': False, 'restoration_verified': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
