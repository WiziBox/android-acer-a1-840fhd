# Device-source components

The published graphics component contains seven project namespace/ABI adapter sources with their existing Apache-2.0 headers and a build definition for five Android modules. Hashes of the adapter files are recorded in `acer-graphics-provenance.json`. The project implementation is separate from the owner-supplied Intel driver; no driver implementation or binary is included here.

The GLES symbol header and i386 assembly are generated locally from the reviewed owner-supplied library by `tools/generate_gles.py`. They are intentionally not a captured Intel export-list snapshot in this repository. See [vendor inputs](../docs/VENDOR-INPUTS.md) for source acquisition and generation.

This is not the complete device tree yet: the product/board definition, audio integration, lights, storage/resume policies, rootdir inputs, source-built private libcutils integration and kernel packaging remain required. Do not copy this component over an unrelated modified device tree or assume the public product is buildable merely because these modules are present.
