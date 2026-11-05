import re
import shutil

from .linux_bt import run


def adb_devices():
    if not shutil.which("adb"):
        return []
    c, o, _ = run(["adb", "devices", "-l"])
    rows = []
    if c == 0:
        for line in o.splitlines()[1:]:
            p = line.split()
            if len(p) >= 2 and p[1] in {"device", "unauthorized", "offline"}:
                rows.append({"serial": p[0], "state": p[1], "details": " ".join(p[2:])})
    return rows


def shell(serial, cmd):
    c, o, e = run(["adb", "-s", serial, "shell", cmd], 12)
    return o if c == 0 else "UNAVAILABLE: " + (e or o)


def inspect_android(serial):
    known = {x["serial"]: x for x in adb_devices()}
    if serial not in known or known[serial]["state"] != "device":
        return {"authorized": False, "state": known.get(serial, {}).get("state", "not found")}
    props = {
        k: shell(serial, v)
        for k, v in {
            "manufacturer": "getprop ro.product.manufacturer",
            "model": "getprop ro.product.model",
            "android_release": "getprop ro.build.version.release",
            "sdk": "getprop ro.build.version.sdk",
            "build_fingerprint": "getprop ro.build.fingerprint",
        }.items()
    }
    dump = shell(serial, "dumpsys bluetooth_manager")
    m = re.search(r"\\bstate:\\s*(ON|OFF|BLE_ON|TURNING_ON|TURNING_OFF)", dump, re.I)
    props["bluetooth_manager_state"] = m.group(1).upper() if m else "NOT EXPOSED"
    props["headphone_link_encryption"] = (
        "NOT VERIFIED: Android did not expose authoritative link encryption evidence"
    )
    return {"authorized": True, **props}
