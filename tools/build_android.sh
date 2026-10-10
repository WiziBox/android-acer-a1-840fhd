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
tool_directory=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
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
export JAVA_HOME="$source_tree/prebuilts/jdk/jdk8/linux-x86"
test -x "$JAVA_HOME/bin/java"
python_prebuilt="$source_tree/prebuilts/python/linux-x86/2.7.5"
test -x "$python_prebuilt/bin/python2.7"
test -f "$source_tree/external/python/cpython2/Modules/zlibmodule.c"
command -v gcc >/dev/null
# Keep this host extension under the new output; never reuse a developer's
# copied zlib.so or change the system Python. Host 32-bit zlib headers/libs
# and GCC multilib are required. Upstream CPython source stays untouched.
mkdir -p "$build_output/host/python2-modules"
gcc -m32 -shared -fPIC -O2 \
    -I "$python_prebuilt/include/python2.7" \
    -include "$tool_directory/python27-zlib-compat.h" \
    "$source_tree/external/python/cpython2/Modules/zlibmodule.c" -lz \
    -o "$build_output/host/python2-modules/zlib.so"
export PYTHONPATH="$build_output/host/python2-modules"
export PYTHONDONTWRITEBYTECODE=1
export PATH="$python_prebuilt/bin:$JAVA_HOME/bin:$PATH"
python2.7 -c 'import sys, zlib; assert sys.version_info[:2] == (2, 7); assert zlib.decompress(zlib.compress("probe")) == "probe"'
export OUT_DIR="$build_output"
cd "$source_tree"
# The historical envsetup script assumes variables may be unset.
set +u
source build/envsetup.sh
lunch lineage_ducati2fhd-userdebug
# Keep nounset disabled while calling old envsetup functions (TOP may be unset).
if [[ $# -eq 0 ]]; then
    set -- systemimage ramdisk
fi
m -j"${BUILD_JOBS:-4}" "$@"
echo 'Host build completed. This is not an OSIP image, a release approval or a device installation.'
