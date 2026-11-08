"""Conservative Bluetooth advertisement decoder; vendor bytes are untrusted evidence."""
COMPANIES = {0x0006: "Microsoft", 0x004C: "Apple", 0x0075: "Samsung"}
STANDARD_SERVICES = {"180D": "Heart Rate", "180F": "Battery Service", "180A": "Device Information", "1800": "Generic Access", "1801": "Generic Attribute"}
MESH_MODELS = {"1011": "Bluetooth Mesh: Generic Admin Property Server", "1012": "Bluetooth Mesh: Generic Manufacturer Property Server", "1014": "Bluetooth Mesh: Generic Client Property Server"}
APPLE_TYPES = {0x02: ("Apple manufacturer payload: iBeacon-type marker", "medium"), 0x07: ("Apple Continuity: AirPods proximity-pairing message", "medium"), 0x10: ("Apple Continuity: Nearby Info message", "medium")}

def _hex(value):
    if isinstance(value, (bytes, bytearray)): return bytes(value).hex()
    if isinstance(value, str): return value.lower().replace(" ", "").replace(":", "")
    return ""

def decode_manufacturer_data(data):
    decoded = []
    if not isinstance(data, dict): return decoded
    for raw_id, raw_payload in data.items():
        try: company_id = int(raw_id, 0) if isinstance(raw_id, str) else int(raw_id)
        except (TypeError, ValueError): company_id = None
        payload = _hex(raw_payload)
        item = {"company_id": company_id, "company": COMPANIES.get(company_id, "Unknown company namespace"), "payload_hex": payload, "description": "Manufacturer-specific payload; format not decoded", "confidence": "low"}
        try: raw = bytes.fromhex(payload)
        except ValueError: raw = b""
        if company_id == 0x004C and raw:
            kind = APPLE_TYPES.get(raw[0])
            if kind:
                description, confidence = kind
                valid = len(raw) >= 2 and raw[1] == len(raw) - 2
                item.update(description=description + ("" if valid else " (length variant or truncated payload)"), confidence=confidence if valid else "low", message_type=f"0x{raw[0]:02X}", length_valid=valid)
        elif company_id == 0x0006 and raw:
            import re
            strings = [x.decode("ascii", errors="ignore") for x in re.findall(rb"[ -~]{6,}", raw)]
            item["printable_text"] = strings
            item["description"] = "Microsoft manufacturer advertisement; Windows ecosystem is possible, but payload schema and device type are not established" + ("; printable payload text: " + ", ".join(strings) if strings else "")
        elif company_id == 0x0075 and raw:
            item["description"] = "Samsung manufacturer advertisement; vendor namespace does not identify model"
        decoded.append(item)
    return decoded

def decode_service_uuids(values):
    output = []
    for value in values or []:
        text = str(value).upper().replace("-", "")
        first_group = text[:8]
        short = first_group[-4:] if len(first_group) >= 4 else first_group
        output.append({"uuid": str(value), "description": MESH_MODELS.get(short, STANDARD_SERVICES.get(short, "UUID not mapped")), "kind": "Bluetooth Mesh model" if short in MESH_MODELS else "GATT/service UUID"})
    return output

def decode_classic_device_class(value):
    try: cod = int(str(value), 0)
    except (TypeError, ValueError): return {"raw": value, "description": "Class of Device unavailable", "confidence": "none"}
    if cod & 0x0FFC == 0x0424:
        return {"raw": f"0x{cod:06X}", "description": "Audio/Video: Set-top box", "confidence": "high"}
    return {"raw": f"0x{cod:06X}", "description": "Bluetooth Class of Device (minor class not mapped)", "confidence": "low"}

def enrich_device(device):
    result = dict(device)
    result["manufacturer_details"] = decode_manufacturer_data(result.get("manufacturer_data", {}))
    result["service_details"] = decode_service_uuids(result.get("service_uuids", []))
    if result.get("device_class"): result["class_details"] = decode_classic_device_class(result["device_class"])
    descriptions = [x["description"] for x in result["manufacturer_details"]]
    descriptions.extend(x["description"] for x in result["service_details"] if x["description"] != "UUID not mapped")
    if result.get("class_details"): descriptions.append(result["class_details"]["description"])
    result["decoded_observations"] = descriptions
    return result
