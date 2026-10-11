# License review and publication scope

Review updated 2026-10-11. This is a technical compliance record, not a legal opinion or a guarantee of zero legal risk.

## Published source changes

The published shared-workspace patches cover 11 projects and 23 upstream files. Original headers identify 22 files as Apache-2.0 and one Skia file as BSD-3-Clause. Project changes to these files follow those respective terms; this is not a blanket license for vendor binaries or withheld source.

The repository preserves license texts under `LICENSES/`, original project notices and file headers under `third-party-notices/`, and upstream/base-commit information under `shared-workspace-patches/`. Modified-file notices identify project changes. The six additional projects also have base-file hashes and license evidence in `additional-provenance.json`.

## Withheld material

The 21 Dangol and 59 Acer device/configuration snapshot files still need file-level provenance review. Missing headers alone do not establish infringement. Generated Intel export/connection code needs its generation and source conditions reviewed. Kernel/boot/system images and Wi-Fi modules are withheld pending corresponding-source and complete-content review.

Google applications and proprietary graphics, audio and Wi-Fi components have not been cleared for redistribution. Personal keys, approvals, user data and device-specific backups are never publication inputs. Earlier private local commits containing withheld material are not ancestors of the published branch.

## Remaining obligations

Kernel source preparation now includes the official archive fingerprint, a 99-file patch against its kernel baseline, the selected configuration, original Linux `COPYING`, and Binder/SELinux/sdcardfs donor records. The preparation tool reconstructs sources and adds dated modification notices while preserving original notices. It was exercised against the exact official archive and verified all 99 patched file results. No private signing key, compiled module or kernel image is included. Complete portable build/module/signing/installation integration and ROM-content review are still required; this source publication does not approve the earlier private ROM binaries.

The public source components now also include seven project graphics namespace/ABI adapter files retaining their existing Apache-2.0 declarations and a project build definition. Their hashes are recorded in `source/acer-graphics-provenance.json`. Instead of redistributing the captured Intel export list or driver binary, the public generator recreates the project bridge inputs locally from an owner-supplied library. This does not grant rights to redistribute that library or approve a full ROM image. The earlier blanket withholding description applies to the remaining unreviewed snapshot files, not these separately reviewed additions.

Establish authorship and exact origins of device sources; preserve applicable notices; provide the selected modified kernel's complete corresponding source and build/install inputs; resolve each vendor component's distribution conditions or provide a lawful owner-extraction procedure; and inspect all ROM contents before publishing images. Licensing review and device functionality testing are separate requirements.

The separately reviewed public device inputs now include project-developed product/board/rootdir configuration, public Android HAL interface declarations, measured hardware policies, audio namespace/ABI glue, lights and storage code. These are project port sources rather than the stock KitKat service list or proprietary HAL implementation. Existing declarations are retained and remaining project inputs carry explicit Apache-2.0 identifiers and dated modification notices. `source/acer-device-provenance.json` records the candidate/development fingerprints and current 34-file public index. Generated Intel export inputs and owner-supplied firmware/calibration/binaries are not included by this publication. No private signing key or personal ADB approval is added. This component review still does not authorize the older private ROM image.

Reference materials: [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html), [GNU GPLv2 FAQ](https://www.gnu.org/licenses/old-licenses/gpl-2.0-faq.html), and [GitHub licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository). Original per-file licenses and notices control their respective components.

## Existing-image repackaging is not binary clearance

On 2026-10-11 the separately repackaged private Acer candidate passed its bounded credential inventory and filesystem checks after Google apps, owner calibration and automatic network ADB were excluded. A subsequent read-only installed-path comparison found **all 87** graphics/audio owner inputs still present with the published baseline or transformation fingerprints. Those entries remain `redistribution_approved=false`. Firmware and the compiled Wi-Fi module are additional inputs outside that 87-entry comparison; this is not a complete licensing inventory of every ROM file.

Thus the candidate is not approved for a public Release. The project license on extraction, transformation or namespace code does not grant rights to distribute the imported libraries or firmware. Continue to use the reviewed owner-input workflow until applicable binary distribution terms are established, or implement a complete owner-side reconstruction path for a base that excludes those inputs. A base missing drivers must not be advertised as an immediately bootable final ROM.

[AOSP's licensing guidance](https://source.android.com/docs/setup/contribute/licenses) distinguishes its preferred Apache-2.0 terms from exceptions, including Linux GPLv2. For distributed GPLv2 object code, follow the applicable source-distribution options in section 3 of the preserved [kernel license](../kernel/COPYING), including the relevant compilation/installation inputs in its source definition. Neither a generic repository URL nor a privacy-check result proves those obligations have been fulfilled for a particular binary. This record remains a technical review, not a legal-risk guarantee.
