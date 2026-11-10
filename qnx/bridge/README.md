# Live BLE stream — first integration stage

The Lenovo host scans its **physical BLE adapter** in successive windows, generating one JSON event per window on stdout. Netcup receives the stream over SSH and incrementally updates the fingerprint/address counts. No pairing, GATT access, or radio transmission is required by this collector.

From Netcup (where `ssh lenovo` resolves to the authorized Lenovo host):

```sh
ssh lenovo 'cd ~/projekty/toretto-bluetooth-security-auditor && .venv/bin/python scripts/live_ble_stream.py --window 5 --max-windows 0' | python3 qnx/bridge/live_receiver.py
```

Run the receiver from the repository directory on Netcup, or supply its absolute path. The receiver currently writes `/tmp/toretto-live-ble.ndjson` and keeps fingerprint/address counts in memory for the duration of the connection. SSH provides transport encryption. The live receiver **runs on Netcup Linux, not in the QNX guest**. Native QNX persistent streaming, reconnect buffering, and GUI are not yet implemented. This is a bounded-memory *per window* scanner but the cumulative scan history currently grows unbounded; limit deployment duration until retention is implemented.

Validated with three 3-second windows: 5, 6, and 10 observations; 21 cumulative, 11 fingerprints; SSH and receiver exited with code 0.
