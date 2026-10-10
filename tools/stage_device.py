#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stage the reviewed Acer device sources into an empty device-tree destination.

Dry-run by default. Requires separately generated GLES bridge inputs.
Does not supply vendor blobs, package a boot image, build or contact a device.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).parents[1]
GENERATED = {'gles_symbols.h': '791b8ea2ec3740585d38b090c6d4139a2d7fd9143a01b8966bb33c3bc6319d22',
             'gles_exports_x86.S': '7e9ddd21ac83330f429d2e0bffe7e6e090717857d2b5465d26ef604cc313efd0'}


def relative(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError('invalid device source path')
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or '..' in path.parts or '.git' in path.parts or str(path) != value:
        raise ValueError('unsafe device source path')
    return path


def stage(source, generated, apply=False, root=ROOT):
    source = source.resolve(strict=True)
    if not (source / 'build/envsetup.sh').is_file():
        raise ValueError('not an Android source workspace')
    output = source / 'device/acer/ducati2fhd'
    if output.exists() or output.is_symlink():
        raise ValueError('device destination must not exist')
    for parent in (source / 'device', source / 'device/acer'):
        if parent.is_symlink():
            raise ValueError('symlink source parent refused')
    index = json.loads((root / 'source/acer-device-provenance.json').read_text())
    if index['schema'] != 1 or index['device'] != 'acer-a1-840fhd':
        raise ValueError('unexpected source index')
    planned = {}
    for entry in index['files']:
        name = str(relative(entry['path']))
        path = root / 'source/device/acer/ducati2fhd' / name
        if name in planned or path.is_symlink() or not path.is_file():
            raise ValueError('invalid indexed source')
        data = path.read_bytes()
        if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError('published source fingerprint mismatch')
        planned[name] = data
    for name, expected in GENERATED.items():
        path = generated / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('invalid generated GLES source')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('generated GLES fingerprint mismatch')
        planned['legacy-hwc/' + name] = data
    if apply:
        # Exclusive creation after complete preflight. A partial new destination
        # is retained if writing fails; no user-tree reset or automatic deletion.
        output.mkdir(parents=True)
        for name, data in planned.items():
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(data)
    return {'device': 'acer-a1-840fhd', 'files_preflighted': len(planned),
            'dry_run': not apply, 'device_sources_staged': apply,
            'vendor_complete': False, 'rom_built': False, 'device_io': False,
            'image_publication_approved': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--generated-gles', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(stage(args.source, args.generated_gles, args.apply), indent=2))
        return 0
    except (ValueError, OSError, KeyError):
        print(json.dumps({'error': 'device source staging refused or failed; preserve any new partial destination',
                          'device_io': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
