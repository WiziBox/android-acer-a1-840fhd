# Restore the saved owner boot and system pair

This describes implemented rollback components, **not** a hardware-validated complete recovery guarantee. No device write is authorized by this document. Keep local access to recovery/Droidboot and stable power. These tools do not restore factory/config/userdata/GPT, recovery or Droidboot regions.

Use the same tablet's completed [owner backup](OWNER-BACKUP.md), including system and its original private receipt. A loose old backup without the supported receipt is not silently accepted. A pre-installation LineageOS backup rolls back to that version; it is not automatically a factory-stock backup. Never copy another tablet's disk header or reserved partition.

## 1. Verify and export the saved Android boot

Run the offline backup verifier with its receipt and system file, as documented in the owner-backup guide. Then create a new private Android boot container:

```sh
python3 tools/extract_boot_template.py \
  --disk-header /path/to/private/backup/acer-disk-header.bin \
  --reserved-backup /path/to/private/backup/acer-reserved.img \
  --output /path/to/private/new-owner-rollback-boot.img
```

Check the extractor's command syntax with `--help` if using a different repository revision. The container preserves the saved Android payload, old ramdisk and supported signed wrapper, but normalizes the exported OSIP descriptor. This is not an image to `dd` onto eMMC. Keep its hash private; the old firmware may contain personal approvals or insecure defaults.

## 2. Restore system first, if necessary

Use the saved `acer-system.img` as the raw input to [cache staging and system installation](SYSTEM-INSTALLATION.md), with its own complete SHA-256, the same serial and system-inclusive backup receipt. Do not use a new ROM hash or apply owner composition to a rollback image that already contains calibration. Recovery, layout and unmounted-system checks still apply. Stop on any failure; neither tool reboots or retries.

If only boot changed and system remains the saved version, a system write is not automatically necessary. Verify that the selected kernel, module and system are the matching saved pair before booting. Do not restore boot against an unrelated system.

## 3. Exact saved boot preflight in Droidboot

Enter Droidboot manually, then run:

```sh
python3 tools/flash_boot.py \
  --fastboot /path/to/platform-tools/fastboot \
  --serial YOUR_OWN_DEVICE_SERIAL \
  --owner-backup /path/to/private/backup \
  --image /path/to/private/new-owner-rollback-boot.img \
  --sha256 YOUR_PRIVATE_ROLLBACK_BOOT_SHA256 \
  --restore-owner-boot
```

The default is preflight only. Restore mode independently verifies the matching private header/reserved receipt, extracts a temporary private container, and requires byte-for-byte equality with the selected image. It is **not** permission to accept an arbitrary signed, insecure or credential-containing image. Current Droidboot serial/product must match the exact-model backup receipt. The old saved security policy is preserved, not presented as safe public ROM policy. Normal installation mode still requires an unsigned secure-ADB candidate.

Only after a successful preflight and explicit local authorization, repeat with **both** `--apply --accept-no-live-layout-readback`. This writes boot only. Live GPT and boot readback are unavailable in this backend; acknowledgements do not prove restored bootability. No reboot, erase, system write or retry follows automatically. Preserve recovery access and investigate incomplete acknowledgements instead of blindly rebooting.

Synthetic coverage includes actual generated header/reserved/receipt extraction and exact-container comparison, signed/unsigned saved containers, altered images and owner-payload mismatch. Hardware restoration and subsequent display/touch/Wi-Fi/storage/media/sleep checks are still required. `complete_factory_restore` and publication approval remain false.
