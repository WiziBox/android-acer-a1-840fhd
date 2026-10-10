# SPDX-License-Identifier: Apache-2.0
import gzip
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from test_audit_boot import archive, osip

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
try:
    import pack_boot as tool
finally:
    sys.path.pop(0)


def checksum(image):
    image[7] = 0
    for byte in image[:56]:
        image[7] ^= byte


def template(signed=False):
    image = bytearray(osip([('default.prop', b'ro.adb.secure=0\n'), ('adb_keys', b'OLD-APPROVAL-FIXTURE')]))
    image[8:10] = b'\x01\x01'
    struct.pack_into('<H', image, 10, 56)
    struct.pack_into('<III', image, 0x24, *tool.GEOMETRY)
    image[52] = 1
    command = b'androidboot.hardware=ducati2fhd\0'
    image[512:512 + len(command)] = command
    if signed:
        wrapper = bytearray(0x400)
        wrapper[:4] = b'$OSM'
        image = image[:512] + wrapper + image[512:]
        image[52] = 0
        struct.pack_into('<I', image, 0x30, (len(image) - 512) // 512)
    checksum(image)
    return bytes(image)


class BootPackTests(unittest.TestCase):
    def inputs(self):
        kernel = bytearray(5000)
        kernel[0x202:0x206] = b'HdrS'
        ramdisk = gzip.compress(archive([('default.prop', b'ro.adb.secure=1\nro.secure=1\n')]), mtime=0)
        return bytes(kernel), ramdisk

    def test_unsigned_template_new_kernel_and_ramdisk(self):
        original = template()
        kernel, ramdisk = self.inputs()
        result, report = tool.pack(original, kernel, ramdisk)
        self.assertTrue(report['boot_key_audit_passed'])
        self.assertFalse(report['publication_approved'])
        self.assertFalse(report['signed_wrapper_removed'])
        self.assertEqual(result[0x3200:0x3200 + len(kernel)], kernel)
        self.assertEqual(struct.unpack_from('<I', result, 512 + 0x400)[0], 8192)
        self.assertNotIn(b'OLD-APPROVAL-FIXTURE', result)
        self.assertEqual(template(), original)

    def test_signed_stock_wrapper_is_not_reused(self):
        kernel, ramdisk = self.inputs()
        result, report = tool.pack(template(True), kernel, ramdisk)
        self.assertTrue(report['signed_wrapper_removed'])
        self.assertEqual(result[52], 1)
        self.assertNotEqual(result[512:516], b'$OSM')

    def test_bad_geometry_refused(self):
        image = bytearray(template())
        struct.pack_into('<I', image, 0x24, 12345)
        checksum(image)
        with self.assertRaises(ValueError):
            tool.pack(bytes(image), *self.inputs())

    def test_new_ramdisk_key_is_not_silently_removed(self):
        kernel, _ = self.inputs()
        ramdisk = gzip.compress(archive([('default.prop', b'ro.adb.secure=1\n'), ('adb_keys', b'fixture')]), mtime=0)
        with self.assertRaises(ValueError):
            tool.pack(template(), kernel, ramdisk)

    def test_personal_cmdline_refused(self):
        image = bytearray(template())
        command = b'androidboot.hardware=ducati2fhd androidboot.serialno=FAKE-TEST\0'
        image[512:512 + len(command)] = command
        with self.assertRaises(ValueError):
            tool.pack(bytes(image), *self.inputs())

    def test_existing_output_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'boot.img'
            output.write_bytes(b'KEEP')
            result = tool.main(['--template', 'missing', '--kernel', 'missing', '--ramdisk', 'missing', '--output', str(output)])
            self.assertEqual(result, 2)
            self.assertEqual(output.read_bytes(), b'KEEP')


if __name__ == '__main__':
    unittest.main()
