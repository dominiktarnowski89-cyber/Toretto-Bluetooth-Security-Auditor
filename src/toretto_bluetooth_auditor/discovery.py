import asyncio
import re

from .collectors.ble_scan import scan_ble
from .collectors.linux_bt import scan_classic
from .decoder import enrich_device


def classify_device(device):
    """Classify identification confidence, not merely protocol visibility."""
    name = str(device.get("name") or "").strip()
    unknown_names = {"", "unknown", "unknown ble device", "unknown classic device"}
    looks_like_address = bool(re.fullmatch(r"[0-9a-fA-F]{2}([:-][0-9a-fA-F]{2}){5}", name))
    has_name = name.casefold() not in unknown_names and not looks_like_address
    has_services = bool(device.get("service_uuids"))
    has_class = bool(device.get("device_class"))

    # A manufacturer company ID alone identifies a vendor namespace, not the
    # device or its owner. Keep it in the unidentified category unless stronger
    # identifying evidence (name, service UUID, or BR/EDR class) is available.
    identified = has_name or has_services or has_class
    device["category"] = (
        device.get("protocol", "Bluetooth") if identified else "Niezidentyfikowane"
    )
    if identified:
        device["identification"] = "Dane identyfikacyjne dostępne; nie oznacza to potwierdzenia modelu ani właściciela"
        if has_class:
            device["identification_confidence"] = "high" if device.get("protocol") == "Bluetooth Classic" else "medium"
        elif has_name:
            device["identification_confidence"] = "medium"
        else:
            device["identification_confidence"] = "low"
    elif device.get("manufacturer_ids"):
        device["identification"] = (
            "Tylko identyfikator producenta; urządzenie pozostaje niezidentyfikowane"
        )
        device["identification_confidence"] = "none"
    else:
        device["identification"] = (
            "Brak nazwy, UUID, identyfikatora producenta i klasy urządzenia"
        )
        device["identification_confidence"] = "none"
    return enrich_device(device)


async def scan_all(timeout=8.0):
    """Run independent BLE and BR/EDR discovery passes, then classify results."""
    ble_devices = await scan_ble(timeout)
    classic_devices = await asyncio.to_thread(scan_classic, timeout)
    return [classify_device(item) for item in ble_devices + classic_devices]
