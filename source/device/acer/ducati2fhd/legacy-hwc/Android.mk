# SPDX-License-Identifier: Apache-2.0
# Project graphics adapters. Generate the two GLES inputs before Android build.
LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := hwcomposer.ducati2fhd
LOCAL_MODULE_RELATIVE_PATH := hw
LOCAL_SRC_FILES := hwcomposer_namespace.c
LOCAL_MULTILIB := 32
LOCAL_SHARED_LIBRARIES := libacer_legacy_loader liblog
LOCAL_HEADER_LIBRARIES := libhardware_headers
LOCAL_CFLAGS := -Wall -Wextra -Werror
include $(BUILD_SHARED_LIBRARY)

# The audio bridge is project source; stock audio libraries remain owner inputs.
include $(CLEAR_VARS)
LOCAL_MODULE := audio.primary.ducati2fhd
LOCAL_MODULE_RELATIVE_PATH := hw
LOCAL_SRC_FILES := audio_namespace.c audio_abi.c
LOCAL_MULTILIB := 32
LOCAL_CXX_STL := none
LOCAL_SHARED_LIBRARIES := libdl liblog
LOCAL_HEADER_LIBRARIES := libhardware_headers
LOCAL_CFLAGS := -Wall -Wextra -Werror
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := libacer_legacy_loader
LOCAL_SRC_FILES := legacy_loader.c
LOCAL_MULTILIB := 32
LOCAL_CXX_STL := none
LOCAL_SHARED_LIBRARIES := libdl liblog
LOCAL_HEADER_LIBRARIES := libhardware_headers
LOCAL_CFLAGS := -Wall -Wextra -Werror
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := gralloc.ducati2fhd
LOCAL_MODULE_RELATIVE_PATH := hw
LOCAL_SRC_FILES := gralloc_namespace.c gralloc_perform_x86.S
LOCAL_MULTILIB := 32
LOCAL_CXX_STL := none
LOCAL_SHARED_LIBRARIES := libacer_legacy_loader liblog
LOCAL_HEADER_LIBRARIES := libhardware_headers
LOCAL_CFLAGS := -Wall -Wextra -Werror
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := libGLES_intel7
LOCAL_MODULE_RELATIVE_PATH := egl
LOCAL_SRC_FILES := gles_namespace.c gles_exports_x86.S
LOCAL_MULTILIB := 32
LOCAL_CXX_STL := none
LOCAL_SHARED_LIBRARIES := libacer_legacy_loader libdl liblog
LOCAL_HEADER_LIBRARIES := libhardware_headers
LOCAL_CFLAGS := -Wall -Wextra -Werror
include $(BUILD_SHARED_LIBRARY)

include $(CLEAR_VARS)
LOCAL_MODULE := libacer_legacy_runtime
LOCAL_LDFLAGS := -Wl,-z,global
LOCAL_HEADER_LIBRARIES := libcutils_headers
LOCAL_CXX_STL := none
LOCAL_MODULE_PATH := $(TARGET_OUT)/legacy-hwc/lib
LOCAL_SRC_FILES := legacy_runtime.c
LOCAL_MULTILIB := 32
LOCAL_CFLAGS := -Wall -Wextra -Werror
include $(BUILD_SHARED_LIBRARY)

include $(LOCAL_PATH)/source-copies.mk
