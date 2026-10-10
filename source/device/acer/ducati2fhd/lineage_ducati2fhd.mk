# SPDX-License-Identifier: Apache-2.0
# WiziBox Android 9 port configuration; modified 2026-10-11.
# The copy rule selects the first source for a destination. Register the
# legacy android_usb replacement before full_base's generic init.usb.rc.
PRODUCT_COPY_FILES += device/acer/ducati2fhd/rootdir/init.usb.rc:root/init.usb.rc

$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base.mk)
$(call inherit-product, vendor/lineage/config/common_full_tablet_wifionly.mk)
$(call inherit-product, device/acer/ducati2fhd/device.mk)

PRODUCT_NAME := lineage_ducati2fhd
PRODUCT_DEVICE := ducati2fhd
PRODUCT_BRAND := Acer
PRODUCT_MODEL := A1-840FHD
PRODUCT_MANUFACTURER := Acer
PRODUCT_CHARACTERISTICS := tablet
