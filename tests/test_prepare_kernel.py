# SPDX-License-Identifier: Apache-2.0
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('prepare_kernel', ROOT / 'tools/prepare_kernel.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class KernelPreparationTests(unittest.TestCase):
    def test_source_paths_are_contained(self):
        self.assertEqual(str(tool.relative('kernel/fs/sdcardfs/file.c')), 'kernel/fs/sdcardfs/file.c')
        for path in ('', '/kernel/file.c', '../kernel/file.c', 'kernel/../escape', 'C:/kernel/file.c', 'kernel\\file.c', 'modules/other.c'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                tool.relative(path)

    def test_dated_notice_preserves_original(self):
        original = b'/* Original GPL copyright/license */\nint fixture;\n'
        result = tool.modification_notice(Path('example.c'), original)
        self.assertIn(b'2026-10-11', result)
        self.assertTrue(result.endswith(original))
        self.assertTrue(tool.modification_notice(Path('Makefile'), b'fixture\n').startswith(b'# '))

    def test_unknown_source_type_refused(self):
        with self.assertRaises(ValueError):
            tool.modification_notice(Path('example.bin'), b'fixture')

    def test_existing_directory_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / 'keep').write_bytes(b'KEEP')
            with self.assertRaises(ValueError):
                tool.prepare(directory / 'missing.zip', directory)
            self.assertEqual((directory / 'keep').read_bytes(), b'KEEP')

    def test_published_kernel_metadata(self):
        index = json.loads((ROOT / 'kernel/inputs.json').read_text())
        self.assertEqual(index['schema'], 1)
        self.assertEqual(index['baseline_files'], 43628)
        self.assertEqual(len(index['changes']), 99)
        self.assertEqual(sum(entry['build_time_override'] for entry in index['changes']), 3)
        self.assertEqual(hashlib.sha256((ROOT / 'kernel/kernel-port.patch').read_bytes()).hexdigest(), index['patch_sha256'])
        self.assertEqual(hashlib.sha256((ROOT / 'kernel/ducati2fhd.config').read_bytes()).hexdigest(), index['config_sha256'])
        evidence = json.loads((ROOT / 'kernel/build-evidence.json').read_text())
        self.assertTrue(index['clean_build_verified'])
        self.assertTrue(evidence['fresh_output_directory'])
        self.assertTrue(evidence['kernel_and_wifi_built'])
        self.assertEqual(evidence['source_patch_sha256'], index['patch_sha256'])
        self.assertEqual(evidence['config_sha256'], index['config_sha256'])
        self.assertFalse(evidence['whole_android_build_verified'])
        self.assertFalse(evidence['image_publication_approved'])
        self.assertFalse(evidence['private_key_published'])
        for entry in index['changes']:
            tool.relative(entry['path'])
            self.assertRegex(entry['result_sha256'], r'^[0-9a-f]{64}$')
        self.assertIn(b'GNU GENERAL PUBLIC LICENSE', (ROOT / 'kernel/COPYING').read_bytes())
        self.assertIn(b'CONFIG_MODULE_SIG_FORCE=y', (ROOT / 'kernel/ducati2fhd.config').read_bytes())


if __name__ == '__main__':
    unittest.main()
