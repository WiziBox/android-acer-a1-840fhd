# Acer device sources and Android build integration

This is the A1-840FHD / `ducati2fhd` product, not A1-840, A1-810 or an emulator. The public device tree now includes 34 indexed source/configuration files: product/board definitions, HIDL declarations, rootdir/USB/fstab policies, navigation overlay, software media registration, graphics/audio bridges, lights and storage policy. It does not include a stock vendor implementation, Google applications, generated GLES export files, firmware, a Wi-Fi module or an OSIP boot image.

## Prepare the device sources

First initialize/sync the pinned Android workspace, apply the public framework patches and materialize the x86 WebView input. Generate GLES bridge inputs from the reviewed owner-supplied Intel library using [the vendor workflow](VENDOR-INPUTS.md). Then, from this distribution repository:

```sh
python3 tools/stage_device.py --source /path/to/android9-source --generated-gles /path/to/generated-gles
# After successful read-only preflight:
python3 tools/stage_device.py --source /path/to/android9-source --generated-gles /path/to/generated-gles --apply
```

The destination `device/acer/ducati2fhd` must not exist. The tool validates all 34 published file hashes and the two generated inputs before creating it. It refuses an existing tree rather than resetting or merging it. Preserve any partial new destination on failure. The command does not copy private keys, contact a tablet or flash anything.

## Vendor and source-built libraries

Import the combined graphics/audio manifests into the new workspace's `vendor/acer/ducati2fhd` using `tools/import_vendor.py` and an owner-supplied stock-system extraction. The parent `vendor/acer` may need creating first. The generated `vendor-stock.mk` is inherited once; old `private-libraries.mk` and `private-audio.mk` snapshots are not additional inputs.

The `source-copies.mk` rules install freshly built Android `libcutils`, `ld-android` and the project runtime in private legacy namespaces. They do not replace the main Android library with a KitKat library. These copy modules still require actual Android build verification; passing Python tests alone does not prove Make/Soong integration.

Firmware and matching kernel/module staging are separate remaining requirements. Do not substitute an old signed Wi-Fi module for the module generated with the new kernel's key. Do not copy another tablet's factory partitions or calibration/user data into this product.

## Host build command

The pinned Android 9 tree needs Linux build packages, host GCC with multilib and 32-bit zlib development headers/libraries. The wrapper uses the pinned source tree's bundled Python 2.7.5 and JDK 8, compiles the tree's CPython zlib module into the new output directory, and tests compression/decompression before Android compilation. It does not copy a developer's zlib binary, change system Python, or download an unpinned interpreter. CPython's original source/license notices remain in its upstream tree; the small project compatibility header is Apache-2.0. Python 3 runs the distribution tools but is not a substitute for these old Android build scripts.

```sh
bash tools/build_android.sh /path/to/android9-source /path/to/new-android-output
# Or select module targets for an incremental integration check:
bash tools/build_android.sh /path/to/android9-source /path/to/different-new-output libacer_legacy_runtime
```

The output must be new and outside the source tree. This wrapper selects `lineage_ducati2fhd-userdebug`, uses the workspace JDK and defaults to `systemimage ramdisk`. It does not create an OSIP image, flash or reboot a device. Missing vendor/firmware/host inputs will stop the build; no complete build is claimed yet.

## Privacy and security defaults

The public product excludes Google packages and automatic network ADB, sets `ro.adb.secure=1` and `ro.secure=1`, and contains no personal ADB approval file or private signing key. This is a userdebug product with USB ADB bring-up, not a hardened consumer ROM. Root/debug capabilities, legacy DRM node access `0666`, Wi-Fi service capabilities and SELinux/boot policy require the release's security documentation and device regression review. These defaults must also be checked in the final packaged ramdisk/system, not just source text.

## Recorded evidence

On 2026-10-11 the public staging tool verified and installed 36 device inputs into the separate fresh Android verification workspace. The public importer verified and staged the combined 87 stock inputs there. Tests total 82 and pass locally. The initial wrapper exposed missing Python/zlib host configuration; the corrected wrapper built a new host extension, passed its zlib test, selected Android 9 / x86 / silvermont for `lineage_ducati2fhd-userdebug`, generated the build graph and began compiling the requested project runtime and its dependencies in a fresh output. Module completion is not yet recorded. Firmware, full Android build, OSIP packaging, installation and recovery remain unverified.

Project source notices and file-level hashes are recorded in [device provenance](../source/acer-device-provenance.json). These license declarations do not grant redistribution rights for owner-supplied proprietary binaries. The older private snapshot commits remain outside the public branch's ancestry.
