"""Native funding warning and typed diagnostics survive both export formats."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from io import BytesIO
from zipfile import ZipFile
import json
import unittest
from tests.ar1_decay_acceptance import crypto_fixture
from core.research.tool_export import report_bytes
from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication,QLabel

class NativeFundingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_diagnostic_and_retired_statistic_export_and_clear(self):
        w=ResearchWindow(auto_refresh=False)
        try:
            pane=w.crypto;out=crypto_fixture();pane.show_result(out);pane.bind_output('Synthetic funding',out)
            self.assertTrue(any('IID bootstrap p retired' in label.text() for label in pane.findChildren(QLabel)))
            raw=report_bytes(pane.report);obj=json.loads(raw)
            self.assertEqual(obj['verdict'],'NOT_RUN')
            self.assertIn(b'"bootstrap_p": null',raw);self.assertIn(b'EXHAUSTIVE_CIRCULAR_PHASE',raw)
            self.assertIn(b'FULL_SAMPLE_RETROSPECTIVE',raw)
            with ZipFile(BytesIO(report_bytes(pane.report,bundle=True))) as z:
                self.assertIsNone(z.testzip());self.assertIn(b'not valid confirmation',z.read('report.html'))
            pane.clear_result();self.assertIsNone(pane.report)
        finally:w.crypto.clear_result();w.close();w.deleteLater();self.app.processEvents()

if __name__=='__main__':unittest.main()
