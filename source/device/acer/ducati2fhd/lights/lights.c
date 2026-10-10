/* SPDX-License-Identifier: Apache-2.0
 * WiziBox Android 9 port implementation; modified 2026-10-11.
 */
#define LOG_TAG "AcerBacklight"
#include <hardware/lights.h>
#include <log/log.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* Real measured Intel sysfs interface: brightness/max_brightness = 0..255.
 * No notification/button lights are advertised when hardware is absent. */
#ifndef ACER_BACKLIGHT_PATH
#define ACER_BACKLIGHT_PATH "/sys/class/backlight/intel_backlight/brightness"
#endif

static int set_backlight(struct light_device_t *device, const struct light_state_t *state) {
    (void)device;
    if (!state) return -EINVAL;
    if (state->brightnessMode != BRIGHTNESS_MODE_USER &&
            state->brightnessMode != BRIGHTNESS_MODE_SENSOR) return -ENOSYS;
    if (state->flashMode != LIGHT_FLASH_NONE) return -EINVAL;
    unsigned int color = state->color;
    unsigned int brightness = (77 * ((color >> 16) & 255) +
            150 * ((color >> 8) & 255) + 29 * (color & 255)) >> 8;
    char value[16];
    int length = snprintf(value, sizeof(value), "%u\n", brightness);
    int fd;
    do { fd = open(ACER_BACKLIGHT_PATH, O_WRONLY | O_CLOEXEC); } while (fd < 0 && errno == EINTR);
    if (fd < 0) {
        int error = errno;
        ALOGE("Cannot open Intel backlight: %s", strerror(error));
        return -error;
    }
    ssize_t written;
    do { written = write(fd, value, (size_t)length); } while (written < 0 && errno == EINTR);
    int result = written == length ? 0 : (written < 0 ? -errno : -EIO);
    close(fd);
    if (result) ALOGE("Cannot set Intel backlight to %u: %d", brightness, result);
    return result;
}

static int close_light(struct hw_device_t *device) { free(device); return 0; }

static int open_light(const struct hw_module_t *module, const char *name,
        struct hw_device_t **out) {
    if (!out || !name || !module) return -EINVAL;
    *out = NULL;
    if (strcmp(name, LIGHT_ID_BACKLIGHT)) return -ENODEV;
    struct light_device_t *device = calloc(1, sizeof(*device));
    if (!device) return -ENOMEM;
    device->common.tag = HARDWARE_DEVICE_TAG;
    device->common.version = LIGHTS_DEVICE_API_VERSION_1_0;
    device->common.module = (struct hw_module_t *)module;
    device->common.close = close_light;
    device->set_light = set_backlight;
    *out = &device->common;
    return 0;
}

static struct hw_module_methods_t methods = { .open = open_light };
struct hw_module_t HAL_MODULE_INFO_SYM = {
    .tag = HARDWARE_MODULE_TAG,
    .module_api_version = HARDWARE_MODULE_API_VERSION(1, 0),
    .hal_api_version = HARDWARE_HAL_API_VERSION,
    .id = LIGHTS_HARDWARE_MODULE_ID,
    .name = "Acer ducati2fhd Intel backlight",
    .author = "Acer Android 9 bring-up",
    .methods = &methods,
};
