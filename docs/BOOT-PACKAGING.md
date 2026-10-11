# Acer OSIP boot packaging

The A1-840FHD does not use a generic Android `boot.img` partition layout. This tool creates a **single-image Droidboot OSIP container**, not a raw eMMC image. Never `dd` this file into a disk, reserved area, GPT/MBR or a guessed partition.

## Required inputs

1. Your own supported Android boot OSIP template, backed up using a device/layout-aware workflow. The container must have one descriptor, the reviewed Android geometry (LBA 36050, load `0x1100000`, entry `0x1101000`) and an actual `ducati2fhd` bootstub command line. A whole disk dump or recovery/Droidboot image is not an acceptable template. Offline extraction from existing supported backups is implemented below. Live backup acquisition and flashing/recovery integration are still being completed; do not invent a raw-read/write command from these numbers.
2. The new `obj/arch/x86/boot/bzImage` from the public kernel build, paired with the module staged into this Android build. Do not mix kernels and modules from different signing keys.
3. The fresh Android product `ramdisk.img` from the completed build. Old diagnostic ramdisks are not substitutes for the final fresh build.

The template's bootstub and command line are preserved except for size fields. This means stock and already-working port templates may retain different boot policy/debug arguments. Those differences require review and boot testing; passing the structural checks does not make a stock command line correct for the new ROM. A literal embedded `androidboot.serialno` or PEM key marker in the preserved prefix is refused rather than published.

## Extract your private template from existing owner backups

The offline extractor accepts the reviewed layout: a 20480-byte disk-header backup and a 234881024-byte reserved-area backup beginning at LBA 40. These are **separate, previously acquired backups from your own supported tablet**, not the new OSIP container or another owner's dump. It requires the observed three OSIP pointers / one image field, checks the header checksum, all descriptor geometries, attributes, bounds and non-overlap, then reads only the Android payload. Android may occupy the observed original LBA 36050 or unsigned alternate LBA 68050; recovery and Droidboot locations remain fixed. It does not accept arbitrary relocated images. It does not prove the integrity of the rest of a backup or establish a connected device's identity.

```sh
python3 tools/extract_boot_template.py \
  --disk-header /path/to/private/your-disk-header.bin \
  --reserved-backup /path/to/private/your-reserved-area.img \
  --output /path/to/private/new-owner-android-template.img
```

The output must be new. The original Android payload, signed wrapper if present, and old ramdisk are preserved exactly. The exported single-image descriptor is normalized to the supported Droidboot input geometry: LBA 36050, load `0x1100000`, entry `0x1101000`. This is necessary when the source payload occupies the alternate slot or recovery has invalidated the main descriptor's load/entry pair to `(0, 0)`. Mixed zero/nonzero address pairs and invalidated recovery/Droidboot descriptors are refused. These are container fields, **not instructions to write raw eMMC sectors**. GPT/MBR and other OSIP descriptors are not exported. The tool validates the actual hardware bootstub, kernel and ramdisk layout. It refuses unexpected layouts rather than guessing offsets. No ADB, fastboot, mount or device write occurs.

**Keep this template private.** An existing owner's ramdisk can contain old ADB approval keys or development policy. Extracting it is not sanitization or permission to publish it. The packer below replaces its entire old ramdisk with the freshly built one and independently audits the replacement. A structurally valid rollback template is not proof that restoration was exercised; preserve the untouched complete backups too.

## Create a new candidate

From this distribution repository:

```sh
python3 tools/pack_boot.py \
  --template /path/to/your-own-supported-android-osip.img \
  --kernel /path/to/new-kernel-build/obj/arch/x86/boot/bzImage \
  --ramdisk /path/to/new-android-output/target/product/ducati2fhd/ramdisk.img \
  --output /path/to/new-private-boot-candidate.img
python3 tools/audit_boot.py --device acer-a1-840fhd /path/to/new-private-boot-candidate.img
```

The output must not exist. The tool checks the descriptor checksum/size, hardware command line, original kernel/ramdisk ranges and archive format before packaging. It aligns the new kernel allocation to 4096 bytes, updates ramdisk and descriptor sizes and the header XOR checksum, and retains the bootstub's other bytes. It applies a conservative 32000-sector payload limit used by the development packers. This is not a universal firmware capacity guarantee.

A supported stock signed template has its original `$OSM` wrapper removed for new content, and the new descriptor is marked unsigned. The tool never claims that the old signature authenticates new content, generates a replacement OEM signature, unlocks a bootloader or proves that the device accepts the candidate. Modified-content acceptance and the supported installation/recovery path are separate mandatory release checks.

The new ramdisk must pass the limited key/authentication audit; keys are **not** silently removed during packing. Rebuild/correct the source when it fails. A pass still leaves `publication_approved=false`: licensing, system/vendor files, calibration, boot acceptance, security policy and runtime operation need their own review. The packer performs no device IO.

## Evidence and limits

On 2026-10-11 the packer passed six synthetic tests and was exercised with both a real stock signed template and a real existing unsigned port template, the freshly built kernel, and an earlier sanitized ramdisk for **format testing only**. Both private outputs passed the limited boot-key audit and preserved their respective stubs except size fields. The signed case removed its old wrapper. No template, binary or calibration file was uploaded, and no device was flashed.

The offline owner-template extractor was exercised with the actual owner's original header/reserved backups. Its Android payload matched the original, with the signed wrapper preserved. The extended parser also passed against two saved real headers: a normally bootable original-slot port header and a recovery-invalidated alternate-slot header. Nine extractor tests and seven GPT/layout tests pass locally, including payload-preserving alternate-slot normalization and refusal of mixed invalidated addresses. These saved-header and synthetic checks are not a new live backup or restoration test. Nothing was flashed or uploaded as part of these checks.

The fresh `systemimage ramdisk` build subsequently completed successfully. Both output SHA-256 values were computed, system format/partition-size checks passed, and the new 1995233-byte ramdisk was packaged with the matching new kernel into an 8365056-byte unsigned OSIP candidate. The candidate passed the limited boot-key audit. This is actual fresh-ramdisk packaging evidence, **not boot or installation evidence**. The private artifacts were not published or flashed. See [system-image evidence and limits](SYSTEM-IMAGE-CHECK.md).
