# Final release acceptance criteria

The requested deliverable is a final, usable distribution. It is not complete until the mandatory criteria below have evidence for the exact release revision and artifacts. A documentation update, successful parser test or existing development-device boot is not a substitute.

## Source and licensing

- [x] Publish a public HTTPS upstream manifest pinned to 709 project commits.
- [x] Publish 11 reviewed upstream patch sets with base commits, hashes and preserved notices.
- [ ] Publish the complete reviewed device tree and all remaining required port changes.
  - [x] Publish and exercise staging of 34 indexed device files plus two locally generated GLES inputs, with product/board/rootdir/audio/lights/storage integration.
  - [x] Verify the four source-built namespace library copies and paired Wi-Fi module in the full Android build; package its new ramdisk with the new kernel.
- [ ] Provide the complete corresponding source, configuration, toolchain and build/installation inputs for the selected modified kernel, including changes temporarily applied during kernel build #18.
  - [x] Reconstruct and verify 99 source modifications from the exact official archive, including all three build-time #18 overrides; preserve GPL/donor notices and the configuration.
  - [x] Build a fresh kernel and matching BCM43241 module using the public tool, retaining signature enforcement and generating the signing key locally.
  - [ ] Complete portable kernel/module/signing/OSIP build and installation integration and clean-build evidence.
  - [x] Provide and exercise offline OSIP packaging with real signed/unsigned templates and a sanitized legacy ramdisk, clearly separate from fresh-ROM boot verification.
- [ ] Supply reviewed vendor components or an owner-extraction procedure with expected hashes.
  - [x] Provide and exercise a hash-checked importer for 32 stock graphics libraries, excluding two source-built inputs.
  - [x] Provide and exercise 55 stock audio inputs with two hash-checked transformations, excluding three source-built inputs.
  - [x] Exercise combined 87-input staging and generate a stock COPY_FILES Makefile.
  - [ ] Complete source-built private libraries, firmware, Wi-Fi module/calibration and full build integration.
  - [x] Build all 12 selected port modules, verify private namespace copy hashes and exercise six owner firmware/module/calibration inputs in the separate workspace.
- [ ] Resolve the provenance and licensing of generated Intel export/connection code.
- [ ] Provide a build product that does not redistribute unapproved Google applications.
  - [x] Remove Google packages and automatic TCP ADB from the public source product; retain authenticated ADB defaults.
  - [ ] Verify those exclusions/defaults in the complete built artifacts.
- [ ] Audit the complete ROM's licenses and contents; do not treat boot audit success as publication approval.
  - [x] Exercise bounded offline file/APK/JAR privacy inventory and read-only ext4 consistency checks on the exact newly built system image; record no limited key/credential findings and flag the known calibration path separately.
  - [ ] Resolve vendor/calibration redistribution rights and complete the wider content/license review; the limited scanner does not approve publication.

## Privacy and security

- [ ] Exclude personal ADB approval keys, private signing keys, device-specific backups and user data from artifacts and published history.
- [ ] Make network ADB opt-in, retain RSA authentication and remove diagnostic forced-approval defaults.
- [ ] Document the release's actual root, SELinux and GPU-access policies and limitations.
- [ ] Generate any necessary private build-signing material locally; never publish that private material.

## Build and installation

- [x] Complete a clean build outside the original development tree using the documented pinned source, staged owner inputs and public build tools; verify full outputs and new ramdisk packaging.
- [ ] Provide downloadable, reviewed release artifacts, their SHA256 checksums and exact source/tooling revisions.
- [ ] Provide an English installation manual and device-aware tools with model/layout checks and explicit write consent.
- [ ] Provide per-device backup and recovery steps for the OSIP/reserved-area layout without writing another tablet's factory data.
- [ ] Exercise the documented installation/recovery path and record evidence for the exact published artifacts.
- [ ] Record boot, display, touch, navigation, audio/video, Wi-Fi, storage and sleep/resume regression results, plus known limitations.

## Current evidence

As of 2026-10-11, fresh upstream initialization, network fetching and local checkout succeeded; all 11 public patches were checked and applied in the separate verification tree. The exact x86 WebView LFS object was materialized and its public download procedure was exercised. The fresh kernel/module and full `systemimage ramdisk` build completed. The new system image passed sparse/ext4 declared-size checks, and the fresh ramdisk was packaged into an OSIP candidate that passed the limited key audit. Four namespace copies match fresh library sources, and the system Wi-Fi module matches the new kernel build's signed module. `system/etc/NOTICE.html.gz` is present; its presence alone does not complete licensing review. Full-image privacy/licensing review and release-artifact installation/recovery are not established. No final ROM is approved for publication yet.

Final does not imply perfect application compatibility. It does require a usable, honestly documented build/download/install/recover path, with evidence rather than unchecked promises.

The latest 170-test local run passed outside the filesystem sandbox, and public Windows/Linux CI for commit `097dc8e9a78c11c3f8fdaeaf46793a7bb558f46b` passed. The public tools now include offline owner-backup verification, an explicit-consent boot-only Droidboot workflow, and verified host-only sparse-to-raw expansion. Boot-write testing is synthetic only; system installation and restoration integration remain incomplete. These tool tests and boot-key checks do not check off whole-ROM privacy or device-installation criteria.

Further full recompilation and new build-disk creation are on hold at the owner's direction. Existing development artifacts are being reviewed first. Read-only inspection of the existing system image confirmed seven installed graphics/storage/network fixes by file checksum; that selected comparison is not full release acceptance. See [candidate evidence](CANDIDATES.md).
