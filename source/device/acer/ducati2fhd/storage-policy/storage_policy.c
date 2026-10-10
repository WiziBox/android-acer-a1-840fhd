/* SPDX-License-Identifier: Apache-2.0
 * WiziBox Android 9 port implementation; modified 2026-10-11.
 */
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/statfs.h>
#include <sys/system_properties.h>
#include <unistd.h>

static int restore_view(const char *path, const char *options) {
    struct statfs fs;
    if (statfs(path, &fs) || (unsigned long)fs.f_type != 0x5dca2df5UL) {
        fprintf(stderr, "Expected mounted sdcardfs at %s\n", path);
        return -1;
    }
    // Keep the original nosuid/nodev/noexec/noatime mount protections.
    if (mount(NULL, path, "sdcardfs",
              MS_REMOUNT | MS_NOSUID | MS_NODEV | MS_NOEXEC | MS_NOATIME,
              options)) {
        fprintf(stderr, "Storage view remount %s: %s\n", path, strerror(errno));
        return -1;
    }
    return 0;
}

int main(void) {
    char device[PROP_VALUE_MAX] = {0};
    __system_property_get("ro.product.device", device);
    if (getuid() != 0 || strcmp(device, "ducati2fhd")) return 2;
    // Late boot re-propagation reaches Zygote/app slave mounts created before
    // vold finalized the read/write view policy. The default view is untouched.
    if (restore_view("/mnt/runtime/read/emulated", "gid=9997,mask=23")) return 1;
    if (restore_view("/mnt/runtime/write/emulated", "gid=9997,mask=7")) return 1;
    __system_property_set("debug.acer.storage_policy_ready", "1");
    puts("Acer storage read/write view policy restored");
    return 0;
}
