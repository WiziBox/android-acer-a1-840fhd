#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stage owner firmware/calibration and the matching newly built Wi-Fi module.

Dry-run by default. Preserves calibration bytes; never prints their contents.
This produces private build inputs, not publication-approved ROM contents.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from build_kernel import require_signatures

ROOT = Path(__file__).parents[1]
AUDIO = {
    'fw_sst_0f28.bin': (851244, '37c1b225972d7f16b5b633ef58776a00f9bc242b68716876fafdf3536d9abed0'),
    'aac_dec_0f28.bin': (203804, 'c0ead6b124647983f070e26534513380c12207a2e0c71c6c49bc556a0fc68838'),
    'mp3_dec_0f28.bin': (101578, '0ac060b0a2603011c1badf3bb590cb8c25c6d145a8c473f31b0c5dcd072cf9a6'),
}
WIFI_SHA = '0e53e2eadb22610c298df18b631f571d216a3eca3d537812a6f074337fb38eca'
BUILD_PATHS = {'kernel': 'obj/arch/x86/boot/bzImage', 'wifi_module': 'wifi/bcm43241.ko',
               'config': 'obj/.config', 'public_certificate': 'obj/signing_key.x509'}


def read_checked(path, size=None, expected=None, limit=16 * 1024 * 1024):
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= limit:
        raise ValueError('missing or unsafe firmware input')
    data = path.read_bytes()
    if size is not None and len(data) != size:
        raise ValueError('input size mismatch')
    if expected is not None and hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('input fingerprint mismatch')
    return data


def calibration(data):
    if not 0 < len(data) <= 65536 or b'\0' in data:
        raise ValueError('invalid calibration size/encoding')
    text = data.decode('ascii')
    if re.search(r'(?im)^\s*(?:ssid|psk|password|passwd|passphrase)\s*=|\bnetwork\s*=\s*\{', text):
        raise ValueError('saved networks and credentials are not calibration')
    if 'PRIVATE KEY' in text or 'adbkey' in text or 'adb_keys' in text:
        raise ValueError('authentication material is not calibration')
    fields = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            raise ValueError('invalid calibration line')
        key, value = line.split('=', 1)
        if key in fields:
            raise ValueError('duplicate calibration field')
        fields[key] = value.strip()
    for key, expected in {'boardtype': '0x5ef', 'boardrev': '0x1100', 'sromrev': '9'}.items():
        if fields.get(key) != expected:
            raise ValueError('calibration does not match reviewed board profile')
    if 'macaddr' in fields and not re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', fields['macaddr']):
        raise ValueError('invalid calibration MAC syntax')
    # Do not rewrite MAC, country, RF power or calibration values.
    return data


def stage(source, stock, kernel_build, wifi, nvram, apply=False):
    source = source.resolve(strict=True)
    vendor = source / 'vendor/acer/ducati2fhd'
    if not (source / 'device/acer/ducati2fhd/BoardConfig.mk').is_file() or not (vendor / 'vendor-stock.mk').is_file():
        raise ValueError('device/stock staging must precede firmware staging')
    if vendor.is_symlink() or source not in vendor.resolve().parents:
        raise ValueError('unsafe vendor destination')
    wifi_out = vendor / 'wifi'
    audio_out = vendor / 'audio-deployment'
    if wifi_out.exists() or wifi_out.is_symlink() or audio_out.is_symlink():
        raise ValueError('firmware destination is already present or unsafe')
    receipt_path = vendor / 'firmware-staging-receipt.json'
    if receipt_path.exists() or receipt_path.is_symlink():
        raise ValueError('firmware receipt already exists')
    build = json.loads((kernel_build / 'build-receipt.json').read_text())
    index = json.loads((ROOT / 'kernel/inputs.json').read_text())
    if not build.get('kernel_and_wifi_built') or build['source_patch_sha256'] != index['patch_sha256'] or build['toolchain_commit'] != index['toolchain']['commit']:
        raise ValueError('kernel build does not match public source inputs')
    artifacts = {}
    for name, relative in BUILD_PATHS.items():
        record = build['artifacts'][name]
        if record['path'] != relative:
            raise ValueError('unexpected kernel build artifact path')
        artifacts[name] = read_checked(kernel_build / relative, record['bytes'], record['sha256'])
    require_signatures(artifacts['config'].decode())
    if hashlib.sha256(artifacts['config']).hexdigest() != index['config_sha256']:
        raise ValueError('kernel configuration differs from reviewed baseline')
    if artifacts['kernel'][0x202:0x206] != b'HdrS' or not artifacts['wifi_module'].startswith(b'\x7fELF\x01') or not artifacts['wifi_module'].endswith(b'~Module signature appended~\n'):
        raise ValueError('unsupported kernel or unsigned/non-ELF32 module')
    planned = {'wifi/fw_bcmdhd.bin_43241_b4': read_checked(wifi, expected=WIFI_SHA),
               'wifi/bcmdhd_aob.cal_43241_b4': calibration(read_checked(nvram, limit=65536)),
               'wifi/bcm43241.ko': artifacts['wifi_module']}
    for name, (size, expected) in AUDIO.items():
        destination = 'audio-deployment/' + name
        target = vendor / destination
        if target.exists() or target.is_symlink():
            raise ValueError('audio firmware destination already exists')
        planned[destination] = read_checked(stock / 'etc/firmware' / name, size, expected)
    report = {'schema': 1, 'device': 'acer-a1-840fhd', 'files_verified': len(planned),
              'dry_run': not apply, 'firmware_staged': apply,
              'kernel_sha256': build['artifacts']['kernel']['sha256'],
              'wifi_module_sha256': build['artifacts']['wifi_module']['sha256'],
              'calibration_preserved': True, 'calibration_contents_logged': False,
              'private_build_inputs': True, 'device_io': False,
              'image_publication_approved': False}
    if apply:
        # All inputs and outputs were preflighted; create only new destinations.
        # Partial new files are retained on failure; never reset/delete a tree.
        wifi_out.mkdir(mode=0o700)
        audio_out.mkdir(exist_ok=True)
        for name, data in planned.items():
            with (vendor / name).open('xb') as stream:
                stream.write(data)
        (wifi_out / 'bcmdhd_aob.cal_43241_b4').chmod(0o600)
        with receipt_path.open('x') as stream:
            json.dump(report, stream, indent=2)
            stream.write('\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--stock-system', required=True, type=Path)
    parser.add_argument('--kernel-build', required=True, type=Path)
    parser.add_argument('--wifi-firmware', required=True, type=Path)
    parser.add_argument('--nvram', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(stage(args.source, args.stock_system, args.kernel_build,
                               args.wifi_firmware, args.nvram, args.apply), indent=2))
        return 0
    except (ValueError, OSError, KeyError, UnicodeError):
        print(json.dumps({'error': 'firmware staging refused or failed; preserve any new partial inputs',
                          'device_io': False, 'image_publication_approved': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
