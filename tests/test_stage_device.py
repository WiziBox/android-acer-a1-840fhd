# SPDX-License-Identifier: Apache-2.0
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('stage_device', ROOT / 'tools/stage_device.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class StageDeviceTests(unittest.TestCase):
    def fixture(self, folder):
        source = Path(folder) / 'android'
        (source / 'build').mkdir(parents=True)
        (source / 'build/envsetup.sh').write_text('fixture')
        generated = Path(folder) / 'generated'
        generated.mkdir()
        hashes = {}
        for name in tool.GENERATED:
            data = ('fixture ' + name).encode()
            (generated / name).write_bytes(data)
            hashes[name] = hashlib.sha256(data).hexdigest()
        return source, generated, hashes

    def test_contained_paths(self):
        for path in ('', '.', '../escape', '/absolute', 'a/../b', '.git/config', 'C:/key', 'a\\b'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                tool.relative(path)

    def test_source_index_and_public_defaults(self):
        index = json.loads((ROOT / 'source/acer-device-provenance.json').read_text())
        self.assertEqual(len(index['files']), 34)
        for entry in index['files']:
            data = (ROOT / 'source/device/acer/ducati2fhd' / entry['path']).read_bytes()
            self.assertEqual(len(data), entry['bytes'])
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry['sha256'])
            self.assertIn(b'SPDX-License-Identifier: Apache-2.0', data[:300])
        product = (ROOT / 'source/device/acer/ducati2fhd/device.mk').read_text()
        self.assertEqual(product.count('$(call inherit-product, vendor/acer/ducati2fhd/vendor-stock.mk)'), 1)
        for private in ('Phonesky', 'PrebuiltGmsCore', 'GoogleServicesFramework', 'acer-network-adb', 'private-audio.mk', 'legacy-hwc/private-libraries.mk'):
            self.assertNotIn(private, product)
        self.assertIn('ro.adb.secure=1 ro.secure=1', product)

    def test_dry_run_then_new_destination_only(self):
        with tempfile.TemporaryDirectory() as folder:
            source, generated, hashes = self.fixture(folder)
            output = source / 'device/acer/ducati2fhd'
            with mock.patch.dict(tool.GENERATED, hashes):
                self.assertTrue(tool.stage(source, generated)['dry_run'])
                self.assertFalse(output.exists())
                report = tool.stage(source, generated, True)
                self.assertEqual(report['files_preflighted'], 36)
                self.assertFalse(report['rom_built'])
                self.assertTrue((output / 'BoardConfig.mk').is_file())
                with self.assertRaises(ValueError):
                    tool.stage(source, generated, True)
                self.assertTrue((output / 'BoardConfig.mk').is_file())

    def test_bad_generated_input_writes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            source, generated, hashes = self.fixture(folder)
            with self.assertRaises(ValueError):
                tool.stage(source, generated, True)
            self.assertFalse((source / 'device').exists())


if __name__ == '__main__':
    unittest.main()
