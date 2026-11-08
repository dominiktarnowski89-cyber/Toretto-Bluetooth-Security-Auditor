import asyncio
import socket
import sys
from datetime import datetime

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .assessment import assess_adapter, assess_android
from .collectors.android_adb import adb_devices, inspect_android
from .collectors.linux_bt import adapter_status, rfkill_status
from .discovery import scan_all
from .identity_worker import IdentityWorker
from .models import AuditReport
from .reporting import save_html, save_json


class Worker(QThread):
    done = Signal(object)
    error = Signal(str)

    def run(self):
        try:
            self.done.emit(asyncio.run(scan_all()))
        except Exception as e:
            self.error.emit(str(e))


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TORETTO Bluetooth Security Auditor")
        self.resize(1100, 720)
        self.r = AuditReport("manual-audit", host=socket.gethostname())
        self.worker = None
        self.identity_worker = None
        tabs = QTabWidget()
        tabs.addTab(self.home(), "Przegląd")
        tabs.addTab(self.ble(), "Wykrywanie Bluetooth")
        tabs.addTab(self.identity(), "Identity & Spoofing")
        tabs.addTab(self.android(), "Android / ADB")
        tabs.addTab(self.reports(), "Raport")
        self.setCentralWidget(tabs)

    def home(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(
            QLabel(
                "<h1>TORETTO Bluetooth Security Auditor</h1>"
                "<p>Audyt read-only: Bluetooth Classic, BLE oraz urządzenia "
                "nierozpoznane. Program nie paruje się i nie łączy automatycznie.</p>"
            )
        )
        self.adapter = QTextEdit()
        self.adapter.setReadOnly(True)
        l.addWidget(self.adapter)
        b = QPushButton("Sprawdź adapter")
        b.clicked.connect(self.check_adapter)
        l.addWidget(b)
        s = QPushButton("Skanuj Bluetooth Classic + BLE")
        s.clicked.connect(self.scan)
        l.addWidget(s)
        return w

    def ble(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.bt = QTableWidget(0, 8)
        self.bt.setHorizontalHeaderLabels(
            ["Kategoria", "Protokół", "Nazwa", "Adres", "RSSI", "Identyfikatory", "Dekodowanie", "Pewność"]
        )
        self.bt.setSortingEnabled(True)
        l.addWidget(self.bt)
        b = QPushButton("Skanuj Bluetooth Classic + BLE")
        b.clicked.connect(self.scan)
        l.addWidget(b)
        self.scan_summary = QLabel(
            "Kategorie: Bluetooth Classic | BLE | Niezidentyfikowane"
        )
        l.addWidget(self.scan_summary)
        return w

    def identity(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(QLabel(
            "<h2>Device Identity & Spoofing Detection</h2>"
            "<p>Analiza podobienstwa danych reklamowych BLE, zmian adresow i historii emisji. "
            "Wynik jest wskazowka do dalszej weryfikacji, nie dowodem ataku.</p>"
        ))
        self.identity_table = QTableWidget(0, 7)
        self.identity_table.setHorizontalHeaderLabels(
            ["Ocena", "Nazwa", "Adresy", "Odcisk", "Obserwacje", "RSSI", "Przelaczenia"]
        )
        self.identity_table.setSortingEnabled(True)
        l.addWidget(self.identity_table)
        self.identity_alerts = QTextEdit()
        self.identity_alerts.setReadOnly(True)
        self.identity_alerts.setMaximumHeight(150)
        l.addWidget(self.identity_alerts)
        self.identity_summary = QLabel("Monitorowanie zatrzymane. Analiza obejmuje tylko dane reklamowe BLE.")
        l.addWidget(self.identity_summary)
        controls = QWidget()
        from PySide6.QtWidgets import QHBoxLayout
        row = QHBoxLayout(controls)
        start = QPushButton("Rozpocznij obserwacje")
        start.clicked.connect(self.start_identity)
        stop = QPushButton("Zatrzymaj")
        stop.clicked.connect(self.stop_identity)
        clear = QPushButton("Wyczysc historie")
        clear.clicked.connect(self.clear_identity)
        row.addWidget(start)
        row.addWidget(stop)
        row.addWidget(clear)
        l.addWidget(controls)
        return w

    def start_identity(self):
        if self.identity_worker and self.identity_worker.isRunning():
            return
        self.identity_summary.setText("Obserwacja BLE uruchomiona. Bez parowania, polaczen i zapytan GATT.")
        self.identity_worker = IdentityWorker(self)
        self.identity_worker.updated.connect(self.identity_updated)
        self.identity_worker.error.connect(self.identity_error)
        self.identity_worker.start()

    def stop_identity(self):
        if self.identity_worker and self.identity_worker.isRunning():
            self.identity_worker.stop()
            self.identity_worker.wait(6000)
        self.identity_summary.setText("Obserwacja zatrzymana.")

    def clear_identity(self):
        self.stop_identity()
        self.r.identity_observations = []
        self.identity_table.setRowCount(0)
        self.identity_alerts.clear()
        self.identity_summary.setText("Historia wyczyszczona.")

    def identity_error(self, error):
        self.identity_summary.setText("Blad obserwacji BLE.")
        QMessageBox.warning(self, "Identity & Spoofing", error)

    def identity_updated(self, devices, alerts, count):
        self.identity_table.setSortingEnabled(False)
        self.identity_table.setRowCount(len(devices))
        for i, item in enumerate(devices):
            values = (
                item.get("status", ""), item.get("name", ""),
                ", ".join(item.get("addresses", [])), item.get("fingerprint_short", ""),
                item.get("observations", 0),
                item.get("last_rssi") if item.get("last_rssi") is not None else "—",
                item.get("handoffs", 0),
            )
            for j, value in enumerate(values):
                self.identity_table.setItem(i, j, QTableWidgetItem(str(value)))
        self.identity_table.setSortingEnabled(True)
        lines = [
            "[" + str(a.get("confidence", "unknown")) + "] " + str(a.get("message", ""))
            + " Adresy: " + ", ".join(a.get("addresses", []))
            for a in alerts[-30:]
        ]
        self.identity_alerts.setPlainText("\\n".join(lines) or "Brak anomalii w dotychczasowych obserwacjach.")
        self.identity_summary.setText(
            f"Obserwacje: {count} | wzorce: {len(devices)} | alerty: {len(alerts)}. "
            "Rotacja adresu BLE moze wygladac jak podszywanie sie; wymaga weryfikacji."
        )
        if self.identity_worker:
            self.r.identity_observations = list(self.identity_worker.observations)

    def android(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.adb = QTableWidget(0, 3)
        self.adb.setHorizontalHeaderLabels(["Serial", "Stan", "Szczegóły"])
        l.addWidget(self.adb)
        b = QPushButton("Wykryj ADB")
        b.clicked.connect(self.refresh_adb)
        l.addWidget(b)
        a = QPushButton("Audyt Android read-only")
        a.clicked.connect(self.audit_android)
        l.addWidget(a)
        self.phone = QTextEdit()
        self.phone.setReadOnly(True)
        l.addWidget(self.phone)
        return w

    def reports(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.rt = QTextEdit()
        self.rt.setReadOnly(True)
        l.addWidget(self.rt)
        for k in ("json", "html"):
            b = QPushButton("Zapisz " + k.upper())
            b.clicked.connect(lambda _, x=k: self.export(x))
            l.addWidget(b)
        return w

    def check_adapter(self):
        a = adapter_status()
        self.r.adapter = a
        self.r.findings = [
            x for x in self.r.findings if not x.check_id.startswith("BT-")
        ] + assess_adapter(a, rfkill_status())
        self.adapter.setPlainText(
            str(a)
            + "\n"
            + "\n".join(f"[{x.status}] {x.title}: {x.detail}" for x in self.r.findings)
        )
        self.refresh_report()

    def scan(self):
        if self.worker and self.worker.isRunning():
            return
        self.scan_summary.setText(
            "Skanowanie BLE (aktywne, bez filtra) i Bluetooth Classic (BR/EDR)..."
        )
        self.worker = Worker()
        self.worker.done.connect(self.ble_done)
        self.worker.error.connect(self.scan_error)
        self.worker.start()

    def scan_error(self, error):
        self.scan_summary.setText("Skanowanie niekompletne — sprawdź komunikat błędu.")
        QMessageBox.warning(self, "Błąd skanowania Bluetooth", error)

    def ble_done(self, ds):
        self.r.nearby_devices = ds
        self.bt.setSortingEnabled(False)
        self.bt.setRowCount(len(ds))
        for i, d in enumerate(ds):
            identifiers = []
            if d.get("service_uuids"):
                identifiers.extend(d["service_uuids"])
            if d.get("manufacturer_ids"):
                identifiers.append(
                    "Manufacturer: " + ", ".join(x.get("company", "Unknown") + " (" + str(x.get("company_id")) + ")" for x in d.get("manufacturer_details", []))
                )
            for j, value in enumerate(
                (
                    d.get("category", ""),
                    d.get("protocol", ""),
                    d.get("name", ""),
                    d.get("address", ""),
                    d.get("rssi") if d.get("rssi") is not None else "—",
                    "; ".join(identifiers) or "Brak",
                    "; ".join(d.get("decoded_observations", [])) or "Brak rozpoznanych danych",
                    d.get("identification_confidence", d.get("class_details", {}).get("confidence", "—")),
                )
            ):
                self.bt.setItem(i, j, QTableWidgetItem(str(value)))
        self.bt.setSortingEnabled(True)
        counts = {
            category: sum(1 for item in ds if item.get("category") == category)
            for category in ("Bluetooth Classic", "BLE", "Niezidentyfikowane")
        }
        self.scan_summary.setText(
            "Wyniki: "
            + " | ".join(f"{key}: {value}" for key, value in counts.items())
            + ". Skanowanie nie potwierdza szyfrowania ani bezpieczeństwa urządzeń."
        )
        self.refresh_report()

    def refresh_adb(self):
        ds = adb_devices()
        self.adb.setRowCount(len(ds))
        for i, d in enumerate(ds):
            for j, k in enumerate(("serial", "state", "details")):
                self.adb.setItem(i, j, QTableWidgetItem(d.get(k, "")))

    def audit_android(self):
        d = next((x for x in adb_devices() if x["state"] == "device"), None)
        if not d:
            QMessageBox.information(
                self, "ADB", "Podłącz telefon, włącz USB debugging i zatwierdź klucz RSA."
            )
            self.refresh_adb()
            return
        p = inspect_android(d["serial"])
        self.r.phone = p
        self.r.findings = [
            x for x in self.r.findings if not x.check_id.startswith("ADB-")
        ] + assess_android(p)
        self.phone.setPlainText(str(p))
        self.refresh_report()

    def refresh_report(self):
        counts = {
            category: sum(
                1 for item in self.r.nearby_devices if item.get("category") == category
            )
            for category in ("Bluetooth Classic", "BLE", "Niezidentyfikowane")
        }
        self.rt.setPlainText(
            "\n".join(f"[{x.status}] {x.title}: {x.detail}" for x in self.r.findings)
            + "\n"
            + "Wykryte urządzenia: "
            + ", ".join(f"{key}: {value}" for key, value in counts.items())
        )

    def closeEvent(self, event):
        self.stop_identity()
        event.accept()

    def export(self, k):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Zapisz raport",
            f"toretto-{datetime.now():%Y%m%d-%H%M%S}.{k}",
            k.upper() + " (*." + k + ")",
        )
        if path:
            try:
                (save_json if k == "json" else save_html)(self.r, path)
                QMessageBox.information(self, "Zapisano", path)
            except OSError as e:
                QMessageBox.critical(self, "Błąd zapisu", str(e))


def main():
    app = QApplication(sys.argv)
    from pathlib import Path
    from PySide6.QtGui import QIcon

    icon = (
        Path(__file__).resolve().parents[2]
        / "assets/icons/toretto-bluetooth-icon.png"
    )
    if icon.is_file():
        app.setWindowIcon(QIcon(str(icon)))

    w = Window()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
