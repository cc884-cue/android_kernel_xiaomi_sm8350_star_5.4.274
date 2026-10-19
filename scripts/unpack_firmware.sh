#!/usr/bin/env bash
# Unpack a Xiaomi/QCOM OTA payload.zip into boot artifacts for reference/patching.
# Usage: ./unpack_firmware.sh <ota_file.zip> [workdir]
set -euo pipefail

OTA="${1:?usage: $0 <ota_file.zip> [workdir]}"
WORK="${2:-$(dirname "$OTA")/extracted}"
BIN="$(mktemp -d)"
trap 'rm -rf "$BIN"' EXIT

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing $1" >&2; exit 1; }; }
need unzip

mkdir -p "$WORK" "$BIN/pl"
unzip -p "$OTA" payload.bin > "$BIN/payload.bin"

if command -v payload-dumper-go >/dev/null 2>&1; then
  payload-dumper-go -o "$WORK" "$BIN/payload.bin"
else
  echo "payload-dumper-go not on PATH; download from https://github.com/osm0sis/payload-dumper-go" >&2
  exit 1
fi

# Split boot.img (header v3) into kernel/ramdisk if magiskboot or unpack_bootimg is available
if command -v magiskboot >/dev/null 2>&1 && [[ -f "$WORK/boot.img" ]]; then
  (cd "$WORK" && magiskboot unpack boot.img)
  echo "boot unpacked: kernel, ramdisk in $WORK"
fi

ls -l "$WORK"
