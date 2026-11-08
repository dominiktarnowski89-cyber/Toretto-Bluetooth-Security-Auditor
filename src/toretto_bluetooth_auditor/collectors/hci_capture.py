"""Capture raw Bluetooth HCI events while performing an authorized BLE scan."""

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from .ble_scan import scan_ble


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def capture_hci_during_ble_scan(duration: float = 20.0, output_path: str | Path | None = None):
    """Capture btsnoop HCI trace concurrently with an unfiltered BLE scan."""
    if duration <= 0:
        raise ValueError("duration must be greater than zero")
    if not shutil.which("btmon"):
        raise RuntimeError("btmon is not installed; install BlueZ tools first")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = Path(output_path) if output_path else Path("reports") / f"ble-hci-{stamp}.btsnoop"
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)

    command = ["btmon", "--write", str(path)]
    if os.geteuid() != 0:
        if not shutil.which("sudo"):
            path.unlink(missing_ok=True)
            raise RuntimeError("btmon needs root privileges; sudo is unavailable")
        command[0:0] = ["sudo", "-n"]

    process = None
    started = datetime.now(UTC).isoformat()
    try:
        process = subprocess.Popen(
            command, stdin=None, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, start_new_session=False
        )
        time.sleep(0.6)
        if process.poll() is not None:
            raise RuntimeError("btmon exited before capture started; check sudo access and adapter (use sudo -v first)")
        devices = asyncio.run(scan_ble(timeout=duration))
    finally:
        if process is not None and process.poll() is None:
            try:
                process.send_signal(signal.SIGINT)
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try:
                    process.terminate()
                except subprocess.TimeoutExpired:
                    process.kill()
                process.wait(timeout=3)

    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError("HCI capture produced an empty trace; no evidence was saved")
    return {
        "schema_version": 1,
        "capture_started_at": started,
        "capture_finished_at": datetime.now(UTC).isoformat(),
        "duration_seconds": duration,
        "capture_file": str(path),
        "capture_size_bytes": path.stat().st_size,
        "capture_sha256": _sha256(path),
        "scan_method": "Bleak active BLE discovery concurrent with btmon HCI capture",
        "connection_attempts": 0,
        "pairing_attempts": 0,
        "gatt_connections": 0,
        "devices": devices,
    }


def main():
    parser = argparse.ArgumentParser(description="Capture raw Bluetooth HCI events during an unfiltered BLE scan.")
    parser.add_argument("--duration", type=float, default=25.0)
    parser.add_argument("--output", help="BTSnoop path; existing files are never overwritten")
    parser.add_argument("--json", help="JSON sidecar path")
    args = parser.parse_args()
    try:
        result = capture_hci_during_ble_scan(args.duration, args.output)
        json_path = Path(args.json) if args.json else Path(result["capture_file"]).with_suffix(".json")
        json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + chr(10), encoding="utf-8")
        print(json.dumps({key: value for key, value in result.items() if key != "devices"}, indent=2))
        print(f"BLE devices observed: {len(result['devices'])}")
        print(f"JSON sidecar: {json_path}")
    except (OSError, RuntimeError, ValueError) as error:
        print(f"HCI capture failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
