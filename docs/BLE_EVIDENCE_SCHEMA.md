# BLE evidence capture (schema v2)

TORETTO stores one identity observation per BLE device returned by each Bleak scan window.

## Fields retained per observation

- UTC observation time and scan-window start/end timestamps
- scan ID and measured scan duration
- address and address type, but only when the backend exposes the type
- RSSI, TX power and connectable flag
- complete parsed Bleak advertising fields: local name, service UUIDs, manufacturer data and service data
- canonical payload fingerprint and structural fingerprint
- a note describing whether raw HCI advertising bytes are available

Manufacturer and service data values are preserved as hexadecimal strings. This makes the bytes exposed by Bleak available for later byte-for-byte comparison rather than retaining only lengths and hashes.

## Important capture limitation

Bleak AdvertisementData exposes parsed advertising fields; it does not guarantee the complete raw HCI advertising PDU. Therefore raw_advertisement_available remains false for ordinary Bleak scans. TORETTO does not fabricate a raw packet from parsed fields.

For raw controller evidence, run the existing HCI collector on Lenovo:

    cd ~/projekty/toretto-bluetooth-security-auditor
    ./scripts/capture_anonymous_ble.sh --duration 30

This creates a BTSnoop capture and JSON sidecar. Inspect the BTSnoop with btmon --read <capture.btsnoop>. HCI advertising reports can provide address type, event type and raw advertising data as exposed by the controller. The capture remains a separate evidence artifact; it is not yet automatically decoded and joined to each Bleak observation.

## Temporal interpretation

multiple_addresses_within_scan_window means two or more addresses with the same fingerprint were returned during one scan window. It does not prove simultaneous radio transmission: a scan window spans time and the observations may have arrived sequentially.

repeated_address_handoff counts transitions between scan windows that each contained exactly one address for that fingerprint. Mixed-address windows are excluded from that handoff sequence.

A shared fingerprint is not a physical-device identity proof. Address rotation, multiple similar devices and deliberate payload copying remain possible explanations. Address type is reported only when actually supplied by the backend; an unknown type is left null.

## Data handling

The JSON report now uses schema version 2. The per-observation parsed advertising payload is retained in identity_observations; reports may therefore be larger. Nearby device identifiers and advertising payloads can be sensitive and should be stored and shared accordingly.
