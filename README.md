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

Published inputs currently include 709 commit-pinned upstream projects and reviewed patches for 11 projects (23 source files). Device/vendor inputs, complete corresponding kernel source, boot packaging and the end-to-end installation path still need completion. See the [final release acceptance criteria](docs/RELEASE-CHECKLIST.md).

## Manuals

- [Source preparation](manifests/README.md): the working upstream initialization and patch workflow; not yet a complete Android build.
- [Owner-supplied vendor inputs](docs/VENDOR-INPUTS.md): verified stock graphics import; other vendor inputs remain in progress.
- [Graphics adapter sources](source/README.md): namespace adapters and locally generated GLES bridge inputs.
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
