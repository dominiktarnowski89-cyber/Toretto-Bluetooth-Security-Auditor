import importlib.util
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / "qnx/contest/verify_demo.py"
spec = importlib.util.spec_from_file_location("verify_demo", MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def make_log(addresses):
    import json
    return "\n".join(json.dumps({
        "engine": "toretto-qnx-live", "windows": i,
        "total_observations": i, "fingerprint_groups": 1,
        "shared_payload_groups": int(i >= 2),
        "repeated_handoff_groups": int(i >= 4),
    }) for i, _ in enumerate(addresses, 1))


def test_valid_demo():
    assert module.verify(make_log(range(5)))["windows"] == 5


def test_missing_window_rejected():
    with pytest.raises(ValueError, match="expected 5"):
        module.verify(make_log(range(4)))


def test_missing_handoff_rejected():
    import json
    rows = [json.loads(line) for line in make_log(range(5)).splitlines()]
    rows[-1]['repeated_handoff_groups'] = 0
    with pytest.raises(ValueError, match='repeated_handoff'):
        module.verify('\n'.join(json.dumps(row) for row in rows))
