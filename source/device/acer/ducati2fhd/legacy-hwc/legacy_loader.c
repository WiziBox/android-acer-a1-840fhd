/* SPDX-License-Identifier: Apache-2.0
 * One process-local namespace for the legacy graphics C HALs.
 */
#define LOG_TAG "AcerLegacyLoader"
#include "legacy_loader.h"
#include <android/dlext.h>
#include <dlfcn.h>
#include <errno.h>
#include <log/log.h>
#include <pthread.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

struct android_namespace_t;
extern struct android_namespace_t *android_create_namespace(
    const char *, const char *, const char *, uint64_t, const char *,
    struct android_namespace_t *);
extern bool android_link_namespaces(struct android_namespace_t *,
                                    struct android_namespace_t *, const char *);
#define LEGACY_LIB "/system/legacy-hwc/lib"
static pthread_mutex_t namespace_lock = PTHREAD_MUTEX_INITIALIZER;
static struct android_namespace_t *legacy_ns;
static void *runtime_handle;

static void *load_object(const char *path) {
    pthread_mutex_lock(&namespace_lock);
    if (legacy_ns == NULL) {
        legacy_ns = android_create_namespace("acer_legacy_graphics",
            LEGACY_LIB, LEGACY_LIB, 1,
            LEGACY_LIB ":/system/lib/hw:/system/lib/egl", NULL);
        if (legacy_ns != NULL && !android_link_namespaces(legacy_ns, NULL,
            "libc.so:libm.so:libdl.so:liblog.so:libc++.so:libacer_legacy_loader.so"))
            legacy_ns = NULL;
    }
    android_dlextinfo info = {0};
    info.flags = ANDROID_DLEXT_USE_NAMESPACE;
    info.library_namespace = legacy_ns;
    if (legacy_ns != NULL && runtime_handle == NULL)
        runtime_handle = android_dlopen_ext(LEGACY_LIB "/libacer_legacy_runtime.so",
                                           RTLD_NOW | RTLD_GLOBAL, &info);
    bool ready = legacy_ns != NULL && runtime_handle != NULL;
    pthread_mutex_unlock(&namespace_lock);
    if (!ready) {
        ALOGE("Legacy namespace/runtime failed: %s", dlerror());
        return NULL;
    }
    /* Do not hold the namespace lock over HAL constructors: a legacy HAL
     * may load the gralloc front-end which re-enters this shared loader.
     */
    void *handle = android_dlopen_ext(path, RTLD_NOW | RTLD_LOCAL, &info);
    if (handle == NULL) {
        ALOGE("%s load failed: %s", path, dlerror());
        return NULL;
    }
    return handle;
}

void *acer_legacy_load_gles(void) {
    return load_object(LEGACY_LIB "/egl/libGLES_intel7.so");
}

int acer_legacy_load_hal(const char *id, const hw_module_t **module) {
    const char *path;
    if (id == NULL || module == NULL) return -EINVAL;
    *module = NULL;
    if (strcmp(id, "hwcomposer") == 0)
        path = LEGACY_LIB "/hw/hwcomposer.baytrail.so";
    else if (strcmp(id, "gralloc") == 0)
        path = LEGACY_LIB "/hw/gralloc.baytrail.so";
    else return -EINVAL;
    void *handle = load_object(path);
    if (handle == NULL) return -ENOENT;
    const hw_module_t *target = dlsym(handle, HAL_MODULE_INFO_SYM_AS_STR);
    if (target == NULL || target->tag != HARDWARE_MODULE_TAG || target->id == NULL ||
        strcmp(target->id, id) != 0 || target->methods == NULL || target->methods->open == NULL)
        return -EINVAL;
    /* Keep the DSO live: callbacks and the module belong to it. */
    *module = target;
    return 0;
}
