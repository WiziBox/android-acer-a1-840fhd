# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).parents[1]


class GraphicsSourceTests(unittest.TestCase):
    def test_graphics_sources_and_inputs(self):
        index = json.loads((ROOT / 'source/acer-graphics-provenance.json').read_text())
        self.assertEqual(index['schema'], 1)
        self.assertEqual(len(index['files']), 7)
        for entry in index['files']:
            path = ROOT / entry['path']
            self.assertTrue(path.resolve().is_relative_to((ROOT / 'source').resolve()))
            payload = path.read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), entry['sha256'])
            self.assertIn(b'SPDX-License-Identifier: Apache-2.0', payload[:300])
        component = ROOT / 'source/device/acer/ducati2fhd/legacy-hwc'
        makefile = (component / 'Android.mk').read_text()
        self.assertEqual(len(re.findall(r'^LOCAL_MODULE := ', makefile, re.M)), 5)
        generated = set(index['generated_inputs'])
        for line in re.findall(r'^LOCAL_SRC_FILES := (.+)$', makefile, re.M):
            for name in line.split():
                self.assertTrue((component / name).is_file() or name in generated)
        for name in generated:
            self.assertFalse((component / name).exists())


if __name__ == '__main__':
    unittest.main()
