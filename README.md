# Acer Iconia Tab 8 A1-840FHD — Android 9

An unofficial Android 9 / LineageOS 16.0 port for the **Acer Iconia Tab 8 A1-840FHD**. This project is not an official Acer or LineageOS release. English is the primary language of the user manuals.

## Supported hardware

- Model: A1-840FHD **only**; not A1-810 or A1-840.
- Device codename: `ducati2fhd`; platform: `baytrail`; board identifier: `baylake`.
- Processor: Intel Atom Z3745.
- Current port: 32-bit x86 Android 9, with a modified 3.10.20+ kernel.
- ARM application translation is not included.

## Release status

The required deliverable is a complete distribution: build from a fresh workspace, download verified images, and install or recover using this repository's documented tools. **That end-to-end deliverable is not complete yet. There is no approved final ROM download in this repository.** The repository will not be labelled final merely because its documentation or tooling tests pass.

Published inputs include 709 commit-pinned upstream projects, reviewed patches for 11 projects (23 source files), the staged device tree, owner vendor/firmware input tools, corresponding kernel reconstruction/build tools and OSIP packaging. The independent kernel/module and Android builds have progressed; full image review, fresh-ramdisk packaging and the end-to-end installation/recovery path remain incomplete. See the [final release acceptance criteria](docs/RELEASE-CHECKLIST.md).

## Manuals

- [Source preparation](manifests/README.md): the working upstream initialization and patch workflow; not yet a complete Android build.
- [Exact WebView input](docs/WEBVIEW-INPUT.md): exercised official download, hash verification and x86 source materialization.
- [Owner-supplied vendor inputs](docs/VENDOR-INPUTS.md): exercised original-backup extraction and graphics/audio import; these private inputs are not redistributed.
- [Firmware and matching Wi-Fi module](docs/FIRMWARE-INPUTS.md): checked private-build staging that preserves your device's calibration.
- [Graphics adapter sources](source/README.md): namespace adapters and locally generated GLES bridge inputs.
- [Device tree and Android build integration](docs/DEVICE-SOURCES.md): reviewed product/configuration sources, staging and source-built namespace library rules.
- [Kernel source and build](kernel/README.md): official archive, verified 99-file port patch, configuration, donor provenance and exercised kernel/Wi-Fi-module build commands.
- [OSIP boot packaging](docs/BOOT-PACKAGING.md): offline owner-template packaging, structural checks and explicit format/bootability limits.
- [Offline system image checks](docs/SYSTEM-IMAGE-CHECK.md): streaming sparse/raw size and checksum checks, with freshly built image evidence and clear content-audit limits.
- [Full system-image privacy inventory](docs/SYSTEM-CONTENT-AUDIT.md): exercised offline regular-file and APK/JAR scanning, redacted findings and explicit licensing/calibration limits.
- [Owner backup before installation](docs/OWNER-BACKUP.md): model/sysfs/OSIP/GPT checks, explicit private backup creation and current backend/verification limits.
- [Build, download, installation and recovery status](docs/PORTABLE-WORKFLOW.md).
- [License review and redistribution boundaries](docs/LICENSE-REVIEW.md).
- [Private development candidate record](docs/CANDIDATES.md): identification only, not downloads or installation instructions.
- [Patch provenance](shared-workspace-patches/PROVENANCE.md).

Earlier `*.ko.md` reports are retained as historical Korean records. The English manuals above are the canonical documentation.

## Development observations and limitations

Development-device work has covered booting, graphics, navigation buttons, backlight, sleep/resume, storage permissions and networking. The selected graphics path does not include the separate imported-framebuffer experiment. These observations are not a claim that the entire newest image has passed a release regression test.

A production Wi-Fi firmware replacement was used after firmware crashes; long-term stability remains unproven. Charging input improved with a different cable; charging safety limits were not bypassed. Camera, DRM playback and compatibility with every application are not guaranteed.

The existing private development system contains Google applications and proprietary vendor components. It is not cleared for redistribution. Public build configuration must handle Google applications separately and provide reviewed vendor inputs or a documented owner-extraction workflow.

## Security and recovery

Existing development settings include root access, SELinux permissive mode, broad GPU device-node access and automatic network ADB on TCP port 5555. These are not safe consumer defaults. Personal ADB approval keys and private signing keys must not be published; public defaults must keep ADB authentication enabled and network ADB opt-in.

The device uses an OSIP/reserved-area boot layout. Do not use generic Android flashing commands, Dangol commands, or another tablet's factory backup. No device-writing command is presented here as approved until its model checks, backup, layout handling and recovery procedure are complete.
