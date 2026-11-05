async def scan_ble(timeout=8.0):
    try:
        from bleak import BleakScanner
    except ImportError as e:
        raise RuntimeError("Bleak missing; run installer") from e
    found = await BleakScanner.discover(timeout=timeout, return_adv=True)
    out = []
    for _, pair in found.items():
        dev, adv = pair
        out.append(
            {
                "name": dev.name or adv.local_name or "Unknown BLE device",
                "address": dev.address,
                "rssi": adv.rssi,
                "service_uuids": list(adv.service_uuids or []),
                "manufacturer_ids": sorted(adv.manufacturer_data.keys()),
                "connectable": getattr(adv, "connectable", None),
                "source": "passive BLE advertisement",
            }
        )
    return sorted(out, key=lambda x: str(x["name"]).casefold())
