# Release preparation without rebuilding

This is the packaging path for existing A1-840FHD development outputs, not permission to upload or flash them. Keep original images unchanged and private. A successful prior build is not invalidated by release preparation.

## Select existing outputs first

Use the original image identities in [CANDIDATES.md](CANDIDATES.md), not a similarly named file or a newer timestamp. Seven installed graphics/storage/network fix files have been compared with the existing system image and match. These changes do not require another compile. Other late changes still need an explicit content comparison; do not infer complete equivalence from those seven files.

Keep the boot kernel and system Wi-Fi module as a reviewed matching pair. A separately built kernel is not an interchangeable replacement simply because both builds succeeded.

## Separate the three operations

| Operation | Requires compilation? | What it proves |
|---|---|---|
| Sparse-to-raw expansion | No | Partition-sized representation and conversion checks, not hardware operation |
| Boot approval-file removal and secure property changes | No | Supported ramdisk changes and limited credential audit, not bootability |
| Missing compiled graphics/kernel/framework fix | Usually yes, for the affected component | Only the rebuilt change; packaging and device acceptance remain separate |

Use [system conversion](SYSTEM-IMAGE-CHECK.md) and the sanitizer commands in [the portable workflow](PORTABLE-WORKFLOW.md). Outputs must use new filenames and receive new hashes. Never substitute the original image checksum for a modified candidate.

## Current blockers to a public binary

The existing system contains Google applications, owner Wi-Fi calibration and automatic network ADB. Do not upload it unchanged. The boot contains an ADB public approval file; this is not evidence of a private RSA key, but it must still be removed.

The boot sanitizer does **not** sanitize the system partition. A limited audit pass also does not grant redistribution rights. Public system packaging must exclude unapproved applications and private calibration, make network ADB opt-in, preserve required notices and filesystem metadata, and be audited again. No general-purpose system sanitizer is supplied here yet. Do not improvise deletion in the only copy of an image or call an untested edited image final.

Where vendor redistribution cannot be established, provide lawful owner extraction/import instructions and distinguish that owner-generated image from a publicly downloadable ROM. Do not upload private calibration merely to make the download self-contained.

## Acceptance after repackaging

Record original and replacement identities privately, review the complete replacement contents, and test the exact replacement boot/system pair with per-device backup and recovery available. Previously tested originals do not establish that sanitized replacements boot. The guarded installation tools remain unexercised on hardware; complete restoration is still unfinished. See [release acceptance](RELEASE-CHECKLIST.md).

No new full build, flash, reboot or binary publication is authorized by this document.
