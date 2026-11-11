# QNX Global Hackathon — release gate

## Engineering evidence

- [x] QNX 8 x86-64 native analyzer runs in QEMU and emits JSON summaries
- [x] Deterministic offline replay is independent of Bluetooth hardware and private Netcup connectivity
- [x] Demo verifies five actual guest results and expected correlation metrics
- [x] Linux-to-QNX real BLE observations demonstrated in a previous integration run
- [x] Source repository has an MIT license
- [x] Rebuilt latest native source with licensed QNX SDP 8 (x86-64 and ARM64), regenerated IFS and reran QNX demo: PASS (2026-11-11)
- [x] Tested malformed JSON and 70 unique addresses / scan IDs in actual QNX guest: 71 accepted windows including empty event, 70 observations; no crash (2026-11-11)
- [x] Hardened native line reader to cap buffered records at 4 MiB, discard oversized input until newline, and continue; QNX x86-64/ARM64 builds passed, rebuilt guest image passed 5-event demo on Netcup (2026-11-11)
- [ ] Complete end-to-end oversized-input stress test with verified byte delivery and flow control. On 2026-11-11, a 4 MiB+18-byte record was written to the host QEMU serial socket in 29.34s, but guest rejection/recovery was not observed; test stopped without PASS. A diagnostic 1 KiB-threshold guest with a 2 KiB input emitted `invalid event` rather than `oversized line` while accepting the following valid event, indicating transport truncation/byte loss is plausible. Host socket send completion is NOT proof of guest byte delivery. Next: instrument guest byte counts or use reliable file/pipe injection before claiming oversized-input PASS.
- [x] Isolated source/output build with existing licensed QNX SDP 8 produced byte-identical x86-64 and ARM64 binaries (2026-11-11)
- [ ] Repeat setup on a genuinely clean licensed QNX 8 installation using repository instructions only
- [x] Reviewed all 24 reachable Git commits, 73 historical paths and 104 unique blobs with additional common credential/token/key/private-host patterns: no matches (2026-11-11)
- [ ] Independent secret scanner and manual review for unusual secrets and personal data before submission

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
