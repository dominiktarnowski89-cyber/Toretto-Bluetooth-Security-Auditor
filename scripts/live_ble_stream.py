#!/usr/bin/env python3
"""Continuous, read-only BLE observations as newline-delimited JSON (NDJSON)."""
import argparse
import asyncio
import json
import signal
import sys
from datetime import UTC, datetime

from toretto_bluetooth_auditor.collectors.ble_scan import scan_ble
from toretto_bluetooth_auditor.identity import build_identity_observations, analyze_observations


async def run(seconds: float, max_windows: int) -> int:
    stop = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            asyncio.get_running_loop().add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass
    history = []
    scan_id = 0
    while not stop.is_set() and (max_windows == 0 or scan_id < max_windows):
        scan_id += 1
        try:
            devices = await scan_ble(seconds)
            observations = build_identity_observations(devices, scan_id)
            history.extend(observations)
            summary = analyze_observations(history)
            record = {"event": "ble_window", "timestamp": datetime.now(UTC).isoformat(),
                      "scan_id": scan_id, "identity_observations": observations,
                      "total_observations": len(history), "alerts": summary["alerts"]}
            print(json.dumps(record, separators=(",", ":")), flush=True)
            print("window={} observations={} cumulative={} alerts={}".format(scan_id, len(observations), len(history), len(summary.get("alerts", []))), file=sys.stderr, flush=True)
        except Exception as exc:
            print(json.dumps({"event": "scan_error", "scan_id": scan_id, "error": str(exc)}), flush=True)
            print(f"window={scan_id} error={exc}", file=sys.stderr, flush=True)
        if stop.is_set():
            break
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--window", type=float, default=5)
    p.add_argument("--max-windows", type=int, default=0, help="0 = continuous")
    args = p.parse_args()
    if args.window <= 0 or args.max_windows < 0:
        p.error("invalid window or max-windows")
    return asyncio.run(run(args.window, args.max_windows))


if __name__ == "__main__":
    raise SystemExit(main())
