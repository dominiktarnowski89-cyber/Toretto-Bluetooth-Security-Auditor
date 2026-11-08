import re
import shutil

from .linux_bt import run

_STATE_PATTERNS = (
    re.compile(r"\bstate\s*:\s*(ON|OFF|BLE_ON|TURNING_ON|TURNING_OFF)\b", re.I),
    re.compile(r"\bmState\s*=\s*(ON|OFF|BLE_ON|TURNING_ON|TURNING_OFF)\b", re.I),
    re.compile(r"\bBluetooth is (ON|OFF)\b", re.I),
)


def parse_bluetooth_manager_state(dump):
    """Extract an explicitly reported Bluetooth state; never infer one."""
    for pattern in _STATE_PATTERNS:
        match = pattern.search(dump or "")
        if match:
            return match.group(1).upper()
    return "NOT EXPOSED"


def adb_devices():
    if not shutil.which("adb"):
        return []
    code, output, _ = run(["adb", "devices", "-l"])
    rows = []
    if code == 0:
        for line in output.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] in {"device", "unauthorized", "offline"}:
                rows.append(
                    {"serial": parts[0], "state": parts[1], "details": " ".join(parts[2:])}
                )
    return rows


def shell(serial, cmd):
    code, output, error = run(["adb", "-s", serial, "shell", cmd], 12)
    if code == 0:
        return output or "EMPTY RESPONSE"
    reason = error or output or f"ADB exited with status {code}"
    return f"UNAVAILABLE: {reason}"


def inspect_android(serial):
    known = {item["serial"]: item for item in adb_devices()}
    if serial not in known or known[serial]["state"] != "device":
        return {
            "authorized": False,
            "state": known.get(serial, {}).get("state", "not found"),
        }

    props = {
        key: shell(serial, command)
        for key, command in {
            "manufacturer": "getprop ro.product.manufacturer",
            "model": "getprop ro.product.model",
            "android_release": "getprop ro.build.version.release",
            "sdk": "getprop ro.build.version.sdk",
            "build_fingerprint": "getprop ro.build.fingerprint",
        }.items()
    }
    dump = shell(serial, "dumpsys bluetooth_manager")
    props["bluetooth_manager_state"] = (
        parse_bluetooth_manager_state(dump)
        if not dump.startswith("UNAVAILABLE:")
        else "NOT VERIFIED: " + dump
    )
    props["headphone_link_encryption"] = (
        "NOT VERIFIED: Android did not expose authoritative link encryption evidence"
    )
    return {"authorized": True, **props}
