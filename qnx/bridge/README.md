# Live BLE stream — first integration stage

The Lenovo host scans its **physical BLE adapter** in successive windows, generating one JSON event per window on stdout. Netcup receives the stream over SSH and incrementally updates the fingerprint/address counts. No pairing, GATT access, or radio transmission is required by this collector.

From Netcup (where `ssh lenovo` resolves to the authorized Lenovo host):

```sh
ssh lenovo 'cd ~/projekty/toretto-bluetooth-security-auditor && .venv/bin/python scripts/live_ble_stream.py --window 5 --max-windows 0' | python3 qnx/bridge/live_receiver.py
```

Run the receiver from the repository directory on Netcup, or supply its absolute path. The receiver currently writes `/tmp/toretto-live-ble.ndjson` and keeps fingerprint/address counts in memory for the duration of the connection. SSH provides transport encryption. The live receiver **runs on Netcup Linux, not in the QNX guest**. Native QNX persistent streaming, reconnect buffering, and GUI are not yet implemented. This is a bounded-memory *per window* scanner but the cumulative scan history currently grows unbounded; limit deployment duration until retention is implemented.

Validated with three 3-second windows: 5, 6, and 10 observations; 21 cumulative, 11 fingerprints; SSH and receiver exited with code 0.

## Confirmed Lenovo → QNX guest live pipeline (QEMU COM2)

On Netcup, build an IFS from the official QNX `mkqnximage` image, adding the `toretto-qnx-live-x86_64` executable. In the QNX startup script, after `devc-ser8250` is started and the system is ready, launch:

```sh
waitfor /dev/ser2
stty -F /dev/ser2 115200 -echo -icanon 2>/dev/null
/proc/boot/toretto-qnx-live < /dev/ser2 &
```

Launch QEMU with two serial ports (the first for the console, the second for the live stream):

```sh
qemu-system-x86_64 -machine pc -accel tcg,thread=multi -cpu max -smp 2 -m 2048 -display none -serial stdio -serial unix:/tmp/toretto-qnx-serial.sock,server=on,wait=off -monitor none -no-reboot -nic none -kernel output/ifs-serial-stream.bin -drive file=output/test-disk/disk-qemu.vmdk,if=ide,format=vmdk
```

From Netcup, while QNX is running:

```sh
ssh lenovo 'cd ~/projekty/toretto-bluetooth-security-auditor && .venv/bin/python scripts/live_ble_stream.py --window 3 --max-windows 2' | python3 qnx/bridge/serial_bridge.py
```

The bridge compacts each real BLE observation into an individual NDJSON event and rate-limits serial writes. **Verified in the running QNX 8 x86-64 guest:** two live Lenovo scan windows produced 19 observations; QNX emitted 19 cumulative summaries, with 12 fingerprint groups, without reboot. SSH encrypts Lenovo→Netcup; the QEMU Unix socket is local to Netcup.

**Limitations:** This is a tested prototype, not a production service. QEMU was launched with a bounded timeout; the test is no longer a continuously running monitor. The bridge retries socket connections and spools failed events, but does not yet automatically replay the spool. It lacks acknowledgement from QNX and therefore a successful socket write alone cannot guarantee guest processing. Guest per-group scan history is not bounded, and no GUI has been integrated. Serial chunking may become a bottleneck at high advertisement rates.
