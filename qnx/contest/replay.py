#!/usr/bin/env python3
"""Send reproducible competition fixture to the running QNX COM2 guest."""
import argparse
import json
import socket
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--socket", default="/tmp/toretto-qnx-serial.sock")
parser.add_argument("--fixture", type=Path, default=Path(__file__).parent / "fixtures/rotation.ndjson")
parser.add_argument("--interval", type=float, default=0.35)
args = parser.parse_args()
if args.interval < 0:
    parser.error("interval must be nonnegative")
with args.fixture.open(encoding="utf-8") as source:
    for i, line in enumerate(source, 1):
        event = json.loads(line)
        if event.get("event") != "ble_window":
            raise ValueError(f"line {i}: unexpected event")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(5)
            conn.connect(args.socket)
            payload = (json.dumps(event, separators=(",", ":")) + "\n").encode()
            for pos in range(0, len(payload), 64):
                conn.sendall(payload[pos:pos+64])
                time.sleep(0.012)
        print(f"sent fixture event {i}", flush=True)
        time.sleep(args.interval)
