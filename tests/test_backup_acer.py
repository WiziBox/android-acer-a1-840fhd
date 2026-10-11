# SPDX-License-Identifier: Apache-2.0
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from test_acer_layout import owner_header

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
try:
    import backup_acer as tool
finally:
    sys.path.pop(0)


class FakeADB:
    def __init__(self, mount='ro'):
        self.mount = mount
    def run(self, args):
        props = {'ro.product.manufacturer': 'Acer', 'ro.product.model': 'A1-840FHD', 'ro.hardware': 'ducati2fhd'}
        return props[args[1].split()[-1]].encode()
    def get_root(self):
        pass
    def header(self):
        return bytes(owner_header())
    def read(self, command):
        values = {
            'cat /sys/class/block/mmcblk0p1/start': '40', 'cat /sys/class/block/mmcblk0p1/size': '458752',
            'cat /sys/class/block/mmcblk0p9/start': '5791784', 'cat /sys/class/block/mmcblk0p9/size': '3686400',
            'cat /sys/class/block/mmcblk0/size': '30212096',
            'cat /proc/mounts': '/dev/block/mmcblk0p9 /system ext4 ' + self.mount + ',relatime 0 0',
            'readlink -f /dev/block/mmcblk0p9': '/dev/block/mmcblk0p9'}
        return values[command]


class BackupTests(unittest.TestCase):
    def test_dry_run_reads_but_no_output(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'new'
            report = tool.backup(FakeADB(), 'SYNTHETIC-SERIAL', output, True)
            self.assertFalse(report['applied'])
            self.assertFalse(report['device_writes'])
            self.assertNotIn('SYNTHETIC-SERIAL', str(report))
            self.assertFalse(output.exists())

    def test_writable_system_refused(self):
        with self.assertRaises(ValueError):
            tool.preflight(FakeADB('rw'), True)

    def test_wrong_model_refused_before_disk_read(self):
        adb = FakeADB()
        with patch.object(adb, 'run', return_value=b'OTHER'), patch.object(adb, 'header') as header:
            with self.assertRaises(ValueError):
                tool.preflight(adb)
            header.assert_not_called()

    def test_live_size_mismatch_refused(self):
        adb = FakeADB()
        with patch.object(adb, 'read', return_value='1'), self.assertRaises(ValueError):
            tool.preflight(adb)

    def test_existing_output_not_touched(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            with self.assertRaises(ValueError):
                tool.backup(FakeADB(), 'SYNTHETIC-SERIAL', output, apply=True)

    def test_binary_transfer_and_hash_match(self):
        class StreamADB:
            def root(self, command):
                return command
            def run(self, args, timeout, stdout):
                stdout.write(b'BINARY\x00FIXTURE')
            def read(self, command):
                return hashlib.sha256(b'BINARY\x00FIXTURE').hexdigest() + ' source'
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'new.img'
            report = tool.transfer(StreamADB(), '/dev/block/mmcblk0p1', target, 14)
            self.assertTrue(report['live_source_hash_matched'])
            self.assertEqual(target.read_bytes(), b'BINARY\x00FIXTURE')

    def test_short_transfer_not_trusted(self):
        class StreamADB:
            def root(self, command):
                return command
            def run(self, args, timeout, stdout):
                stdout.write(b'SHORT')
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
            tool.transfer(StreamADB(), '/dev/block/mmcblk0p1', Path(folder) / 'new.img', 100)
