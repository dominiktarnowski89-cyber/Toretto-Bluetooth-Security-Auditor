import html
import json
from pathlib import Path


def save_json(report, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def render_html(report):
    d = report.to_dict()
    rows = []
    for x in d["findings"]:
        rows.append(
            "<tr>"
            + "".join(
                f"<td>{html.escape(str(v))}</td>"
                for v in (x["status"], x["title"], x["detail"], x.get("recommendation", ""))
            )
            + "</tr>"
        )
    return (
        "<!doctype html><html lang='pl'><meta charset='utf-8'><title>TORETTO audit</title><h1>TORETTO Bluetooth Security Auditor</h1><p>Scenario: "
        + html.escape(str(d["scenario"]))
        + "</p><table><tr><th>Status</th><th>Check</th><th>Evidence</th><th>Recommendation</th></tr>"
        + "".join(rows)
        + "</table><p>NOT VERIFIED = insufficient evidence.</p></html>"
    )


def save_html(report, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_html(report), encoding="utf-8")
    return p
