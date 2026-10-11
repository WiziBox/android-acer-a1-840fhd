# SPDX-License-Identifier: Apache-2.0
import json
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from test_backup_acer import FakeADB
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import flash_system as tool
from acer_layout import layout
from test_acer_layout import owner_header

HASH = '1' * 64
IMAGE = '/cache/acer-system-' + HASH + '.raw.img'


class Recovery(FakeADB):
    def __init__(self):
        super().__init__()
        self.writes = []
        self.mounts = ''
        self.mode = 'recovery'
        self.source_hash = self.readback_hash = HASH
    def read(self, command):
        values = {'getprop ro.bootmode': self.mode,
                  'test -f /tmp/recovery.log && echo RECOVERY': 'RECOVERY',
                  'readlink -f /dev/block/platform/intel/by-label/system': '/dev/block/mmcblk0p9',
                  'cat /proc/mounts': self.mounts,
                  'test -f ' + IMAGE + ' && test ! -L ' + IMAGE + ' && echo REGULAR': 'REGULAR',
                  'stat -t ' + IMAGE: IMAGE + ' ' + str(tool.SYSTEM_BYTES) + ' other-fields',
                  'sha256sum ' + IMAGE: self.source_hash + ' ' + IMAGE}
        return values[command] if command in values else super().read(command)
    def root(self, command):
        return command
    def run(self, args, timeout=30):
        if args[0] == 'shell' and args[1].startswith('set -e; dd if='):
            self.writes.append(args[1])
            return ('1800+0 records in\n1800+0 records out\n' + self.readback_hash + ' /dev/block/mmcblk0p9\n').encode()
        return super().run(args)


class SystemFlashTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.receipt = {'serial': 'SYNTHETIC', 'includes_system': True, 'layout': layout(owner_header())}
        self.save()
        self.mock = patch.object(tool, 'verify', return_value={'saved_receipt_checksums_matched': True})
        self.mock.start()
        self.addCleanup(self.mock.stop)
    def save(self):
        (self.root / 'private-backup-receipt.json').write_text(json.dumps(self.receipt))
    def invoke(self, adb, apply=False):
        return tool.install(adb, 'SYNTHETIC', self.root, HASH, IMAGE, apply)
    def test_dry_run_no_write(self):
        adb = Recovery()
        self.assertFalse(self.invoke(adb)['applied'])
        self.assertEqual(adb.writes, [])
    def test_system_only_write_and_readback(self):
        adb = Recovery()
        report = self.invoke(adb, True)
        self.assertTrue(report['system_readback_verified'])
        self.assertEqual(len(adb.writes), 1)
        self.assertIn('of=/dev/block/mmcblk0p9 bs=1048576', adb.writes[0])
        self.assertFalse(report['boot_written'])
        self.assertFalse(report['reboot'])
    def test_any_system_mount_refused(self):
        for options in ('ro', 'rw'):
            adb = Recovery()
            adb.mounts = '/dev/block/mmcblk0p9 /system ext4 ' + options + ' 0 0'
            with self.assertRaises(ValueError):
                self.invoke(adb, True)
            self.assertEqual(adb.writes, [])
    def test_non_recovery_refused(self):
        adb = Recovery()
        adb.mode = 'normal'
        with self.assertRaises(ValueError):
            self.invoke(adb, True)
        self.assertEqual(adb.writes, [])
    def test_incomplete_or_wrong_owner_backup(self):
        for key, value in (('serial', 'OTHER'), ('includes_system', False)):
            with self.subTest(key=key):
                self.receipt[key] = value
                self.save()
                adb = Recovery()
                with self.assertRaises(ValueError):
                    self.invoke(adb, True)
                self.assertEqual(adb.writes, [])
    def test_wrong_remote_checksum_no_write(self):
        adb = Recovery()
        adb.source_hash = '2' * 64
        with self.assertRaises(ValueError):
            self.invoke(adb, True)
        self.assertEqual(adb.writes, [])
    def test_wrong_readback_not_success_and_no_retry(self):
        adb = Recovery()
        adb.readback_hash = '2' * 64
        with self.assertRaises(ValueError):
            self.invoke(adb, True)
        self.assertEqual(len(adb.writes), 1)
    def test_unsafe_remote_path_refused(self):
        adb = Recovery()
        with self.assertRaises(ValueError):
            tool.install(adb, 'SYNTHETIC', self.root, HASH, '/cache/a;reboot', True)
        self.assertEqual(adb.writes, [])
    def test_current_layout_change_refused(self):
        self.receipt['layout']['system']['sectors'] += 1
        self.save()
        adb = Recovery()
        with self.assertRaises(ValueError):
            self.invoke(adb, True)
        self.assertEqual(adb.writes, [])
    def test_mount_appears_before_write_refused(self):
        adb = Recovery()
        original = adb.read
        checks = 0
        def changing(command):
            nonlocal checks
            if command == 'cat /proc/mounts':
                checks += 1
                if checks > 1:
                    return '/dev/block/mmcblk0p9 /system ext4 ro 0 0'
            return original(command)
        with patch.object(adb, 'read', side_effect=changing), self.assertRaises(ValueError):
            self.invoke(adb, True)
        self.assertEqual(adb.writes, [])
    def test_header_changes_before_write_refused(self):
        adb = Recovery()
        header = adb.header()
        with patch.object(adb, 'header', side_effect=[header, b'CHANGED']), self.assertRaises(ValueError):
            self.invoke(adb, True)
        self.assertEqual(adb.writes, [])
    def test_other_system_alias_mounted_refused(self):
        adb = Recovery()
        adb.mounts = '/dev/block/alias-system /mnt/other ext4 ro 0 0'
        original = adb.read
        def alias(command):
            return '/dev/block/mmcblk0p9' if command == 'readlink -f /dev/block/alias-system' else original(command)
        with patch.object(adb, 'read', side_effect=alias), self.assertRaises(ValueError):
            self.invoke(adb, True)
        self.assertEqual(adb.writes, [])
    def test_non_object_receipt_refused_before_device_io(self):
        for value in ([], 'PRIVATE_FIXTURE_DO_NOT_PRINT', None, 7):
            (self.root / 'private-backup-receipt.json').write_text(json.dumps(value))
            adb = Recovery()
            with self.assertRaises(ValueError):
                self.invoke(adb, True)
            self.assertEqual(adb.writes, [])
    def test_cli_failure_never_prints_receipt_or_paths(self):
        (self.root / 'private-backup-receipt.json').write_text(json.dumps('PRIVATE_FIXTURE_DO_NOT_PRINT'))
        output, errors = io.StringIO(), io.StringIO()
        adb = Recovery()
        with patch.object(tool, 'RecoveryADB', return_value=adb), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = tool.main(['--adb', 'unused', '--serial', 'SYNTHETIC',
                              '--owner-backup', str(self.root), '--raw-sha256', HASH,
                              '--remote-image', IMAGE])
        self.assertEqual(code, 2)
        self.assertNotIn('PRIVATE_FIXTURE_DO_NOT_PRINT', output.getvalue())
        self.assertNotIn(str(self.root), output.getvalue())
        self.assertEqual(errors.getvalue(), '')
        self.assertEqual(adb.writes, [])
