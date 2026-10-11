# Guarded boot-only installation

This component supports the Acer Iconia Tab 8 A1-840FHD's Android **boot** container through Droidboot. It is not the complete ROM installer: system installation, exact-artifact boot testing and OSIP-aware recovery remain separate requirements. The new tool has synthetic tests, including an actual synthetic backup/receipt parser integration, but has **not been exercised on a tablet**. Do not treat its acknowledgement as readback or successful boot.

The instructions below are for normal new-ROM installation. A separate explicit [exact-owner boot rollback mode](OWNER-ROLLBACK.md) accepts only the container independently extracted from the same checked private backup. It preserves that saved firmware's security policy and supported signature wrapper; it does not relax normal candidate requirements or provide complete factory restoration.

## Prerequisites

- Your own new unsigned OSIP boot candidate from [boot packaging](BOOT-PACKAGING.md), its independently recorded SHA-256, and the matching installed system/kernel-module pair. Mixing versions can prevent boot.
- A private backup directory produced by [the supported backup backend](OWNER-BACKUP.md), containing `acer-disk-header.bin`, `acer-reserved.img`, and `private-backup-receipt.json`. Do not fabricate a receipt for an older backup. The checker verifies its recorded checksums and supported saved layout before any fastboot operation.
- Official Platform Tools, Python 3.9+, the exact selected device serial, stable power and a working local recovery path. Enter Droidboot yourself. The tool does not reboot Android into Droidboot.

`baylake` alone is not model identification. The tool requires the previously exact-model-checked backup receipt and matching current fastboot serial/product. Receipts are private local evidence, not cryptographically signed device certificates. No current GPT readback is available in this backend; if the disk was repartitioned after backup or the device identity cannot be established, stop and obtain a fresh supported backup instead.

## Dry-run preflight

```sh
python3 tools/flash_boot.py \
  --fastboot /path/to/platform-tools/fastboot \
  --serial YOUR_OWN_DEVICE_SERIAL \
  --owner-backup /path/to/private/backup \
  --image /path/to/new/boot.img \
  --sha256 YOUR_INDEPENDENTLY_RECORDED_LOWERCASE_SHA256
```

On Windows, use `python`, `fastboot.exe`, and quote paths. Default operation validates local inputs and reads only `getvar product` and `getvar serialno`. It does not record images, erase anything, reboot, or create a report. Console output omits the serial, backup hashes and owner file contents.

The candidate must satisfy the reviewed single-descriptor geometry and payload-size bound, and pass the bounded secure-ADB ramdisk audit. This is not whole-ROM privacy, licensing or hardware verification. Do not modify the image or backup while the tool is running.

## Explicit boot write

Only after reviewing the dry-run, matching system and rollback prerequisites, repeat the same command with **both** `--apply --accept-no-live-layout-readback`. The second flag explicitly acknowledges the lack of current GPT readback; it is not a way to skip checksum/model/backup checks.

The tool sends only `fastboot flash boot ...` and requires both sending and writing acknowledgements. It never runs `erase`, `format`, a system flash, a raw sector write or automatic reboot/retry. An error may occur after a partial boot write: keep Droidboot available and inspect the failure rather than blindly retrying or rebooting. The owner's untouched backup remains private and unchanged.

Even a successful acknowledgement leaves `boot_readback_verified=false` and `installation_boot_verified=false`. A supported recovery/restoration procedure and exact-artifact hardware acceptance are still required before this repository can claim a final portable ROM release. Never write an OSIP container to an eMMC partition using `dd`, or replace GPT/factory data with another tablet's backup.
