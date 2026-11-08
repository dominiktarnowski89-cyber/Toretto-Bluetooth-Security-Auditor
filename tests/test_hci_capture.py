import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from toretto_bluetooth_auditor.collectors.hci_capture import (
    _sha256,
    capture_hci_during_ble_scan,
)


class HciCaptureHelperTests(unittest.TestCase):
    def test_sha256_reads_capture_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.btsnoop"
            path.write_bytes(b"trace")
            self.assertEqual(len(_sha256(path)), 64)

    def test_rejects_non_positive_duration(self):
        with self.assertRaises(ValueError):
            capture_hci_during_ble_scan(0)

    def test_never_overwrites_existing_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.btsnoop"
            path.write_bytes(b"original")
            with patch(
                "toretto_bluetooth_auditor.collectors.hci_capture.shutil.which",
                return_value="/usr/bin/btmon",
            ):
                with self.assertRaises(FileExistsError):
                    capture_hci_during_ble_scan(1, path)
            self.assertEqual(path.read_bytes(), b"original")


if __name__ == "__main__":
    unittest.main()
