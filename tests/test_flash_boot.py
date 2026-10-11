# SPDX-License-Identifier: Apache-2.0
import hashlib
import contextlib
import io
import json
from pathlib import Path
import tempfile
import sys
import struct
import unittest
from unittest.mock import patch
import test_pack_boot as fixtures
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import flash_boot as tool
from pack_boot import pack
from test_acer_layout import owner_header
from test_extract_boot_template import checksum
import verify_owner_backup as backup_tools


class Client:
    def __init__(self, product='baylake', serial='SYNTHETIC', acknowledgement=True):
        self.calls, self.product, self.serial, self.acknowledgement = [], product, serial, acknowledgement

    def run(self, args, timeout=30):
        self.calls.append(args)
        if args[:1] == ['getvar']:
            value = self.product if args[1] == 'product' else self.serial
            return '(bootloader) ' + args[1] + ': ' + value + '\nFinished.\n'
        return "Sending 'boot' OKAY\nWriting 'boot' OKAY\n" if self.acknowledgement else "Sending 'boot' OKAY\n"


class FlashBootTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / 'candidate.img'
        kernel, ramdisk = fixtures.BootPackTests().inputs()
        self.image.write_bytes(pack(fixtures.template(), kernel, ramdisk)[0])
        self.sha = hashlib.sha256(self.image.read_bytes()).hexdigest()
        (self.root / 'private-backup-receipt.json').write_text(json.dumps({'serial': 'SYNTHETIC'}))
        self.mock = patch.object(tool, 'verify', return_value={'saved_receipt_checksums_matched': True})
        self.mock.start()
        self.addCleanup(self.mock.stop)

    def invoke(self, client, **kwargs):
        return tool.install(client, self.image, self.sha, self.root, 'SYNTHETIC', **kwargs)

    def test_dry_run_only_reads_identity(self):
        client = Client()
        report = self.invoke(client)
        self.assertEqual(client.calls, [['getvar', 'product'], ['getvar', 'serialno']])
        self.assertFalse(report['applied'])
        self.assertFalse(report['current_gpt_layout_read_back'])

    def test_apply_requires_separate_risk_acceptance(self):
        client = Client()
        with self.assertRaises(ValueError):
            self.invoke(client, apply=True)
        self.assertFalse(any(call[0] == 'flash' for call in client.calls))

    def test_boot_only_no_reboot_or_erase(self):
        client = Client()
        report = self.invoke(client, apply=True, accept_no_live_layout=True)
        self.assertEqual(client.calls[-1], ['flash', 'boot', str(self.image.resolve())])
        self.assertEqual(len(client.calls), 3)
        self.assertTrue(report['boot_write_acknowledged'])
        self.assertFalse(report['boot_readback_verified'])
        self.assertFalse(report['reboot'])

    def test_wrong_product_and_serial_refused(self):
        for client in (Client(product='other'), Client(serial='OTHER')):
            with self.assertRaises(ValueError):
                self.invoke(client, apply=True, accept_no_live_layout=True)
            self.assertFalse(any(call[0] == 'flash' for call in client.calls))

    def test_checksum_refused_before_device_io(self):
        client = Client()
        self.image.write_bytes(self.image.read_bytes() + b'X')
        with self.assertRaises(ValueError):
            self.invoke(client)
        self.assertEqual(client.calls, [])

    def test_old_approval_image_refused(self):
        self.image.write_bytes(fixtures.template())
        self.sha = hashlib.sha256(self.image.read_bytes()).hexdigest()
        client = Client()
        with self.assertRaises(ValueError):
            self.invoke(client)
        self.assertEqual(client.calls, [])

    def test_incomplete_acknowledgement_not_success(self):
        client = Client(acknowledgement=False)
        with self.assertRaises(ValueError):
            self.invoke(client, apply=True, accept_no_live_layout=True)
        self.assertEqual(len(client.calls), 3)

    def test_backup_mismatch_before_device_io(self):
        with patch.object(tool, 'verify', side_effect=ValueError('checksum differs')):
            client = Client()
            with self.assertRaises(ValueError):
                self.invoke(client)
            self.assertEqual(client.calls, [])

    def test_real_synthetic_backup_receipt_integration(self):
        header = owner_header()
        payloads = (fixtures.template(True)[512:], fixtures.template()[512:], fixtures.template(True)[512:])
        for index, payload in enumerate(payloads):
            struct.pack_into('<I', header, 48 + index * 24, len(payload) // 512)
        checksum(header)
        hp, rp = self.root / 'acer-disk-header.bin', self.root / 'acer-reserved.img'
        hp.write_bytes(header)
        with rp.open('wb') as stream:
            stream.truncate(backup_tools.RESERVED_BYTES)
            for entry, payload in zip(backup_tools.records(header, backup_tools.RESERVED_BYTES), payloads):
                stream.seek(entry[-2])
                stream.write(payload)
        verification = backup_tools.verify(hp, rp)
        receipt = {'serial': 'SYNTHETIC', 'applied': True, 'model_checked': True,
                   'live_layout_checked': True, 'layout': backup_tools.layout(header),
                   'files': verification['files']}
        (self.root / 'private-backup-receipt.json').write_text(json.dumps(receipt))
        with patch.object(tool, 'verify', backup_tools.verify):
            client = Client()
            self.assertTrue(self.invoke(client)['backup_checksums_matched'])
            self.assertEqual(len(client.calls), 2)

    def test_wrong_receipt_serial_before_device_io(self):
        (self.root / 'private-backup-receipt.json').write_text(json.dumps({'serial': 'OTHER'}))
        client = Client()
        with self.assertRaises(ValueError):
            self.invoke(client)
        self.assertEqual(client.calls, [])

    def test_non_object_receipt_refused_without_traceback(self):
        for value in ([], 'PRIVATE_FIXTURE_DO_NOT_PRINT', None, 7):
            (self.root / 'private-backup-receipt.json').write_text(json.dumps(value))
            client = Client()
            with self.assertRaises(ValueError):
                self.invoke(client)
            self.assertEqual(client.calls, [])

    def test_cli_failure_never_prints_receipt_or_paths(self):
        (self.root / 'private-backup-receipt.json').write_text(json.dumps('PRIVATE_FIXTURE_DO_NOT_PRINT'))
        output, errors = io.StringIO(), io.StringIO()
        client = Client()
        with patch.object(tool, 'Fastboot', return_value=client), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = tool.main(['--fastboot', 'unused', '--serial', 'SYNTHETIC',
                              '--image', str(self.image), '--sha256', self.sha,
                              '--owner-backup', str(self.root)])
        self.assertEqual(code, 2)
        self.assertNotIn('PRIVATE_FIXTURE_DO_NOT_PRINT', output.getvalue())
        self.assertNotIn(str(self.root), output.getvalue())
        self.assertEqual(errors.getvalue(), '')
        self.assertEqual(client.calls, [])
