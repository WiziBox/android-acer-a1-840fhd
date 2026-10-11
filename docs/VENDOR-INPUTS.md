# Owner-supplied vendor inputs

The public repository does not include the proprietary stock libraries listed here. The published metadata does not grant permission to redistribute them. Use only inputs you are entitled to use. A complete vendor workflow is still being integrated; the implemented importer covers **32 stock graphics inputs and 55 stock audio inputs**, not the entire device or ROM.

## Input format

Provide a directory containing extracted stock `/system` contents, with `lib/`, `etc/` and `vendor/` directly beneath it. It must not be a dump of `/data` or another tablet's factory partition. `vendor-inputs/graphics-stock.json` records the exact relative source paths, build-input destinations, intended system destinations, sizes and SHA256 checksums for the reviewed stock baseline. A different firmware revision may fail these checks; do not suppress hash failures or substitute arbitrary files.

The importer uses no ADB and executes none of the supplied libraries. A separate raw-image extractor is implemented below. Live backup acquisition and the complete installation/recovery path remain separate work. No automatic device write is performed.

## Extract allowlisted inputs from your own original backup

On Linux/WSL, use Python 3.9+ and `debugfs` from `e2fsprogs`. The input must be your original A1-840FHD **raw ext4 system backup**, exactly 1887436800 bytes, not the new LineageOS image, a sparse container or another owner's backup. Output must be a new directory under an existing private parent.

```sh
# Read-only preflight; no output directory is created.
python3 tools/extract_vendor.py \
  --system-image /path/to/private/your-stock-system.img \
  --output /path/to/private/new-stock-inputs

# After preflight succeeds, create only the allowlisted private inputs.
python3 tools/extract_vendor.py \
  --system-image /path/to/private/your-stock-system.img \
  --output /path/to/private/new-stock-inputs --apply
```

The extractor verifies all 87 graphics/audio input entries, including the required importer transformations, before writing. Shared source files are extracted once: 75 unique graphics/audio paths plus three DSP firmware files and your own calibration file, 79 files total. It does not copy Google applications, `/data`, private keys, the whole system or unrelated factory files. Stock symlinks are resolved only within the image, including `/system/` targets; loops and unsupported paths are refused. No filesystem is mounted or extracted wholesale and no `debugfs -w` is used.

Calibration bytes stay unchanged. Its contents, MAC and fingerprint are not included in the receipt, which contains only counts and status. Linux output permissions restrict the private files. Keep the resulting directory and any build image containing it out of public Git/Releases. Extraction does not grant redistribution permission.

Use this new directory as `--input-root` for the combined importer and as `--stock-system` for firmware staging. Its `lib/egl/libGLES_intel7.so` is also the owner input for the GLES generator. Its `etc/firmware/bcmdhd_aob.cal_43241_b4` is the staging calibration path. The selected production Wi-Fi firmware is acquired **separately** under its upstream terms; this extractor does not substitute stock test firmware for it.

The actual original backup passed preflight and 79-file extraction. The resulting directory passed all 87 combined importer checks, and its Intel library generated the expected 1663-export bridge inputs and both recorded source hashes. Ten synthetic tests cover duplicate source paths, incorrect fingerprints/profiles, refused applications, output preservation, private receipts and symlink handling. These are input-preparation checks, not device tests.

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

## Import the audio inputs

Use a separate new output directory and explicitly select the audio manifest:

```sh
python3 tools/import_vendor.py --device acer-a1-840fhd --manifest vendor-inputs/audio-stock.json --input-root /path/to/extracted-stock-system --output /path/to/new-audio-inputs
python3 tools/import_vendor.py --device acer-a1-840fhd --manifest vendor-inputs/audio-stock.json --input-root /path/to/extracted-stock-system --output /path/to/new-audio-inputs --apply
```

The 55-file list includes stock audio libraries and parameter-framework configuration. Two entries require hash-checked transformations: the reviewed resampler's sole text relocation is converted to a register-preserving PIC GOT thunk, and plugin folders are redirected to the private audio namespace. Both input and transformed output hashes are checked before staging. The script does not execute supplied libraries or disable executable-page protections. Unknown inputs, transforms and output fingerprints are refused.

