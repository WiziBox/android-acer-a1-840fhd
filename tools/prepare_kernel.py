#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare reviewed Acer kernel sources in a new directory (Python 3.12+).

Uses the exact official archive, preserved source licenses and the reviewed
port patch. No build, key generation, device access or flashing is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import zipfile

ROOT = Path(__file__).parents[1]
NOTICE = 'Modified for the WiziBox Android 9 port on 2026-10-11; original license/copyright notices retained.'


def relative(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError('invalid source path')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or str(path) != value or path.parts[0] != 'kernel':
        raise ValueError('unsafe source path')
    return path


def file_sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def modification_notice(path, data):
    if path.suffix in {'.c', '.h'}:
        return ('/* ' + NOTICE + ' */\n').encode() + data
    if path.name in {'Makefile', 'Kconfig'} or path.suffix == '.tbl':
        return ('# ' + NOTICE + '\n').encode() + data
    # Auxiliary JSON provenance is not compiled source. Its modification
    # record remains in the published input index and preparation receipt.
    if path.suffix == '.json':
        return data
    raise ValueError('unreviewed source type for modification notice')


def prepare(archive_path, output, kernel_dir=ROOT / 'kernel'):
    if not callable(getattr(tarfile, 'data_filter', None)):
        raise ValueError('Python 3.12+ with tar data filtering is required')
    if output.exists() or output.is_symlink():
        raise ValueError('output must be a new directory')
    index = json.loads((kernel_dir / 'inputs.json').read_text(encoding='utf-8'))
    if index['schema'] != 1 or not archive_path.is_file() or archive_path.stat().st_size != index['archive_bytes']:
        raise ValueError('missing or wrong-size official archive')
    if file_sha(archive_path) != index['archive_sha256']:
        raise ValueError('official archive checksum mismatch')
    patch = kernel_dir / 'kernel-port.patch'
    if file_sha(patch) != index['patch_sha256'] or file_sha(kernel_dir / 'ducati2fhd.config') != index['config_sha256']:
        raise ValueError('published patch/config checksum mismatch')
    for change in index['changes']:
        relative(change['path'])
    output.mkdir()
    with zipfile.ZipFile(archive_path) as outer:
        with outer.open(index['archive_member']) as stream, tarfile.open(fileobj=stream, mode='r|gz') as source:
            count = 0
            for member in source:
                if member.name != 'kernel_src' and not member.name.startswith('kernel_src/'):
                    raise ValueError('unexpected archive root')
                if member.size > 128 * 1024 * 1024:
                    raise ValueError('excessive archive member')
                source.extract(member, path=output, filter='data')
                count += 1
                if count > 100000:
                    raise ValueError('excessive source archive entries')
    tree = output / 'kernel_src'
    for change in index['changes']:
        path = tree / change['path']
        expected = change['base_sha256']
        if expected is None:
            if path.exists() or path.is_symlink():
                raise ValueError('unexpected existing new-file input')
        elif not path.is_file() or path.is_symlink() or file_sha(path) != expected:
            raise ValueError('kernel baseline file checksum mismatch')
    subprocess.run(['git', 'apply', '--check', str(patch.resolve())], cwd=tree, check=True, capture_output=True)
    subprocess.run(['git', 'apply', str(patch.resolve())], cwd=tree, check=True, capture_output=True)
    prepared = []
    for change in index['changes']:
        path = tree / change['path']
        if not path.is_file() or file_sha(path) != change['result_sha256']:
            raise ValueError('patched source fingerprint mismatch')
        data = modification_notice(path, path.read_bytes())
        # Newly created preparation tree only; no existing development files.
        path.write_bytes(data)
        prepared.append({'path': change['path'], 'sha256': hashlib.sha256(data).hexdigest()})
    report = {'schema': 1, 'modified_files_verified': len(prepared), 'source_files': prepared,
              'archive_sha256': index['archive_sha256'], 'patch_sha256': index['patch_sha256'],
              'modification_notice': NOTICE, 'source_prepared': True, 'clean_build_verified': False,
              'device_io': False, 'image_publication_approved': False}
    with (output / 'kernel-source-receipt.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = prepare(args.archive, args.output)
        print(json.dumps({key: value for key, value in report.items() if key != 'source_files'}, indent=2))
        return 0
    except (ValueError, OSError, KeyError, tarfile.TarError, zipfile.BadZipFile, subprocess.SubprocessError):
        print(json.dumps({'error': 'kernel preparation refused or failed; preserve and inspect any partial output', 'device_io': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
