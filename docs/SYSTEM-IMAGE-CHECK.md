# Offline system image checks

From this repository, use Python 3.9 or later:

```sh
python3 tools/inspect_system.py --device acer-a1-840fhd /path/to/private/system.img
```

The tool performs no device I/O, decompression to disk, mounting or file modification. It accepts raw or Android sparse v1.0 images covering **exactly** the known system partition size: 1887436800 bytes for A1-840FHD. A shared `--device dangol` profile uses 2147483648 bytes; that does not authorize applying a Dangol image to an Acer tablet.

Sparse format facts were checked against `libsparse/sparse_format.h` in the pinned `system/core` checkout. The independently written inspector checks chunk lengths/types, block totals, bounds, trailers, any supplied CRC32 chunks and any nonzero header checksum. It computes a streaming SHA-256 and CRC32 of the logical expanded data. It also checks the ext4 superblock magic and declared filesystem size. Only canonical v1.0 headers are accepted; future extensions require review.

**Don't-care chunks are counted as zero only for logical hashing/CRC**, as specified by the sparse format. A flashing implementation can leave existing contents in skipped regions. Therefore this expanded hash is not automatically a raw-device readback hash and must not be used to claim that skipped physical blocks were erased. No formatting or erase command is executed.

A structural pass does not check ext4 consistency, filesystem permissions, file contents, credentials, bundled Google/vendor licensing, device identity or bootability. The report deliberately keeps `filesystem_integrity_verified`, `contents_privacy_audited` and `publication_approved` false. An absent embedded checksum is reported as absent, not as a successful checksum comparison.

## Exercised build evidence

The fresh Acer `systemimage ramdisk` build completed all 66480 jobs. Its system image is a 1062093044-byte sparse file that expands to 1887436800 bytes, with an ext4 superblock declaring the same size. All 18 sparse chunks passed the structural checks. The image contains 825344000 don't-care bytes and no CRC chunks; a computed logical checksum is not a claim that the builder supplied one. Seven synthetic tests cover raw/fill/don't-care/CRC parsing, checksum errors, truncation, unknown chunks and partition/filesystem bounds.

The new 1995233-byte ramdisk was packaged with the matching newly built kernel into an 8365056-byte unsigned OSIP candidate. That candidate passed the limited boot-key audit. The owner's original template remained untouched; the new content does not reuse its old OEM signed wrapper. Full image privacy/licensing review and installation/boot/recovery verification remain required. These private artifacts, including owner Wi-Fi calibration in system, have not been published.
