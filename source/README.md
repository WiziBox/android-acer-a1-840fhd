# Device-source components

The published graphics component contains seven project namespace/ABI adapter sources with their existing Apache-2.0 headers and a build definition for five Android modules. Hashes of the adapter files are recorded in `acer-graphics-provenance.json`. The project implementation is separate from the owner-supplied Intel driver; no driver implementation or binary is included here.

The GLES symbol header and i386 assembly are generated locally from the reviewed owner-supplied library by `tools/generate_gles.py`. They are intentionally not a captured Intel export-list snapshot in this repository. See [vendor inputs](../docs/VENDOR-INPUTS.md) for source acquisition and generation.

The additional public tree now contains product/board definitions, audio adapters, lights, storage/resume policy and rootdir inputs. The 34-file device index records current hashes and review scope; two GLES files remain local generation inputs. Source-built private library copy rules and a no-Google/no-automatic-network-ADB product are included. See [device staging and build integration](../docs/DEVICE-SOURCES.md).

The staging procedure was exercised in a fresh Android workspace. The host Python/zlib bootstrap and product selection now work and module compilation has begun. That is not a complete Android build: firmware/module staging, completed Make/Soong integration and OSIP packaging/installation still need completion. Do not copy this tree over an unrelated modified device tree or assume an installable ROM merely because the sources are present.
