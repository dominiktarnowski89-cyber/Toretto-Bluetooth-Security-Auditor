# TORETTO Bluetooth Security Auditor — QNX 8 competition demonstration

## Pitch

A native QNX 8 C++17 engine correlates Bluetooth Low Energy advertising observations across scan windows to flag suspicious-looking address changes. The radio receiver is an ordinary Linux Bluetooth adapter (Lenovo G500); a small SSH/serial bridge streams observations to the QNX guest. No pairing or access to nearby devices is attempted.

## Why QNX?

The analyzer is compiled for QNX 8 x86-64 and AArch64 using the QNX SDK, uses the QNX `libjson` API, and has been executed inside QNX 8 x86-64 under QEMU. It does not merely run a Linux application inside QEMU. AArch64 has been cross-compiled, not executed.

## Reproducible demonstration

1. Provision a licensed QNX SDP 8 SDK and follow `../vm/README.md` to create an official QNX 8 x86-64 QEMU image using `mkqnximage`. QNX SDK and proprietary OS files are **not** redistributed in this repository.
2. Compile `../native/main.cpp` and `../native/live.cpp` using `../native/build-qnx.sh`. Include `toretto-qnx-live-x86_64` in the official QNX IFS. In the QNX startup script after `devc-ser8250`, run `waitfor /dev/ser2` and `/proc/boot/toretto-qnx-live < /dev/ser2 &`.
3. Boot QEMU with the usual official image flags and **two serial ports**: `-display none -serial stdio -serial unix:/tmp/toretto-qnx-serial.sock,server=on,wait=off` (console first, BLE data second). See `../bridge/README.md` for the complete tested QEMU command.
4. Run `python3 qnx/contest/replay.py` from the repository root on the QEMU host. It sends five deterministic events. QNX emits one JSON summary per event to its console; expected final `shared_payload_groups=1` and `repeated_handoff_groups=1` (five scan windows, four address handoffs).
5. Optional **live mode**: run the authorized Lenovo collector through `../bridge/serial_bridge.py` as documented in `../bridge/README.md`. This needs a working Bluetooth adapter, SSH connectivity and an accessible QNX serial socket.

## Judging demonstration script (3 minutes)

- **0:00–0:30** Show architecture: Lenovo radio → SSH → QEMU COM2 → native QNX C++ analyzer.
- **0:30–1:15** Show QNX boot and the native `TORETTO_STREAM_PID` startup marker.
- **1:15–2:00** Run deterministic fixture replay; watch QNX count fingerprints and address handoffs.
- **2:00–2:40** Run a short real Bluetooth scan on Lenovo; observe incremental QNX output.
- **2:40–3:00** Explain that shared advertising payloads are ambiguous: normal BLE address rotation or copied advertisements. They do not prove an intrusion.

## Scope and limitations

This is a read-only BLE observation and correlation prototype. The Linux scanner does not connect to nearby devices; the QNX VM does not own a physical Bluetooth adapter. It is not a packet sniffer, an intrusion proof system, or a production-grade continuous service. A successful host socket write is not an acknowledgement from QNX; spool replay, end-to-end delivery acknowledgement, GUI integration, and long-duration reliability remain unfinished. QNX per-group scan/address retention is bounded, but cumulative counters and the fixed fingerprint-group limit have trade-offs. For contest readiness, check the actual competition rules, accepted architectures, submission deadline, licensing and required video format separately; no compliance claim is made here.

## One-command offline contest verification

With an official, **locally licensed and prepared** QNX 8 image containing the native analyzer, and the matching official QEMU disk, run:

```bash
QNX_IMAGE=/absolute/path/ifs-serial-stream.bin QNX_DISK=/absolute/path/disk-qemu.vmdk bash qnx/contest/demo-run.sh
```

The script boots QNX, replays five synthetic BLE events, verifies the native guest log (five events, address sharing, repeated handoff) and shuts down QEMU. It does not need Lenovo, Netcup, or an Internet connection. This intentionally does **not** package or redistribute proprietary QNX binaries. The official-image customization still needs to be documented as a portable build recipe.

## Boundary test (QNX guest)

`boundary-test.py` boots the prepared local QNX image, sends malformed JSON, a non-BLE event, an empty BLE event and 70 BLE events with distinct addresses and scan IDs. It validates the native guest output and terminates QEMU. This tests the 32-address / 64-scan retention caps. Run on a machine with the prepared licensed QNX 8 image at the paths in the script. On 2026-11-11, result: `QNX_BOUNDARY_PASS`, 71 processed BLE windows and 70 observations. An oversized-input test and clean-room build remain outstanding.
