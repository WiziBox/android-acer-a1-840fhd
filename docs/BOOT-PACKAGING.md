# Acer OSIP boot packaging

The A1-840FHD does not use a generic Android `boot.img` partition layout. This tool creates a **single-image Droidboot OSIP container**, not a raw eMMC image. Never `dd` this file into a disk, reserved area, GPT/MBR or a guessed partition.

## Required inputs

1. Your own supported Android boot OSIP template, backed up using a device/layout-aware workflow. The container must have one descriptor, the reviewed Android geometry (LBA 36050, load `0x1100000`, entry `0x1101000`) and an actual `ducati2fhd` bootstub command line. A whole disk dump or recovery/Droidboot image is not an acceptable template. Template acquisition and flashing/recovery integration are still being completed; do not invent a raw-read/write command from these numbers.
2. The new `obj/arch/x86/boot/bzImage` from the public kernel build, paired with the module staged into this Android build. Do not mix kernels and modules from different signing keys.
3. The fresh Android product `ramdisk.img` from the completed build. Old diagnostic ramdisks are not substitutes for the final fresh build.

The template's bootstub and command line are preserved except for size fields. This means stock and already-working port templates may retain different boot policy/debug arguments. Those differences require review and boot testing; passing the structural checks does not make a stock command line correct for the new ROM. A literal embedded `androidboot.serialno` or PEM key marker in the preserved prefix is refused rather than published.

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

This does not establish successful packaging/booting with the new complete Android build's ramdisk. That candidate and its exact installation/recovery evidence remain required. Local tooling tests total 92, not 92 hardware tests.
