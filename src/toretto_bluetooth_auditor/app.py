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
from .collectors.ble_scan import scan_ble
from .collectors.linux_bt import adapter_status, rfkill_status
from .models import AuditReport
from .reporting import save_html, save_json


class Worker(QThread):
    done = Signal(object)
    error = Signal(str)

    def run(self):
        try:
            self.done.emit(asyncio.run(scan_ble()))
        except Exception as e:
            self.error.emit(str(e))


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TORETTO Bluetooth Security Auditor")
        self.resize(1000, 700)
        self.r = AuditReport("manual-audit", host=socket.gethostname())
        self.worker = None
        tabs = QTabWidget()
        tabs.addTab(self.home(), "Przegląd")
        tabs.addTab(self.ble(), "Skan BLE")
        tabs.addTab(self.android(), "Android / ADB")
        tabs.addTab(self.reports(), "Raport")
        self.setCentralWidget(tabs)

    def home(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.addWidget(
            QLabel(
                "<h1>TORETTO Bluetooth Security Auditor</h1><p>Audyt Bluetooth w trybie read-only.</p>"
            )
        )
        self.adapter = QTextEdit()
        self.adapter.setReadOnly(True)
        l.addWidget(self.adapter)
        b = QPushButton("Sprawdź adapter")
        b.clicked.connect(self.check_adapter)
        l.addWidget(b)
        s = QPushButton("Skanuj BLE")
        s.clicked.connect(self.scan)
        l.addWidget(s)
        return w

    def ble(self):
        w = QWidget()
        l = QVBoxLayout(w)
        self.bt = QTableWidget(0, 4)
        self.bt.setHorizontalHeaderLabels(["Nazwa", "Adres", "RSSI", "Usługi"])
        l.addWidget(self.bt)
        b = QPushButton("Rozpocznij pasywny skan BLE")
        b.clicked.connect(self.scan)
        l.addWidget(b)
        return w

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
            + "\\n"
            + "\\n".join(f"[{x.status}] {x.title}: {x.detail}" for x in self.r.findings)
        )
        self.refresh_report()

    def scan(self):
        if self.worker and self.worker.isRunning():
            return
        self.worker = Worker()
        self.worker.done.connect(self.ble_done)
        self.worker.error.connect(lambda e: QMessageBox.warning(self, "BLE unavailable", e))
        self.worker.start()

    def ble_done(self, ds):
        self.r.nearby_devices = ds
        self.bt.setRowCount(len(ds))
        for i, d in enumerate(ds):
            for j, v in enumerate(
                (
                    d.get("name"),
                    d.get("address"),
                    d.get("rssi"),
                    ", ".join(d.get("service_uuids", [])),
                )
            ):
                self.bt.setItem(i, j, QTableWidgetItem(str(v)))
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
        self.rt.setPlainText(
            "\\n".join(f"[{x.status}] {x.title}: {x.detail}" for x in self.r.findings)
            + f"\\nBLE devices: {len(self.r.nearby_devices)}"
        )

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
    w = Window()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
