# SPDX-License-Identifier: Apache-2.0
# WiziBox Android 9 port configuration; modified 2026-10-11.
# Public-product candidate: no Google APKs or automatic TCP ADB.
LOCAL_PATH := device/acer/ducati2fhd

# This installation has no usable physical navigation keys. Keep the software
# bar enabled and at the bottom in both portrait and landscape orientations.
DEVICE_PACKAGE_OVERLAYS += device/acer/ducati2fhd/overlay

# Framework software capability: required by the bundled Email widget and
# launcher widget host. Do not inherit unverified tablet sensor capabilities.
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.software.app_widgets.xml:system/etc/permissions/android.software.app_widgets.xml

PRODUCT_PACKAGES += android.hardware.media.omx@1.0-service libstagefright_omx
PRODUCT_COPY_FILES += \
    device/acer/ducati2fhd/media_codecs.xml:system/vendor/etc/media_codecs.xml \
    frameworks/av/media/libstagefright/data/media_codecs_google_audio.xml:system/vendor/etc/media_codecs_google_audio.xml \
    frameworks/av/media/libstagefright/data/media_codecs_google_video.xml:system/vendor/etc/media_codecs_google_video.xml

PRODUCT_PACKAGES += android.hardware.wifi@1.0-service wpa_supplicant wpa_cli fs_config_files fs_config_dirs
PRODUCT_PROPERTY_OVERRIDES += wifi.interface=wlan0
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.wifi.xml:system/etc/permissions/android.hardware.wifi.xml \
    device/acer/ducati2fhd/acer-wifi.rc:system/vendor/etc/init/acer-wifi.rc \
    device/acer/ducati2fhd/acer-approved-gpu-access.rc:system/etc/init/acer-approved-gpu-access.rc \
    vendor/acer/ducati2fhd/wifi/bcm43241.ko:system/vendor/lib/modules/bcm43241.ko \
    vendor/acer/ducati2fhd/wifi/fw_bcmdhd.bin_43241_b4:system/vendor/firmware/fw_bcmdhd.bin_43241_b4 \
    vendor/acer/ducati2fhd/wifi/bcmdhd_aob.cal_43241_b4:system/vendor/firmware/bcmdhd_aob.cal_43241_b4

# Original Intel SST DSP firmware required by the actual LPE audio device.
PRODUCT_COPY_FILES += \
    vendor/acer/ducati2fhd/audio-deployment/fw_sst_0f28.bin:system/vendor/firmware/fw_sst_0f28.bin \
    vendor/acer/ducati2fhd/audio-deployment/aac_dec_0f28.bin:system/vendor/firmware/aac_dec_0f28.bin \
    vendor/acer/ducati2fhd/audio-deployment/mp3_dec_0f28.bin:system/vendor/firmware/mp3_dec_0f28.bin

# Hardware services/blobs and Intel rootdir are added only after ABI inspection.
# This scaffold can validate build configuration, not produce a bootable ROM.
PRODUCT_PROPERTY_OVERRIDES += \
    ro.sf.lcd_density=320 \
    qemu.hw.mainkeys=0

# Restore the manufacturer's measured 2 GB tablet heap profile. Omitting these
# leaves ART's 16 MB fallback, which is insufficient for Pie system services.
PRODUCT_PROPERTY_OVERRIDES += \
    dalvik.vm.heapstartsize=16m \
    dalvik.vm.heapgrowthlimit=192m \
    dalvik.vm.heapsize=512m \
    dalvik.vm.heaptargetutilization=0.75 \
    dalvik.vm.heapminfree=2m \
    dalvik.vm.heapmaxfree=8m

PRODUCT_PACKAGES += \
    hwcomposer.ducati2fhd \
    gralloc.ducati2fhd \
    libacer_legacy_loader \
    libGLES_intel7 \
    libacer_legacy_runtime \
    libdrm \
    android.hardware.graphics.allocator@2.0-impl \
    android.hardware.graphics.allocator@2.0-service \
    android.hardware.graphics.mapper@2.0-impl \
    android.hardware.graphics.composer@2.1-impl \
    android.hardware.graphics.composer@2.1-service

# Real AOSP keymaster HAL. No legacy hardware keystore module is installed,
# so the default implementation reports software-backed security honestly.
PRODUCT_PACKAGES += \
    android.hardware.keymaster@3.0-service \
    android.hardware.keymaster@3.0-impl

PRODUCT_PROPERTY_OVERRIDES += \
    ro.hardware.hwcomposer=ducati2fhd \
    ro.hardware.gralloc=ducati2fhd \
    ro.hardware.egl=intel7
$(call inherit-product, vendor/acer/ducati2fhd/vendor-stock.mk)

# Audio API2 uses a verified Intel C ABI adapter and independent C++ namespace.
PRODUCT_PACKAGES += \
    audio.primary.ducati2fhd \
    android.hardware.audio@2.0-service \
    android.hardware.audio@2.0-impl \
    android.hardware.audio.effect@2.0-impl
# Stock audio inputs are included once by vendor-stock.mk above.

PRODUCT_COPY_FILES += \
    device/acer/ducati2fhd/acer-graphics-sync.rc:system/etc/init/acer-graphics-sync.rc \
    device/acer/ducati2fhd/rootdir/init.ducati2fhd.rc:root/init.ducati2fhd.rc \
    device/acer/ducati2fhd/rootdir/fstab.ducati2fhd:root/fstab.ducati2fhd \
    device/acer/ducati2fhd/rootdir/ueventd.ducati2fhd.rc:root/ueventd.ducati2fhd.rc \
    frameworks/native/data/etc/android.hardware.usb.host.xml:system/etc/permissions/android.hardware.usb.host.xml \
    frameworks/native/data/etc/android.hardware.touchscreen.multitouch.xml:system/etc/permissions/android.hardware.touchscreen.multitouch.xml

# Intel backlight control, without advertising absent button/notification LEDs.
PRODUCT_PACKAGES += \
    lights.ducati2fhd \
    android.hardware.light@2.0-impl \
    android.hardware.light@2.0-service
PRODUCT_COPY_FILES += \
    device/acer/ducati2fhd/acer-backlight.rc:system/etc/init/acer-backlight.rc

# Permanent Acer legacy display, resume and storage policies.
PRODUCT_PACKAGES += acer_storage_policy
PRODUCT_COPY_FILES += \
    device/acer/ducati2fhd/acer-storage-policy.rc:system/etc/init/acer-storage-policy.rc \
    device/acer/ducati2fhd/acer-client-composition-bringup.rc:system/etc/init/acer-client-composition-bringup.rc \
    device/acer/ducati2fhd/acer-legacy-resume.rc:system/etc/init/acer-legacy-resume.rc

# Fresh source-built libraries copied into private legacy namespaces.
PRODUCT_PACKAGES += \
    acer_hwc_libcutils_copy \
    acer_audio_libcutils_copy \
    acer_audio_linker_copy \
    acer_audio_runtime_copy

# Authenticate ADB; no personal approval file or automatic TCP listener.
PRODUCT_DEFAULT_PROPERTY_OVERRIDES += ro.adb.secure=1 ro.secure=1
