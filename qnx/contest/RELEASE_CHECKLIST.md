# QNX Global Hackathon — release gate

## Engineering evidence

- [x] QNX 8 x86-64 native analyzer runs in QEMU and emits JSON summaries
- [x] Deterministic offline replay is independent of Bluetooth hardware and private Netcup connectivity
- [x] Demo verifies five actual guest results and expected correlation metrics
- [x] Linux-to-QNX real BLE observations demonstrated in a previous integration run
- [x] Source repository has an MIT license
- [x] Rebuilt latest native source with licensed QNX SDP 8 (x86-64 and ARM64), regenerated IFS and reran QNX demo: PASS (2026-11-11)
- [x] Tested malformed JSON and 70 unique addresses / scan IDs in actual QNX guest: 71 accepted windows including empty event, 70 observations; no crash (2026-11-11)
- [ ] Complete oversized-input test: 4 MiB serial test did not finish within test window (38/71 windows). Need transport-throughput-aware timeout and separate parser stress test; do not claim a parser vulnerability
- [x] Isolated source/output build with existing licensed QNX SDP 8 produced byte-identical x86-64 and ARM64 binaries (2026-11-11)
- [ ] Repeat setup on a genuinely clean licensed QNX 8 installation using repository instructions only
- [x] Scanned 23 reachable Git commits for common token/private-key patterns and suspicious tracked filenames (no matches; not a comprehensive secret scan)
- [ ] Complete deeper secret scanning with dedicated tooling and manual review

## Submission evidence

- [ ] Reconfirm exact current rules, category, and eligibility against official contest page
- [x] Generated 98-second English draft video from verified QNX log data (local Lenovo video-assets; silent slide presentation, not screen recording)
- [ ] Record authentic terminal/QNX screen footage and voice-over, review, publish public video and confirm required duration
- [ ] English Devpost text, screenshots, code link, category, license and required fields
- [ ] Submit and verify Devpost confirmation before deadline

## Explicitly out of scope for contest MVP

- Android APK polish, QNX GUI, always-on Netcup service, guest ACKs and durable spool replay

## Honest product boundaries

Read-only BLE identity correlation is not intrusion proof, device attribution or Bluetooth encryption verification. The offline fixture is synthetic and must be labeled as such. No QNX proprietary files are redistributed.
