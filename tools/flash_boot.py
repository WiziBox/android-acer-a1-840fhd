#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Guarded Acer Android boot-only Droidboot workflow; dry-run by default.

Does not install system, restore a backup, erase data or reboot. A backup
receipt identifies the previously checked tablet, not its current GPT layout.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import struct
import sys
import zlib
from audit_boot import audit_bytes, MAX_IMAGE
from pack_boot import template_prefix, MAX_PAYLOAD
from verify_owner_backup import verify


class Fastboot:
    def __init__(self, executable, serial):
        if not executable.is_file() or not re.fullmatch(r'[A-Za-z0-9._:-]{1,128}', serial):
            raise ValueError('explicit executable and serial required')
        self.executable, self.serial = executable, serial

    def run(self, arguments, timeout=30):
        result = subprocess.run([str(self.executable), '-s', self.serial] + arguments,
                                capture_output=True, timeout=timeout)
        text = (result.stdout + result.stderr).decode('utf-8', 'strict')
        if result.returncode or re.search(r'\bFAILED\b', text):
            raise ValueError('fastboot operation failed; no automatic reboot')
        return text


def install(client, image, expected_sha256, backup_dir, serial, apply=False,
            accept_no_live_layout=False):
    if not re.fullmatch(r'[0-9a-f]{64}', expected_sha256):
        raise ValueError('explicit lowercase SHA-256 required')
    if image.is_symlink() or not image.is_file() or not 0 < image.stat().st_size <= min(MAX_IMAGE, MAX_PAYLOAD + 512):
        raise ValueError('unsupported image file')
    data = image.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError('image checksum mismatch')
    _, attribute = template_prefix(data)
    if attribute != 1 or not audit_bytes(data, 'acer-a1-840fhd')['boot_key_audit_passed']:
        raise ValueError('new unsigned secure-ADB image required')
    receipt_path = backup_dir / 'private-backup-receipt.json'
    if receipt_path.is_symlink() or not receipt_path.is_file() or receipt_path.stat().st_size > 65536:
        raise ValueError('private owner backup receipt required')
    receipt = json.loads(receipt_path.read_text())
    if not isinstance(receipt, dict):
        raise ValueError('unsupported private receipt structure')
    if receipt.get('serial') != serial:
        raise ValueError('backup belongs to another selected serial')
    # Boot-only rollback scope. Do not claim a system or complete factory backup.
    verified = verify(backup_dir / 'acer-disk-header.bin', backup_dir / 'acer-reserved.img',
                      receipt_path=receipt_path)
    if not verified['saved_receipt_checksums_matched']:
        raise ValueError('matching backup checksums required')
    for variable, expected in (('product', 'baylake'), ('serialno', serial)):
        response = client.run(['getvar', variable])
        found = re.findall(r'(?m)^(?:\(bootloader\)\s*)?' + variable + r':\s*(\S+)\s*$', response)
        if found != [expected]:
            raise ValueError('selected Droidboot identity differs from backup')
    report = {'device': 'acer-a1-840fhd', 'backup_checksums_matched': True,
              'identity_basis': 'prior exact-model backup receipt plus current fastboot serial/product',
              'current_gpt_layout_read_back': False, 'applied': False,
              'boot_write_acknowledged': False, 'boot_readback_verified': False,
              'system_written': False, 'data_erased': False, 'reboot': False,
              'installation_boot_verified': False, 'publication_approved': False}
    if not apply:
        return report
    if not accept_no_live_layout:
        raise ValueError('explicit no-live-layout-readback risk acceptance required')
    # Recheck bytes immediately before passing the path to fastboot. Do not
    # pretend this is an immutable snapshot against concurrent host writers.
    if image.is_symlink() or not image.is_file() or hashlib.sha256(image.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError('image changed during preflight')
    response = client.run(['flash', 'boot', str(image.resolve())], timeout=600)
    if not re.search(r"Sending ['\"]boot['\"].*?OKAY", response, re.S) or not re.search(r"Writing ['\"]boot['\"].*?OKAY", response, re.S):
        raise ValueError('boot flash acknowledgement incomplete; keep Droidboot, do not reboot')
    report['applied'] = report['boot_write_acknowledged'] = True
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fastboot', required=True, type=Path)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--image', required=True, type=Path)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--owner-backup', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--accept-no-live-layout-readback', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = install(Fastboot(args.fastboot, args.serial), args.image, args.sha256,
                         args.owner_backup, args.serial, args.apply,
                         args.accept_no_live_layout_readback)
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, EOFError, struct.error, zlib.error, subprocess.SubprocessError):
        # A failed command may already have changed boot; never report no-write.
        print(json.dumps({'error': 'preflight refused or boot write incomplete',
                          'device_write_may_have_started': args.apply,
                          'reboot': False, 'automatic_retry': False}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
