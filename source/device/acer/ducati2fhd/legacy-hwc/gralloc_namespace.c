/* SPDX-License-Identifier: Apache-2.0
 * C gralloc0 bridge. The original module receives every callback, not a
 * shallow copy with missing vendor-private state beyond the public struct.
 */
#include "legacy_loader.h"
#include <errno.h>
#include <hardware/gralloc.h>
#include <pthread.h>
#include <log/log.h>
#include <string.h>

static const gralloc_module_t *target;
static pthread_once_t once = PTHREAD_ONCE_INIT;
static int load_error = -ENOENT;
__attribute__((visibility("hidden"))) const gralloc_module_t *acer_gralloc_original_module;
__attribute__((visibility("hidden"))) void *acer_gralloc_original_perform;
extern int acer_gralloc_perform(const gralloc_module_t *, int, ...);
extern gralloc_module_t HAL_MODULE_INFO_SYM;
static int (*original_alloc)(alloc_device_t *, int, int, int, int, buffer_handle_t *, int *);
static int (*original_free)(alloc_device_t *, buffer_handle_t);
static int diagnostic_free(alloc_device_t *device, buffer_handle_t handle) {
    /* Intel blob disassembly reads the GEM flink name at byte 0x24.
     * Log only after checking the exact known handle layout. */
    int name = handle && handle->numFds == 0 && handle->numInts == 14 ? handle->data[6] : -1;
    ALOGE("ACER_GRALLOC_FREE_BEGIN name=%d", name);
    int rc = original_free(device, handle);
    ALOGE("ACER_GRALLOC_FREE_END name=%d rc=%d", name, rc);
    return rc;
}
static int diagnostic_alloc(alloc_device_t *device, int width, int height, int format,
        int usage, buffer_handle_t *handle, int *stride) {
    int rc = original_alloc(device, width, height, format, usage, handle, stride);
    ALOGE("ACER_GRALLOC_ALLOC %dx%d format=%d usage=%x rc=%d", width, height, format, usage, rc);
    if (!rc && handle && *handle) {
        ALOGE("ACER_GRALLOC_HANDLE version=%d fds=%d ints=%d stride=%d",
                (*handle)->version, (*handle)->numFds, (*handle)->numInts,
                stride ? *stride : -1);
        if ((*handle)->numFds == 0 && (*handle)->numInts == 14)
            ALOGE("ACER_GRALLOC_ALLOC_NAME name=%d", (*handle)->data[6]);
    }
    return rc;
}

static void load_module(void) {
    const hw_module_t *module = NULL;
    load_error = acer_legacy_load_hal("gralloc", &module);
    if (load_error != 0) return;
    if (module->module_api_version < GRALLOC_MODULE_API_VERSION_0_1 ||
        module->module_api_version > GRALLOC_MODULE_API_VERSION_0_3) {
        load_error = -EPROTONOSUPPORT;
        return;
    }
    target = (const gralloc_module_t *)module;
    if (!target->registerBuffer || !target->unregisterBuffer || !target->lock || !target->unlock) {
        target = NULL;
        load_error = -EINVAL;
        return;
    }
    acer_gralloc_original_module = target;
    acer_gralloc_original_perform = (void *)target->perform;
    HAL_MODULE_INFO_SYM.common.module_api_version = module->module_api_version;
    load_error = 0;
}

