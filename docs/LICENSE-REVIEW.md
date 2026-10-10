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

Reference materials: [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html), [GNU GPLv2 FAQ](https://www.gnu.org/licenses/old-licenses/gpl-2.0-faq.html), and [GitHub licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository). Original per-file licenses and notices control their respective components.
