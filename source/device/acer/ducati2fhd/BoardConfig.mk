# SPDX-License-Identifier: Apache-2.0
# WiziBox Android 9 port configuration; modified 2026-10-11.
# Acer A1-840FHD bring-up. NOT flash-ready: Intel OSIP packing is separate.
TARGET_ARCH := x86
TARGET_ARCH_VARIANT := silvermont
TARGET_CPU_ABI := x86
TARGET_CPU_VARIANT := silvermont
TARGET_KERNEL_ARCH := x86
TARGET_KERNEL_HEADER_ARCH := x86

# Keep a 32-bit Binder ABI for legacy x86 vendor processes; the kernel still
# needs modern multi-context/scatter-gather support before Android 9 boots.
TARGET_USES_64_BIT_BINDER := false
TARGET_NO_BOOTLOADER := true
TARGET_NO_RADIOIMAGE := true
TARGET_NO_KERNEL := true
TARGET_USES_HWC2 := true
TARGET_SCREEN_WIDTH := 1200
TARGET_SCREEN_HEIGHT := 1920
DEVICE_MANIFEST_FILE := device/acer/ducati2fhd/manifest.xml
# Compile the boot classpath and system-server jars on the host. The tablet's
# measured startup currently generates its boot image and verifies all apps.
# Keep third-party app/account data unchanged; this is a ROM build setting.
WITH_DEXPREOPT := true
WITH_DEXPREOPT_BOOT_IMG_AND_SYSTEM_SERVER_ONLY := true
TARGET_FS_CONFIG_GEN := device/acer/ducati2fhd/config.fs

# Actual SDIO BCM43241, rebuilt against the device's signed 3.10 kernel.
BOARD_WLAN_DEVICE := bcmdhd
BOARD_WPA_SUPPLICANT_DRIVER := NL80211
BOARD_HOSTAPD_DRIVER := NL80211
WPA_SUPPLICANT_VERSION := VER_0_8_X
BOARD_WPA_SUPPLICANT_PRIVATE_LIB := lib_driver_cmd_bcmdhd
BOARD_HOSTAPD_PRIVATE_LIB := lib_driver_cmd_bcmdhd
WPA_SUPPLICANT_USE_HIDL := y
WIFI_HIDL_FEATURE_DISABLE_AP := true
WIFI_DRIVER_MODULE_PATH := /vendor/lib/modules/bcm43241.ko
WIFI_DRIVER_MODULE_NAME := bcm43241
WIFI_DRIVER_MODULE_ARG := firmware_path=/vendor/firmware/fw_bcmdhd.bin_43241_b4\ nvram_path=/vendor/firmware/bcmdhd_aob.cal_43241_b4\ iface_name=wlan
WIFI_DRIVER_FW_PATH_PARAM := /sys/module/bcm43241/parameters/firmware_path

# Measured partition size, not an emulator layout.
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 1887436800
BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE := ext4
TARGET_USERIMAGES_USE_EXT4 := true
BOARD_CACHEIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_ROOT_EXTRA_FOLDERS := factory acer-config logs
BOARD_FLASH_BLOCK_SIZE := 512

# No BOARD_BOOTIMAGE_PARTITION_SIZE: OSIP images share reserved, not partitions.
# No emulator EGL driver: actual Intel HAL integration is pending.
