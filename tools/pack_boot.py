#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Create an unsigned Acer OSIP candidate from an owner template and new inputs.

Offline only. This is a Droidboot container, never a raw disk/partition image.
No signature forgery, boot acceptance, device write or publication approval.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zlib
from audit_boot import MAX_IMAGE, align, audit_bytes, ramdisk_from_boot, cpio_entries

MAX_PAYLOAD = 32000 * 512
GEOMETRY = (36050, 0x1100000, 0x1101000)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def template_prefix(template):
    if len(template) < 0x3200 or len(template) > MAX_IMAGE or template[:4] != b'$OS$':
        raise ValueError('expected single-image OSIP container')
    if template[8:10] != b'\x01\x01' or struct.unpack_from('<H', template, 10)[0] != 56 or any(template[56:512]):
        raise ValueError('unsupported OSIP table or raw disk data')
    checksum = 0
    for byte in template[:56]:
        checksum ^= byte
    if checksum or len(template) != 512 + struct.unpack_from('<I', template, 0x30)[0] * 512:
        raise ValueError('OSIP checksum/length mismatch')
    if struct.unpack_from('<III', template, 0x24) != GEOMETRY:
        raise ValueError('template does not match reviewed Acer boot geometry')
    attribute = template[52]
    if attribute not in (0, 1):
        raise ValueError('not the supported Android boot descriptor')
    offset = 512
    if attribute == 0:
        if template[offset:offset + 4] != b'$OSM':
            raise ValueError('unknown signed wrapper')
        offset += 0x400
    prefix = template[offset:offset + 0x3000]
    if len(prefix) != 0x3000 or b'androidboot.hardware=ducati2fhd' not in prefix[:0x400]:
        raise ValueError('wrong bootstub hardware command line')
    if b'androidboot.serialno=' in prefix[:0x400] or re.search(rb'-----BEGIN .*KEY-----', prefix):
        raise ValueError('personal/authentication data in preserved prefix')
    old_kernel, old_ramdisk = struct.unpack_from('<II', prefix, 0x400)
    start = offset + 0x3000
    end = start + old_kernel + old_ramdisk
    if not old_kernel or old_kernel % 4096 or not old_ramdisk or end > len(template) or any(template[end:]):
        raise ValueError('unsupported template allocation/trailer')
    if template[start + 0x202:start + 0x206] != b'HdrS':
        raise ValueError('invalid template kernel')
    # Validate the original ramdisk/container layout without requiring its old
    # ADB policy: none of that ramdisk is copied into the new candidate.
    inspection = bytearray(template[:512]) + prefix + template[start:end]
    inspection += bytes((-len(inspection)) % 512)
    inspection[52] = 1
    struct.pack_into('<I', inspection, 0x30, (len(inspection) - 512) // 512)
    inspection[7] = 0
    for byte in inspection[:56]:
        inspection[7] ^= byte
    _, original_archive = ramdisk_from_boot(bytes(inspection), 'acer-a1-840fhd')
    list(cpio_entries(original_archive))
    return prefix, attribute


def pack(template, kernel, ramdisk):
    prefix, attribute = template_prefix(template)
    if not 0x206 <= len(kernel) <= MAX_PAYLOAD or kernel[0x202:0x206] != b'HdrS':
        raise ValueError('expected x86 bzImage')
    if not ramdisk or len(ramdisk) > MAX_PAYLOAD or ramdisk[:2] != b'\x1f\x8b':
        raise ValueError('expected gzip ramdisk')
    kernel_size = align(len(kernel), 4096)
    changed = bytearray(prefix)
    struct.pack_into('<II', changed, 0x400, kernel_size, len(ramdisk))
    payload = bytes(changed) + kernel + bytes(kernel_size - len(kernel)) + ramdisk
    payload += bytes((-len(payload)) % 512)
    if len(payload) > MAX_PAYLOAD:
        raise ValueError('candidate exceeds conservative validated payload bound')
    header = bytearray(template[:512])
    header[52] = 1  # Unsigned new content; never retain an old signed wrapper.
    struct.pack_into('<I', header, 0x30, len(payload) // 512)
    header[7] = 0
    for byte in header[:56]:
        header[7] ^= byte
    result = bytes(header) + payload
    audit = audit_bytes(result, 'acer-a1-840fhd')
    if not audit['boot_key_audit_passed']:
        raise ValueError('new ramdisk fails authentication/key audit')
    check = bytearray(changed)
    check[0x400:0x408] = prefix[0x400:0x408]
    if check != prefix or result[0x3200:0x3200 + len(kernel)] != kernel:
        raise ValueError('payload preservation failed')
    return result, {'schema': 1, 'bytes': len(result), 'sha256': digest(result),
                    'kernel_sha256': digest(kernel), 'ramdisk_sha256': digest(ramdisk),
                    'stub_preserved_except_size_fields': True,
                    'signed_wrapper_removed': attribute == 0,
                    'unsigned_descriptor': True, 'boot_key_audit_passed': True,
                    'bootability_verified': False, 'device_io': False,
                    'whole_rom_audited': False, 'publication_approved': False}


def bounded(path):
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_IMAGE:
        raise ValueError('missing or excessive input')
    return path.read_bytes()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', required=True, type=Path)
    parser.add_argument('--kernel', required=True, type=Path)
    parser.add_argument('--ramdisk', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('output must be new')
        image, report = pack(bounded(args.template), bounded(args.kernel), bounded(args.ramdisk))
        with args.output.open('xb') as stream:
            stream.write(image)
        print(json.dumps(report, indent=2))
        return 0
    except (ValueError, OSError, EOFError, struct.error, zlib.error):
        print(json.dumps({'error': 'OSIP packing refused or failed', 'device_io': False, 'publication_approved': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
