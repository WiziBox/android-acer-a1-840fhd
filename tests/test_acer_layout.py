# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
import struct
import sys
import unittest
import zlib
from test_extract_boot_template import disk_header, checksum

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
try:
    import acer_layout as tool
finally:
    sys.path.pop(0)


def owner_header():
    result = disk_header(100)
    table = bytearray(16384)
    for index, name, start, length in ((0, 'reserved', 40, 458752), (8, 'system', 5791784, 3686400)):
        offset = index * 128
        table[offset:offset + 16] = bytes([1]) * 16  # Synthetic type GUID.
        table[offset + 16:offset + 32] = bytes([2]) * 16
        struct.pack_into('<2Q', table, offset + 32, start, start + length - 1)
        encoded = name.encode('utf-16-le')
        table[offset + 56:offset + 56 + len(encoded)] = encoded
    result[1024:1024 + len(table)] = table
    gpt = bytearray(512)
    gpt[:8] = b'EFI PART'
    struct.pack_into('<4I', gpt, 8, 0x10000, 92, 0, 0)
    struct.pack_into('<4Q', gpt, 24, 1, 30212095, 34, 30212062)
    struct.pack_into('<Q3I', gpt, 72, 2, 128, 128, zlib.crc32(table))
    struct.pack_into('<I', gpt, 16, zlib.crc32(gpt[:92]))
    result[512:1024] = gpt
    return result


def repair_crc(header):
    struct.pack_into('<I', header, 512 + 88, zlib.crc32(header[1024:17408]))
    struct.pack_into('<I', header, 512 + 16, 0)
    struct.pack_into('<I', header, 512 + 16, zlib.crc32(header[512:604]))


class LayoutTests(unittest.TestCase):
    def test_supported_profile_without_guids_in_report(self):
        report = tool.layout(bytes(owner_header()))
        self.assertEqual(report['reserved']['start_sector'], 40)
        self.assertEqual(report['system']['sectors'], 3686400)
        self.assertNotIn('guid', str(report).lower())
        self.assertFalse(report['device_identity_verified'])

    def test_header_crc_refused(self):
        header = owner_header()
        header[512 + 16] ^= 1
        with self.assertRaises(ValueError):
            tool.layout(bytes(header))

    def test_alternate_android_slot_does_not_change_gpt_roles(self):
        header = owner_header()
        struct.pack_into('<III', header, 36, 68050, 0, 0)
        header[52] = 1
        checksum(header)
        report = tool.layout(bytes(header))
        self.assertEqual(report['reserved']['start_sector'], 40)
        self.assertEqual(report['system']['start_sector'], 5791784)

    def test_table_crc_refused(self):
        header = owner_header()
        header[1024 + 50] ^= 1
        with self.assertRaises(ValueError):
            tool.layout(bytes(header))

    def test_system_role_size_refused(self):
        header = owner_header()
        struct.pack_into('<Q', header, 1024 + 8 * 128 + 40, 5791784 + 100)
        repair_crc(header)
        with self.assertRaises(ValueError):
            tool.layout(bytes(header))

    def test_overlap_refused(self):
        header = owner_header()
        struct.pack_into('<2Q', header, 1024 + 8 * 128 + 32, 41, 41 + 3686400 - 1)
        repair_crc(header)
        with self.assertRaises(ValueError):
            tool.layout(bytes(header))

    def test_table_outside_backup_refused(self):
        header = owner_header()
        struct.pack_into('<Q', header, 512 + 72, 39)
        repair_crc(header)
        with self.assertRaises(ValueError):
            tool.layout(bytes(header))
