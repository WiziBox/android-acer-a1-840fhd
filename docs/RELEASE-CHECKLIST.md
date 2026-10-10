# Final release acceptance criteria

The requested deliverable is a final, usable distribution. It is not complete until the mandatory criteria below have evidence for the exact release revision and artifacts. A documentation update, successful parser test or existing development-device boot is not a substitute.

## Source and licensing

- [x] Publish a public HTTPS upstream manifest pinned to 709 project commits.
- [x] Publish 11 reviewed upstream patch sets with base commits, hashes and preserved notices.
- [ ] Publish the complete reviewed device tree and all remaining required port changes.
  - [x] Publish and exercise staging of 34 indexed device files plus two locally generated GLES inputs, with product/board/rootdir/audio/lights/storage integration.
  - [ ] Verify source-built namespace library copy modules and remaining firmware/kernel packaging in the full Android build.
- [ ] Provide the complete corresponding source, configuration, toolchain and build/installation inputs for the selected modified kernel, including changes temporarily applied during kernel build #18.
  - [x] Reconstruct and verify 99 source modifications from the exact official archive, including all three build-time #18 overrides; preserve GPL/donor notices and the configuration.
  - [x] Build a fresh kernel and matching BCM43241 module using the public tool, retaining signature enforcement and generating the signing key locally.
  - [ ] Complete portable kernel/module/signing/OSIP build and installation integration and clean-build evidence.
- [ ] Supply reviewed vendor components or an owner-extraction procedure with expected hashes.
  - [x] Provide and exercise a hash-checked importer for 32 stock graphics libraries, excluding two source-built inputs.
  - [x] Provide and exercise 55 stock audio inputs with two hash-checked transformations, excluding three source-built inputs.
  - [x] Exercise combined 87-input staging and generate a stock COPY_FILES Makefile.
  - [ ] Complete source-built private libraries, firmware, Wi-Fi module/calibration and full build integration.
- [ ] Resolve the provenance and licensing of generated Intel export/connection code.
- [ ] Provide a build product that does not redistribute unapproved Google applications.
  - [x] Remove Google packages and automatic TCP ADB from the public source product; retain authenticated ADB defaults.
  - [ ] Verify those exclusions/defaults in the complete built artifacts.
- [ ] Audit the complete ROM's licenses and contents; do not treat boot audit success as publication approval.

## Privacy and security

- [ ] Exclude personal ADB approval keys, private signing keys, device-specific backups and user data from artifacts and published history.
- [ ] Make network ADB opt-in, retain RSA authentication and remove diagnostic forced-approval defaults.
- [ ] Document the release's actual root, SELinux and GPU-access policies and limitations.
- [ ] Generate any necessary private build-signing material locally; never publish that private material.

## Build and installation

- [ ] Complete a clean build outside the original development tree using only documented inputs.
- [ ] Provide downloadable, reviewed release artifacts, their SHA256 checksums and exact source/tooling revisions.
- [ ] Provide an English installation manual and device-aware tools with model/layout checks and explicit write consent.
- [ ] Provide per-device backup and recovery steps for the OSIP/reserved-area layout without writing another tablet's factory data.
- [ ] Exercise the documented installation/recovery path and record evidence for the exact published artifacts.
- [ ] Record boot, display, touch, navigation, audio/video, Wi-Fi, storage and sleep/resume regression results, plus known limitations.

## Current evidence

As of 2026-10-11, fresh upstream initialization, network fetching and local checkout succeeded; all 11 public patches were checked and applied in the separate verification tree. The exact x86 WebView LFS object was materialized and its public download procedure was exercised. The local tooling suite has 78 passing tests. Clean ROM build and release-artifact installation/recovery have not been established. No final ROM is approved for publication yet.

Final does not imply perfect application compatibility. It does require a usable, honestly documented build/download/install/recover path, with evidence rather than unchecked promises.

The subsequent unsigned-boot sanitizer adds 10 synthetic tests (36 total per repository). Local tests passed and a separate Acer candidate passed the limited boot-key audit with its kernel allocation preserved. This does not check off the whole-ROM privacy, clean-build or device-installation criteria.
