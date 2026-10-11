# Limited system-image privacy inventory

Use Linux or WSL with Python 3.9+, current `e2fsprogs` (`debugfs`), sufficient private temporary space, and the `simg2img` built from your pinned Android workspace. **These are offline host commands, not tablet commands.**

```sh
python3 tools/audit_system.py \
  --device acer-a1-840fhd \
  --image /path/to/private/android-output/target/product/ducati2fhd/system.img \
  --simg2img /path/to/private/android-output/host/linux-x86/bin/simg2img \
  --work-dir /path/to/existing/private-work-directory \
  --check-filesystem \
  --report /path/to/private/new-system-inventory.json
```

Provide a new report filename. The tool first checks the complete partition-size/format constraints. For sparse input it creates a private temporary raw file, compares its logical SHA-256 to the inspected sparse data, and removes only that owned temporary directory afterward. Raw input is read in place. Device nodes and direct image symlinks are refused. No filesystem mount, `debugfs -w`, ADB, fastboot or network operation occurs.

The tool lists ext4 directories with read-only `debugfs` and reads every supported regular file within bounded inspection limits. It never extracts filesystem or ZIP member paths to the host. Symlinks are counted but not followed; unsafe filesystem paths, unsupported special entries, short reads, malformed archives and inspection limits cause an **incomplete/refused** result rather than a pass. APK/JAR/ZIP members are scanned after decompression/CRC verification; nested archives are not recursively unpacked. Android's normal `$` resource names are supported safely inside ZIPs, not passed as filesystem commands.

The limited checks cover named authentication/signing files, PEM private-key blocks, serialized Android ADB approvals, selected network identity/password fields, insecure ADB defaults and recognizable unapproved Google APK names. A positive network-ADB directive requires its trigger/default context to be reviewed; an opt-in action is not automatically an unsafe startup default. Known owner calibration paths are reported separately even if no explicit credential field is found. Reports contain paths and reasons, not key bytes, MAC addresses, passwords, host comments or calibration fingerprints.

Exit codes: `0` means the supported limited inventory finished without findings; `1` means it finished with findings; `2` means incomplete/refused. **None means publication approval.** Unknown encrypted/DER secrets, all possible account-data formats, APK package identity/signing, every embedded/nested container, filesystem consistency and vendor redistribution rights are not fully proved by these scans. Calibration clearance and licensing stay false in the report. Review the source/input provenance and full license obligations separately.

## Actual new-ROM evidence

The optional `--check-filesystem` runs `e2fsck -f -n` on the offline regular image file, with no repair requested. Only exit code 0 records `filesystem_integrity_verified=true`; a nonzero result aborts the operation as incomplete. Without this flag, that field remains false. This is a consistency check, not a license/security or hardware test.

The new Acer system image was converted privately and its logical raw hash matched the sparse inspector. Read-only inventory scanned 2065 regular files, 221 directories and 1056537589 file bytes; 370 symlinks were not followed. `etc/NOTICE.html.gz` was present. There were no limited key/credential findings. The subsequent final-tool run also passed `e2fsck -f -n` with exit code 0 and reported the known owner calibration path separately. The actual image includes owner-supplied calibration and proprietary graphics/audio/firmware, so it remains private; it is not an approved ROM download. No device was changed. Thirteen synthetic tests cover parsing, redacted findings, policy checks, compressed archive scanning, valid Android resource names, refused traversal/empty inventory and the no-repair filesystem-check invocation.
