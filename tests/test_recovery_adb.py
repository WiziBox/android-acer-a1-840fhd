# SPDX-License-Identifier: Apache-2.0
import hashlib
from pathlib import Path
import sys
import unittest
from test_acer_layout import owner_header
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from recovery_adb import RecoveryADB


class SimulatedRecovery(RecoveryADB):
    def __init__(self, legacy=True):
        self.legacy_header_staging = legacy
        self.root_prefix = ''
        self.calls = []
        self.payload = bytes(owner_header())
        self.mode = 'recovery'
        self.hash_wrong = self.mkdir_fail = self.pull_fail = False
    def run(self, args, timeout=30, stdout=None):
        self.calls.append(args)
        if args[0] == 'exec-out':
            return self.payload
        if args[0] == 'pull':
            if self.pull_fail:
                raise ValueError('simulated pull failed')
            Path(args[2]).write_bytes(self.payload)
            return b''
        command = args[1]
        if command == 'getprop ro.bootmode':
            return self.mode.encode()
        if command == 'test -d /tmp && echo TMP':
            return b'TMP'
        if command.startswith('sha256sum '):
            hashed = '0' * 64 if self.hash_wrong else hashlib.sha256(self.payload).hexdigest()
            return (hashed + ' private-file').encode()
        if 'mkdir ' in command and self.mkdir_fail:
            raise ValueError('simulated existing temporary directory')
        return b''


class RecoveryHeaderTests(unittest.TestCase):
    def test_default_exec_out_no_device_temp_write(self):
        adb = SimulatedRecovery(False)
        self.assertEqual(adb.header(), adb.payload)
        self.assertEqual(len(adb.calls), 1)
        self.assertEqual(adb.calls[0][0], 'exec-out')
    def test_explicit_legacy_read_and_exact_cleanup(self):
        adb = SimulatedRecovery()
        self.assertEqual(adb.header(), adb.payload)
        commands = [call[1] for call in adb.calls if call[0] == 'shell']
        dd = [command for command in commands if command.startswith('dd ')]
        self.assertEqual(len(dd), 1)
        self.assertIn('if=/dev/block/mmcblk0 of=/tmp/acer-header-', dd[0])
        self.assertTrue(dd[0].endswith(' bs=512 count=40'))
        self.assertTrue(commands[-1].startswith('rm -f /tmp/acer-header-'))
        self.assertNotIn('rm -r', commands[-1])
    def test_non_recovery_no_temporary_write(self):
        adb = SimulatedRecovery()
        adb.mode = 'normal'
        with self.assertRaises(ValueError):
            adb.header()
        self.assertEqual(len(adb.calls), 1)
    def test_failed_mkdir_never_removes_unowned_path(self):
        adb = SimulatedRecovery()
        adb.mkdir_fail = True
        with self.assertRaises(ValueError):
            adb.header()
        self.assertFalse(any('rm -f' in call[1] for call in adb.calls))
    def test_failed_pull_still_cleans_owned_staging(self):
        adb = SimulatedRecovery()
        adb.pull_fail = True
        with self.assertRaises(ValueError):
            adb.header()
        self.assertTrue(adb.calls[-1][1].startswith('rm -f '))
    def test_wrong_checksum_and_short_pull_refused(self):
        for short in (False, True):
            adb = SimulatedRecovery()
            if short:
                adb.payload = b'SHORT'
            else:
                adb.hash_wrong = True
            with self.assertRaises(ValueError):
                adb.header()
            self.assertTrue(adb.calls[-1][1].startswith('rm -f '))
