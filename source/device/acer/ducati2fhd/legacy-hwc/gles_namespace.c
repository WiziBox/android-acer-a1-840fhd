/* SPDX-License-Identifier: Apache-2.0
 * Bind actual C exports inside the private graphics namespace. The generated
 * i386 tail stubs retain caller arguments and callee results unchanged.
 */
#define LOG_TAG "AcerLegacyGLES"
#include "legacy_loader.h"
#include "gles_symbols.h"
#include <dlfcn.h>
#include <log/log.h>
#include <stdlib.h>
__attribute__((visibility("hidden"))) void *acer_gles_targets[ACER_GLES_SYMBOL_COUNT];
static unsigned loaded_count;
__attribute__((constructor)) static void bind_driver(void) {
    void *driver = acer_legacy_load_gles();
    if (!driver) { ALOGE("Intel GLES loading failed"); return; }
    for (unsigned i = 0; i < ACER_GLES_SYMBOL_COUNT; ++i) {
        acer_gles_targets[i] = dlsym(driver, acer_gles_symbols[i]);
        if (!acer_gles_targets[i]) {
            ALOGE("Intel GLES export missing: %s", acer_gles_symbols[i]);
            return;
        }
    }
    loaded_count = ACER_GLES_SYMBOL_COUNT;
}
/* Metadata for bring-up diagnostics, never pretends a failed driver works. */
unsigned acer_gles_loaded_count(void) { return loaded_count; }
__attribute__((noreturn, visibility("hidden"))) void acer_gles_missing(void) {
    ALOGE("Call to unbound Intel GLES export; refusing a fabricated result");
    abort();
}
