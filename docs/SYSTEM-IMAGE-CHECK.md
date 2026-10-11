# Offline system image checks

From this repository, use Python 3.9 or later:

```sh
python3 tools/inspect_system.py --device acer-a1-840fhd /path/to/private/system.img
```

The tool performs no device I/O, decompression to disk, mounting or file modification. It accepts raw or Android sparse v1.0 images covering **exactly** the known system partition size: 1887436800 bytes for A1-840FHD.

Sparse format facts were checked against `libsparse/sparse_format.h` in the pinned `system/core` checkout. The independently written inspector checks chunk lengths/types, block totals, bounds, trailers, any supplied CRC32 chunks and any nonzero header checksum. It computes a streaming SHA-256 and CRC32 of the logical expanded data. It also checks the ext4 superblock magic and declared filesystem size. Only canonical v1.0 headers are accepted; future extensions require review.

**Don't-care chunks are counted as zero only for logical hashing/CRC**, as specified by the sparse format. A flashing implementation can leave existing contents in skipped regions. Therefore this expanded hash is not automatically a raw-device readback hash and must not be used to claim that skipped physical blocks were erased. No formatting or erase command is executed.

A structural pass does not check ext4 consistency, filesystem permissions, file contents, credentials, bundled Google/vendor licensing, device identity or bootability. The report deliberately keeps `filesystem_integrity_verified`, `contents_privacy_audited` and `publication_approved` false. An absent embedded checksum is reported as absent, not as a successful checksum comparison.

## Exercised build evidence

### Create a new private raw image

The host-only `expand_system.py` tool accepts the independently recorded SHA-256 of the **input** file and a new private output path outside this repository:

```sh
python3 tools/expand_system.py --device acer-a1-840fhd \
  --input /path/to/private/system.img \
  --output /path/to/private/new-system.raw.img \
  --sha256 YOUR_INPUT_FILE_LOWERCASE_SHA256
```

Default execution verifies the checksum and complete image format without creating output. Add `--apply` to create the new host file. Allow at least 1887436800 bytes of free space for Acer. The tool validates the input before writing, explicitly writes zeros for every don't-care region, then rereads the output to compare its SHA-256. It refuses existing destinations and never contacts a device, mounts a filesystem, flashes, reboots or deletes a partial output. On failure preserve but do not flash the partial file; choose a new filename after fixing the cause.

The printed `raw_sha256` identifies the **expanded output**, not the original sparse file. Use the appropriate hash when checking each artifact. Since the raw file has no skipped ranges, its hash can be compared against a complete raw device readback in a separate supported installation procedure; this tool does not perform that procedure. Keep owner calibration and all original/private artifacts out of GitHub.

The actual freshly built Acer sparse image was converted into a new private 1887436800-byte raw file with 825344000 bytes explicitly zeroed, and output reread/checksum verification passed. Six synthetic conversion tests cover dry-run, raw copy, sparse raw/fill/zero expansion, source-checksum refusal, malformed sparse input and existing-output preservation. This establishes host conversion only, not hardware installation or redistribution rights.

The fresh Acer `systemimage ramdisk` build completed all 66480 jobs. Its system image is a 1062093044-byte sparse file that expands to 1887436800 bytes, with an ext4 superblock declaring the same size. All 18 sparse chunks passed the structural checks. The image contains 825344000 don't-care bytes and no CRC chunks; a computed logical checksum is not a claim that the builder supplied one. Seven synthetic tests cover raw/fill/don't-care/CRC parsing, checksum errors, truncation, unknown chunks and partition/filesystem bounds.

The new 1995233-byte ramdisk was packaged with the matching newly built kernel into an 8365056-byte unsigned OSIP candidate. That candidate passed the limited boot-key audit. The owner's original template remained untouched; the new content does not reuse its old OEM signed wrapper. Full image privacy/licensing review and installation/boot/recovery verification remain required. These private artifacts, including owner Wi-Fi calibration in system, have not been published.
