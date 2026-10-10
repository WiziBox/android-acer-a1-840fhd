#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify and stage explicitly listed owner-supplied stock inputs.

Dry-run by default. Never contacts a tablet, downloads blobs, modifies a
live device or permits redistribution. Does not import source-built libraries.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile

MAX_FILE = 128 * 1024 * 1024


def relative(value):
    if not isinstance(value, str) or not value or not re.fullmatch(r'[A-Za-z0-9_./+@-]+', value):
        raise ValueError('invalid relative path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or str(path) != value or '.git' in path.parts:
        raise ValueError('unsafe relative path')
    return path


def validate(manifest, root, device):
    if manifest.get('schema') != 1 or manifest.get('device') != device:
        raise ValueError('manifest schema/device mismatch')
    if not root.is_dir():
        raise ValueError('input root missing')
    root = root.resolve()
    files = manifest.get('files')
    if not isinstance(files, list) or not files:
        raise ValueError('empty input list')
    destinations = set()
    installs = set()
    planned = []
    for entry in files:
        source = relative(entry['source'])
        destination = relative(entry['destination'])
        install = relative(entry['install'])
        if install.parts[0] != 'system':
            raise ValueError('unsupported install partition')
        if str(destination).lower() in destinations or str(install).lower() in installs:
            raise ValueError('duplicate destination')
        destinations.add(str(destination).lower())
        installs.add(str(install).lower())
        expected = entry['sha256']
        if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
            raise ValueError('invalid checksum')
        size = entry['bytes']
        if type(size) is not int or not 0 < size <= MAX_FILE:
            raise ValueError('invalid input size')
        path = root.joinpath(*source.parts)
        if not path.resolve().is_relative_to(root) or not path.is_file() or path.stat().st_size != size:
            raise ValueError('missing, unsafe or wrong-size input')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('input checksum mismatch')
        # Source path values belong to a reviewed allowlist; block obvious
        # personal/authentication/application inputs even in a custom manifest.
        if any(part.lower() in {'data', 'factory', 'adb_keys', 'adbkey', 'adbkey.pub', '.ssh'} for part in source.parts):
            raise ValueError('personal/authentication input is forbidden')
        if source.suffix.lower() in {'.apk', '.pk8', '.pem', '.priv', '.jks', '.keystore'}:
            raise ValueError('application/signing input is forbidden')
        planned.append((path, destination, install, expected, size))
    return planned


def import_inputs(manifest, root, output, device, apply=False):
    planned = validate(manifest, root, device)
    if output.exists() or output.is_symlink():
        raise ValueError('output must be a new directory')
    source_root = root.resolve()
    target = output.resolve()
    if target.is_relative_to(source_root) or source_root.is_relative_to(target):
        raise ValueError('input and output directories must be separate')
    report = {'device': device, 'files_verified': len(planned), 'applied': False,
              'complete_vendor_tree': False, 'device_io': False, 'redistribution_approved': False,
              'source_built_inputs_remaining': manifest.get('source_built_inputs', [])}
    if not apply:
        return report
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise ValueError('output parent must be an existing real directory')
    with tempfile.TemporaryDirectory(prefix='.vendor-stage-', dir=output.parent) as folder:
        staging = Path(folder) / 'inputs'
        staging.mkdir()
        for source, destination, _, expected, size in planned:
            # Recheck bytes during copying; do not accept a changed source.
            data = source.read_bytes()
            if len(data) != size or hashlib.sha256(data).hexdigest() != expected:
                raise ValueError('input changed after preflight')
            path = staging.joinpath(*destination.parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(data)
        with (staging / 'import-receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
            json.dump({'schema': 1, 'device': device, 'files': manifest['files'],
                       'redistribution_approved': False}, stream, indent=2)
            stream.write('\n')
        # mkdir is exclusive. An output appearing during preflight is never
        # merged with, emptied or overwritten. Failure leaves explicit partial
        # output rather than deleting a user's directory.
        output.mkdir()
        for path in staging.iterdir():
            shutil.move(str(path), str(output / path.name))
    report['applied'] = True
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path(__file__).parents[1] / 'vendor-inputs/graphics-stock.json')
    parser.add_argument('--input-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', choices=['acer-a1-840fhd'], required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
        report = import_inputs(manifest, args.input_root, args.output, args.device, args.apply)
        print(json.dumps(report, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError):
        print(json.dumps({'error': 'vendor import refused or failed; inspect any new output before retrying',
                          'device_io': False, 'redistribution_approved': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
