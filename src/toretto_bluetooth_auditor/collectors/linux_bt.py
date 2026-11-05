import shutil
import subprocess


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
