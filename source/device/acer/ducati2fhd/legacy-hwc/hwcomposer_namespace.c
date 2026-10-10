/* SPDX-License-Identifier: Apache-2.0
 * Stable C HWC interface; KitKat GraphicBuffer stays in the shared private
 * graphics namespace. Preserve the original device/module for close().
 */
#include "legacy_loader.h"
#include <errno.h>
#include <hardware/hwcomposer.h>
#include <pthread.h>
#include <log/log.h>
#include <string.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <sys/system_properties.h>
static pthread_once_t once = PTHREAD_ONCE_INIT;
static const hw_module_t *target;
static int load_error = -ENOENT;
static void (*original_register_procs)(hwc_composer_device_1_t *, const hwc_procs_t *);
static int (*original_prepare)(hwc_composer_device_1_t *, size_t, hwc_display_contents_1_t **);
static int (*original_set)(hwc_composer_device_1_t *, size_t, hwc_display_contents_1_t **);
static int fence_trace_enabled(void) {
    char value[PROP_VALUE_MAX] = {0};
    __system_property_get("debug.acer.hwc_trace", value);
    return value[0] == '1' && value[1] == '\0';
}
static int diagnostic_prepare(hwc_composer_device_1_t *hwc, size_t count,
                              hwc_display_contents_1_t **contents) {
    long tid = syscall(__NR_gettid);
    int trace = fence_trace_enabled();
    if (trace) ALOGI("ACER_HWC_PREPARE_BEGIN tid=%ld", tid);
    int rc = original_prepare(hwc, count, contents);
    if (trace) ALOGI("ACER_HWC_PREPARE_END tid=%ld rc=%d", tid, rc);
    if (rc) ALOGE("ACER_HWC_PREPARE_ERROR tid=%ld rc=%d", tid, rc);
    return rc;
}
static int diagnostic_set(hwc_composer_device_1_t *hwc, size_t count,
                          hwc_display_contents_1_t **contents) {
    long tid = syscall(__NR_gettid);
    int trace = fence_trace_enabled();
    if (trace) {
        ALOGI("ACER_HWC_SET_BEGIN tid=%ld displays=%zu", tid, count);
        for (size_t d = 0; d < count; ++d) {
            if (!contents[d]) continue;
            ALOGI("ACER_HWC_INPUT display=%zu flags=%u layers=%zu", d,
                  contents[d]->flags, contents[d]->numHwLayers);
            for (size_t l = 0; l < contents[d]->numHwLayers; ++l) {
                const hwc_layer_1_t *layer = &contents[d]->hwLayers[l];
                ALOGI("ACER_HWC_LAYER display=%zu layer=%zu type=%d handle=%p acquire=%d release=%d", d, l,
                      layer->compositionType, (const void *)layer->handle,
                      layer->acquireFenceFd, layer->releaseFenceFd);
            }
        }
    }
    int rc = original_set(hwc, count, contents);
    if (trace) {
        ALOGI("ACER_HWC_SET_END tid=%ld rc=%d", tid, rc);
        for (size_t d = 0; d < count; ++d) {
            if (!contents[d]) continue;
            ALOGI("ACER_HWC_OUTPUT display=%zu retire=%d", d, contents[d]->retireFenceFd);
            for (size_t l = 0; l < contents[d]->numHwLayers; ++l)
                ALOGI("ACER_HWC_RELEASE display=%zu layer=%zu fence=%d", d, l,
                      contents[d]->hwLayers[l].releaseFenceFd);
        }
    }
    if (rc) ALOGE("ACER_HWC_SET_ERROR tid=%ld rc=%d", tid, rc);
    return rc;
}
static void diagnostic_register_procs(hwc_composer_device_1_t *hwc, const hwc_procs_t *procs) {
    original_register_procs(hwc, procs);
    if (hwc->getDisplayConfigs && hwc->getDisplayAttributes) {
        uint32_t configs[8] = {0};
        size_t count = 8;
        int rc = hwc->getDisplayConfigs(hwc, HWC_DISPLAY_PRIMARY, configs, &count);
        ALOGE("ACER_HWC_POST_REGISTER rc=%d count=%zu", rc, count);
        if (!rc && count) {
            const uint32_t attrs[] = {HWC_DISPLAY_VSYNC_PERIOD, HWC_DISPLAY_WIDTH,
                HWC_DISPLAY_HEIGHT, HWC_DISPLAY_NO_ATTRIBUTE};
            int32_t values[] = {-1, -1, -1};
            int ar = hwc->getDisplayAttributes(hwc, HWC_DISPLAY_PRIMARY, configs[0], attrs, values);
            ALOGE("ACER_HWC_POST_ATTR rc=%d period=%d width=%d height=%d",
                ar, values[0], values[1], values[2]);
        }
    }
}
static void load_module(void) {
    load_error = acer_legacy_load_hal(HWC_HARDWARE_MODULE_ID, &target);
}
static int bridge_open(const hw_module_t *module, const char *id, hw_device_t **device) {
    (void)module;
    if (!id || !device) return -EINVAL;
    *device = NULL;
    pthread_once(&once, load_module);
    if (load_error) return load_error;
    int rc = target->methods->open(target, id, device);
    ALOGE("ACER_HWC_OPEN rc=%d device=%p", rc, (void *)*device);
    if (!rc && *device && !strcmp(id, HWC_HARDWARE_COMPOSER)) {
        hwc_composer_device_1_t *hwc = (hwc_composer_device_1_t *)*device;
        if (hwc->prepare && hwc->prepare != diagnostic_prepare) {
            original_prepare = hwc->prepare;
            hwc->prepare = diagnostic_prepare;
        }
        if (hwc->set && hwc->set != diagnostic_set) {
            original_set = hwc->set;
            hwc->set = diagnostic_set;
        }
        if (hwc->registerProcs && hwc->registerProcs != diagnostic_register_procs) {
            original_register_procs = hwc->registerProcs;
            hwc->registerProcs = diagnostic_register_procs;
        }
        if (hwc->getDisplayConfigs && hwc->getDisplayAttributes) {
            uint32_t configs[8] = {0};
            size_t count = 8;
            int cr = hwc->getDisplayConfigs(hwc, HWC_DISPLAY_PRIMARY, configs, &count);
            ALOGE("ACER_HWC_CONFIGS api=%x rc=%d count=%zu", hwc->common.version, cr, count);
            if (!cr && count) {
                const uint32_t attrs[] = {HWC_DISPLAY_VSYNC_PERIOD, HWC_DISPLAY_WIDTH,
                    HWC_DISPLAY_HEIGHT, HWC_DISPLAY_NO_ATTRIBUTE};
                int32_t values[] = {-1, -1, -1};
                int ar = hwc->getDisplayAttributes(hwc, HWC_DISPLAY_PRIMARY, configs[0], attrs, values);
                ALOGE("ACER_HWC_ATTR config=%u rc=%d period=%d width=%d height=%d",
                    configs[0], ar, values[0], values[1], values[2]);
            }
        }
    }
    return rc;
}
static hw_module_methods_t methods = { .open = bridge_open };
hwc_module_t HAL_MODULE_INFO_SYM = {
    .common = {
        .tag = HARDWARE_MODULE_TAG,
        .module_api_version = HARDWARE_MODULE_API_VERSION(0, 1),
        .hal_api_version = HARDWARE_HAL_API_VERSION,
        .id = HWC_HARDWARE_MODULE_ID,
        .name = "Acer Bay Trail isolated legacy HWC bridge",
        .author = "Acer Android 9 port", .methods = &methods,
    },
};
