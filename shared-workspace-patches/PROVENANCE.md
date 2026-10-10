# Provenance, licensing and modification notice

These are **modified** upstream sources distributed as textual patches, not unmodified upstream releases. Changes were made during the WiziBox dangol/Acer Android 9 development project. The patch changes are distributed under Apache-2.0; original copyrights and applicable notices remain in force. See `../LICENSES/Apache-2.0.txt` and `../third-party-notices/`.

| Patch | Upstream repository | Base commit |
|---|---|---|
| frameworks-native.patch | https://github.com/LineageOS/android_frameworks_native | 38be48f36da1acd812670fbecb75bffca9b4cd98 |
| frameworks-base.patch | https://github.com/LineageOS/android_frameworks_base | ea0de66d71ac88db42f26d9b63c9c1941aa097fc |
| frameworks-av.patch | https://github.com/LineageOS/android_frameworks_av | 541d785e2b89cfbc60df0ecae0edff7977283351 |
| system-core.patch | https://github.com/LineageOS/android_system_core | 976019d07ad1c007043b78450857f428a1440f06 |
| system-netd.patch | https://github.com/LineageOS/android_system_netd | 02458b0a19ce2d3214a00f9779bd36868541b7ca |

## Modified files and purposes

- frameworks/native: `libs/ui/Gralloc2.cpp` (allocation diagnostics), `services/inputflinger/InputReader.cpp` (dangol touch rotation), `services/surfaceflinger/SurfaceFlinger.cpp` (legacy display compatibility and client composition)
- frameworks/base: `core/jni/fd_utils.cpp` (isolated-process optional trace access), `libs/hwui/Properties.cpp` (SystemUI renderer selection), `services/core/java/com/android/server/display/ColorFade.java` (legacy display capture guard), `services/core/java/com/android/server/net/NetworkPolicyManagerService.java` (legacy network compatibility)
- frameworks/av: `media/libstagefright/ACodec.cpp` (legacy codec extension/crop handling), `media/libstagefright/colorconversion/SoftwareRenderer.cpp` (software rendering compatibility)
- system/core: `libsuspend/autosuspend_wakeup_count.cpp` (legacy resume handling)
- system/netd: `server/TetherController.cpp` (legacy counter-chain initialization)

All eleven base files carry Apache-2.0 headers. Their preserved headers and upstream project NOTICE files are included as attribution evidence. Patch application was checked against the current worktree without changing files; this is not a complete build or functional validation.

No proprietary library implementation, firmware, Google APK, kernel binary or device backup is included. This subset must not be mistaken for a complete corresponding kernel source distribution or a complete ROM source tree.
