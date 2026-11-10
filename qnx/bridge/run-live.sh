#!/usr/bin/env bash
# Netcup host: launch a bounded-memory QNX guest and continuously stream Lenovo BLE scans.
set -Eeuo pipefail
ROOT="${TORETTO_QNX_ROOT:-$HOME/projekty/qnx8-development/vm/official}"
REPO="${TORETTO_REPO:-$HOME/projekty/toretto-bluetooth-security-auditor}"
SOCKET="${TORETTO_QNX_SOCKET:-/tmp/toretto-qnx-serial.sock}"
mkdir -p "$ROOT/../logs"
cd "$ROOT"
if [[ ! -f output/ifs-serial-stream.bin || ! -f output/test-disk/disk-qemu.vmdk ]]; then
  echo "Missing QNX image or test disk" >&2; exit 2
fi
if [[ -S "$SOCKET" ]]; then
  echo "QNX socket already exists; refusing to replace an active session" >&2; exit 2
fi
qemu-system-x86_64 -machine pc -accel tcg,thread=multi -cpu max -smp 2 -m 2048 \
  -display none -serial stdio -serial "unix:$SOCKET,server=on,wait=off" \
  -monitor none -no-reboot -nic none -kernel output/ifs-serial-stream.bin \
  -drive file=output/test-disk/disk-qemu.vmdk,if=ide,format=vmdk \
  > "$ROOT/../logs/qnx-live-service.log" 2>&1 &
qemu_pid=$!
cleanup() { kill "$qemu_pid" 2>/dev/null || true; wait "$qemu_pid" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
for _ in $(seq 1 100); do
  if grep -aq TORETTO_STREAM_PID "$ROOT/../logs/qnx-live-service.log"; then break; fi
  if ! kill -0 "$qemu_pid" 2>/dev/null; then echo "QNX exited during startup" >&2; exit 1; fi
  sleep 1
done
if ! grep -aq TORETTO_STREAM_PID "$ROOT/../logs/qnx-live-service.log"; then echo "QNX stream not ready" >&2; exit 1; fi
while kill -0 "$qemu_pid" 2>/dev/null; do
  ssh -o BatchMode=yes -o ConnectTimeout=10 lenovo \
    "cd ~/projekty/toretto-bluetooth-security-auditor && .venv/bin/python scripts/live_ble_stream.py --window 5 --max-windows 0" \
    | python3 "$REPO/qnx/bridge/serial_bridge.py" || true
  sleep 5
done
