#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate project-owned i386 GLES tail-call thunks from owner-supplied ELF.

Does not execute the library or copy its implementation. Requires readelf.
Writes only a new directory; no device access or publication approval.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

EXPECTED = '8090d2bd8775d8095167a2fe08fd0030c66a5c2e57113e56830cbcf5b51fc67c'


def symbols(text):
    names = set()
    for line in text.splitlines():
        fields = line.split()
        if len(fields) >= 8 and fields[3] == 'FUNC' and fields[4] in ('GLOBAL', 'WEAK') and fields[6] != 'UND':
            name = fields[7]
            if re.fullmatch(r'(egl|gl)[A-Z][A-Za-z0-9_]*', name):
                names.add(name)
    if not {'eglGetDisplay', 'eglInitialize', 'eglGetProcAddress', 'glDrawArrays'} <= names:
        raise ValueError('required GLES/EGL exports missing')
    if not 100 < len(names) < 5000:
        raise ValueError('unexpected export count')
    return sorted(names)


def generate(names):
    if names != sorted(set(names)) or any(not re.fullmatch(r'(egl|gl)[A-Z][A-Za-z0-9_]*', name) for name in names):
        raise ValueError('invalid symbol list')
    header = ('/* Generated from inspected Intel7 dynamic exports. SPDX-License-Identifier: Apache-2.0 */\n'
              '#pragma once\n#define ACER_GLES_SYMBOL_COUNT ' + str(len(names)) + '\n'
              'static const char *const acer_gles_symbols[] = {\n')
    header += ''.join('    "' + name + '",\n' for name in names) + '};\n'
    assembly = ('/* Generated C export thunks, measured i386 ABI. SPDX-License-Identifier: Apache-2.0 */\n'
                '#if !defined(__i386__)\n#error "Intel7 thunk ABI requires i386"\n#endif\n'
                '    .text\n    .hidden acer_gles_targets\n    .hidden acer_gles_missing\n')
    for index, name in enumerate(names):
        assembly += (f'    .p2align 4\n    .globl {name}\n    .type {name},@function\n{name}:\n'
                     f'    call .Lgles_pc_{index}\n.Lgles_pc_{index}:\n    popl %eax\n'
                     f'    addl $_GLOBAL_OFFSET_TABLE_+(. - .Lgles_pc_{index}), %eax\n'
                     f'    movl acer_gles_targets+{index * 4}@GOTOFF(%eax), %edx\n'
                     f'    testl %edx, %edx\n    jz acer_gles_missing\n    jmp *%edx\n'
                     f'    .size {name}, .-{name}\n')
    assembly += '    .section .note.GNU-stack,"",@progbits\n'
    return {'gles_symbols.h': header.encode(), 'gles_exports_x86.S': assembly.encode()}


def inspect(library, readelf='readelf'):
    if not library.is_file() or not 52 <= library.stat().st_size <= 32 * 1024 * 1024:
        raise ValueError('missing or excessive library')
    data = library.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED:
        raise ValueError('library does not match reviewed stock baseline')
    if data[:6] != b'\x7fELF\x01\x01' or struct.unpack_from('<HH', data, 16) != (3, 3):
        raise ValueError('expected little-endian i386 shared ELF')
    result = subprocess.run([readelf, '--dyn-syms', '--wide', str(library.resolve())],
                            capture_output=True, text=True, check=True, timeout=30)
    return symbols(result.stdout)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--readelf', default='readelf')
    args = parser.parse_args(argv)
    try:
        if args.output.exists() or args.output.is_symlink():
            raise ValueError('output must be new')
        names = inspect(args.library, args.readelf)
        payloads = generate(names)
        args.output.mkdir()
        for name, payload in payloads.items():
            with (args.output / name).open('xb') as stream:
                stream.write(payload)
        print(json.dumps({'exports': len(names), 'input_sha256': EXPECTED,
                          'outputs': {name: hashlib.sha256(payload).hexdigest() for name, payload in payloads.items()},
                          'device_io': False, 'runtime_verified': False, 'redistribution_approved': False}, indent=2))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError, struct.error):
        print(json.dumps({'error': 'generation refused or failed; inspect any new partial output', 'device_io': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
