# Private development candidate record

Recorded 2026-10-10. This document identifies private development outputs; it is not a download or installation guide. These files are not approved release artifacts.

| Artifact | SHA256 | Recorded status |
|---|---|---|
| `system.img` | `a01c2807ca887904e3064536bd57407eb3b62bb9cdedb57100fbfac8be9cda82` | Build completed and selected configuration files compared. The entire newest image was not flashed to the device. |
| `boot-NATIVE-CHARGING-oct10.img` | `ea014a26c2921878365bb192660243ffb48bf3ccc9efee9bda9f5dcda660c617` | Device-tested kernel #18 candidate; contains a personal ADB public approval key and must not be published unchanged. Corresponding-source and public-default review remain required. |

Selected-file comparison is not complete functional validation. Later individual changes, including Wi-Fi replacements, were applied on the development device; they must not be confused with validation of the whole listed system image.

Developer paths, IP addresses, device serial numbers and key contents are intentionally excluded. Sanitized or rebuilt replacements must receive new hashes and independent records.

## Separate sanitized candidate — 2026-10-11

The sanitizer produced a new private candidate with SHA256 `d5bc760965bcefffb5b0831aa6e984ce406ff38a807a2fb526e6a68888693b7f` (8,355,840 bytes). Its ramdisk approval file was removed, the boot-key audit passed, and the kernel allocation and boot stub were preserved except for required size/checksum fields. The original input hash remained unchanged. This candidate is **not** a published ROM, does not resolve the system image's redistribution status, and has not been boot-tested.
