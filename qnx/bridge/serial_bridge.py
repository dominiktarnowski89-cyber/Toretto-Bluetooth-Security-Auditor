#!/usr/bin/env python3
"""Forward Lenovo BLE NDJSON from stdin into QEMU guest COM2, reconnecting per event."""
import json
import socket
import sys
import time
from pathlib import Path

SOCKET = '/tmp/toretto-qnx-serial.sock'
SPOOL = Path('/home/dominik/projekty/qnx8-development/vm/logs/serial-pending.ndjson')

def deliver(line):
    for attempt in range(8):
        try:
            with socket.socket(socket.AF_UNIX) as conn:
                conn.settimeout(4)
                conn.connect(SOCKET)
                payload = line.encode('utf-8') + b'\n'
                for offset in range(0, len(payload), 64):
                    conn.sendall(payload[offset:offset+64])
                    time.sleep(0.012)
            return True
        except OSError:
            time.sleep(min(2 ** attempt, 8))
    return False

for line in sys.stdin:
    try:
        event = json.loads(line)
        if event.get('event') != 'ble_window':
            continue
        delivered = 0
        failed = False
        for obs in event.get('identity_observations', []):
            compact = {'event': 'ble_window', 'identity_observations': [
                {'fingerprint': obs.get('fingerprint'), 'address': obs.get('address'), 'scan_id': obs.get('scan_id')} ]}
            if not deliver(json.dumps(compact, separators=(',', ':'))):
                failed = True
                break
            delivered += 1
            time.sleep(0.07)
        if failed:
            SPOOL.parent.mkdir(parents=True, exist_ok=True)
            with SPOOL.open('a') as out:
                out.write(line)
            print('QNX_UNAVAILABLE buffered scan='+str(event.get('scan_id')),file=sys.stderr,flush=True)
        else:
            print('QNX_DELIVERED scan='+str(event.get('scan_id'))+' observations='+str(delivered),file=sys.stderr,flush=True)
    except (ValueError,TypeError) as exc:
        print('INVALID_EVENT '+str(exc),file=sys.stderr,flush=True)
