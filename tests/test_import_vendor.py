# SPDX-License-Identifier: Apache-2.0
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('import_vendor', ROOT / 'tools/import_vendor.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class ImportVendorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'stock'
        (self.root / 'lib').mkdir(parents=True)
        (self.root / 'lib/example.so').write_bytes(b'SYNTHETIC_VENDOR_FIXTURE')
        self.output = self.root.parent / 'new-vendor'
        self.manifest = {'schema': 1, 'device': 'acer-a1-840fhd', 'files': [{
            'source': 'lib/example.so', 'destination': 'legacy-hwc/lib/example.so',
            'install': 'system/legacy-hwc/lib/example.so', 'bytes': 24,
            'sha256': hashlib.sha256(b'SYNTHETIC_VENDOR_FIXTURE').hexdigest()}]}

    def test_dry_run(self):
        report = tool.import_inputs(self.manifest, self.root, self.output, 'acer-a1-840fhd')
        self.assertFalse(report['applied'])
        self.assertFalse(self.output.exists())

    def test_apply_and_receipt(self):
        report = tool.import_inputs(self.manifest, self.root, self.output, 'acer-a1-840fhd', True)
        self.assertTrue(report['applied'])
        self.assertEqual((self.output / 'legacy-hwc/lib/example.so').read_bytes(), b'SYNTHETIC_VENDOR_FIXTURE')
        receipt = json.loads((self.output / 'import-receipt.json').read_text())
        self.assertFalse(receipt['redistribution_approved'])
        self.assertNotIn(str(self.root), json.dumps(receipt))
        makefile = (self.output / 'vendor-stock.mk').read_text()
        self.assertIn('vendor/acer/ducati2fhd/legacy-hwc/lib/example.so:system/legacy-hwc/lib/example.so', makefile)

    def test_existing_output_untouched(self):
        self.output.mkdir()
        (self.output / 'keep').write_bytes(b'KEEP')
        with self.assertRaises(ValueError):
            tool.import_inputs(self.manifest, self.root, self.output, 'acer-a1-840fhd', True)
        self.assertEqual((self.output / 'keep').read_bytes(), b'KEEP')

    def test_wrong_device(self):
        with self.assertRaises(ValueError):
            tool.import_inputs(self.manifest, self.root, self.output, 'dangol')

    def test_wrong_checksum(self):
        self.manifest['files'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            tool.import_inputs(self.manifest, self.root, self.output, 'acer-a1-840fhd', True)
        self.assertFalse(self.output.exists())

    def test_duplicate_destination(self):
        self.manifest['files'].append(copy.deepcopy(self.manifest['files'][0]))
        with self.assertRaises(ValueError):
            tool.validate(self.manifest, self.root, 'acer-a1-840fhd')

    def test_unsafe_paths(self):
        for value in ('../escape', '/absolute', 'C:/drive', 'lib\\windows', 'lib/a b', '.git/config'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                tool.relative(value)

    def test_missing_input(self):
        (self.root / 'lib/example.so').unlink()
        with self.assertRaises(ValueError):
            tool.validate(self.manifest, self.root, 'acer-a1-840fhd')

    def test_nested_output_rejected(self):
        with self.assertRaises(ValueError):
            tool.import_inputs(self.manifest, self.root, self.root / 'output', 'acer-a1-840fhd', True)

    def test_real_metadata_has_stock_only_inputs(self):
        index = json.loads((ROOT / 'vendor-inputs/graphics-stock.json').read_text())
        self.assertEqual(len(index['files']), 32)
        self.assertEqual(len(index['source_built_inputs']), 2)
        self.assertFalse(index['redistribution_approved'])
        for item in index['files']:
            self.assertTrue(item['source'].startswith('lib/'))
            self.assertNotIn('libacer_legacy_runtime.so', item['source'])
            self.assertNotEqual(item['source'], 'lib/libcutils.so')

    def test_plugin_path_transformation(self):
        original = b'<Config><SubsystemPlugins><Location Folder="/system/lib/parameter-framework-plugins/Audio"/></SubsystemPlugins></Config>'
        expected = original.replace(b'/system/lib/parameter-framework-plugins/Audio', b'/system/legacy-audio/lib')
        entry = {'transform': 'acer-audio-plugin-paths-v1', 'output_bytes': len(expected),
                 'output_sha256': hashlib.sha256(expected).hexdigest()}
        self.assertEqual(tool.transformed(original, entry), expected)
        entry['output_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            tool.transformed(original, entry)

    def test_unknown_transform_refused(self):
        with self.assertRaises(ValueError):
            tool.transformed(b'fixture', {'transform': 'unreviewed'})

    def test_audio_metadata_excludes_generated_and_google(self):
        index = json.loads((ROOT / 'vendor-inputs/audio-stock.json').read_text())
        self.assertEqual(len(index['files']), 55)
        self.assertEqual(sum('transform' in entry for entry in index['files']), 2)
        self.assertEqual(len(index['source_built_inputs']), 3)
        for item in index['files']:
            self.assertNotIn('privapp-permissions', item['source'])
            self.assertNotIn('libacer_legacy_runtime.so', item['source'])

    def test_combined_actual_input_inventory(self):
        manifests = [json.loads((ROOT / ('vendor-inputs/' + name)).read_text())
                     for name in ('graphics-stock.json', 'audio-stock.json')]
        combined = tool.combine(manifests, 'acer-a1-840fhd')
        self.assertEqual(len(combined['files']), 87)
        self.assertEqual(len({item['install'] for item in combined['files']}), 87)
        with self.assertRaises(ValueError):
            tool.combine(manifests, 'dangol')


if __name__ == '__main__':
    unittest.main()
