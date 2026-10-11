# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
try:
    import stage_firmware as tool
finally:
    sys.path.pop(0)


class FirmwareTests(unittest.TestCase):
    CAL = b'boardtype=0x5ef\nboardrev=0x1100\nsromrev=9\nmacaddr=02:00:00:00:00:01\n'

    def fixture(self, folder):
        root = Path(folder)
        source, stock, build = root / 'android', root / 'stock', root / 'kernel-build'
        vendor = source / 'vendor/acer/ducati2fhd'
        (vendor / 'audio-deployment').mkdir(parents=True)
        (vendor / 'vendor-stock.mk').write_text('fixture')
        device = source / 'device/acer/ducati2fhd'
        device.mkdir(parents=True)
        (device / 'BoardConfig.mk').write_text('fixture')
        (stock / 'etc/firmware').mkdir(parents=True)
        audio = {}
        for name in tool.AUDIO:
            data = ('fixture-' + name).encode()
            (stock / 'etc/firmware' / name).write_bytes(data)
            audio[name] = (len(data), hashlib.sha256(data).hexdigest())
        wifi, nvram = root / 'wifi.bin', root / 'owner.cal'
        wifi.write_bytes(b'wifi-fixture')
        nvram.write_bytes(self.CAL)
        index = json.loads((ROOT / 'kernel/inputs.json').read_text())
        kernel = bytearray(0x206)
        kernel[0x202:0x206] = b'HdrS'
        payloads = {'kernel': bytes(kernel), 'wifi_module': b'\x7fELF\x01fixture~Module signature appended~\n',
                    'config': (ROOT / 'kernel/ducati2fhd.config').read_bytes(), 'public_certificate': b'public-fixture'}
        artifacts = {}
        for name, data in payloads.items():
            path = build / tool.BUILD_PATHS[name]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            artifacts[name] = {'path': tool.BUILD_PATHS[name], 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        receipt = {'kernel_and_wifi_built': True, 'source_patch_sha256': index['patch_sha256'],
                   'toolchain_commit': index['toolchain']['commit'], 'artifacts': artifacts}
        (build / 'build-receipt.json').write_text(json.dumps(receipt))
        return source, stock, build, wifi, nvram, vendor, audio

    def test_calibration_profile_and_authentication_rejection(self):
        self.assertEqual(tool.calibration(self.CAL), self.CAL)
        for data in (self.CAL.replace(b'0x5ef', b'0xffff'), self.CAL + b'boardrev=0x1100\n',
                     self.CAL + b'key=-----BEGIN RSA PRIVATE KEY-----\n', b'\0'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                tool.calibration(data)

    def test_dry_run_apply_and_calibration_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            source, stock, build, wifi, nvram, vendor, audio = self.fixture(folder)
            with mock.patch.dict(tool.AUDIO, audio), mock.patch.object(tool, 'WIFI_SHA', hashlib.sha256(wifi.read_bytes()).hexdigest()):
                self.assertTrue(tool.stage(source, stock, build, wifi, nvram)['dry_run'])
                self.assertFalse((vendor / 'wifi').exists())
                result = tool.stage(source, stock, build, wifi, nvram, True)
                self.assertEqual(result['files_verified'], 6)
                self.assertFalse(result['image_publication_approved'])
                self.assertEqual((vendor / 'wifi/bcmdhd_aob.cal_43241_b4').read_bytes(), self.CAL)
                self.assertNotIn('02:00:00', (vendor / 'firmware-staging-receipt.json').read_text())
                with self.assertRaises(ValueError):
                    tool.stage(source, stock, build, wifi, nvram, True)

    def test_saved_networks_never_accepted_as_calibration(self):
        for field in (b'ssid=PRIVATE_SYNTHETIC', b'PSK=PRIVATE_SYNTHETIC',
                      b'password=PRIVATE_SYNTHETIC', b'passphrase=PRIVATE_SYNTHETIC',
                      b'network={'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                tool.calibration(self.CAL + field + b'\n')

    def test_bad_module_writes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            source, stock, build, wifi, nvram, vendor, audio = self.fixture(folder)
            (build / tool.BUILD_PATHS['wifi_module']).write_bytes(b'tampered-module')
            with mock.patch.dict(tool.AUDIO, audio), mock.patch.object(tool, 'WIFI_SHA', hashlib.sha256(wifi.read_bytes()).hexdigest()):
                with self.assertRaises(ValueError):
                    tool.stage(source, stock, build, wifi, nvram, True)
            self.assertFalse((vendor / 'wifi').exists())

    def test_existing_audio_file_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            source, stock, build, wifi, nvram, vendor, audio = self.fixture(folder)
            target = vendor / 'audio-deployment/fw_sst_0f28.bin'
            target.write_bytes(b'KEEP')
            with mock.patch.dict(tool.AUDIO, audio), mock.patch.object(tool, 'WIFI_SHA', hashlib.sha256(wifi.read_bytes()).hexdigest()):
                with self.assertRaises(ValueError):
                    tool.stage(source, stock, build, wifi, nvram, True)
            self.assertEqual(target.read_bytes(), b'KEEP')
            self.assertFalse((vendor / 'wifi').exists())


if __name__ == '__main__':
    unittest.main()
