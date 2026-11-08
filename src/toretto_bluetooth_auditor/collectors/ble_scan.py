from datetime import UTC, datetime
from time import monotonic


async def scan_ble(timeout=8.0):
    """Discover BLE advertisements and retain all parsed advertising fields.

    Bleak returns parsed advertisement data, not necessarily the complete raw
    HCI advertising PDU. Active scanning can request scan-response data; it
    does not pair, connect, or exchange GATT/application data.
    """
    try:
        from bleak import BleakError, BleakScanner
    except ImportError as error:
        raise RuntimeError("Bleak missing; run installer") from error

    started_wall = datetime.now(UTC).isoformat()
    started_mono = monotonic()
    try:
        found = await BleakScanner.discover(
            timeout=timeout, return_adv=True, scanning_mode="active",
        )
    except (BleakError, NotImplementedError, ValueError) as error:
        raise RuntimeError(f"BLE scanning unavailable: {error}") from error

    completed_wall = datetime.now(UTC).isoformat()
    duration = round(monotonic() - started_mono, 3)
    output = []
    for device, advertisement in found.values():
        service_uuids = list(advertisement.service_uuids or [])
        manufacturer_data = {str(k): bytes(v).hex() for k, v in sorted(advertisement.manufacturer_data.items())}
        service_data = {str(k).lower(): bytes(v).hex() for k, v in sorted((advertisement.service_data or {}).items())}
        local_name = advertisement.local_name
        name = device.name or local_name or ""
        details = getattr(device, "details", None)
        address_type = getattr(device, "address_type", None)
        if address_type is None and isinstance(details, dict):
            address_type = details.get("AddressType") or details.get("address_type")
        output.append({
            "protocol": "BLE", "name": name or "Unknown BLE device",
            "address": device.address, "address_type": address_type,
            "rssi": advertisement.rssi, "service_uuids": service_uuids,
            "manufacturer_ids": sorted(advertisement.manufacturer_data.keys()),
            "manufacturer_data": manufacturer_data, "service_data": service_data,
            "tx_power": advertisement.tx_power, "local_name": local_name,
            "connectable": getattr(advertisement, "connectable", None),
            "observed_at": completed_wall, "scan_started_at": started_wall,
            "scan_completed_at": completed_wall, "scan_duration_seconds": duration,
            "raw_advertisement_data": None,
            "source": "unfiltered active BLE advertisement scan (Bleak parsed fields)",
        })
    return output
