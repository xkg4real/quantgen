"""Native ETF/Crypto diagnostic meaning survives JSON and HTML exports."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from io import BytesIO
from zipfile import ZipFile
import json
import unittest
from tests.ar1_decay_acceptance import etf_fixture,crypto_fixture
from core.research.tool_export import report_bytes
from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication


class NativeDecayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_both_panes_reports_and_clear(self):
        w=ResearchWindow(auto_refresh=False)
        try:
            for pane,out in ((w.etf,etf_fixture()),(w.crypto,crypto_fixture())):
                pane.show_result(out);pane.bind_output('AR1 fixture',out)
                report=json.loads(report_bytes(pane.report))
                self.assertIn('oscillates in sign',str(report))
                self.assertNotIn('slow-moving enough',str(report))
                self.assertIn('amplitude half-life',str(report))
                self.assertEqual(report['verdict'],'NOT_RUN')
                with ZipFile(BytesIO(report_bytes(pane.report,bundle=True))) as z:
                    self.assertIsNone(z.testzip());self.assertIn(b'oscillates in sign',z.read('report.html'))
                pane.clear_result();self.assertIsNone(pane.report)
        finally:w.close();w.deleteLater();self.app.processEvents()


if __name__=='__main__':unittest.main()
