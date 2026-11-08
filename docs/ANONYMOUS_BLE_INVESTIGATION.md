# Anonymous BLE investigation

## Evidence so far

The preserved discovery report contains two anonymous BLE entries:
- `47:23:AD:65:0B:DA` (suffix `0B:DA`), RSSI -93 dBm
- `52:0D:A1:C7:4D:F5` (suffix `4D:F5`), RSSI -94 dBm

Both have random address type, no local name, no service UUIDs, no manufacturer data, no service data, and BlueZ exposes Advertising Flags `0x04`. In BLE Flags, bit 2 means BR/EDR Not Supported. This is a transport capability flag, not a vendor or device identifier.

## HCI capture

Run from a terminal on Lenovo:

```bash
cd ~/projekty/toretto-bluetooth-security-auditor
./scripts/capture_anonymous_ble.sh --duration 25
```

The collector starts `btmon --write` and performs an unfiltered Bleak active scan concurrently. `sudo` may prompt for the local password. It creates a BTSnoop trace and a JSON sidecar under `reports/`, refuses to overwrite an existing trace, and records SHA-256. It does not pair, connect, or issue GATT requests.

Inspect the resulting trace with:

```bash
btmon --read reports/ble-hci-YYYYMMDD-HHMMSS.btsnoop
```

The HCI trace can expose raw advertising reports, address type, event type, advertising data length/content, and scan-response observations available to the host/controller. It cannot reveal an identity that the device does not transmit. Treat captures as sensitive because nearby device identifiers may be present.
