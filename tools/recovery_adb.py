#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Explicit legacy recovery header read with private 20KiB staging.

Only the opted-in backend creates temporary device files. Never writes block
devices, enables root, mounts, reboots or recursively removes directories.
"""
import hashlib
from pathlib import Path
import tempfile
import uuid
from backup_acer import ADB
from acer_layout import HEADER_BYTES


class RecoveryADB(ADB):
    def __init__(self, executable, serial, legacy_header_staging=False):
        super().__init__(executable, serial)
        self.legacy_header_staging = legacy_header_staging

    def header(self):
        if not self.legacy_header_staging:
            return super().header()
        # Existing root has already been checked by the shared preflight.
        folder = '/tmp/acer-header-' + uuid.uuid4().hex
        remote = folder + '/header.bin'
        if self.read('getprop ro.bootmode') != 'recovery':
            raise ValueError('legacy staging requires supported recovery mode')
        if self.read('test -d /tmp && echo TMP') != 'TMP':
            raise ValueError('supported recovery temporary directory missing')
        self.run(['shell', self.root('umask 077; mkdir ' + folder)])
        try:
            self.run(['shell', self.root('dd if=/dev/block/mmcblk0 of=' + remote + ' bs=512 count=40')])
            expected = self.read('sha256sum ' + remote).split()
            with tempfile.TemporaryDirectory(prefix='acer-private-header-') as local:
                output = Path(local) / 'header.bin'
                self.run(['pull', remote, str(output)])
                if output.is_symlink() or not output.is_file() or output.stat().st_size != HEADER_BYTES:
                    raise ValueError('short or contaminated private header read')
                data = output.read_bytes()
            if not expected or expected[0] != hashlib.sha256(data).hexdigest():
                raise ValueError('staged header checksum mismatch')
            return data
        finally:
            # Private unique directory was created successfully by this call.
            # Remove only its exact one file, then the now-empty directory.
            # Any error stops the caller; no automatic partition write follows.
            self.run(['shell', self.root('rm -f ' + remote + '; rmdir ' + folder)])
