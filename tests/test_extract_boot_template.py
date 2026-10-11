# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from test_pack_boot import template

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
try:
    import extract_boot_template as tool
finally:
    sys.path.pop(0)


def disk_header(payload_sectors):
    header = bytearray(tool.HEADER_BYTES)
    header[:4] = b'$OS$'
    header[8:10] = b'\x03\x01'
    struct.pack_into('<H', header, 10, 104)
    for i, (lba, attributes) in enumerate(tool.LAYOUT):
        struct.pack_into('<HHIIIIB3x', header, 32 + i * 24,
                         0, 0, lba, 0x1100000, 0x1101000,
                         payload_sectors if i == 0 else 1, attributes[0])
    checksum(header)
    return header


def checksum(header):
    header[7] = 0
    for value in header[:104]:
        header[7] ^= value


class TemplateExtractTests(unittest.TestCase):
    def test_actual_payload_roundtrip_synthetic(self):
        owner = template(True)
        payload = owner[512:]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            header = root / 'header.bin'
            header.write_bytes(disk_header(len(payload) // 512))
            reserved = root / 'reserved.img'
            with reserved.open('wb') as stream:
                stream.truncate(tool.RESERVED_BYTES)
                stream.seek((36050 - 40) * 512)
                stream.write(payload)
            output = root / 'private-template.img'
            report = tool.extract(header, reserved, output)
            self.assertEqual(output.read_bytes()[512:], payload)
            self.assertEqual(output.read_bytes()[52], 0)
            self.assertFalse(report['publication_approved'])
            self.assertTrue(report['old_ramdisk_preserved'])
            self.assertFalse(report['device_io'])

    def test_bad_checksum_refused(self):
        header = disk_header(100)
        header[7] ^= 1
        with self.assertRaises(ValueError):
            tool.records(bytes(header), tool.RESERVED_BYTES)

    def test_wrong_layout_and_overlap_refused(self):
        for offset, value in ((36, 12345), (48, 32000 * 2)):
            header = disk_header(100)
            struct.pack_into('<I', header, offset, value)
            checksum(header)
            with self.assertRaises(ValueError):
                tool.records(bytes(header), tool.RESERVED_BYTES)

    def test_reserved_size_refused(self):
        with self.assertRaises(ValueError):
            tool.records(bytes(disk_header(100)), 1000)

    def test_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'boot.img'
            output.write_bytes(b'KEEP')
            self.assertEqual(tool.main(['--disk-header', 'missing', '--reserved-backup', 'missing', '--output', str(output)]), 2)
            self.assertEqual(output.read_bytes(), b'KEEP')
