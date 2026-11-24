#!/usr/bin/env python3
"""Forward NDJSON over a single TCP session; require a native QNX result per record."""
import argparse
import json
import socket
import sys

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=18765)
    p.add_argument("--timeout", type=float, default=90)
    args = p.parse_args()
    with socket.create_connection(("127.0.0.1", args.port), timeout=args.timeout) as conn:
        with conn.makefile("rb") as replies:
            for seq, line in enumerate(sys.stdin.buffer, 1):
                payload = line.rstrip(b"\r\n")
                event = json.loads(payload)
                if event.get("event") != "ble_window" or len(payload) > 4*1024*1024:
                    raise ValueError("invalid or oversized BLE window")
                conn.sendall(payload + b"\n")
                reply = json.loads(replies.readline(65536))
                if reply.get("engine") != "toretto-qnx-live" or reply.get("windows") != seq:
                    raise RuntimeError("missing or unexpected QNX processing confirmation")
                print(json.dumps(reply), flush=True)

if __name__ == "__main__":
    main()
