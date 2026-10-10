# SPDX-License-Identifier: Apache-2.0
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('build_kernel', ROOT / 'tools/build_kernel.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class KernelBuildTests(unittest.TestCase):
    def test_signature_enforcement_required(self):
        config = (ROOT / 'kernel/ducati2fhd.config').read_text()
        tool.require_signatures(config)
        for option in ('MODULE_SIG', 'MODULE_SIG_FORCE', 'MODULE_SIG_ALL', 'MODULE_SIG_SHA256'):
            with self.subTest(option=option), self.assertRaises(ValueError):
                tool.require_signatures(config.replace('CONFIG_' + option + '=y', 'CONFIG_' + option + '=n'))

    def test_existing_output_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            marker = out / 'user-file'
            marker.write_text('keep')
            with self.assertRaises(ValueError):
                tool.preflight(Path('missing-source'), Path('missing-toolchain'), out, 4)
            self.assertEqual(marker.read_text(), 'keep')

    def test_job_bounds(self):
        for jobs in (0, -1, 65):
            with self.subTest(jobs=jobs), self.assertRaises(ValueError):
                tool.preflight(Path('missing-source'), Path('missing-toolchain'), Path('missing-out'), jobs)


if __name__ == '__main__':
    unittest.main()
