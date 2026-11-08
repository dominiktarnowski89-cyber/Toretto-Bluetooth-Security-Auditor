# Roadmap

1. Lenovo audit: PASS — Ubuntu 26.04.1, Python 3.14.4, Git 2.53, BlueZ and ADB present; target path absent before setup; GitHub CLI authenticated. Evidence: ENVIRONMENT_AUDIT.md.
2. Repository/GUI: PASS — private GitHub repository cloned to Lenovo; PySide6 GUI initializes successfully in offscreen smoke test. Interactive desktop review remains pending.
3. Bluetooth adapter diagnostics: PASS — BlueZ controller detected; powered ON, discoverable NO, pairable NO; rfkill unblocked. These are Lenovo host results.
4. Bluetooth discovery implementation: PASS — separate unfiltered active BLE scan and BR/EDR inquiry; no Flags/manufacturer/name/UUID allowlist; Classic results verified against BlueZ BR/EDR Class property; unidentified category added. No pairing or automatic connections.
5. Live discovery smoke test: PASS — latest 5-second BLE + Classic scan returned 20 records: 18 BLE and 2 Classic; 16 were classified as unidentified, 2 BLE and 2 Classic as identified. Counts are environment-specific, not a guarantee of all nearby devices.
6. Android ADB preflight: PASS — preflight script and three-scenario acceptance procedure created. ADB device list was empty at execution time; no phone evidence collected.
7. Oukitel Tank 2 scenarios A/B/C: NOT VERIFIED — requires physical USB connection and owner RSA approval. See docs/ANDROID_ACCEPTANCE.md.
8. Headphone link encryption: NOT VERIFIED — pairing/connection is not proof of encryption; authoritative OS evidence is still required.
9. Vulnerability intelligence: pending exact model/build advisory matching after ADB identifies the precise build fingerprint.
10. Reports: JSON/HTML export implemented; integrity hash and default MAC redaction pending review.
11. Verification: 11 unit tests, Ruff, compileall, pip check and git diff --check PASS. Hardware acceptance on Oukitel pending.
12. Packaging: Ubuntu installer written; .deb/desktop launcher and final acceptance pending.

Implemented does not mean hardware-verified. No PASS is assigned to the phone without evidence.


## Decoder implementation (2026-11-05)

- PASS — BLE scan retains manufacturer-specific bytes, service-data bytes, TX power, service UUIDs and connectability as evidence; scan remains unfiltered and does not pair/connect.
- PASS — conservative decoder maps known company identifiers (Microsoft, Apple, Samsung), selected Apple Continuity message types, standard Heart Rate/Device Information/Battery UUIDs and selected Bluetooth Mesh model identifiers. Unknown payloads remain raw and are not guessed.
- PASS — Microsoft printable ASCII runs are exposed as evidence only; they do not establish exact device model or ownership.
- PASS — Bluetooth Classic Class of Device `0x0424` maps to Audio/Video set-top box; unknown classes remain unmapped.
- PASS — GUI adds decoded observations and identification-confidence column; HTML report now includes nearby devices and decoded observations. JSON retains raw payload evidence.
- PASS — confidence is separated from identity: vendor company ID alone does not identify a device. Apple signatures are descriptive clues, not proof of a particular product.
- NOT VERIFIED — exact Apple product models, full Microsoft CDP schema, ownership of nearby devices, and any vulnerability status. No active GATT probing or connections were added.

## Identity & Spoofing Detection (2026-11-05)

- IMPLEMENTED — new desktop GUI tab performs repeated unfiltered BLE discovery windows, fingerprints available advertising fields independently of address/RSSI, groups matching fingerprints across addresses, and counts repeated exclusive address handoffs.
- IMPLEMENTED — report JSON retains the observation history; HTML reports include the observation count and an explicit identity-evidence limitation.
- PASS — identity unit tests cover address/RSSI-independent fingerprinting, empty payload handling, shared fingerprints across addresses, and repeated handoffs.
- IMPLEMENTED — native Android companion under `android/`, package `com.toretto.bluetoothauditor`, min SDK 26 / target SDK 36. It hashes raw advertising records provided by Android, displays address changes, and exports JSON.
- PASS — Android Java compilation, D8 dex conversion, APK alignment, v2/v3 signing verification, and package/SDK metadata inspection.
- NOT VERIFIED — live BLE behavior on Oukitel Tank 2; no Android device was attached to ADB during build verification.
- PLATFORM LIMITATION — Android ordinary apps cannot access raw controller HCI/BTSnoop events. Use Lenovo/Linux for HCI evidence. Android scan filtering/throttling may hide some advertisements.
- CAUTION — identical fingerprints under multiple addresses may be BLE privacy rotation or multiple transmitters. The scanner does not claim physical-device identity or prove malicious spoofing.
