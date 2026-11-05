from .models import Finding


def assess_adapter(a, rf):
    if not a.get("available"):
        return [
            Finding(
                "BT-001", "Bluetooth adapter", "NOT VERIFIED", str(a.get("error", "No evidence"))
            )
        ]
    out = []
    p = a.get("powered")
    out.append(
        Finding(
            "BT-002",
            "Bluetooth radio",
            "WARN" if p is True else "PASS" if p is False else "NOT VERIFIED",
            "Adapter powered on; this is exposure, not proof of a vulnerability."
            if p is True
            else "Adapter reports Powered: no."
            if p is False
            else "Power state not exposed.",
        )
    )
    d = a.get("discoverable")
    out.append(
        Finding(
            "BT-003",
            "Discoverability",
            "WARN" if d is True else "PASS" if d is False else "NOT VERIFIED",
            "Discoverable: yes."
            if d is True
            else "Discoverable: no."
            if d is False
            else "State not exposed.",
        )
    )
    if rf:
        blocked = any(
            x.get("soft_blocked") == "blocked" or x.get("hard_blocked") == "blocked" for x in rf
        )
        out.append(
            Finding(
                "BT-004",
                "Radio block",
                "PASS" if blocked else "WARN",
                "rfkill reports blocked." if blocked else "Bluetooth not blocked by rfkill.",
            )
        )
    else:
        out.append(Finding("BT-004", "Radio block", "NOT VERIFIED", "rfkill evidence unavailable."))
    return out


def assess_android(p):
    if not p.get("authorized"):
        return [
            Finding(
                "ADB-001",
                "ADB authorization",
                "NOT VERIFIED",
                f"Phone unavailable: {p.get('state', 'unknown')}.",
            )
        ]
    return [
        Finding(
            "ADB-001",
            "ADB authorization",
            "PASS",
            "Owner-authorized Android answered read-only queries.",
        ),
        Finding(
            "ADB-BT-001",
            "Headphone link encryption",
            "NOT VERIFIED",
            str(p.get("headphone_link_encryption", "No authoritative evidence.")),
        ),
    ]
