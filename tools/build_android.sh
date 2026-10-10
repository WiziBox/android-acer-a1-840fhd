#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Build on the host only. No flashing or automatic download occurs here.
set -euo pipefail
if [[ $# -lt 2 ]]; then
    echo 'Usage: bash tools/build_android.sh SOURCE NEW_OUT_DIR [make targets...]' >&2
    exit 2
fi
source_tree=$(realpath "$1")
build_output=$(realpath -m "$2")
shift 2
if [[ -e "$build_output" || -L "$build_output" ]]; then
    echo 'Refusing to reuse an existing output directory.' >&2
    exit 2
fi
case "$build_output/" in
    "$source_tree/"*) echo 'Output must be outside the source tree.' >&2; exit 2;;
esac
test -f "$source_tree/build/envsetup.sh"
test -f "$source_tree/device/acer/ducati2fhd/device.mk"
test -f "$source_tree/vendor/acer/ducati2fhd/vendor-stock.mk"
command -v python2 >/dev/null || { echo 'Python 2.7 is required by this pinned Android 9 tree.' >&2; exit 2; }
python2 -c 'import sys, zlib; assert sys.version_info[:2] == (2, 7)'
export JAVA_HOME="$source_tree/prebuilts/jdk/jdk8/linux-x86"
test -x "$JAVA_HOME/bin/java"
export PATH="$JAVA_HOME/bin:$PATH"
export OUT_DIR="$build_output"
cd "$source_tree"
# The historical envsetup script assumes variables may be unset.
set +u
source build/envsetup.sh
lunch lineage_ducati2fhd-userdebug
set -u
if [[ $# -eq 0 ]]; then
    set -- systemimage ramdisk
fi
m -j"${BUILD_JOBS:-4}" "$@"
echo 'Host build completed. This is not an OSIP image, a release approval or a device installation.'
