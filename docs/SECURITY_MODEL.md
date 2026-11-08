# Security model

In scope: local Linux adapter diagnostics, unfiltered active BLE advertisement discovery, Bluetooth Classic BR/EDR inquiry, read-only inspection of an explicitly authorized Android device via ADB, and local reports.

BLE active scanning may request scan-response data from advertisers. It does not pair with, connect to, or exchange application data with discovered devices. Classic inquiry discovers devices that respond to BR/EDR inquiry; a cached device is not counted as Classic unless BlueZ exposes its BR/EDR Class property.

Out of scope: exploit execution, brute force, MITM, packet injection, pairing attacks, third-party device access, or reading personal phone data.

Missing evidence is NOT VERIFIED. Bluetooth powered on is not itself a vulnerability. Nearby names/MAC addresses are potentially identifying. Reports are never uploaded automatically.

No scanner can guarantee detection of every Bluetooth-capable device: powered-off, out-of-range, non-advertising BLE, and non-discoverable Classic devices may not appear. BLE private/random addresses may rotate.

## Identity correlation limits

The identity analyzer fingerprints only fields exposed by the scanner. A matching fingerprint under multiple BLE addresses is a correlation, not proof of a cloned transmitter: a single device may rotate a private address, and multiple devices may emit the same public payload. RSSI is not a reliable distance estimate. Repeated address handoffs are an anomaly requiring controlled multi-receiver follow-up, not a compromise verdict.

The Android companion requests BLE scan/connect permissions for scanning metadata, but does not initiate Bluetooth pairing, Classic connections, GATT connections, or network communication. Android does not expose raw controller HCI traces to ordinary apps; raw BTSnoop capture remains Linux-only.
