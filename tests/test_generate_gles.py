# SPDX-License-Identifier: Apache-2.0
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('generate_gles', Path(__file__).parents[1] / 'tools/generate_gles.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class GlesGeneratorTests(unittest.TestCase):
    def fixture(self):
        names = ['eglGetDisplay', 'eglInitialize', 'eglGetProcAddress', 'glDrawArrays']
        names += ['glFixture' + str(index) for index in range(110)]
        return '\n'.join(f'1: 00000000 4 FUNC GLOBAL DEFAULT 1 {name}' for name in names)

    def test_select_defined_c_exports(self):
        text = self.fixture() + '\n1: 0 4 FUNC GLOBAL DEFAULT UND glUndefined\n1: 0 4 OBJECT GLOBAL DEFAULT 1 glObject\n1: 0 4 FUNC GLOBAL DEFAULT 1 _Zother'
        names = tool.symbols(text)
        self.assertEqual(len(names), 114)
        self.assertNotIn('glUndefined', names)
        self.assertNotIn('glObject', names)

    def test_required_exports(self):
        with self.assertRaises(ValueError):
            tool.symbols('')

    def test_reproducible_tail_thunks(self):
        names = tool.symbols(self.fixture())
        first = tool.generate(names)
        self.assertEqual(first, tool.generate(names))
        self.assertIn(b'#define ACER_GLES_SYMBOL_COUNT 114', first['gles_symbols.h'])
        self.assertIn(b'jmp *%edx', first['gles_exports_x86.S'])
        self.assertIn(b'.note.GNU-stack', first['gles_exports_x86.S'])
        self.assertNotIn(b'ret\n', first['gles_exports_x86.S'])

    def test_assembly_injection_refused(self):
        with self.assertRaises(ValueError):
            tool.generate(['glName;injected'])

    def test_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'existing'
            output.mkdir()
            self.assertEqual(tool.main(['--library', str(Path(folder) / 'absent.so'), '--output', str(output)]), 2)
            self.assertEqual(list(output.iterdir()), [])

    def test_unknown_binary_rejected_before_readelf(self):
        with tempfile.TemporaryDirectory() as folder:
            library = Path(folder) / 'unknown.so'
            library.write_bytes(bytes(128))
            with self.assertRaises(ValueError):
                tool.inspect(library, 'must-not-be-executed')


if __name__ == '__main__':
    unittest.main()
