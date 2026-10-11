# Owner backup before installation

These tools are for your own **Acer Iconia Tab 8 A1-840FHD**, not any device identified only as `baylake`. They read the selected device and create private host backups; they never flash, reboot, remount, erase, enable root or change ADB authentication. Use a stable powered USB connection and an authenticated, already-authorized root ADB session.

## Supported backend and scope

`backup_acer.py` currently supports the Android 9 `adb exec-out` backend. It requires exact `Acer` / `A1-840FHD` / `ducati2fhd` properties, existing root, the reviewed OSIP layout, primary GPT CRCs and live sysfs partition/media matches. Stock KitKat adbd may not support this raw backend: it fails rather than silently using a device-staging workaround. Legacy backup acquisition still needs a separate supported procedure.

Default backup scope is the first 40 disk sectors plus `reserved` (234881024 bytes). These contain the OSIP/GPT header and boot/recovery/Droidboot area. `--include-system` adds the 1887436800-byte raw system partition. A writable system mount is refused, including recognized block aliases. Source hashes are compared after streaming each partition; the full header/layout is checked again at the end. This is not an atomic snapshot under concurrent privileged partition writes: stop OTA/update operations first.

**This is not a complete device backup.** Userdata, factory, config, FWUP, eMMC boot hardware areas and the alternate GPT are not all copied. Do not erase those regions or assume these backups recover every possible failure. A system backup of a running LineageOS port is a rollback copy of that port, not the original stock image required by vendor extraction.

## Read-only preflight

Use official Android Platform Tools and Python 3.9+. Explicitly select the serial from `adb devices -l`; the tool does not choose a device automatically. Output must be a new private directory **outside this repository**, under an existing parent with sufficient free space.

```sh
python3 tools/backup_acer.py \
  --adb /path/to/platform-tools/adb \
  --serial YOUR_OWN_DEVICE_SERIAL \
  --output /path/to/private/new-acer-backup \
  --include-system
```

On Windows, use `python`, quote paths and provide `adb.exe`. The tool streams binary data directly into a Python file handle; it does not use PowerShell's text redirection for images. The preflight performs device reads, including a 20480-byte header read, but does not create the backup output or write the device. Existing root via adbd or `su` is required; any root permission prompt remains your responsibility.

## Explicitly create the private backup

Repeat the successful preflight command with `--apply`. With system included, allow at least about 2.1 GB of free host space and several minutes. No device temporary file is created. Failure preserves any new partial backup directory; do not use its images as a verified rollback set and do not overwrite it on retry.

The resulting `private-backup-receipt.json` contains the selected serial, layout and hashes **only in the private folder**. Console output does not print serials, GUIDs or image hashes. Keep the untouched backups and receipt together, preferably with a second offline copy. On Linux the tool restricts permissions; on Windows also ensure your account's NTFS ACL protects the folder. Do not upload any backup, receipt, approval key or factory data to GitHub.

You can inspect the saved header without contacting the tablet:

```sh
python3 tools/acer_layout.py /path/to/private/new-acer-backup/acer-disk-header.bin
```

This validates the supported OSIP descriptors, primary GPT header/table CRCs, partition bounds/non-overlap and reserved/system roles. It does not output device/partition GUIDs or establish device identity by itself. Use [owner-template extraction](BOOT-PACKAGING.md) only with the corresponding private reserved backup. Never `dd` an OSIP container to a disk or copy another tablet's header/factory data.

## Evidence and remaining work

The offline layout parser passed against the actual original owner header, confirming reserved start 40 / 458752 sectors and system index 9 / 3686400 sectors. Six synthetic layout tests cover CRC corruption, bounds, overlaps and incorrect roles. Seven backup tests cover model/live-layout refusal, writable mounts, dry-run/output preservation and binary-transfer/hash handling.

The new live backup backend has **not yet been exercised on a connected tablet**. Its tests and the original-header checks do not prove a complete device backup or successful restoration. Installation/recovery integration and exact-artifact hardware verification remain mandatory; this document is not authorization for an unattended flash.
