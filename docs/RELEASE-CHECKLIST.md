# Final release acceptance criteria

The requested deliverable is a final, usable distribution. It is not complete until the mandatory criteria below have evidence for the exact release revision and artifacts. A documentation update, successful parser test or existing development-device boot is not a substitute.

## Source and licensing

- [x] Publish a public HTTPS upstream manifest pinned to 709 project commits.
- [x] Publish 11 reviewed upstream patch sets with base commits, hashes and preserved notices.
- [ ] Publish the complete reviewed device tree and all remaining required port changes.
- [ ] Provide the complete corresponding source, configuration, toolchain and build/installation inputs for the selected modified kernel, including changes temporarily applied during kernel build #18.
- [ ] Supply reviewed vendor components or an owner-extraction procedure with expected hashes.
- [ ] Resolve the provenance and licensing of generated Intel export/connection code.
- [ ] Provide a build product that does not redistribute unapproved Google applications.
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

As of 2026-10-11, fresh upstream initialization and 11 base-commit patch checks succeeded. The 26 existing tooling tests passed on Windows and Linux. The complete source sync, clean ROM build and release-artifact installation/recovery cycle have not been established. No final ROM is approved for publication yet.

Final does not imply perfect application compatibility. It does require a usable, honestly documented build/download/install/recover path, with evidence rather than unchecked promises.

The subsequent unsigned-boot sanitizer adds 10 synthetic tests (36 total per repository). Local tests passed and a separate Acer candidate passed the limited boot-key audit with its kernel allocation preserved. This does not check off the whole-ROM privacy, clean-build or device-installation criteria.
