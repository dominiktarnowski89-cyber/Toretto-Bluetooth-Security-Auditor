from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Literal

Status = Literal["PASS", "WARN", "FAIL", "NOT VERIFIED"]


@dataclass(slots=True)
class Finding:
    check_id: str
    title: str
    status: Status
    detail: str
    recommendation: str = ""
    evidence: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class AuditReport:
    scenario: str
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    host: str = "unknown"
    phone: dict[str, object] = field(default_factory=dict)
    adapter: dict[str, object] = field(default_factory=dict)
    nearby_devices: list[dict[str, object]] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self):
        return {
            "schema_version": 1,
            "application": "TORETTO Bluetooth Security Auditor",
            "scenario": self.scenario,
            "started_at": self.started_at,
            "host": self.host,
            "phone": self.phone,
            "adapter": self.adapter,
            "nearby_devices": self.nearby_devices,
            "findings": [asdict(x) for x in self.findings],
        }