__attribute__((constructor)) static void initialize(void) {
    pthread_once(&once, load_module);
}
#define GET_TARGET() do { pthread_once(&once, load_module); if (load_error) return load_error; } while (0)
static int bridge_open(const hw_module_t *module, const char *id, hw_device_t **device) {
    (void)module;
    if (!id || !device) return -EINVAL;
    *device = NULL;
    GET_TARGET();
    int rc = target->common.methods->open(&target->common, id, device);
    if (!rc && *device && !strcmp(id, GRALLOC_HARDWARE_GPU0)) {
        alloc_device_t *alloc = (alloc_device_t *)*device;
        if (alloc->alloc && alloc->alloc != diagnostic_alloc) {
            original_alloc = alloc->alloc;
            alloc->alloc = diagnostic_alloc;
        }
        if (alloc->free && alloc->free != diagnostic_free) {
            original_free = alloc->free;
            alloc->free = diagnostic_free;
        }
    }
    return rc;
}
static int register_buffer(const gralloc_module_t *module, buffer_handle_t handle) {
    (void)module; GET_TARGET();
    int rc = target->registerBuffer(target, handle);
    ALOGE("ACER_GRALLOC_REGISTER rc=%d version=%d fds=%d ints=%d", rc,
            handle ? handle->version : -1, handle ? handle->numFds : -1,
            handle ? handle->numInts : -1);
    return rc;
}
static int unregister_buffer(const gralloc_module_t *module, buffer_handle_t handle) {
    (void)module; GET_TARGET(); return target->unregisterBuffer(target, handle);
}
static int lock_buffer(const gralloc_module_t *module, buffer_handle_t handle,
        int usage, int l, int t, int w, int h, void **address) {
    (void)module; GET_TARGET(); return target->lock(target, handle, usage, l, t, w, h, address);
}
static int unlock_buffer(const gralloc_module_t *module, buffer_handle_t handle) {
    (void)module; GET_TARGET(); return target->unlock(target, handle);
}
static int lock_ycbcr(const gralloc_module_t *module, buffer_handle_t handle,
        int usage, int l, int t, int w, int h, struct android_ycbcr *layout) {
    (void)module; GET_TARGET();
    if (target->common.module_api_version < GRALLOC_MODULE_API_VERSION_0_2 || !target->lock_ycbcr)
        return -ENOSYS;
    return target->lock_ycbcr(target, handle, usage, l, t, w, h, layout);
}
static int lock_async(const gralloc_module_t *module, buffer_handle_t handle,
        int usage, int l, int t, int w, int h, void **address, int fence) {
    (void)module; GET_TARGET();
    if (target->common.module_api_version < GRALLOC_MODULE_API_VERSION_0_3 || !target->lockAsync)
        return -ENOSYS;
    return target->lockAsync(target, handle, usage, l, t, w, h, address, fence);
}
static int unlock_async(const gralloc_module_t *module, buffer_handle_t handle, int *fence) {
    (void)module; GET_TARGET();
    if (target->common.module_api_version < GRALLOC_MODULE_API_VERSION_0_3 || !target->unlockAsync)
        return -ENOSYS;
    return target->unlockAsync(target, handle, fence);
}
static int lock_async_ycbcr(const gralloc_module_t *module, buffer_handle_t handle,
        int usage, int l, int t, int w, int h, struct android_ycbcr *layout, int fence) {
    (void)module; GET_TARGET();
    if (target->common.module_api_version < GRALLOC_MODULE_API_VERSION_0_3 || !target->lockAsync_ycbcr)
        return -ENOSYS;
    return target->lockAsync_ycbcr(target, handle, usage, l, t, w, h, layout, fence);
}
static hw_module_methods_t methods = { .open = bridge_open };
gralloc_module_t HAL_MODULE_INFO_SYM = {
    .common = {
        .tag = HARDWARE_MODULE_TAG,
        .module_api_version = GRALLOC_MODULE_API_VERSION_0_1,
        .hal_api_version = HARDWARE_HAL_API_VERSION,
        .id = GRALLOC_HARDWARE_MODULE_ID,
        .name = "Acer isolated Intel gralloc bridge",
        .author = "Acer Android 9 port",
        .methods = &methods,
    },
    .registerBuffer = register_buffer, .unregisterBuffer = unregister_buffer,
    .lock = lock_buffer, .unlock = unlock_buffer, .perform = acer_gralloc_perform,
    .lock_ycbcr = lock_ycbcr, .lockAsync = lock_async,
    .unlockAsync = unlock_async, .lockAsync_ycbcr = lock_async_ycbcr,
};
