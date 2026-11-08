import unittest

from toretto_bluetooth_auditor.identity import analyze_observations, make_observation


class IdentityTests(unittest.TestCase):
    def device(self, address, payload="010203", rssi=-70):
        return {
            "address": address, "name": "test", "local_name": "test", "rssi": rssi,
            "service_uuids": ["180d"], "manufacturer_data": {"76": payload}, "service_data": {},
        }

    def test_fingerprint_ignores_address_and_rssi(self):
        a = make_observation(self.device("AA:AA", rssi=-40), 1)
        b = make_observation(self.device("BB:BB", rssi=-90), 2)
        self.assertEqual(a["fingerprint"], b["fingerprint"])

    def test_empty_advertisement_is_not_given_fake_identity(self):
        self.assertIsNone(make_observation({"address": "AA", "rssi": -80}, 1))

    def test_same_fingerprint_on_two_addresses_creates_cautious_alert(self):
        a = make_observation(self.device("AA:AA"), 1)
        b = make_observation(self.device("BB:BB"), 2)
        result = analyze_observations([a, b])
        self.assertEqual(result["devices"][0]["address_count"], 2)
        self.assertEqual(result["alerts"][0]["type"], "shared_payload_multiple_addresses")
        self.assertIn("rotacja", result["alerts"][0]["message"])

    def test_repeated_exclusive_handoffs_are_counted(self):
        items = [
            make_observation(self.device(address), scan_id)
            for scan_id, address in enumerate(["AA", "BB", "AA", "BB", "AA"], 1)
        ]
        result = analyze_observations(items)
        self.assertEqual(result["devices"][0]["handoffs"], 4)
        self.assertEqual(result["alerts"][-1]["type"], "repeated_address_handoff")

    def test_full_advertising_fields_are_retained_in_observation(self):
        device = self.device("AA:AA")
        device.update({
            "address_type": "random", "tx_power": -8, "connectable": True,
            "scan_started_at": "2026-11-06T10:00:00+00:00",
            "scan_completed_at": "2026-11-06T10:00:04+00:00",
            "scan_duration_seconds": 4.0,
        })
        item = make_observation(device, 7)
        self.assertEqual(item["advertising_payload"]["manufacturer_data"]["76"], "010203")
        self.assertEqual(item["address_type"], "random")
        self.assertEqual(item["tx_power"], -8)
        self.assertTrue(item["connectable"])
        self.assertEqual(item["scan_id"], 7)
        self.assertFalse(item["raw_advertisement_available"])

    def test_raw_advertisement_bytes_are_hex_encoded_when_backend_supplies_them(self):
        device = self.device("AA:AA")
        device["raw_advertisement_data"] = bytes.fromhex("020106")
        item = make_observation(device, 1)
        self.assertEqual(item["raw_advertisement_hex"], "020106")
        self.assertTrue(item["raw_advertisement_available"])

    def test_same_fingerprint_in_one_scan_window_is_not_called_simultaneous(self):
        a = make_observation(self.device("AA:AA"), 1)
        b = make_observation(self.device("BB:BB"), 1)
        result = analyze_observations([a, b])
        alert = next(x for x in result["alerts"] if x["type"] == "multiple_addresses_within_scan_window")
        self.assertEqual(alert["confidence"], "low")
        self.assertIn("nie potwierdza jednoczesnej emisji", alert["message"])
        self.assertEqual(result["devices"][0]["multi_address_scan_windows"], 1)


if __name__ == "__main__":
    unittest.main()
