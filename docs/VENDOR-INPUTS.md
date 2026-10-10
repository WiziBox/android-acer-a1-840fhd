# Owner-supplied vendor inputs

The public repository does not include the proprietary stock libraries listed here. The published metadata does not grant permission to redistribute them. Use only inputs you are entitled to use. A complete vendor workflow is still being integrated; the implemented importer currently covers **32 stock graphics libraries**, not the entire device or ROM.

## Input format

Provide a directory containing extracted stock `/system` contents, with `lib/`, `etc/` and `vendor/` directly beneath it. It must not be a dump of `/data` or another tablet's factory partition. `vendor-inputs/graphics-stock.json` records the exact relative source paths, build-input destinations, intended system destinations, sizes and SHA256 checksums for the reviewed stock baseline. A different firmware revision may fail these checks; do not suppress hash failures or substitute arbitrary files.

The tool uses no ADB, executes none of the supplied binaries, and does not extract a raw image. Raw/sparse-image extraction and the full build integration remain separate work. No automatic device write is performed.

## Verify, then import to a new directory

From this repository, with Python 3 installed:

```sh
python3 tools/import_vendor.py --device acer-a1-840fhd --input-root /path/to/extracted-stock-system --output /path/to/new-vendor-inputs
python3 tools/import_vendor.py --device acer-a1-840fhd --input-root /path/to/extracted-stock-system --output /path/to/new-vendor-inputs --apply
```

On Windows, use `python` and Windows paths. The output directory must not exist, and its parent must already exist. The first command is read-only. The second verifies all inputs before staging them, rechecks bytes during copying and creates the output exclusively. It writes a receipt containing relative paths and hashes, not developer paths or device identifiers. A failed final move can leave a new partial output directory; inspect it before choosing another output path. Never merge a partial result into an existing vendor tree blindly.

The importer deliberately reports `complete_vendor_tree=false` and `redistribution_approved=false`. It does not enable graphics, verify loader compatibility, build a ROM or establish that the full device tree is ready.

## Do not mix stock and Android 9 libraries

The previous private graphics package also contains Android 9 build outputs: `libacer_legacy_runtime.so` and a private copy of modern `libcutils.so`. They are excluded from stock extraction and recorded separately under `source_built_inputs`. The complete build workflow must build/install these from its selected sources rather than silently using stock KitKat replacements.

Stock libraries must remain under the private legacy namespace. Do not replace Android 9's ordinary `system/lib/libui.so`, `libbinder.so` or other core libraries with the stock versions.

## Remaining inputs

Audio dependencies/configuration and their required transformations, firmware, the source-built Wi-Fi module, device-specific calibration handling and complete generated Makefile integration are still required. Google APKs are not accepted by this importer and will not be silently included in the public product. Separating those applications from the full product configuration remains part of completing the device tree.

## Evidence recorded on 2026-10-11

All 32 stock graphics inputs matched the recorded dependency-package hashes. The importer passed a dry-run and created a separate local output from the actual extracted stock backup. Its 10 tests increased the Acer tooling suite to 46 passing local tests. This verifies this input-import stage, not a clean Android build, a ROM's redistribution rights or tablet functionality.
