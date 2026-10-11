# Compose a private owner system image without rebuilding

Linux/WSL, Python 3.9+, `debugfs` and `e2fsck` are required. This is a host-only packaging step, not a downloader or installer. No currently private candidate is approved for a public ROM release.

Use a reviewed, checksum-identified **raw** system image with its calibration destination absent. Obtain your own A1-840FHD calibration with [owner stock extraction](VENDOR-INPUTS.md). Do not use another tablet's file. A board-profile check cannot prove ownership or identify a tablet from an offline image.

```sh
python3 tools/compose_owner_image.py \
  --device acer-a1-840fhd \
  --input /path/to/private/reviewed-base.raw.img \
  --base-sha256 YOUR_BASE_RAW_SHA256 \
  --calibration /path/to/private/stock-inputs/etc/firmware/bcmdhd_aob.cal_43241_b4 \
  --output /path/to/private/new-owner-system.raw.img
```

Default execution only checks inputs. After success, repeat with **both** `--apply --confirm-owner-input` to create a new private host file. Output must be outside this repository and not already exist. Originals are preserved; partial new files remain on failure, without automatic retry or deletion.

The tool checks the full base checksum, raw ext4 magic/partition length and read-only filesystem consistency. It requires real firmware directories and refuses an existing calibration destination. It validates the calibration profile and rejects saved network credentials or authentication material, then preserves the bytes exactly. It writes only `/vendor/firmware/bcmdhd_aob.cal_43241_b4` into the new copy, sets root ownership, mode 0644 and `u:object_r:vendor_file:s0`, and independently reads back contents, permissions and label. Filesystem consistency and the unchanged original checksum are checked again.

The success report includes the **private whole-image** checksum, not the calibration checksum or MAC. Keep the output, source calibration and report private. The added owner input makes the resulting image unsuitable for public upload. Publication approval always remains false. This bounded operation does not audit other base contents, establish licensing, verify a kernel/module pair, boot the device or supply restoration.

On 2026-10-11 the actual host-only composition completed for the private Acer candidate, including calibration contents/permissions/label readback and filesystem checks. Nine synthetic tests cover dry-run, new outputs, owner confirmation, credentials, profile/hash/raw rejection, failed readback and non-disclosure. No device installation was exercised.

Use the resulting new hash for [cache staging and system installation](SYSTEM-INSTALLATION.md), not the base hash. Those tools' hardware acceptance and complete rollback are still unfinished; this command does not authorize flashing.