The three audio namespace inputs `libacer_legacy_runtime.so`, modern `libcutils.so` and `ld-android.so` must come from the selected Android 9 build, not stock extraction. Old vendor-directory Google permission files and unrelated telephony inputs are excluded from the audio manifest.

The resampler can also be prepared independently, preserving the input:

```sh
python3 tools/prepare_audio_resampler.py --input /path/to/extracted-stock-system/lib/libaudioresample.so --output /path/to/new-resampler.so
```

Its output must not already exist. It requires the exact reviewed input SHA256 and verifies the exact output SHA256 before writing. These checks remain enabled with Python optimization. This local transformation does not establish redistribution permission for the resulting library.

## Prepare combined stock inputs for the build

To stage all 87 graphics/audio inputs in one new directory:

```sh
python3 tools/import_vendor.py --device acer-a1-840fhd --manifest vendor-inputs/graphics-stock.json vendor-inputs/audio-stock.json --input-root /path/to/extracted-stock-system --output /path/to/new-combined-vendor --apply
```

Omit `--apply` for a dry-run. The importer also creates `vendor-stock.mk`, listing the staged stock files under their intended `vendor/acer/ducati2fhd/` source prefix and system destinations. That generated Makefile must be integrated once by the complete product workflow; it does not stage the separate source-built libraries or replace all remaining vendor inputs. Do not inherit both this list and the earlier private development COPY_FILES lists for the same destinations.

## Generate GLES bridge inputs

Use Linux/WSL with Python 3 and GNU `readelf` installed:

```sh
python3 tools/generate_gles.py --library /path/to/extracted-stock-system/lib/egl/libGLES_intel7.so --output /path/to/new-gles-generated
```

The library must match the reviewed SHA256 baseline and be a little-endian i386 shared ELF. The generator reads dynamic symbols without executing the library, filters defined C EGL/GLES functions, and emits project tail-call thunks plus their name header. It refuses an existing output directory. On a write failure inspect any new partial directory before retrying. The generated files are build inputs, not a runtime or redistribution approval.

For the actual baseline, generation produced 1,663 exports and byte-for-byte matched both existing development build inputs: `gles_symbols.h` SHA256 `791b8ea2ec3740585d38b090c6d4139a2d7fd9143a01b8966bb33c3bc6319d22`, and `gles_exports_x86.S` SHA256 `7e9ddd21ac83330f429d2e0bffe7e6e090717857d2b5465d26ef604cc313efd0`. Six synthetic tests increased the local suite to 52 passing tests. The [graphics adapter sources](../source/README.md) still need integration into the complete device build workflow.

## Remaining inputs

The public device product now includes the combined Makefile once and builds source-based private-library copy modules, which were exercised with matching output hashes. [Owner firmware/calibration and Wi-Fi-module staging](FIRMWARE-INPUTS.md) is also available and was exercised with six inputs. Google APKs are not accepted by this importer and are excluded from the public product, as is automatic network ADB. The complete system/ramdisk build has begun but is not yet established as successful; OSIP packaging, full-image review and installation/recovery remain required.

## Evidence recorded on 2026-10-11

All 32 stock graphics inputs matched the recorded dependency-package hashes. The importer passed a dry-run and created a separate local output from the actual extracted stock backup. Its 10 tests increased the Acer tooling suite to 46 passing local tests. This verifies this input-import stage, not a clean Android build, a ROM's redistribution rights or tablet functionality.

Subsequently all 55 audio inputs were verified and staged from the actual stock extraction. Both transformations matched the development build inputs; the prepared resampler SHA256 is `61acc00630b8ebd24dd9493afccf458f8bc0f33275936f239a8db5aa3146d8cb`. Combined staging of all 87 inputs and Makefile generation also succeeded. The extended local tooling suite passed 61 tests. Neither the stock nor prepared proprietary files were uploaded.
