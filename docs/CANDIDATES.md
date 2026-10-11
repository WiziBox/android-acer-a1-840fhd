# Private development candidate record

Recorded 2026-10-10. This document identifies private development outputs; it is not a download or installation guide. These files are not approved release artifacts.

| Artifact | SHA256 | Recorded status |
|---|---|---|
| `system.img` | `a01c2807ca887904e3064536bd57407eb3b62bb9cdedb57100fbfac8be9cda82` | Build completed and selected configuration files compared. The entire newest image was not flashed to the device. |
| `boot-NATIVE-CHARGING-oct10.img` | `ea014a26c2921878365bb192660243ffb48bf3ccc9efee9bda9f5dcda660c617` | Device-tested kernel #18 candidate; contains a personal ADB public approval key and must not be published unchanged. Corresponding-source and public-default review remain required. |

Selected-file comparison is not complete functional validation. Later individual changes, including Wi-Fi replacements, were applied on the development device; they must not be confused with validation of the whole listed system image.

On 2026-10-11 the existing `a01c2807...` system image was expanded into a separate private raw file, without rebuilding or changing the original. Read-only filesystem inspection confirmed that seven files inside the image match the recorded installed fixes: `lib/libhwui.so`, `vendor/lib/libhwc2on1adapter.so`, `bin/acer_storage_policy`, `etc/init/acer-storage-policy.rc`, `lib/libandroid_runtime.so`, `bin/netd`, and `etc/init/acer-network-adb.rc`. Thus those specific graphics/storage/network fixes do not require recompilation. This does not establish every later fix, whole-image hardware testing or publication rights. In particular the automatic network-ADB file is a development default, not an approved public-release default; public tooling keeps network ADB opt-in.

The complete bounded inventory scanned 2090 regular files and supported APK/JAR members; read-only filesystem consistency checks passed. The inventory flagged the automatic network-ADB directive, bundled Google applications, and an APK-internal `google.jks` filename. A subsequent read-only bounded structure check of that exact member found 70 trusted-certificate entries and zero private-key entries. The filename finding is therefore **not evidence of the owner's private RSA key**. Entry-type classification does not verify the integrity password or certificate validity. Format facts were checked against [OpenJDK's JKS implementation](https://github.com/openjdk/jdk8u/blob/master/jdk/src/share/classes/sun/security/provider/JavaKeyStore.java); no aliases or key/certificate contents were printed. An owner Wi-Fi calibration file is also present and has no publication clearance. Therefore the existing image remains private, irrespective of its selected-fix matches or filesystem pass. No user-data partition was scanned or published.

Developer paths, IP addresses, device serial numbers and key contents are intentionally excluded. Sanitized or rebuilt replacements must receive new hashes and independent records.

## Separate sanitized candidate — 2026-10-11

The sanitizer produced a new private candidate with SHA256 `d5bc760965bcefffb5b0831aa6e984ce406ff38a807a2fb526e6a68888693b7f` (8,355,840 bytes). Its ramdisk approval file was removed, the boot-key audit passed, and the kernel allocation and boot stub were preserved except for required size/checksum fields. The original input hash remained unchanged. This candidate is **not** a published ROM, does not resolve the system image's redistribution status, and has not been boot-tested.
