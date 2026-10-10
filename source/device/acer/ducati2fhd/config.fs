# SPDX-License-Identifier: Apache-2.0
# WiziBox Android 9 port configuration; modified 2026-10-11.
# Explicitly user-approved service file capabilities for kernel 3.10, which
# cannot propagate init ambient capabilities. Services retain the wifi UID.
[vendor/bin/hw/android.hardware.wifi@1.0-service]
mode: 0755
user: AID_ROOT
group: AID_ROOT
caps: NET_ADMIN NET_RAW SYS_MODULE

[system/bin/wificond]
mode: 0755
user: AID_ROOT
group: AID_ROOT
caps: NET_ADMIN NET_RAW

[vendor/bin/hw/wpa_supplicant]
mode: 0755
user: AID_ROOT
group: AID_ROOT
caps: NET_ADMIN NET_RAW
