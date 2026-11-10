#!/usr/bin/env python3
"""Read live BLE NDJSON over SSH stdin; append evidence and publish cumulative stats."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

out = Path('/tmp/toretto-live-ble.ndjson')
out.parent.mkdir(parents=True, exist_ok=True)
seen = {}
with out.open('a', encoding='utf-8') as log:
    for line in sys.stdin:
        try:
            event = json.loads(line)
            if event.get('event') != 'ble_window':
                print('SCAN_ERROR', event, flush=True)
                continue
            for obs in event.get('identity_observations', []):
                fp = obs.get('fingerprint')
                if fp:
                    seen.setdefault(fp, set()).add(obs.get('address', 'unknown'))
            log.write(json.dumps(event, separators=(',', ':')) + '\n')
            log.flush()
            shared = sum(len(addresses) > 1 for addresses in seen.values())
            print(f"RECEIVED scan={event['scan_id']} observations={len(event['identity_observations'])} fingerprints={len(seen)} multi_address_fingerprints={shared}", flush=True)
        except (ValueError, KeyError, TypeError) as exc:
            print(f'INVALID_EVENT {exc}', file=sys.stderr, flush=True)
