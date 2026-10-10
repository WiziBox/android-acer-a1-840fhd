# SPDX-License-Identifier: Apache-2.0
# WiziBox Android 9 port configuration; modified 2026-10-11.
LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := acer_storage_policy
LOCAL_SRC_FILES := storage_policy.c
LOCAL_MULTILIB := 32
LOCAL_CFLAGS := -Wall -Wextra -Werror
include $(BUILD_EXECUTABLE)
