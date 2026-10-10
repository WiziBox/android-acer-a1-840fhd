# Build, download, install and recover

This is the canonical English workflow document for the Acer Iconia Tab 8 A1-840FHD. The required outcome is a complete, portable distribution, not a documentation-only project. The complete workflow is still unfinished; the commands below cover only the implemented source preparation and audit stages.

## Requirements for the implemented tools

Use Python 3 and Git. Source synchronization requires Linux or WSL, the Android `repo` tool and Git LFS. See [source preparation](../manifests/README.md) for the pinned manifest and patch commands. Do not expect the upstream manifest alone to produce this device's ROM.

From a clone of this repository:

```sh
python3 -m unittest discover -s tests -v
python3 tools/audit_boot.py --device acer-a1-840fhd /path/to/boot.img
```

On Windows, use `python` if that is the installed interpreter command. These commands do not connect to, modify or flash a tablet.

The boot audit returns 0 for a supported boot/ramdisk audit pass, 1 for findings, and 2 for missing input, unsupported format or parsing errors. It checks named key files, supported PEM key markers, serialized Android ADB public keys and explicit secure ADB defaults inside a gzip/newc ramdisk. It does not print key contents or host identifiers.

A pass is not complete forensic assurance: system/vendor contents, embedded kernel material, licensing, flash layout and device operation are outside its scope. The report deliberately keeps `publication_approved=false`, even on a boot-key audit pass.

## Create a separate sanitized boot candidate

For the supported unsigned Android v0 or single-descriptor Acer OSIP layouts:

```sh
python3 tools/sanitize_boot.py --device acer-a1-840fhd --input /path/to/private-boot.img --output /path/to/new-candidate.img
```

The output must not already exist. The tool removes named ADB public approval files, sets `ro.adb.secure=1` and `ro.secure=1` in the existing `default.prop`, and preserves kernel payloads and the supported boot stub/layout. It rejects unknown trailers, unsupported signed layouts, missing properties and remaining audit findings. It does not remove unknown private-key files silently, switch off automatic network ADB, fix vendor contents, flash a tablet or establish bootability. Only use a separate new filename; neither a successful operation nor the output hash approves publication.

## Completion requirements

1. Supply the reviewed device tree, vendor input/extraction workflow, kernel source and toolchain, WebView LFS objects and boot-packaging inputs. Record exact revisions and hashes; do not rely on the developer's existing output directory or absolute paths.
2. Preserve third-party licenses and notices. Exclude components without established redistribution permission; document lawful owner extraction when redistribution is unavailable.
3. Package a new boot image without personal ADB approvals or private signing keys. Keep ADB authentication enabled and network ADB opt-in. Document root, SELinux and GPU-access limitations.
4. Audit the complete ROM, including sparse/ext4 system contents and bundled applications. A ramdisk-only audit is insufficient.
5. Complete a clean build in a separate workspace and record its exact inputs and output hashes.
6. Provide release downloads, checksums and model/layout checks, followed by explicit installation consent, per-device backup and OSIP-aware recovery instructions. `baylake` alone is not sufficient identification of an A1-840FHD.
7. Record device regression results for the exact published artifacts and distinguish known limitations from untested behavior. See [final release acceptance criteria](RELEASE-CHECKLIST.md).

## Existing candidate audit

On 2026-10-11, the private `boot-NATIVE-CHARGING-oct10.img` failed the boot audit because its ramdisk contains `/adb_keys` and a serialized ADB public approval key. It must not be published unchanged. This does not mean that an ADB private key was found. A replacement image requires its own filename, hash and review; the old image's hash cannot identify a sanitized replacement.

## What has actually been checked

The pinned upstream manifest initialized successfully in an empty WSL directory; `repo list --all` resolved 709 projects. On 2026-10-11, the separate verification workspace completed network fetching and local checkout, and the public patch tool checked and applied all 11 patches there. WebView LFS smudging was initially skipped; the public tools subsequently downloaded and verified the exact x86 object and materialized it in that workspace. ARM objects were downloaded and verified separately, not installed into the Acer workspace. See [WebView commands and evidence](WEBVIEW-INPUT.md). The local tooling suite now has 78 passing tests. This evidence does not establish a clean Android build, bootability, or a successful installation/recovery cycle.
