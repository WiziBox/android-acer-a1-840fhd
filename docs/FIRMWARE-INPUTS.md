# Owner firmware, calibration and matching Wi-Fi module

This stage is for a private A1-840FHD build. It does not grant firmware redistribution rights and does not authorize uploading a calibration file or whole output directory. Complete source/vendor preparation and [the kernel build](../kernel/README.md) first.

## Inputs

- Your extracted stock `system` directory, containing `etc/firmware/fw_sst_0f28.bin`, `aac_dec_0f28.bin` and `mp3_dec_0f28.bin`.
- The exact BCM43241 B4 production Wi-Fi firmware used by this port: SHA256 `0e53e2eadb22610c298df18b631f571d216a3eca3d537812a6f074337fb38eca`. Its development provenance is the official linux-firmware project, path `brcm/brcmfmac43241b4-sdio.bin`. Obtain that exact input under its upstream terms; do not substitute an arbitrary similarly named firmware. Firmware is not bundled here.
- Your own device's `bcmdhd_aob.cal_43241_b4`. Keep its MAC, country, RF power and calibration values unchanged. Do not use another device's factory partition or calibration file. The tool checks the reviewed profile `boardtype=0x5ef`, `boardrev=0x1100`, `sromrev=9`, but that is not a substitute for knowing the file belongs to your device.
- The new kernel build directory containing `build-receipt.json`, the kernel, configuration, public certificate and its freshly signed `wifi/bcm43241.ko`. Private `obj/signing_key.priv` is never copied by this tool.

## Stage into the prepared Android workspace

```sh
python3 tools/stage_firmware.py \
  --source /path/to/android9-source \
  --stock-system /path/to/extracted-stock-system \
  --kernel-build /path/to/new-kernel-build \
  --wifi-firmware /path/to/exact-brcmfmac43241b4-sdio.bin \
  --nvram /path/to/your-own-bcmdhd_aob.cal_43241_b4
# Repeat with --apply only after the read-only preflight succeeds.
```

The device tree and combined stock vendor import must already be present. The `vendor/acer/ducati2fhd/wifi` directory, three audio firmware destination files and firmware receipt must not exist. The tool validates all six inputs before creating destinations; it never resets or overwrites an existing vendor tree. Failure can leave new partial files: preserve and inspect them before retrying.

The build receipt must match the reviewed kernel patch/toolchain, and all four build artifact fingerprints must match that receipt. Signature enforcement and the configuration fingerprint are checked, along with x86 kernel/ELF32 signed-module format. This is receipt/hash/format validation, not an independent cryptographic proof that a fabricated receipt contains a matching trusted kernel/module. Use the actual output of the public kernel build, not an edited receipt or foreign module.

Calibration contents and MAC are not printed or included in the receipt. The calibration input is copied byte-for-byte and made owner-readable/writable on the build host. The eventual private system image still contains this owner input. **Do not upload that image without a separate full-image privacy and licensing review.** No tablet is contacted, flashed or rebooted by staging.

## Audio fingerprints

| Stock input | Bytes | SHA256 |
| --- | ---: | --- |
| `fw_sst_0f28.bin` | 851244 | `37c1b225972d7f16b5b633ef58776a00f9bc242b68716876fafdf3536d9abed0` |
| `aac_dec_0f28.bin` | 203804 | `c0ead6b124647983f070e26534513380c12207a2e0c71c6c49bc556a0fc68838` |
| `mp3_dec_0f28.bin` | 101578 | `0ac060b0a2603011c1badf3bb590cb8c25c6d145a8c473f31b0c5dcd072cf9a6` |

## Evidence

On 2026-10-11 staging all six real inputs succeeded in the separate Android verification tree using the freshly built kernel/module. Calibration was preserved; no private key was staged. Four synthetic tests cover calibration/profile validation, complete preflight, hash rejection and existing-output preservation. The local suite totals 86 passing tests. This does not prove Wi-Fi/audio operation of a complete new ROM or approve publication.
