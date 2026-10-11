# Guarded system installation from recovery

This tool writes only the A1-840FHD raw **system** partition. It is an implemented component of the full portable workflow, not a validated final release installer. It has synthetic safety tests; the new backend has not yet been exercised on a connected tablet. No currently private candidate is approved for public redistribution.

## Prerequisites and order

1. Identify your own Acer Iconia Tab 8 A1-840FHD and create a fresh [owner backup](OWNER-BACKUP.md) with `--include-system`. Keep its original header, reserved backup, system backup and private receipt together, outside GitHub. An old backup without the supported receipt is not silently accepted.
2. Prepare the matching boot/system/kernel-module pair. Validate and [expand the system image](SYSTEM-IMAGE-CHECK.md) into a new full 1887436800-byte raw file; independently record the **raw** SHA-256. Do not substitute the sparse input's hash or another model's image.
3. Enter a supported root-ADB recovery yourself, with stable power and local access to Droidboot/recovery. The tool does not reboot, root, unmount or repair a device. The system partition must already be unmounted, even if its mount would be read-only. Close other update/staging operations.
4. Stage the exact raw image into `/cache/acer-system-RAW_SHA256.raw.img`, replacing `RAW_SHA256` with the full lowercase checksum. Use the guarded staging command below; do not overwrite a previous cache image or remove unrelated cache files. This full raw file needs about 1.8 GiB plus a 16 MiB free-space reserve. If cache capacity or recovery identity cannot be established, stop instead of using userdata as an unchecked fallback.
5. Run the preflight below. Only after a successful system write/readback, apply the matching [boot container](BOOT-INSTALLATION.md). Neither tool automatically reboots. Booting mismatched components can fail.

This procedure does not currently supply a complete factory restoration workflow. The saved system/reserved files are not generic flashable containers. Keep local recovery available; never `dd` another tablet's GPT/reserved/factory data to this device.

## Default preflight

First check the host raw image and recovery cache without uploading:

```sh
python3 tools/stage_system.py \
  --adb /path/to/platform-tools/adb \
  --serial YOUR_OWN_DEVICE_SERIAL \
  --input /path/to/private/system.raw.img \
  --raw-sha256 YOUR_RAW_IMAGE_LOWERCASE_SHA256
```

After a successful check, repeat with `--apply` to upload only the cache file, **not** to flash. The tool checks raw ext4 geometry/hash, exact model/layout, recovery, unmounted system and writable real cache. It requires `stat -f -c "%a:%S" /cache`; unsupported capacity queries cause refusal. It uploads into a newly created private cache directory, verifies size/hash, then uses a hard link that refuses an existing checksum-named destination. Successful staging removes only that owned temporary file and empty directory. Failure preserves partial files, performs no retry and does not flash/reboot. This staging backend has synthetic tests, not hardware acceptance. Legacy header acquisition requires the same explicit `--legacy-header-staging` option described below and writes a temporary header even without `--apply`.

Then run the separate installation preflight:

```sh
python3 tools/flash_system.py \
  --adb /path/to/platform-tools/adb \
  --serial YOUR_OWN_DEVICE_SERIAL \
  --owner-backup /path/to/private/backup \
  --raw-sha256 YOUR_RAW_IMAGE_LOWERCASE_SHA256 \
  --remote-image /cache/acer-system-YOUR_RAW_IMAGE_LOWERCASE_SHA256.raw.img
```

On Windows use `python`, `adb.exe`, and quoted paths. Default header acquisition uses `adb exec-out`. There is no automatic legacy fallback. If your recovery lacks this protocol, explicitly add `--legacy-header-staging`: this mode creates a unique private `/tmp` directory and 20480-byte header file, pulls it into a private host temporary directory, checks the hash, and removes only its exact owned file and empty directory. **This opt-in preflight therefore writes temporary files, but never a block partition.** Any failure stops the procedure; no root enabling, recursive cleanup or reboot follows.

The preflight checks the selected serial's backup/receipt hashes, exact model properties, existing root, current primary GPT/OSIP layout and live partition/media sizes. It also requires `ro.bootmode=recovery`, the recovery marker, the expected Intel system block alias, no system mount, the exact regular staged-file size and its SHA-256. Cache staging must resolve to the unchanged checksum-named path on one writable ext4 `/cache` mount backed by the reviewed `mmcblk0p7`; redirected paths, nested cache mounts, RAM-backed cache and userdata staging are refused. This mount/path check is repeated immediately before writing. It does not reserve free space or make the operation atomic against concurrent root changes. Missing properties, unsupported stat/hash commands or unexpected recovery formats cause refusal, not relaxed checks. A successful old hand-written flash is not evidence that this newer automated backend works in that recovery.

## Explicit write and readback

Repeat a successful command with `--apply` to authorize only the system write. The tool rechecks the saved current header and mount inventory immediately before writing, runs `dd` to the reviewed `mmcblk0p9` partition, flushes writes, hashes the whole partition and checks the header again. It does not upload the image, erase userdata, write boot/GPT, remove the staged system file, reboot or retry.

Do not change staging files, mount partitions or run other privileged updates concurrently. These checks are not an atomic transaction against other root processes. Disconnection or power loss can leave an incomplete system partition. Any failure must be investigated while recovery remains available; do not treat a timeout or partial write as success and do not blindly retry/reboot.

Success reports `system_readback_verified=true`, but `installation_boot_verified=false` and `publication_approved=false`. Complete rollback/restoration and exact-artifact boot/display/touch/Wi-Fi/storage/media/sleep checks remain required before claiming final release acceptance. Private calibration, credentials, Google/vendor licensing and whole-ROM content review are separate gates.
