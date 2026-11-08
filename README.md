# TORETTO Bluetooth Security Auditor

Read-only Ubuntu desktop auditor for Bluetooth Classic (BR/EDR), Bluetooth Low Energy (BLE), unidentified nearby Bluetooth devices, and owner-authorized Android via ADB. Initial target: Oukitel Tank 2 / Android 14 on Lenovo G500 / Ubuntu 26.04.

Discovery uses two independent passes:
- Bluetooth Classic: BlueZ BR/EDR inquiry; devices are retained as Classic only when BlueZ exposes a BR/EDR Class property.
- BLE: unfiltered active advertisement scan; no Flags, manufacturer, name, or UUID allowlist is applied. Active scanning can request scan-response data, but it does not pair with or connect to devices.
- Unidentified: devices seen by either pass without a usable name, service UUID, or BR/EDR class. A manufacturer company ID alone is treated as partial vendor metadata, not a unique device identity.

The application does not pair with, trust, connect to, or exchange application data with discovered devices. Android queries require USB debugging and explicit RSA approval. Missing evidence is NOT VERIFIED, never PASS. Bluetooth enabled alone is not proof of a vulnerability. Reports stay local.

Install: `bash scripts/install_ubuntu.sh`; run `.venv/bin/toretto-bt-auditor`.

Test separately: Bluetooth off; Bluetooth on without headphones; Bluetooth on with headphones. Host-side scanning cannot reliably confirm encryption of the Android-to-headphone link; it remains NOT VERIFIED unless authoritative OS evidence is available.

Discovery cannot guarantee visibility of devices that are powered off, out of range, not advertising, or not discoverable through Classic inquiry. Randomized BLE addresses may change between scans.

## Identity & Spoofing Detection

The desktop GUI includes a continuous BLE observation tab that groups identical advertising-data fingerprints across addresses and checks for repeated address handoffs across scan windows. Matching data can result from BLE privacy address rotation or multiple transmitters; it is an investigative signal, not proof of cloning or compromise.

## Android companion

A native Android BLE companion is in `android/`. Build with `bash android/build.sh`. It observes Android-provided raw BLE advertising records, fingerprints them with SHA-256, and exports JSON. Android does not expose raw controller HCI/BTSnoop capture to ordinary apps; use the Lenovo Linux build for full HCI traces. The Android build targets API 36 and requires Android 8.0 or later.

## Launching the desktop application and CLI

- Ubuntu application menu: search for **TORETTO Bluetooth Security Auditor**. The user launcher is `~/.local/share/applications/toretto-bluetooth-auditor.desktop`.
- Desktop terminal (inside the logged-in graphical session): `./.venv/bin/toretto-bt-auditor`.
- Terminal CLI: `./.venv/bin/toretto-bt-auditor-cli --help`.
- Adapter status: `./.venv/bin/toretto-bt-auditor-cli status`.
- BLE scan: `./.venv/bin/toretto-bt-auditor-cli scan --mode ble --timeout 15 --identity`.
- BLE + Classic scan with local JSON and HTML reports: `./.venv/bin/toretto-bt-auditor-cli scan --mode all --timeout 12 --json reports/scan.json --html reports/scan.html`.

The GUI needs an active graphical desktop session (Wayland/X11). A plain SSH/TTY shell normally has no `DISPLAY` or `WAYLAND_DISPLAY`, so launching the GUI from that shell fails even when Qt libraries are installed. Use the Ubuntu application menu or a terminal opened inside the graphical desktop. The CLI does not require a graphical session.
