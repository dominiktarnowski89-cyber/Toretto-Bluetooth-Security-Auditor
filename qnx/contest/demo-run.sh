#!/usr/bin/env bash
# Run from repository root on a host with a licensed, prebuilt QNX 8 image.
set -Eeuo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
QNX_IMAGE="${QNX_IMAGE:?Set QNX_IMAGE to the QNX 8 IFS containing toretto-qnx-live}"
QNX_DISK="${QNX_DISK:?Set QNX_DISK to the official QNX QEMU disk image}"
OUT="${QNX_DEMO_OUTPUT:-$REPO/qnx/contest/demo-output}"
mkdir -p "$OUT"
SOCKET="$OUT/guest-serial.sock"
LOG="$OUT/qnx-console.log"
if [[ -e "$SOCKET" ]]; then echo "Refusing to replace existing socket: $SOCKET" >&2; exit 2; fi
qemu-system-x86_64 -machine pc -accel tcg,thread=multi -cpu max -smp 2 -m 2048 \
  -display none -serial stdio -serial "unix:$SOCKET,server=on,wait=off" \
  -monitor none -no-reboot -nic none -kernel "$QNX_IMAGE" \
  -drive "file=$QNX_DISK,if=ide,format=vmdk" > "$LOG" 2>&1 &
PID=$!
cleanup() { kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; }
trap cleanup EXIT
ready=0
for _ in $(seq 1 60); do
  if grep -aq TORETTO_STREAM_PID "$LOG"; then ready=1; break; fi
  if ! kill -0 "$PID" 2>/dev/null; then echo "Guest exited during startup" >&2; exit 1; fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then echo "QNX native analyzer did not start" >&2; exit 1; fi
python3 "$REPO/qnx/contest/replay.py" --socket "$SOCKET"
for _ in $(seq 1 20); do
  if [[ $(grep -ac '"engine":"toretto-qnx-live"' "$LOG" || true) -ge 5 ]]; then break; fi
  sleep 1
done
python3 "$REPO/qnx/contest/verify_demo.py" "$LOG"
