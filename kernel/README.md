# Acer A1-840FHD kernel source inputs

This source bundle reconstructs the port's kernel input from Acer's official 2015-12-21 source archive and a 99-file patch. It includes the three changes temporarily applied when building development kernel #18; the restored development directory alone did not include those changes.

The archive is 455,836,203 bytes, SHA256 `b6d205b5ea9816b57b84c651fcd9e0f3ac743b92af2fa606ea14e4d02722d86c`, with member `Ducati2FHD/kernel_src.tar.gz`. Obtain it from [Acer's source download](https://global-download.acer.com/GDFiles/Document/App.%20Guide/App.%20Guide_Acer_20151221_A_A.zip?acerid=635862918024567370&Step1=TABLET&Step2=ICONIA%20TAB%208&Step3=A1-840FHD&OS=ALL&LC=it&BC=ACER&SC=EMEA_17). A hash mismatch is not permission to use an arbitrary replacement.

## Prepare sources

Use Linux/WSL, Git and Python 3.12 or newer. From this repository:

```sh
python3 tools/prepare_kernel.py --archive /path/to/acer-source.zip --output /path/to/new-kernel-source
```

The output directory must not exist. The tool validates the archive, uses tar data filtering, checks every patched baseline file, applies the patch in the new tree, verifies every result, and adds dated modification notices while retaining original copyright/license text. It writes a receipt with the prepared source hashes. On failure preserve and inspect any partial new output rather than merging it into a development tree.

The source tree will be under `new-kernel-source/kernel_src/`, including Acer's original sibling `modules/` directory needed by kernel symlinks. It must not be replaced with an unrelated generic kernel. The included configuration is the development #18 configuration, not a fully tested release configuration. No signing private key or prebuilt kernel/module is included.

## Provenance and licenses

The Linux kernel's original `COPYING` is preserved. The patch retains the original notices in source/context; project modifications were made during the WiziBox Android 9 port. Binder/SELinux donor sources are recorded at LineageOS `android_kernel_samsung_universal7580` commit `3bf673eabc8ee77e6d765a1fe8d4c6f7bab5e8e5`. The sdcardfs donor is Android common commit `0ca4bf51323a447f8301fcc1ad51ed1b3188ea3f`. File-level donor records are provided alongside `inputs.json`. Applicable original per-file licenses remain in effect; the Android tooling's Apache license is not a replacement for kernel licensing.

All 43,628 regular baseline kernel files were compared with the official archive. The 99-file patch passed a read-only applicability check against the extracted official source. These facts do not establish a clean kernel build, module-signature compatibility or bootability of a new image.

On 2026-10-11 the published preparation tool was exercised against that archive in a separate empty WSL directory. All 99 patched source fingerprints passed, and a preparation receipt recorded hashes after the dated notices were added. The local tooling suite passed 66 tests. Those unit tests do not download/extract Acer's archive in CI or build/flash a kernel.

## Still required for the complete build

The selected toolchain is `i686-linux-android-4.7`, commit `c7931763d41be602407ed9d71e2c0292c6597e00`, from the public repository recorded in `inputs.json`. Build integration must use a new output directory and locally generated signing material, compile the matching BCM43241 module and sign it with that build's key. The configuration enforces module signatures: do not combine a new signed kernel with another build's module or disable signature enforcement as a shortcut.

## Build the kernel and matching Wi-Fi module

Use Linux/WSL with `make`, host GCC, OpenSSL, Perl, `bc` and the host libraries needed by the old compiler. Obtain the public toolchain at the exact revision in `inputs.json`; do not substitute another toolchain or use an unreviewed binary mirror.

```sh
git clone https://android.googlesource.com/platform/prebuilts/gcc/linux-x86/x86/i686-linux-android-4.7 /path/to/toolchain
git -C /path/to/toolchain checkout --detach c7931763d41be602407ed9d71e2c0292c6597e00
python3 tools/build_kernel.py --source /path/to/new-kernel-source --toolchain /path/to/toolchain --output /path/to/new-kernel-build --jobs 4
```

The output directory must not exist and must be outside the source/toolchain. The tool checks the preparation receipt and configuration, verifies a clean toolchain revision, builds out of tree and signs the freshly compiled BCM43241 module with that build's locally generated key. Kernel signature enforcement remains enabled. A failure leaves its new directory and `build.log` for inspection; it does not delete files or silently reuse another build's outputs.

**Never upload the output directory or `obj/signing_key.priv`.** It contains private signing material. The receipt records only relative paths and hashes for the kernel, module, configuration and public certificate. Kernel/module artifacts alone are not an OSIP boot image or a complete ROM, and success does not certify bootability or redistribution rights for firmware.

On 2026-10-11 this command completed successfully on Ubuntu 24.04 / WSL in a new output directory, from the reconstructed official sources. The kernel and signed Wi-Fi module were produced, the selected configuration remained byte-identical, and `modinfo` reported the expected `3.10.20+` vermagic and SHA256 X.509 signature. See [build evidence](build-evidence.json). OpenSSL 3 emitted a deprecation warning for the original Perl signer's `rsautl` command, but signing completed; this is not evidence that all future host versions are supported. Unit tests now total 69.

This verifies a fresh kernel/module build, not a whole Android build or an installed ROM. No binary or private signing key from the verification build is published. Locally generated keys mean another independent build's hashes will differ. OSIP packaging and device-installation/recovery evidence still need completion. This is not yet an installable ROM release.
