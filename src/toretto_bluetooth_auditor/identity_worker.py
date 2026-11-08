import asyncio
import threading

from PySide6.QtCore import QThread, Signal

from .collectors.ble_scan import scan_ble
from .identity import analyze_observations, build_identity_observations


class IdentityWorker(QThread):
    updated = Signal(object, object, int)
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop_event = threading.Event()
        self.observations = []
        self.scan_id = 0

    def stop(self):
        self._stop_event.set()

    def run(self):
        async def loop():
            while not self._stop_event.is_set():
                self.scan_id += 1
                try:
                    devices = await scan_ble(timeout=4.0)
                except Exception as exc:
                    self.error.emit(str(exc))
                    return
                self.observations.extend(build_identity_observations(devices, self.scan_id))
                self.observations = self.observations[-5000:]
                result = analyze_observations(self.observations)
                self.updated.emit(result["devices"], result["alerts"], result["observation_count"])
                await asyncio.sleep(0.8)
        try:
            asyncio.run(loop())
        except Exception as exc:
            self.error.emit(str(exc))
