/* SPDX-License-Identifier: Apache-2.0
 * Keep the stock Intel audio C HAL and C++ dependencies out of modern audio
 * and graphics namespaces. Forward actual device callbacks, never fake IO.
 */
#define LOG_TAG "AcerLegacyAudio"
#include <android/dlext.h>
#include <dlfcn.h>
#include <errno.h>
#include <hardware/audio.h>
#include <log/log.h>
#include <pthread.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
struct android_namespace_t;
extern struct android_namespace_t *android_create_namespace(const char *, const char *, const char *, uint64_t, const char *, struct android_namespace_t *);
extern bool android_link_namespaces(struct android_namespace_t *, struct android_namespace_t *, const char *);
#define AUDIO_LIB "/system/legacy-audio/lib"
static pthread_once_t once = PTHREAD_ONCE_INIT;
static const hw_module_t *target;
static void *runtime_handle;
static void *hal_handle;
static int load_error = -ENOENT;
extern int acer_audio_wrap(hw_device_t **device);
static void load_module(void) {
    struct android_namespace_t *ns = android_create_namespace("acer_legacy_audio", AUDIO_LIB, AUDIO_LIB, 1, AUDIO_LIB, NULL);
    if (!ns || !android_link_namespaces(ns, NULL, "libc.so:libm.so:libdl.so:liblog.so:libc++.so")) goto fail;
    android_dlextinfo info = { .flags = ANDROID_DLEXT_USE_NAMESPACE, .library_namespace = ns };
    runtime_handle = android_dlopen_ext(AUDIO_LIB "/libacer_legacy_runtime.so", RTLD_NOW|RTLD_GLOBAL, &info);
    if (!runtime_handle) goto fail;
    hal_handle = android_dlopen_ext(AUDIO_LIB "/hw/audio.primary.ducati2fhd.so", RTLD_NOW|RTLD_LOCAL, &info);
    if (!hal_handle) goto fail;
    target = dlsym(hal_handle, HAL_MODULE_INFO_SYM_AS_STR);
    if (!target || target->tag != HARDWARE_MODULE_TAG || !target->id || strcmp(target->id, AUDIO_HARDWARE_MODULE_ID) || !target->methods || !target->methods->open) {
        target = NULL;
        load_error = -EINVAL;
        return;
    }
    load_error = 0;
    return;
fail:
    ALOGE("Intel audio namespace load failed: %s", dlerror());
}
static int bridge_open(const hw_module_t *module, const char *id, hw_device_t **device) {
    (void)module;
    if (!id || !device) return -EINVAL;
    *device = NULL;
    pthread_once(&once, load_module);
    if (load_error) return load_error;
    int rc = target->methods->open(target, id, device);
    if (!rc && *device) rc = acer_audio_wrap(device);
    ALOGI("Intel audio open rc=%d api=%x", rc, !rc && *device ? (*device)->version : 0);
    return rc;
}
static hw_module_methods_t methods = { .open = bridge_open };
struct audio_module HAL_MODULE_INFO_SYM = {
    .common = {
        .tag = HARDWARE_MODULE_TAG,
        .module_api_version = AUDIO_MODULE_API_VERSION_0_1,
        .hal_api_version = HARDWARE_HAL_API_VERSION,
        .id = AUDIO_HARDWARE_MODULE_ID,
        .name = "Acer isolated Intel audio bridge",
        .author = "Acer Android 9 port",
        .methods = &methods,
    },
};
