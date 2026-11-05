import unittest

from toretto_bluetooth_auditor.assessment import assess_adapter, assess_android
from toretto_bluetooth_auditor.collectors.linux_bt import parse_show
from toretto_bluetooth_auditor.models import AuditReport, Finding
from toretto_bluetooth_auditor.reporting import render_html


class Tests(unittest.TestCase):
    def test_parser(self):
        d = parse_show(
            "Controller AA:BB:CC:DD:EE:FF"
            + chr(10)
            + " Powered: yes"
            + chr(10)
            + " Discoverable: no"
        )
        self.assertTrue(d["powered"])
        self.assertFalse(d["discoverable"])

    def test_radio_on_not_claimed_vulnerable(self):
        f = assess_adapter({"available": True, "powered": True, "discoverable": False}, [])
        self.assertEqual(f[0].status, "WARN")
        self.assertIn("not proof", f[0].detail)

    def test_missing_is_not_verified(self):
        self.assertTrue(
            any(x.status == "NOT VERIFIED" for x in assess_adapter({"available": True}, []))
        )

    def test_encryption_not_assumed(self):
        self.assertEqual(assess_android({"authorized": True})[1].status, "NOT VERIFIED")

    def test_html_escaping(self):
        r = AuditReport("<script>")
        r.findings.append(Finding("x", "<img>", "WARN", "<script>"))
        out = render_html(r)
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)


if __name__ == "__main__":
    unittest.main()
