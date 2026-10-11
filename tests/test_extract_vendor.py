# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
try:
    import extract_vendor as tool
finally:
    sys.path.pop(0)

CAL = b'boardtype=0x5ef\nboardrev=0x1100\nsromrev=9\nmacaddr=02:00:00:00:00:01\n'


class ExtractVendorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.image = self.root / 'owner.img'
        image = bytearray(4096)
        image[1080:1082] = b'\x53\xef'
        self.image.write_bytes(image)
        self.output = self.root / 'stock-inputs'
        self.manifest = {'schema': 1, 'device': 'acer-a1-840fhd', 'redistribution_approved': False,
                         'files': [{'source': 'lib/example.so', 'bytes': 7,
                                    'sha256': hashlib.sha256(b'FIXTURE').hexdigest()}]}
        self.payloads = {'lib/example.so': b'FIXTURE', 'etc/firmware/fw.bin': b'FW', tool.CAL: CAL}
        self.addCleanup(patch.stopall)
        patch.object(tool, 'AUDIO', {'fw.bin': (2, hashlib.sha256(b'FW').hexdigest())}).start()
        patch.object(tool, 'PARTITION', 4096).start()
        patch.object(tool.sys, 'platform', 'linux').start()

    def reader(self, image, name):
        return self.payloads[name]

    def test_plan_deduplicates_source_not_install_entries(self):
        self.manifest['files'].append(dict(self.manifest['files'][0]))
        result = tool.plan(self.image, self.manifest, self.reader)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[tool.CAL], CAL)

    def test_wrong_hash_refused(self):
        self.manifest['files'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            tool.plan(self.image, self.manifest, self.reader)

    def test_bad_owner_profile_refused(self):
        self.payloads[tool.CAL] = CAL.replace(b'0x5ef', b'0xBAD')
        with self.assertRaises(ValueError):
            tool.plan(self.image, self.manifest, self.reader)

    def test_apps_refused_before_read(self):
        self.manifest['files'][0]['source'] = 'app/Google.apk'
        with self.assertRaises(ValueError):
            tool.plan(self.image, self.manifest, self.reader)

    def test_existing_output_preserved(self):
        self.output.mkdir()
        (self.output / 'keep').write_bytes(b'KEEP')
        with self.assertRaises(ValueError):
            tool.extract(self.image, self.output, self.manifest, True)
        self.assertEqual((self.output / 'keep').read_bytes(), b'KEEP')

    def test_apply_private_calibration_not_in_receipt(self):
        with patch.object(tool, 'read_ext4', side_effect=self.reader):
            # plan's default reader is bound at definition time; explicitly
            # route this fixture through the tested planner.
            planned = tool.plan(self.image, self.manifest, self.reader)
        with patch.object(tool, 'plan', return_value=planned):
            result = tool.extract(self.image, self.output, self.manifest, True)
        self.assertTrue(result['applied'])
        self.assertEqual((self.output / tool.CAL).read_bytes(), CAL)
        receipt = (self.output / 'owner-extraction-receipt.json').read_text()
        self.assertNotIn('02:00:00', receipt)
        self.assertNotIn(hashlib.sha256(CAL).hexdigest(), receipt)

    def test_dry_run_creates_nothing(self):
        with patch.object(tool, 'plan', return_value=self.payloads):
            self.assertFalse(tool.extract(self.image, self.output, self.manifest)['applied'])
        self.assertFalse(self.output.exists())

    def test_absolute_system_symlink_resolves_inside_image(self):
        replies = [subprocess.CompletedProcess([], 0, b'Type: symlink Fast link dest: "/system/lib/real.so"', b''),
                   subprocess.CompletedProcess([], 0, b'Type: regular Size: 7', b''),
                   subprocess.CompletedProcess([], 0, b'FIXTURE', b'')]
        with patch.object(tool.subprocess, 'run', side_effect=replies) as run:
            self.assertEqual(tool.read_ext4(self.image, 'lib/link.so'), b'FIXTURE')
        self.assertEqual(run.call_args_list[1].args[0][2], 'stat /lib/real.so')
        for call in run.call_args_list:
            self.assertNotIn('-w', call.args[0])

    def test_symlink_loop_refused(self):
        reply = subprocess.CompletedProcess([], 0, b'Type: symlink Fast link dest: "loop"', b'')
        with patch.object(tool.subprocess, 'run', return_value=reply), self.assertRaises(ValueError):
            tool.read_ext4(self.image, 'loop')

    def test_real_allowlist_inventory(self):
        indexes = [json.loads((ROOT / 'vendor-inputs' / name).read_text()) for name in ('graphics-stock.json', 'audio-stock.json')]
        rows = tool.combine(indexes, 'acer-a1-840fhd')['files']
        self.assertEqual(len(rows), 87)
        self.assertEqual(len({row['source'] for row in rows}), 75)
        self.assertNotIn(tool.CAL, {row['source'] for row in rows})
