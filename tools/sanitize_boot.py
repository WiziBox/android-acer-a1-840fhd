#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Create a separate unsigned boot candidate without personal ADB approvals.

Never flashes a device or approves publication. Originals and existing outputs
are never overwritten. Unsupported signatures/layouts and remaining key
findings cause refusal before output creation.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct
import sys
import zlib

from audit_boot import MAX_IMAGE, align, audit_bytes, cpio_entries, ramdisk_from_boot

APPROVAL_NAMES = {'adb_keys', 'adbkey.pub'}


def clean_archive(raw):
    # Validate every member and the complete trailer before constructing output.
    list(cpio_entries(raw))
    result = bytearray()
    removed = []
    changed = []
    position = 0
    found_properties = False
    while True:
        header = raw[position:position + 110]
        fields = [int(header[6 + i * 8:14 + i * 8], 16) for i in range(13)]
        size, name_size = fields[6], fields[11]
        encoded = raw[position + 110:position + 110 + name_size]
        name = str(PurePosixPath(encoded[:-1].decode('utf-8')))
        start = align(position + 110 + name_size, 4)
        data = raw[start:start + size]
        position = align(start + size, 4)
        if name == 'TRAILER!!!':
            result += header + encoded
            result += bytes((-len(result)) % 4)
            break
        if PurePosixPath(name).name.lower() in APPROVAL_NAMES:
            if fields[4] != 1:
                raise ValueError('hard-linked approval file is unsupported')
            removed.append(name)
            continue
        if name == 'default.prop':
            if fields[1] & 0o170000 != 0o100000 or fields[4] != 1:
                raise ValueError('default.prop must be a non-hard-linked regular file')
            found_properties = True
            original = data
            for prop in (b'ro.adb.secure', b'ro.secure'):
                pattern = rb'(?m)^[ \t]*' + re.escape(prop) + rb'[ \t]*=[^\r\n]*'
                data, count = re.subn(pattern, prop + b'=1', data)
                if not count:
                    data = data.rstrip(b'\r\n') + b'\n' + prop + b'=1\n'
            if data != original:
                changed.append(name)
                fields[6] = len(data)
                fields[12] = sum(data) & 0xffffffff if header[:6] == b'070702' else 0
                header = header[:6] + b''.join(f'{value:08x}'.encode() for value in fields)
        result += header + encoded
        result += bytes((-len(result)) % 4)
        result += data
        result += bytes((-len(result)) % 4)
    if not found_properties:
        raise ValueError('missing default.prop; no implicit archive insertion')
    return bytes(result), removed, changed


def repackage(image, compressed, device):
    if device == 'acer-a1-840fhd':
        # One unsigned OSIP image descriptor, matching the known Acer container.
        if image[8:10] != b'\x01\x01' or struct.unpack_from('<H', image, 10)[0] != 56 or image[52] != 1:
            raise ValueError('unsupported or signed OSIP descriptor')
        kernel_size, old_size = struct.unpack_from('<II', image, 512 + 0x400)
        start = 0x3200 + kernel_size
        if any(image[start + old_size:]):
            raise ValueError('unknown OSIP trailer/signature')
        result = bytearray(image[:start]) + compressed
        result += bytes((-len(result)) % 512)
        struct.pack_into('<I', result, 512 + 0x404, len(compressed))
        struct.pack_into('<I', result, 0x30, (len(result) - 512) // 512)
        result[7] = 0
        checksum = 0
        for byte in result[:56]:
            checksum ^= byte
        result[7] = checksum
        # Compare every preserved byte, allowing only the three sizing/checksum fields.
        check = bytearray(result[:start])
        for offset, count in ((7, 1), (0x30, 4), (512 + 0x404, 4)):
            check[offset:offset + count] = image[offset:offset + count]
        if check != image[:start]:
            raise ValueError('OSIP stub/kernel preservation failed')
        preserved = {'kernel_allocation_sha256': hashlib.sha256(image[0x3200:start]).hexdigest()}
    else:
        raise ValueError('unsupported device')
    if len(result) > MAX_IMAGE:
        raise ValueError('sanitized image exceeds size limit')
    return bytes(result), preserved


def sanitize(image, device):
    _, raw = ramdisk_from_boot(image, device)
    cleaned, removed, changed = clean_archive(raw)
    # gzip mtime is fixed; source paths or hostnames are never put in its header.
    result, preserved = repackage(image, gzip.compress(cleaned, mtime=0), device)
    report = audit_bytes(result, device)
    if not report['boot_key_audit_passed']:
        raise ValueError('remaining key/security findings; output refused')
    report.update({'removed_entries': removed, 'changed_entries': changed,
                   'preserved_payloads': preserved, 'bootability_verified': False})
    return result, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device', required=True, choices=['acer-a1-840fhd'])
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if not args.input.is_file() or args.input.stat().st_size > MAX_IMAGE:
            raise ValueError('missing input or excessive size')
        if args.output.exists() or args.input.resolve() == args.output.resolve():
            raise ValueError('output must be a new file distinct from input')
        result, report = sanitize(args.input.read_bytes(), args.device)
        # Exclusive creation prevents a race from overwriting a user's file.
        with args.output.open('xb') as stream:
            stream.write(result)
        print(json.dumps(report, indent=2))
        return 0
    except (ValueError, OSError, EOFError, struct.error, zlib.error):
        # Avoid OS exception text exposing local paths or any artifact contents.
        print(json.dumps({'error': 'sanitization refused or output write failed',
                          'publication_approved': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
