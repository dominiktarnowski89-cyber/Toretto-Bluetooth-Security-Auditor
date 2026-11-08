"""BLE advertising evidence capture and conservative temporal correlation."""
import hashlib
import json
from collections import defaultdict
from datetime import UTC, datetime


def _payload(device):
    data = {
        "local_name": str(device.get("local_name") or ""),
        "service_uuids": sorted(str(x).lower() for x in (device.get("service_uuids") or [])),
        "manufacturer_data": {str(k): str(v).lower() for k, v in sorted((device.get("manufacturer_data") or {}).items())},
        "service_data": {str(k).lower(): str(v).lower() for k, v in sorted((device.get("service_data") or {}).items())},
    }
    if not data["local_name"] and not data["service_uuids"] and not data["manufacturer_data"] and not data["service_data"]:
        return None
    return data


def _optional_hex(value):
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).hex()
    if isinstance(value, str):
        return value.lower().replace(":", "").replace(" ", "")
    return None


def make_observation(device, scan_id, observed_at=None):
    payload = _payload(device)
    if payload is None:
        return None
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    structure = {
        "local_name": bool(payload["local_name"]),
        "service_uuids": payload["service_uuids"],
        "manufacturer_ids": sorted(payload["manufacturer_data"]),
        "manufacturer_lengths": sorted(len(x) // 2 for x in payload["manufacturer_data"].values()),
        "service_data_ids": sorted(payload["service_data"]),
        "service_data_lengths": sorted(len(x) // 2 for x in payload["service_data"].values()),
    }
    raw_advertisement = _optional_hex(device.get("raw_advertisement_data"))
    return {
        "observed_at": observed_at or device.get("observed_at") or datetime.now(UTC).isoformat(),
        "scan_id": int(scan_id),
        "scan_started_at": device.get("scan_started_at"),
        "scan_completed_at": device.get("scan_completed_at"),
        "scan_duration_seconds": device.get("scan_duration_seconds"),
        "address": str(device.get("address") or "unknown"),
        "address_type": device.get("address_type"),
        "name": str(device.get("local_name") or device.get("name") or ""),
        "rssi": device.get("rssi"),
        "tx_power": device.get("tx_power"),
        "connectable": device.get("connectable"),
        "fingerprint": hashlib.sha256(raw).hexdigest(),
        "structure_fingerprint": hashlib.sha256(json.dumps(structure, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "payload_fields": structure,
        "advertising_payload": payload,
        "raw_advertisement_hex": raw_advertisement,
        "raw_advertisement_available": raw_advertisement is not None,
        "evidence_note": "Bleak exposes parsed advertising fields; this is not a complete raw HCI advertising PDU." if raw_advertisement is None else "Raw advertising bytes supplied by backend.",
    }


def build_identity_observations(devices, scan_id):
    return [x for d in devices if (x := make_observation(d, scan_id))]


def analyze_observations(observations):
    groups = defaultdict(list)
    for item in observations:
        if item.get("fingerprint"):
            groups[item["fingerprint"]].append(item)
    devices, alerts = [], []
    for fp, items in groups.items():
        items = sorted(items, key=lambda x: (x.get("scan_id", 0), x.get("observed_at", "")))
        addresses = sorted({x.get("address", "unknown") for x in items})
        by_scan = defaultdict(set)
        for item in items:
            by_scan[item.get("scan_id", 0)].add(item.get("address", "unknown"))
        exclusive = [(sid, next(iter(v))) for sid, v in sorted(by_scan.items()) if len(v) == 1]
        handoffs = sum(a != b for (_, a), (_, b) in zip(exclusive, exclusive[1:], strict=False))
        multi_address_windows = {sid: sorted(values) for sid, values in by_scan.items() if len(values) > 1}
        status = "Jeden adres"
        if len(addresses) > 1:
            status = "Ten sam wzorzec danych na wielu adresach"
            alerts.append({
                "type": "shared_payload_multiple_addresses", "confidence": "medium",
                "fingerprint": fp, "addresses": addresses,
                "message": "Identyczny odcisk danych reklamowych wystapil pod roznymi adresami. Mozliwa rotacja prywatnego adresu albo wiele nadajnikow; same dane nie rozstrzygaja, ktory wariant zachodzi.",
            })
        if handoffs >= 3:
            status = "Powtarzalne przelaczanie adresow"
            alerts.append({
                "type": "repeated_address_handoff", "confidence": "medium",
                "fingerprint": fp, "addresses": addresses, "handoffs": handoffs,
                "message": "Wylaczne okna skanowania wskazuja na powtarzalne zmiany adresu dla tego samego wzorca. To zgodne z rotacja BLE, ale nie dowodzi wspolnej tozsamosci fizycznej.",
            })
        if multi_address_windows:
            alerts.append({
                "type": "multiple_addresses_within_scan_window", "confidence": "low",
                "fingerprint": fp, "addresses": addresses,
                "scan_ids": sorted(multi_address_windows),
                "address_sets_by_scan": {str(k): v for k, v in sorted(multi_address_windows.items())},
                "message": "Ten sam wzorzec zarejestrowano pod wieloma adresami w jednym oknie skanowania. Okno nie potwierdza jednoczesnej emisji radiowej.",
            })
        rssi = [x["rssi"] for x in items if isinstance(x.get("rssi"), (int, float))]
        address_types = sorted({str(x.get("address_type")) for x in items if x.get("address_type")})
        devices.append({
            "fingerprint": fp, "fingerprint_short": fp[:12], "addresses": addresses,
            "address_count": len(addresses), "observations": len(items),
            "first_seen": items[0].get("observed_at", ""), "last_seen": items[-1].get("observed_at", ""),
            "last_rssi": items[-1].get("rssi"),
            "average_rssi": round(sum(rssi) / len(rssi), 1) if rssi else None,
            "handoffs": handoffs, "multi_address_scan_windows": len(multi_address_windows),
            "address_types_reported": address_types, "status": status,
            "confidence": "medium" if len(addresses) > 1 else "low",
            "name": next((x.get("name") for x in reversed(items) if x.get("name")), ""),
            "payload_fields": items[-1].get("payload_fields", {}),
            "advertising_payload": items[-1].get("advertising_payload", {}),
            "evidence_note": items[-1].get("evidence_note", ""),
        })
    devices.sort(key=lambda x: (x["address_count"], x["observations"]), reverse=True)
    return {"devices": devices, "alerts": alerts, "observation_count": len(observations)}
