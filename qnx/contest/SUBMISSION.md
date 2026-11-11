# Submission draft — TORETTO Bluetooth Security Auditor for QNX 8

## Title
TORETTO Bluetooth Security Auditor — Native QNX 8 BLE Identity Correlation

## Short description
A native QNX 8 C++17 engine that analyzes Bluetooth Low Energy advertisement fingerprints across scan windows to highlight repeated address changes and shared advertising payloads, with reproducible offline and optional real-world live demonstrations.

## The problem
Bluetooth LE devices frequently use randomized addresses. A single advertising payload observed under different addresses may indicate normal privacy rotation or multiple transmitters with identical payloads. These cases are easy to misinterpret, and raw scan data is difficult to review systematically.

## Our solution
TORETTO collects read-only BLE observations on Linux and streams compact JSON events over SSH to a native QNX 8 process via a QEMU virtual serial interface. The QNX engine groups observations by advertising fingerprint and tracks addresses and scan-window transitions. A deterministic offline fixture makes the core behavior independently demonstrable without a Bluetooth adapter.

## QNX implementation
- Native C++17 executable, built against QNX SDP 8 and its JSON decoding library.
- Tested inside QNX 8 x86-64 under QEMU, not inside Linux.
- ARM64 QNX target cross-compiles but has not been runtime tested.
- Event-by-event processing, bounded fingerprint groups and per-group scan/address retention.

## Reproduction
See qnx/contest/README.md. With a licensed QNX 8 SDK and prepared official QEMU image, qnx/contest/demo-run.sh launches QNX, replays five events, validates the native output and exits. The repository does not redistribute QNX proprietary binaries.

## Security and responsible interpretation
The scanner does not pair with, connect to or attack devices. A shared BLE advertising fingerprint is an investigative signal, not proof of spoofing, interception, compromise, or a single physical device. The tool does not verify Bluetooth link encryption.

## Verified evidence
- Native QNX 8 x86-64 test: 5 replay events; shared-payload group and repeated handoff group both detected; QNX_DEMO_PASS.
- Earlier live Lenovo-to-QNX pipeline: 19 observations processed during an end-to-end run.
- Python test suite: 31 passed at time of drafting.

## Known limitations
- Guest acknowledgements and durable replay after interruption are not implemented.
- QNX guest does not directly control the Bluetooth adapter.
- No integrated QNX graphical interface.
- SDK, official QNX image and licensed dependencies are not included.

## Submission assets to finish
- [ ] Select and add an OSI-approved license with repository owner's consent.
- [ ] Confirm repository visibility is public and submission branch is accessible.
- [ ] Confirm contest category, eligibility, deadlines, and exact required fields against current official rules.
- [ ] Record and publish an English-language demo video meeting contest duration and accessibility requirements.
- [ ] Capture a screenshot of the native QNX guest's successful result.
- [ ] Test setup from a clean machine with a valid QNX SDP license.
- [ ] Submit through the contest portal and retain confirmation.
