# Toretto QNX native offline BLE evidence analyzer (prototype)

Read-only analyzer for the existing `identity_observations` array in the Python auditor's schema-v2 JSON reports. Uses the QNX `sys/json.h` API and `libjson`; no BlueZ, radio access, pairing, or connection attempts. Groups canonical fingerprints, counts unique addresses, exclusive-window handoffs, and multi-address scan windows. Findings are investigative signals, not proof of spoofing or compromise.

Build on Netcup: `source ~/projekty/qnx8-development/sdp8/qnxsdp-env.sh && qcc -Vgcc_ntox86_64 -std=c++17 main.cpp -ljson -o toretto-qnx-x86_64` (use `-Vgcc_ntoaarch64le` for ARM64). Run only on a QNX target; Netcup Debian is a cross-compile host.

Prototype limitations: requires identity_observations; ignores rows without fingerprints; does not verify that supplied fingerprints match payloads; does not perform live Bluetooth scanning. The QNX report schema is a separate lightweight output, not a drop-in replacement for the Python report.

## Reproducible cross-build

Run `bash qnx/native/build-qnx.sh` from the repository on a Linux host with QNX SDP 8.0 installed. Override the SDK location with `QNX_SDP_ROOT` or pass an output directory as the first argument. The script builds x86-64 and AArch64 with warnings treated as errors. Generated binaries go to `qnx/native/build/` by default and are intentionally excluded from version control.

Runtime validation on a QNX 8.0 target is still required. Cross-compilation alone does not establish runtime correctness or Bluetooth hardware support.

## Native incremental NDJSON processor

`live.cpp` is built as `toretto-qnx-live-x86_64` and `toretto-qnx-live-aarch64`. It reads one `ble_window` JSON object per input line, updates cumulative fingerprint/address counts, and emits one summary JSON line per window. It supports a configurable maximum number of fingerprint groups (default 2048), but per-group scan history and addresses are **not yet bounded**; do not run unattended indefinitely. Its input must be trusted or validated at the transport boundary.

**Verified in QNX 8 x86-64 under QEMU/TCG:** replayed three NDJSON windows captured live on Lenovo (5, 6, 10 observations). Native process returned 0 and emitted totals 5/11/21 observations and 5/8/11 fingerprint groups. This was replay inside QNX, **not yet direct live guest transport**. ARM64 is cross-compiled but not runtime tested.
