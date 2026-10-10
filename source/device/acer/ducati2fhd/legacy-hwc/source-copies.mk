# SPDX-License-Identifier: Apache-2.0
# Copy freshly built platform/project libraries into legacy namespaces.
# ETC modules avoid replacing or relinking the main platform shared libraries.

include $(CLEAR_VARS)
LOCAL_MODULE := acer_hwc_libcutils_copy
LOCAL_MODULE_CLASS := ETC
LOCAL_MODULE_STEM := libcutils.so
LOCAL_MODULE_PATH := $(TARGET_OUT)/legacy-hwc/lib
LOCAL_PREBUILT_MODULE_FILE := $(TARGET_OUT_SHARED_LIBRARIES)/libcutils.so
LOCAL_REQUIRED_MODULES := libcutils
include $(BUILD_PREBUILT)

include $(CLEAR_VARS)
LOCAL_MODULE := acer_audio_libcutils_copy
LOCAL_MODULE_CLASS := ETC
LOCAL_MODULE_STEM := libcutils.so
LOCAL_MODULE_PATH := $(TARGET_OUT)/legacy-audio/lib
LOCAL_PREBUILT_MODULE_FILE := $(TARGET_OUT_SHARED_LIBRARIES)/libcutils.so
LOCAL_REQUIRED_MODULES := libcutils
include $(BUILD_PREBUILT)

include $(CLEAR_VARS)
LOCAL_MODULE := acer_audio_linker_copy
LOCAL_MODULE_CLASS := ETC
LOCAL_MODULE_STEM := ld-android.so
LOCAL_MODULE_PATH := $(TARGET_OUT)/legacy-audio/lib
LOCAL_PREBUILT_MODULE_FILE := $(TARGET_OUT_SHARED_LIBRARIES)/ld-android.so
LOCAL_REQUIRED_MODULES := ld-android
include $(BUILD_PREBUILT)

include $(CLEAR_VARS)
LOCAL_MODULE := acer_audio_runtime_copy
LOCAL_MODULE_CLASS := ETC
LOCAL_MODULE_STEM := libacer_legacy_runtime.so
LOCAL_MODULE_PATH := $(TARGET_OUT)/legacy-audio/lib
LOCAL_PREBUILT_MODULE_FILE := $(TARGET_OUT)/legacy-hwc/lib/libacer_legacy_runtime.so
LOCAL_REQUIRED_MODULES := libacer_legacy_runtime
include $(BUILD_PREBUILT)
