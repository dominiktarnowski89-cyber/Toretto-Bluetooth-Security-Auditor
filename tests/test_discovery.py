import unittest

from toretto_bluetooth_auditor.decoder import (
    decode_classic_device_class,
    decode_manufacturer_data,
    decode_service_uuids,
)
from toretto_bluetooth_auditor.discovery import classify_device


class DiscoveryClassificationTests(unittest.TestCase):
    def test_unidentified_ble_without_flags_or_identity(self):
        item = classify_device(
            {
                "protocol": "BLE",
                "name": "Unknown BLE device",
                "service_uuids": [],
                "manufacturer_ids": [],
            }
        )
        self.assertEqual(item["category"], "Niezidentyfikowane")

    def test_manufacturer_id_alone_is_not_device_identity(self):
        item = classify_device(
            {
                "protocol": "BLE",
                "name": "Unknown BLE device",
                "service_uuids": [],
                "manufacturer_ids": [76],
            }
        )
        self.assertEqual(item["category"], "Niezidentyfikowane")
        self.assertIn("Tylko identyfikator producenta", item["identification"])

    def test_mac_like_alias_is_not_identity(self):
        item = classify_device(
            {"protocol": "Bluetooth Classic", "name": "62-4C-FF-A0-F9-DC"}
        )
        self.assertEqual(item["category"], "Niezidentyfikowane")

    def test_named_classic_device_is_classified(self):
        item = classify_device({"protocol": "Bluetooth Classic", "name": "Headphones"})
        self.assertEqual(item["category"], "Bluetooth Classic")

    def test_manufacturer_and_service_data_classifies_ble(self):
        item = classify_device(
            {
                "protocol": "BLE",
                "name": "Unknown BLE device",
                "service_uuids": ["180D"],
                "manufacturer_ids": [76],
            }
        )
        self.assertEqual(item["category"], "BLE")


    def test_apple_nearby_info_signature_is_descriptive_not_identity(self):
        decoded = decode_manufacturer_data({"76": "1005aabbccddee"})[0]
        self.assertEqual(decoded["company"], "Apple")
        self.assertIn("Nearby Info", decoded["description"])
        self.assertEqual(decoded["confidence"], "medium")

    def test_apple_truncated_payload_lowers_confidence(self):
        decoded = decode_manufacturer_data({"76": "1010aabb"})[0]
        self.assertEqual(decoded["confidence"], "low")
        self.assertIn("truncated", decoded["description"])

    def test_microsoft_vendor_id_does_not_claim_device_type(self):
        decoded = decode_manufacturer_data({"6": "01020304"})[0]
        self.assertEqual(decoded["company"], "Microsoft")
        self.assertIn("not established", decoded["description"])

    def test_microsoft_printable_payload_is_exposed_as_evidence(self):
        decoded = decode_manufacturer_data({"6": "4c4150544f502d3234305641373041"})[0]
        self.assertIn("LAPTOP-240VA70A", decoded["printable_text"])

    def test_mesh_model_uuids_are_not_mislabelled_as_gatt_services(self):
        decoded = decode_service_uuids(["00001011-0000-1000-8000-00805f9b34fb"])[0]
        self.assertEqual(decoded["kind"], "Bluetooth Mesh model")
        self.assertIn("Admin Property", decoded["description"])

    def test_heart_rate_uuid_is_decoded(self):
        self.assertEqual(decode_service_uuids(["0000180d-0000-1000-8000-00805f9b34fb"])[0]["description"], "Heart Rate")

    def test_classic_set_top_box_class(self):
        decoded = decode_classic_device_class("0x000a0424")
        self.assertEqual(decoded["description"], "Audio/Video: Set-top box")
        self.assertEqual(decoded["confidence"], "high")


if __name__ == "__main__":
    unittest.main()
