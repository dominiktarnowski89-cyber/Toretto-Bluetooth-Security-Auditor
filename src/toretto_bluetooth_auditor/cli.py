"""Terminal interface for TORETTO Bluetooth Security Auditor."""
from __future__ import annotations

import argparse
import asyncio
import json
import socket
import sys
from datetime import UTC, datetime
from pathlib import Path

from .assessment import assess_adapter
from .collectors.ble_scan import scan_ble
from .collectors.linux_bt import adapter_status, rfkill_status, scan_classic
from .discovery import classify_device
from .identity import analyze_observations, build_identity_observations
from .models import AuditReport
from .reporting import save_html, save_json


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="toretto-bt-auditor-cli",
        description="TORETTO Bluetooth Security Auditor — read-only CLI (BLE + Bluetooth Classic).",
        epilog=(
            "Examples: status | scan --mode all --timeout 12 | "
            "scan --mode ble --timeout 20 --json reports/scan.json --html reports/scan.html"
        ),
    )
    parser.add_argument(
        "--version", action="version", version="TORETTO Bluetooth Security Auditor 0.2.0"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show local Bluetooth adapter and rfkill state")
    status.add_argument("--json", metavar="FILE", help="Write status JSON to FILE (use - for stdout)")

    scan = sub.add_parser("scan", help="Discover nearby Bluetooth devices")
    scan.add_argument("--mode", choices=("all", "ble", "classic"), default="all")
    scan.add_argument("--timeout", type=float, default=8.0, help="Scan duration in seconds (default: 8)")
    scan.add_argument("--json", metavar="FILE", help="Write full JSON report to FILE (use - for stdout)")
    scan.add_argument("--html", metavar="FILE", help="Write HTML report to FILE")
    scan.add_argument("--quiet", action="store_true", help="Do not print the device table")
    scan.add_argument("--identity", action="store_true", help="Summarize advertising fingerprints in this scan")
    return parser


def _write_json(data: object, destination: str | None) -> None:
    if not destination:
        return
    rendered = json.dumps(data, indent=2, ensure_ascii=False)
    if destination == "-":
        print(rendered)
    else:
        path = Path(destination).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
        print(f"JSON zapisany: {path}", file=sys.stderr)


def _status(args: argparse.Namespace) -> int:
    adapter = adapter_status()
    rfkill = rfkill_status()
    data = {
        "host": socket.gethostname(),
        "checked_at": datetime.now(UTC).isoformat(),
        "adapter": adapter,
        "rfkill": rfkill,
    }
    if args.json == "-":
        _write_json(data, "-")
    else:
        print("TORETTO Bluetooth Security Auditor — status")
        print(f"Host:       {data['host']}")
        print(f"Adapter:    {'available' if adapter.get('available') else 'unavailable'}")
        for key in ("name", "address", "powered", "discoverable", "pairable", "discovering"):
            if key in adapter:
                print(f"{key:12}{adapter[key]}")
        if adapter.get("error"):
            print(f"Błąd:       {adapter['error']}")
        print(f"rfkill:     {rfkill if rfkill else 'brak danych'}")
        _write_json(data, args.json)
    return 0 if adapter.get("available") else 2


def _print_devices(devices: list[dict[str, object]]) -> None:
    if not devices:
        print("Nie wykryto urządzeń w tym oknie skanowania.")
        return
    headers = ("PROTO", "RSSI", "ADDRESS", "NAME", "IDENTIFICATION")
    rows = []
    for device in devices:
        rows.append(
            (
                str(device.get("protocol", "")),
                str(device.get("rssi") if device.get("rssi") is not None else "—"),
                str(device.get("address", "")),
                str(device.get("name", ""))[:30],
                str(device.get("identification_confidence", "none")),
            )
        )
    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
    print("  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    print("  ".join("─" * width for width in widths))
    for row in rows:
        print("  ".join(row[i].ljust(widths[i]) for i in range(len(headers))))


async def _collect(
    mode: str, timeout: float
) -> tuple[list[dict[str, object]], list[str]]:
    devices: list[dict[str, object]] = []
    errors: list[str] = []
    if mode in ("all", "ble"):
        try:
            devices.extend(await scan_ble(timeout))
        except Exception as error:
            errors.append(f"BLE: {error}")
    if mode in ("all", "classic"):
        try:
            devices.extend(await asyncio.to_thread(scan_classic, timeout))
        except Exception as error:
            errors.append(f"Bluetooth Classic: {error}")
    return [classify_device(item) for item in devices], errors


def _scan(args: argparse.Namespace) -> int:
    if args.timeout <= 0:
        print("Błąd: --timeout musi być większy od zera.", file=sys.stderr)
        return 2
    started = datetime.now(UTC).isoformat()
    print(f"TORETTO — skan {args.mode.upper()}, czas: {args.timeout:g} s")
    print(
        "Tryb obserwacyjny: bez parowania, połączeń GATT i wysyłania danych aplikacyjnych.\n"
    )
    devices, errors = asyncio.run(_collect(args.mode, args.timeout))
    report = AuditReport(
        "cli-scan", started_at=started, host=socket.gethostname(), nearby_devices=devices
    )
    adapter = adapter_status()
    report.adapter = adapter
    report.findings.extend(assess_adapter(adapter, rfkill_status()))

    observations = build_identity_observations(
        [device for device in devices if device.get("protocol") == "BLE"], scan_id=1
    )
    report.identity_observations = observations
    if not args.quiet:
        _print_devices(devices)
    ble_count = sum(device.get("protocol") == "BLE" for device in devices)
    classic_count = sum(device.get("protocol") == "Bluetooth Classic" for device in devices)
    print(f"\nWynik: {len(devices)} urządzeń (BLE: {ble_count}, Classic: {classic_count})")
    for error in errors:
        print(f"OSTRZEŻENIE: {error}", file=sys.stderr)

    if args.identity:
        summary = analyze_observations(observations)
        print(
            f"\nFingerprinty BLE: {len(summary['devices'])}; "
            f"obserwacje: {summary['observation_count']}; alerty: {len(summary['alerts'])}"
        )
        for item in summary["devices"]:
            print(
                f"  {item['fingerprint_short']}  adresy={item['address_count']}  "
                f"RSSI={item['last_rssi']}  {item['status']}"
            )
        if summary["alerts"]:
            print("Uwaga: wspólny fingerprint nie dowodzi, że to ten sam fizyczny nadajnik.")

    if args.json:
        if args.json == "-":
            _write_json(report.to_dict(), "-")
        else:
            save_json(report, args.json)
            print(f"JSON zapisany: {Path(args.json).expanduser()}")
    if args.html:
        save_html(report, args.html)
        print(f"HTML zapisany: {Path(args.html).expanduser()}")
    if not devices and errors:
        return 2
    return 0


def main() -> int:
    args = _parser().parse_args()
    if args.command == "status":
        return _status(args)
    if args.command == "scan":
        return _scan(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
