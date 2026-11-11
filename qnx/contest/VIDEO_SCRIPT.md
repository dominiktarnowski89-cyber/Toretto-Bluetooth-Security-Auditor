# English demo video script (target: 2:30–2:50)

**0:00–0:25 — Problem**
Bluetooth Low Energy devices may rotate their addresses for privacy. Seeing the same advertisement under different addresses does not automatically mean an attack. We built TORETTO to correlate these observations and expose patterns without jumping to conclusions.

**0:25–0:55 — Architecture**
The radio scan runs on Linux, where the Bluetooth adapter is available. Observations can be sent securely to a native QNX 8 C++17 engine. The engine runs inside QNX itself, not in a Linux container.

**0:55–1:45 — Reproducible QNX demo**
For a reliable demonstration, we boot the official QNX QEMU image and replay five synthetic events. Watch the native QNX process report one fingerprint, two addresses and repeated address handoffs. The test script validates the actual guest output.

**1:45–2:20 — Optional live demo**
The same engine also accepts real observations collected on our Lenovo Bluetooth adapter, streamed into QNX through a virtual serial port. We previously verified this end-to-end path with live BLE data.

**2:20–2:45 — Responsible conclusion**
Our output is a correlation signal, not evidence of intrusion. Next steps include confirmed delivery, better retention and a QNX user interface. The project is open for reproducible evaluation with a licensed QNX SDK.

Show real terminal output, the QNX guest marker, the five JSON results, and the final QNX_DEMO_PASS line. Do not imply that a recorded replay is a live radio scan.
