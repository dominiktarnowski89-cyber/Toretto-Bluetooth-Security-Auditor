# Lenovo environment audit

- Host: s1l3ntsamura11-Lenovo-G500
- OS: Ubuntu 26.04.1 LTS
- Kernel: 7.0.0-42-generic
- Python: 3.14.4
- Git: 2.53.0
- Available: bluetoothctl, bluetoothd, adb, Python, Git
- GitHub CLI: authenticated as dominiktarnowski89-cyber
- Target path: did not exist before this project was created
- Project path: /home/s1l3ntsamura11/projekty/toretto-bluetooth-security-auditor

## Hardware observations from this session

- Bluetooth controller detected by BlueZ.
- Controller power: ON.
- Discoverable: NO.
- Pairable: NO.
- rfkill: Bluetooth not soft- or hard-blocked.
- Passive BLE scan: PASS; 7 advertisements observed in a 6-second scan.
- ADB: no Android device connected; Oukitel audit NOT VERIFIED.
- GUI: PySide6 import and offscreen window initialization PASS.
- Unit tests: 5/5 PASS.
- Ruff: PASS.
- compileall: PASS.

These observations describe the Lenovo host only. They do not establish the security state of the Oukitel phone or any nearby BLE device.
