#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Read only allowlisted owner stock inputs from a raw ext4 system backup.

Linux/WSL debugfs without -w; no mounts, device access, Google apps or download.
Dry-run first. Private calibration is preserved without publishing its hash.
"""
import argparse
import hashlib
import json
from pathlib import Path
import posixpath
import re
import subprocess
import sys
from import_vendor import combine, relative, transformed
from stage_firmware import AUDIO, calibration

ROOT = Path(__file__).parents[1]
CAL = 'etc/firmware/bcmdhd_aob.cal_43241_b4'
PARTITION = 1887436800


def read_ext4(image, value, depth=0):
    name = str(relative(value))
    if depth > 8:
        raise ValueError('symlink loop')
    info = subprocess.run(['debugfs', '-R', 'stat /' + name, str(image)], check=True, capture_output=True, timeout=60)
    if b'Type: symlink' in info.stdout:
        match = re.search(rb'Fast link dest: "([A-Za-z0-9_./+@-]+)"', info.stdout)
        if not match:
            raise ValueError('unsupported symlink')
        target = match[1].decode('ascii')
        if target.startswith('/system/'):
            target = target[len('/system/'):]
        elif not target.startswith('/'):
            target = posixpath.join(posixpath.dirname(name), target)
        target = posixpath.normpath(target).lstrip('/')
        return read_ext4(image, target, depth + 1)
    size = re.search(rb'\bSize:\s*(\d+)', info.stdout)
    if b'Type: regular' not in info.stdout or not size or not 0 < int(size[1]) <= 32 * 1024 * 1024:
        raise ValueError('missing or excessive stock input')
    result = subprocess.run(['debugfs', '-R', 'cat /' + name, str(image)], check=True, capture_output=True, timeout=60)
    if len(result.stdout) != int(size[1]):
        raise ValueError('short stock read')
    return result.stdout


def plan(image, manifest, reader=read_ext4):
    if manifest.get('schema') != 1 or manifest.get('device') != 'acer-a1-840fhd' or manifest.get('redistribution_approved', False):
        raise ValueError('unexpected manifest')
    payloads = {}
    for entry in manifest['files']:
        name = str(relative(entry['source']))
        if name == CAL or any(p.lower() in {'data', 'factory', 'adbkey', 'adb_keys', '.ssh'} for p in relative(name).parts):
            raise ValueError('personal/authentication input')
        if Path(name).suffix.lower() in {'.apk', '.pk8', '.pem', '.jks', '.keystore'}:
            raise ValueError('application/signing input')
        data = payloads.get(name)
        if data is None:
            data = reader(image, name)
        if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError('stock fingerprint mismatch')
        transformed(data, entry)  # Verify any later import transform now.
        payloads[name] = data
    for base, (size, digest) in AUDIO.items():
        name = 'etc/firmware/' + base
        data = reader(image, name)
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('stock DSP firmware mismatch')
        payloads[name] = data
    payloads[CAL] = calibration(reader(image, CAL))
    return payloads


def extract(image, output, manifest, apply=False):
    if not sys.platform.startswith('linux') or image.is_symlink() or not image.is_file() or image.stat().st_size != PARTITION:
        raise ValueError('regular owner raw image of supported size required')
    if output.exists() or output.is_symlink():
        raise ValueError('new output required')
    if image.resolve().is_relative_to(output.resolve()):
        raise ValueError('output overlaps input')
    with image.open('rb') as stream:
        stream.seek(1080)
        if stream.read(2) != b'\x53\xef':
            raise ValueError('raw ext4 required; sparse image is not accepted')
    payloads = plan(image, manifest)
    report = {'stock_graphics_audio_entries_verified': len(manifest['files']),
              'unique_files_planned': len(payloads), 'stock_dsp_firmware_files': len(AUDIO),
              'owner_calibration_validated': True, 'applied': False,
              'device_io': False, 'input_modified': False, 'redistribution_approved': False}
    if not apply:
        return report
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise ValueError('existing real output parent required')
    output.mkdir(mode=0o700)
    for name, data in payloads.items():
        path = output.joinpath(*relative(name).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
        path.chmod(0o600)
    report['applied'] = True
    # Only counts/status, never calibration values, fingerprints or host IDs.
    with (output / 'owner-extraction-receipt.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--system-image', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        manifests = [json.loads((ROOT / 'vendor-inputs' / name).read_text()) for name in ('graphics-stock.json', 'audio-stock.json')]
        manifest = combine(manifests, 'acer-a1-840fhd')
        print(json.dumps(extract(args.system_image, args.output, manifest, args.apply), indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print(json.dumps({'error': 'owner extraction refused; preserve any new partial output', 'device_io': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
