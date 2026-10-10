/* SPDX-License-Identifier: Apache-2.0
 * KitKat libc wrappers removed from Android 9. Preserve kernel error/errno
 * semantics; do not fake success or alter scheduler settings at load time.
 */
#include <sys/syscall.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <errno.h>
#include <time.h>

/* Emit the platform's existing legacy atomic API as real exported C symbols.
 * Keep its documented ordering/return contracts, not ad-hoc replacements.
 */
#define ANDROID_ATOMIC_INLINE
#include <cutils/atomic.h>

int ioprio_get(int which, int who);
int ioprio_set(int which, int who, int priority);
int __futex_syscall3(volatile void *address, int operation, int value);
int __futex_syscall4(volatile void *address, int operation, int value,
                     const struct timespec *timeout);
void set_process_name(const char *name);
const char *get_process_name(void);

/* AOSP 4.4 libcutils process_name contract, for this non-emulator target.
 * Returned names remain valid after later calls, as in the original API.
 */
static const char *legacy_process_name = "unknown";
void set_process_name(const char *name) {
    if (name == NULL) return;
    char *copy = strdup(name);
    if (copy == NULL) return;
    __atomic_store_n(&legacy_process_name, copy, __ATOMIC_RELEASE);
    size_t size = strlen(name);
    prctl(PR_SET_NAME, (unsigned long)(size < 16 ? name : name + size - 15), 0, 0, 0);
}
const char *get_process_name(void) {
    return __atomic_load_n(&legacy_process_name, __ATOMIC_ACQUIRE);
}

int ioprio_get(int which, int who) {
    return (int)syscall(__NR_ioprio_get, which, who);
}

int ioprio_set(int which, int who, int priority) {
    return (int)syscall(__NR_ioprio_set, which, who, priority);
}

/* Old x86 bionic used a raw int 0x80 futex wrapper: return -errno directly
 * and leave thread errno untouched. Modern syscall() uses -1/errno, so
 * convert that contract without changing the requested operation. */
int __futex_syscall4(volatile void *address, int operation, int value,
                     const struct timespec *timeout) {
    int saved_errno = errno;
    long result = syscall(__NR_futex, address, operation, value, timeout, NULL, 0);
    int raw_result = result < 0 ? -errno : (int)result;
    errno = saved_errno;
    return raw_result;
}
int __futex_syscall3(volatile void *address, int operation, int value) {
    return __futex_syscall4(address, operation, value, NULL);
}
