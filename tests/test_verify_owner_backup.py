# SPDX-License-Identifier: Apache-2.0
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from test_pack_boot import template
from test_acer_layout import owner_header
from test_extract_boot_template import checksum

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
spec = importlib.util.spec_from_file_location('verify_owner', ROOT / 'tools/verify_owner_backup.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class OwnerBackupTests(unittest.TestCase):
    @staticmethod
    def member(name, data=b'', crc=False):
        encoded = name.encode() + b'\0'
        fields = [0] * 13
        fields[6], fields[11] = len(data), len(encoded)
        fields[12] = sum(data) & 0xffffffff if crc else 0
        result = (b'070702' if crc else b'070701') + ''.join('%08x' % item for item in fields).encode() + encoded
        result += bytes((-len(result)) % 4)
        result += data
        return result + bytes((-len(result)) % 4)

    def test_legacy_duplicates_counted_but_new_rom_refuses(self):
        raw = self.member('init', b'a') + self.member('./init', b'b') + self.member('TRAILER!!!')
        self.assertEqual(tool.legacy_recovery_inventory(raw), (2, 1))
        with self.assertRaises(ValueError):
            list(tool.cpio_entries(raw))

    def test_legacy_unsafe_truncated_and_trailing_data_refused(self):
        for raw in (self.member('../key') + self.member('TRAILER!!!'),
                    self.member('/init') + self.member('TRAILER!!!'),
                    self.member('init', b'123')[:-1],
                    self.member('TRAILER!!!') + b'X'):
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                tool.legacy_recovery_inventory(raw)

    def test_legacy_crc_checked(self):
        raw = self.member('init', b'ABC', crc=True) + self.member('TRAILER!!!')
        self.assertEqual(tool.legacy_recovery_inventory(raw), (1, 0))
        changed = raw.replace(b'ABC', b'ABD', 1)
        with self.assertRaises(ValueError):
            tool.legacy_recovery_inventory(changed)

    def test_unsigned_and_signed_payload(self):
        for signed, attribute in ((False, 1), (True, 14)):
            report = tool.payload_check(template(signed)[512:], attribute)
            self.assertTrue(report['structure_checked'])
            self.assertFalse(report['oem_signature_cryptographically_verified'])

    def test_recovery_partial_sector_erased_padding_only(self):
        payload = template(False)[512:]
        kernel, ramdisk = struct.unpack_from('<II', payload, 0x400)
        end = 0x3000 + kernel + ramdisk
        padded = payload[:end] + bytes([255]) * (len(payload) - end)
        self.assertGreater(len(payload) - end, 0)
        self.assertEqual(tool.payload_check(padded, 13)['last_sector_padding'], 'erased_ff')
        with self.assertRaises(ValueError):
            tool.payload_check(padded, 1)

    def test_unknown_and_full_sector_trailers_refused(self):
        payload = template(False)[512:]
        for tail in (b'NOT_A_PADDING', bytes([255]) * 512):
            with self.subTest(size=len(tail)), self.assertRaises(ValueError):
                tool.payload_check(payload + tail, 13)

    def test_signed_wrapper_missing(self):
        with self.assertRaises(ValueError):
            tool.payload_check(template(False)[512:], 14)

    def test_digest_exact_size(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'backup'
            path.write_bytes(b'SYNTHETIC')
            self.assertEqual(len(tool.digest(path, 9)), 64)
            with self.assertRaises(ValueError):
                tool.digest(path, 10)

    def test_three_payloads_and_privacy_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            header = owner_header()
            payloads = (template(True)[512:], template(False)[512:], template(True)[512:])
            for index, payload in enumerate(payloads):
                struct.pack_into('<I', header, 48 + index * 24, len(payload) // 512)
            checksum(header)
            (root / 'header.bin').write_bytes(header)
            with (root / 'reserved.img').open('wb') as stream:
                stream.truncate(tool.RESERVED_BYTES)
                for entry, payload in zip(tool.records(header, tool.RESERVED_BYTES), payloads):
                    stream.seek(entry[-2])
                    stream.write(payload)
            report = tool.verify(root / 'header.bin', root / 'reserved.img')
            self.assertEqual(len(report['osip_payloads']), 3)
            self.assertFalse(report['saved_receipt_checksums_matched'])
            self.assertFalse(report['restoration_verified'])
            self.assertFalse(report['publication_approved'])
            self.assertFalse(report['device_io'])
            receipt = {'applied': True, 'model_checked': True, 'live_layout_checked': True,
                       'layout': tool.layout(header), 'files': report['files']}
            receipt_path = root / 'receipt.json'
            receipt_path.write_text(json.dumps(receipt))
            matched = tool.verify(root / 'header.bin', root / 'reserved.img', receipt_path=receipt_path)
            self.assertTrue(matched['saved_receipt_checksums_matched'])
            receipt['files'][0]['sha256'] = '0' * 64
            receipt_path.write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):
                tool.verify(root / 'header.bin', root / 'reserved.img', receipt_path=receipt_path)


if __name__ == '__main__':
    unittest.main()
