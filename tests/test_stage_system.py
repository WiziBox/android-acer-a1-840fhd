# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from test_flash_system import Recovery, HASH, IMAGE
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import stage_system as tool


class StagingRecovery(Recovery):
    def __init__(self):
        super().__init__()
        self.operations = []
        self.capacity = '1000000:4096'
        self.absent = 'ABSENT'
        self.upload_hash = HASH
        self.fail_link = False
    def read(self, command):
        if command == 'stat -f -c "%a:%S" /cache':
            return self.capacity
        if command.startswith('test ! -e '):
            return self.absent
        if command.startswith('stat -t /cache/acer-stage-'):
            return command[len('stat -t '):] + ' ' + str(tool.SYSTEM_BYTES) + ' other'
        if command.startswith('sha256sum /cache/acer-stage-'):
            return self.upload_hash + ' ' + command[len('sha256sum '):]
        return super().read(command)
    def run(self, args, timeout=30):
        if args[0] == 'shell' and args[1].startswith('getprop '):
            return super().run(args, timeout)
        self.operations.append(args)
        if args[0] == 'shell' and args[1].startswith('ln ') and self.fail_link:
            raise ValueError('existing target')
        if args[0] in ('shell', 'push'):
            return b''
        return super().run(args, timeout)


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.inspector = patch.object(tool, 'inspect_source')
        self.inspector.start()
        self.addCleanup(self.inspector.stop)
    def invoke(self, adb, apply=False):
        return tool.stage(adb, Path('synthetic.raw.img'), HASH, apply)
    def test_dry_run_no_upload_or_commands(self):
        adb = StagingRecovery()
        self.assertFalse(self.invoke(adb)['applied'])
        self.assertEqual(adb.operations, [])
    def test_upload_verify_link_cleanup_no_partition(self):
        adb = StagingRecovery()
        result = self.invoke(adb, True)
        self.assertTrue(result['remote_checksum_verified'])
        self.assertFalse(result['partition_written'])
        commands = [args[1] for args in adb.operations if args[0] == 'shell']
        self.assertEqual(len(commands), 3)
        self.assertTrue(commands[0].startswith('umask 077; mkdir /cache/acer-stage-'))
        self.assertTrue(commands[1].startswith('ln /cache/acer-stage-'))
        self.assertTrue(commands[1].endswith(' ' + IMAGE))
        self.assertTrue(commands[2].startswith('rm /cache/acer-stage-'))
        self.assertFalse(any('dd ' in command or 'reboot' in command for command in commands))
    def test_no_space_or_unsupported_query_refused(self):
        for capacity in ('1:4096', 'PRIVATE_INVALID_RESPONSE', '-1:4096', '1000000:0'):
            adb = StagingRecovery()
            adb.capacity = capacity
            with self.assertRaises(ValueError):
                self.invoke(adb, True)
            self.assertEqual(adb.operations, [])
    def test_existing_target_not_overwritten(self):
        adb = StagingRecovery()
        adb.absent = ''
        with self.assertRaises(ValueError):
            self.invoke(adb, True)
        self.assertEqual(adb.operations, [])
    def test_wrong_upload_hash_preserved_no_link(self):
        adb = StagingRecovery()
        adb.upload_hash = '2' * 64
        with self.assertRaises(ValueError):
            self.invoke(adb, True)
        self.assertEqual(len(adb.operations), 2)
        self.assertEqual(adb.operations[-1][0], 'push')
    def test_destination_race_not_overwritten_or_cleaned(self):
        adb = StagingRecovery()
        adb.fail_link = True
        with self.assertRaises(ValueError):
            self.invoke(adb, True)
        self.assertEqual(len(adb.operations), 3)
        self.assertTrue(adb.operations[-1][1].startswith('ln '))
    def test_header_change_prevents_upload(self):
        adb = StagingRecovery()
        header = adb.header()
        with patch.object(adb, 'header', side_effect=[header, b'CHANGED']), self.assertRaises(ValueError):
            self.invoke(adb, True)
        self.assertEqual(adb.operations, [])
    def test_local_image_failure_prevents_device_access(self):
        adb = StagingRecovery()
        with patch.object(tool, 'inspect_source', side_effect=ValueError('invalid image')), patch.object(adb, 'header') as header:
            with self.assertRaises(ValueError):
                self.invoke(adb, True)
            header.assert_not_called()
        self.assertEqual(adb.operations, [])
