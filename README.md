# TORETTO Bluetooth Security Auditor

Read-only Ubuntu desktop auditor for local Bluetooth and owner-authorized Android via ADB. Initial target: Oukitel Tank 2 / Android 14 on Lenovo G500 / Ubuntu 26.04.

Passive BLE advertisements only; no pairing, active connections to discovered devices, exploits, packet injection or phone setting changes. Android queries require USB debugging and explicit RSA approval. Missing evidence is NOT VERIFIED, never PASS. Bluetooth enabled alone is not proof of a vulnerability. Reports stay local.

Install: `bash scripts/install_ubuntu.sh`; run `.venv/bin/toretto-bt-auditor`.

Test separately: Bluetooth off; Bluetooth on without headphones; Bluetooth on with headphones. Host-side scanning cannot reliably confirm encryption of the Android-to-headphone link; it remains NOT VERIFIED unless authoritative OS evidence is available.
