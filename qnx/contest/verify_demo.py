#!/usr/bin/env python3
"""Check native QNX guest output from the deterministic contest fixture."""
import argparse
import json
from pathlib import Path


def verify(log: str) -> dict:
    events = []
    for line in log.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("engine") == "toretto-qnx-live":
            events.append(item)
    if len(events) != 5:
        raise ValueError(f"expected 5 native QNX results, got {len(events)}")
    for index, item in enumerate(events, 1):
        if item.get("windows") != index or item.get("total_observations") != index:
            raise ValueError(f"unexpected counter in result {index}: {item}")
    last = events[-1]
    for key, value in {"fingerprint_groups": 1, "shared_payload_groups": 1, "repeated_handoff_groups": 1}.items():
        if last.get(key) != value:
            raise ValueError(f"expected {key}={value}, got {last.get(key)}")
    return last


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    print("QNX_DEMO_PASS", json.dumps(verify(args.log.read_text(errors="replace")), sort_keys=True))


if __name__ == "__main__":
    main()
