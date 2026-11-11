# QNX Global Hackathon — release gate

## Engineering evidence

- [x] QNX 8 x86-64 native analyzer runs in QEMU and emits JSON summaries
- [x] Deterministic offline replay is independent of Bluetooth hardware and private Netcup connectivity
- [x] Demo verifies five actual guest results and expected correlation metrics
- [x] Linux-to-QNX real BLE observations demonstrated in a previous integration run
- [x] Source repository has an MIT license
- [ ] Rebuild the latest native source using the licensed QNX SDP 8, regenerate the IFS and rerun demo
- [ ] Run malformed/oversized input and retention-boundary tests against the actual QNX binary
- [ ] Repeat setup on a clean licensed QNX 8 installation using repository instructions only
- [ ] Review the public Git history and repository for credentials and private data

## Submission evidence

- [ ] Reconfirm exact current rules, category, and eligibility against official contest page
- [ ] Public video demonstrating native QNX output (under required duration)
- [ ] English Devpost text, screenshots, code link, category, license and required fields
- [ ] Submit and verify Devpost confirmation before deadline

## Explicitly out of scope for contest MVP

- Android APK polish, QNX GUI, always-on Netcup service, guest ACKs and durable spool replay

## Honest product boundaries

Read-only BLE identity correlation is not intrusion proof, device attribution or Bluetooth encryption verification. The offline fixture is synthetic and must be labeled as such. No QNX proprietary files are redistributed.
