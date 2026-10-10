#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Create a separate PIC candidate from the exact reviewed stock resampler.

No device access, execution of the library or publication approval. The input
and resulting output fingerprints are mandatory even with Python -O.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

INPUT_SHA = 'f37a5cdef70a797da053b952153bd1c80b6bb0724ed0205cc09416117719765d'
OUTPUT_SHA = '61acc00630b8ebd24dd9493afccf458f8bc0f33275936f239a8db5aa3146d8cb'
SIZE = 791236


def prepare(data):
    if len(data) != SIZE or hashlib.sha256(data).hexdigest() != INPUT_SHA:
        raise ValueError('resampler does not match reviewed stock input')
    image = bytearray(data)
    u32 = lambda offset: struct.unpack_from('<I', image, offset)[0]
    phoff = u32(28)
    phsize, phnum = struct.unpack_from('<HH', image, 42)
    headers = [(phoff + i * phsize, struct.unpack_from('<8I', image, phoff + i * phsize)) for i in range(phnum)]
    rx_offset, rx = next((offset, header) for offset, header in headers if header[0] == 1 and header[6] == 5)
    dynamic = next(header for _, header in headers if header[0] == 2)
    entries = []
    for offset in range(dynamic[1], dynamic[1] + dynamic[4], 8):
        tag, value = struct.unpack_from('<II', image, offset)
        if not tag:
            break
        entries.append((tag, value))
    tags = dict(entries)
    relocations = [struct.unpack_from('<II', image, offset) for offset in range(tags[17], tags[17] + tags[18], 8)]
    # Project-written CALL/POP + GOT tail jump preserves EBX, the original
    # caller arguments and return address. Executable pages remain non-writable.
    thunk_address = 0xbf1e0
    thunk = bytes.fromhex('e800000000588b80') + struct.pack('<i', 0xc0fe0 - (thunk_address + 5)) + bytes.fromhex('ffe0')
    image[thunk_address:thunk_address + len(thunk)] = thunk
    struct.pack_into('<i', image, 0xf8b, thunk_address - 0xf8f)
    struct.pack_into('<I', image, rx_offset + 16, rx[4] + len(thunk))
    struct.pack_into('<I', image, rx_offset + 20, rx[5] + len(thunk))
    kept = [entry for entry in relocations if entry != (0xf8b, 0x502)]
    for index, entry in enumerate(kept):
        struct.pack_into('<II', image, tags[17] + index * 8, *entry)
    image[tags[17] + len(kept) * 8:tags[17] + tags[18]] = bytes(8)
    updated = [(tag, len(kept) * 8 if tag == 18 else value & ~4 if tag == 30 else value)
               for tag, value in entries if tag != 22]
    image[dynamic[1]:dynamic[1] + dynamic[4]] = bytes(dynamic[4])
    for index, entry in enumerate(updated):
        struct.pack_into('<II', image, dynamic[1] + index * 8, *entry)
    shoff = u32(32)
    shsize, shnum = struct.unpack_from('<HH', image, 46)
    for index in range(shnum):
        offset = shoff + index * shsize
        if u32(offset + 4) == 9 and u32(offset + 16) == tags[17]:
            struct.pack_into('<I', image, offset + 20, len(kept) * 8)
    result = bytes(image)
    if len(result) != SIZE or hashlib.sha256(result).hexdigest() != OUTPUT_SHA:
        raise ValueError('unexpected prepared resampler output')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.output.exists() or args.output.is_symlink() or args.input.resolve() == args.output.resolve():
            raise ValueError('output must be new and separate')
        if not args.input.is_file() or args.input.stat().st_size != SIZE:
            raise ValueError('missing or wrong-size input')
        result = prepare(args.input.read_bytes())
        with args.output.open('xb') as stream:
            stream.write(result)
        print(json.dumps({'input_sha256': INPUT_SHA, 'output_sha256': OUTPUT_SHA,
                          'bytes': SIZE, 'device_io': False, 'runtime_verified': False,
                          'redistribution_approved': False}, indent=2))
        return 0
    except (ValueError, OSError, struct.error, StopIteration):
        print(json.dumps({'error': 'resampler preparation refused or failed; inspect any new partial output', 'device_io': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
