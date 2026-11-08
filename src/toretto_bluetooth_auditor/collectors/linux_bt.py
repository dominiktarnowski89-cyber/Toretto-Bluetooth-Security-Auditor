import re
import shutil
import subprocess
import time


def run(args, timeout=8):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return (127 if isinstance(e, FileNotFoundError) else 124), "", str(e)


def parse_show(text):
    d = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        k, v = line.strip().split(":", 1)
        k = k.strip().lower().replace(" ", "_")
        v = v.strip()
        if k in {"powered", "discoverable", "pairable", "discovering"}:
            d[k] = v.lower() == "yes"
        elif k in {"name", "alias", "address", "modalias", "class"}:
            d[k] = v
    return d


def adapter_status():
    if not shutil.which("bluetoothctl"):
        return {"available": False, "error": "bluetoothctl missing"}
    c, o, e = run(["bluetoothctl", "show"])
    if c:
        return {"available": False, "error": e or o}
    d = parse_show(o)
    d.update(available=True, raw_status=o)
    return d


def rfkill_status():
    if not shutil.which("rfkill"):
        return []
    c, o, _ = run(["rfkill", "--output", "ID,TYPE,DEVICE,SOFT,HARD", "--noheadings"])
    rows = []
    if c == 0:
        for line in o.splitlines():
            p = line.split()
            if len(p) >= 5 and p[1].lower() == "bluetooth":
                rows.append(
                    dict(
                        zip(
                            ("id", "type", "device", "soft_blocked", "hard_blocked"),
                            p,
                            strict=False,
                        )
                    )
                )
    return rows


def scan_classic(timeout=8.0):
    """Run a BR/EDR inquiry and retain only devices seen during this scan."""
    if not shutil.which("bluetoothctl"):
        raise RuntimeError("bluetoothctl missing; Bluetooth Classic scan unavailable")

    process = subprocess.Popen(
        ["bluetoothctl"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        assert process.stdin is not None
        process.stdin.write("scan.transport bredr\nscan on\n")
        process.stdin.flush()
        time.sleep(max(1.0, float(timeout)))
        process.stdin.write("scan off\nquit\n")
        process.stdin.flush()
        scan_output, _ = process.communicate(timeout=6)
    except (OSError, subprocess.TimeoutExpired) as error:
        process.kill()
        process.communicate()
        raise RuntimeError(f"Bluetooth Classic scan failed: {error}") from error

    # bluetoothctl may colorize NEW/CHG event labels. Strip ANSI escapes before parsing.
    clean_output = re.sub(r"\x1b\[[0-9;]*m", "", scan_output)
    discovered = set(
        re.findall(r"\[(?:NEW|CHG)\]\s+Device\s+([0-9A-Fa-f:]{17})", clean_output)
    )

    devices = {}
    for address in sorted(discovered):
        info_code, info, _ = run(["bluetoothctl", "info", address], timeout=4)
        class_match = re.search(r"^\s*Class:\s*(0x[0-9a-fA-F]+)", info, re.M)
        if info_code or not class_match:
            continue
        name_match = re.search(r"^\s*(?:Name|Alias):\s*(.+)$", info, re.M)
        name = name_match.group(1).strip() if name_match else ""
        devices[address] = {
            "protocol": "Bluetooth Classic",
            "name": name or "Unknown Classic device",
            "address": address,
            "device_class": class_match.group(1),
            "manufacturer_data": {},
            "service_data": {},
            "tx_power": None,
            "rssi": None,
            "service_uuids": [],
            "manufacturer_ids": [],
            "source": "BlueZ BR/EDR inquiry event + device Class property",
        }
    return list(devices.values())
