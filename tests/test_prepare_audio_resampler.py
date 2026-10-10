# SPDX-License-Identifier: Apache-2.0
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('prepare_audio_resampler', Path(__file__).parents[1] / 'tools/prepare_audio_resampler.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class AudioResamplerTests(unittest.TestCase):
    def test_unknown_input_refused(self):
        with self.assertRaises(ValueError):
            tool.prepare(bytes(tool.SIZE))

    def test_wrong_size_refused(self):
        with self.assertRaises(ValueError):
            tool.prepare(b'ELF fixture')

    def test_existing_output_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'existing.so'
            path.write_bytes(b'KEEP')
            self.assertEqual(tool.main(['--input', str(path), '--output', str(path)]), 2)
            self.assertEqual(path.read_bytes(), b'KEEP')

    def test_no_output_on_unknown_input(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.so'
            output = Path(folder) / 'new.so'
            source.write_bytes(bytes(tool.SIZE))
            self.assertEqual(tool.main(['--input', str(source), '--output', str(output)]), 2)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
