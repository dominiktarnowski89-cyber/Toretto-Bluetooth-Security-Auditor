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
    device_rows = []
    for device in d.get("nearby_devices", []):
        observations = "; ".join(device.get("decoded_observations", [])) or "Brak rozpoznanych danych producenta/usługi"
        device_rows.append("<tr>" + "".join(
            f"<td>{html.escape(str(value))}</td>" for value in (
                device.get("category", ""), device.get("protocol", ""),
                device.get("name", ""), device.get("address", ""),
                device.get("rssi", ""), observations,
                device.get("identification_confidence", "none"),
            )
        ) + "</tr>")
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
        + "</p><h2>Wykryte urządzenia Bluetooth</h2><table><tr><th>Kategoria</th><th>Protokół</th><th>Nazwa</th><th>Adres</th><th>RSSI</th><th>Rozpoznane dane</th><th>Pewność identyfikacji</th></tr>"
        + "".join(device_rows)
        + "</table><h2>Obserwacje tozsamosci BLE</h2><p>Liczba obserwacji: " + str(len(d.get("identity_observations", []))) + ". Odciski danych nie sa kryptograficznym dowodem tozsamosci fizycznego urzadzenia.</p><h2>Ustalenia audytu</h2><table><tr><th>Status</th><th>Kontrola</th><th>Dowody</th><th>Zalecenie</th></tr>"
        + "".join(rows)
        + "</table><p>NOT VERIFIED = niewystarczające dowody. Dane producenta i nazwy nie potwierdzają właściciela, modelu, podatności ani złośliwego działania.</p></html>"
    )


def save_html(report, path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_html(report), encoding="utf-8")
    return p
