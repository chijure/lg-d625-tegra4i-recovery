#!/usr/bin/env bash
set -euo pipefail
recovery_mingw_prefix="${MINGW_PREFIX:-/mingw64}"
export PATH="$recovery_mingw_prefix/bin:/usr/bin:$PATH"
export PKG_CONFIG_PATH="$recovery_mingw_prefix/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
host_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$(cd -- "${1:?Pass the patched tegrarcm source directory}" && pwd)"
cp "$host_dir/compat.h" "$source_dir/compat.h"
cp "$host_dir/config.h" "$source_dir/config.h"
cd "$source_dir"
mkdir -p recovery-build
for unit in main usb rcm nv3p debug; do
    gcc -std=gnu99 -DDEBUG -Isrc -I. $(pkg-config --cflags libusb-1.0) \
        -include compat.h -c "src/$unit.c" -o "recovery-build/$unit.o"
done
for unit in aes-cmac rsa-pss; do
    g++ -std=c++11 -Isrc -I. -c "src/$unit.cpp" -o "recovery-build/$unit.o"
done
g++ recovery-build/*.o -o recovery-build/tegrarcm-t148.exe \
    $(pkg-config --libs libusb-1.0) -lcryptopp
echo "Built: $source_dir/recovery-build/tegrarcm-t148.exe"
