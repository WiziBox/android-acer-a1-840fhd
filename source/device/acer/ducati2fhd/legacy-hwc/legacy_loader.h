/* SPDX-License-Identifier: Apache-2.0 */
#pragma once
#include <hardware/hardware.h>
int acer_legacy_load_hal(const char *id, const hw_module_t **module);
void *acer_legacy_load_gles(void);
