"""Offscreen native display/export of actual portfolio constraint scope."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import json
from io import BytesIO
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from tests.portfolio_scope_acceptance import output_fixture
from core.research.tool_export import report_bytes
from quantgen_desktop.portfolio import PortfolioPane
from PyQt6.QtWidgets import QApplication


class NativePortfolioScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_native_rows_json_zip_and_clear_keep_actual_scope(self):
        with patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden")):
            pane = PortfolioPane()
            try:
                pane.show_result(output_fixture("min_vol", .1, negative=True))
                self.assertIn("10.00% requested", pane.scope.text())
                self.assertIn("No asset has positive", pane.notes.text())
                self.assertIn("100.00%", pane.comparison.item(0, 5).text())
                self.assertIn("selected", pane.comparison.item(1, 5).text())
                report = json.loads(report_bytes(pane.exports.report))
                scope = next(s["data"] for s in report["sections"] if s["type"] == "constraint_scope")
                self.assertEqual(scope["objectives"]["min_vol"]["requested_max_weight"], .1)
                self.assertEqual(scope["objectives"]["min_vol"]["effective_max_weight"], 1/3+1e-9)
                self.assertEqual(scope["frontier"]["effective_max_weight"], 1.)
                self.assertFalse(scope["frontier"]["uses_selected_cap"])
                self.assertEqual(report["verdict"], "NOT_RUN")
                with ZipFile(BytesIO(report_bytes(pane.exports.report, bundle=True))) as z:
                    self.assertIsNone(z.testzip())
                    self.assertIn(b"No asset has positive", z.read("report.html"))
                    self.assertIn(b"constraint_scope", z.read("analysis.json"))
                pane.clear_result()
                self.assertEqual(pane.comparison.rowCount(), 0)
                self.assertIsNone(pane.exports.report)
                self.assertNotIn("10.00% requested", pane.scope.text())
            finally:
                pane.close(); pane.deleteLater(); self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
