#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build the prepared Acer kernel and matching signed Wi-Fi module on Linux.

Requires a new output directory. No device access or image publication.
Private signing material is generated locally and must never be uploaded.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).parents[1]


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def require_signatures(config):
    lines = set(config.splitlines())
    required = {'CONFIG_MODULE_SIG=y', 'CONFIG_MODULE_SIG_FORCE=y',
                'CONFIG_MODULE_SIG_ALL=y', 'CONFIG_MODULE_SIG_SHA256=y'}
    if not required.issubset(lines):
        raise ValueError('module signature enforcement must remain enabled')


def preflight(source, toolchain, output, jobs):
    if jobs < 1 or jobs > 64:
        raise ValueError('jobs must be between 1 and 64')
    if output.exists() or output.is_symlink():
        raise ValueError('output must be a new directory')
    source = source.resolve(strict=True)
    toolchain = toolchain.resolve(strict=True)
    output = output.absolute()
    if source == output or source in output.parents or toolchain in output.parents:
        raise ValueError('output must be outside source/toolchain')
    index = json.loads((ROOT / 'kernel/inputs.json').read_text())
    receipt = json.loads((source / 'kernel-source-receipt.json').read_text())
    if receipt['archive_sha256'] != index['archive_sha256'] or receipt['patch_sha256'] != index['patch_sha256']:
        raise ValueError('source receipt mismatch')
    records = receipt['source_files']
    if {item['path'] for item in records} != {item['path'] for item in index['changes']}:
        raise ValueError('incomplete source receipt')
    for item in records:
        path = source / 'kernel_src' / item['path']
        if path.is_symlink() or sha(path) != item['sha256']:
            raise ValueError('prepared source was changed')
    config = ROOT / 'kernel/ducati2fhd.config'
    if sha(config) != index['config_sha256']:
        raise ValueError('configuration checksum mismatch')
    require_signatures(config.read_text())
    revision = subprocess.check_output(['git', '-C', str(toolchain), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != index['toolchain']['commit']:
        raise ValueError('wrong toolchain revision')
    if subprocess.check_output(['git', '-C', str(toolchain), 'status', '--porcelain'], text=True).strip():
        raise ValueError('toolchain must be clean')
    compiler = toolchain / 'bin/i686-linux-android-gcc'
    if not compiler.is_file():
        raise ValueError('missing compiler')
    return source, toolchain, output, index


def build(source, toolchain, output, jobs):
    if sys.platform != 'linux':
        raise ValueError('Linux/WSL is required')
    source, toolchain, output, index = preflight(source, toolchain, output, jobs)
    for name in ('make', 'gcc', 'openssl', 'perl', 'bc'):
        if not shutil.which(name):
            raise ValueError('missing host build dependency: ' + name)
    output.mkdir(mode=0o700)
    obj = output / 'obj'
    obj.mkdir(mode=0o700)
    shutil.copyfile(ROOT / 'kernel/ducati2fhd.config', obj / '.config')
    kernel = source / 'kernel_src/kernel'
    module = output / 'wifi'
    shutil.copytree(source / 'kernel_src/modules/wlan/PRIVATE/bcm43xx/src', module, symlinks=True)
    env = os.environ.copy()
    env.update({'KBUILD_BUILD_USER': 'WiziBox', 'KBUILD_BUILD_HOST': 'portable-build',
                'KBUILD_BUILD_TIMESTAMP': 'Sun Oct 11 00:00:00 UTC 2026'})
    command = ['make', '-C', str(kernel), 'O=' + str(obj), 'ARCH=x86',
               'CROSS_COMPILE=' + str(toolchain / 'bin/i686-linux-android-'),
               'HOSTCFLAGS=-O2 -fcommon', 'KCFLAGS=-mfpmath=387']
    with (output / 'build.log').open('x') as log:
        def run(args):
            subprocess.run(args, check=True, stdout=log, stderr=subprocess.STDOUT, env=env)
        run(command + ['olddefconfig'])
        require_signatures((obj / '.config').read_text())
        run(command + ['-j' + str(jobs), 'bzImage', 'modules'])
        run(command + ['M=' + str(module), 'CONFIG_BCMDHD=m', 'CONFIG_BCM43241=y',
                       'CONFIG_DHD_USE_SCHED_SCAN=y', 'TARGET_BUILD_VARIANT=userdebug',
                       'TARGET_PRODUCT=ducati2fhd', '-j' + str(jobs), 'modules'])
        # The generated key is embedded in this kernel; use only this build's key.
        (obj / 'signing_key.priv').chmod(0o600)
        run([str(kernel / 'scripts/sign-file'), 'sha256', str(obj / 'signing_key.priv'),
             str(obj / 'signing_key.x509'), str(module / 'bcm43241.ko')])
    artifacts = {'kernel': obj / 'arch/x86/boot/bzImage', 'wifi_module': module / 'bcm43241.ko',
                 'config': obj / '.config', 'public_certificate': obj / 'signing_key.x509'}
    report = {'schema': 1, 'kernel_and_wifi_built': True, 'device_io': False,
              'bootability_verified': False, 'image_publication_approved': False,
              'toolchain_commit': index['toolchain']['commit'],
              'source_patch_sha256': index['patch_sha256'],
              'artifacts': {name: {'path': str(path.relative_to(output)), 'bytes': path.stat().st_size,
                                    'sha256': sha(path)} for name, path in artifacts.items()}}
    with (output / 'build-receipt.json').open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path, help='prepare_kernel.py output directory')
    parser.add_argument('--toolchain', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build(args.source, args.toolchain, args.output, args.jobs), indent=2))
        return 0
    except (ValueError, OSError, KeyError, subprocess.SubprocessError):
        print(json.dumps({'error': 'kernel build refused or failed; inspect the new output build.log',
                          'device_io': False, 'image_publication_approved': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
