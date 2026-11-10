#!/usr/bin/env bash
set -Eeuo pipefail
SDK="${QNX_SDP_ROOT:-$HOME/projekty/qnx8-development/sdp8}"
if [[ ! -f "$SDK/qnxsdp-env.sh" ]]; then echo "QNX SDP not found: $SDK" >&2; exit 2; fi
source "$SDK/qnxsdp-env.sh"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$HERE/build}"
mkdir -p "$OUT"
for spec in "gcc_ntox86_64:x86_64" "gcc_ntoaarch64le:aarch64"; do
  target="${spec%%:*}"; arch="${spec#*:}"
  qcc -V"$target" -std=c++17 -Wall -Wextra -Werror "$HERE/main.cpp" -ljson -o "$OUT/toretto-qnx-$arch"
  qcc -V"$target" -std=c++17 -Wall -Wextra -Werror "$HERE/live.cpp" -ljson -o "$OUT/toretto-qnx-live-$arch"
  file "$OUT/toretto-qnx-$arch" "$OUT/toretto-qnx-live-$arch"
done
