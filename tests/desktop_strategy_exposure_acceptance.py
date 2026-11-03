"""N1 native display and exported reports keep exposure scope."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json
from io import BytesIO
from zipfile import ZipFile
import unittest
from unittest.mock import patch
from tests.strategy_exposure_acceptance import fixture
from core.research.strategy_analysis import StrategyRequest, StrategyOutput
from core.research.tool_export import report_bytes
from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication


class NativeExposureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def test_both_families_display_json_zip_and_clear(self):
        with patch('requests.sessions.Session.request',side_effect=AssertionError('network forbidden')), \
             patch('core.quant.validate.load_cards',side_effect=AssertionError('cards forbidden')):
            w=ResearchWindow(auto_refresh=False)
            try:
                pane=w.strategy
                for family in ('vol_target','crypto_trend'):
                    out=StrategyOutput(StrategyRequest(family=family),fixture(family))
                    pane.show_result(out);pane.bind_output('Strategy Lab',out)
                    report=json.loads(report_bytes(pane.report))
                    self.assertIn('OOS held gross exposure: mean 4.00',str(report))
                    self.assertIn('no portfolio gross cap',str(report))
                    self.assertIn('not exposure-matched',str(report))
                    self.assertEqual(report['verdict'],'NOT_RUN')
                    with ZipFile(BytesIO(report_bytes(pane.report,bundle=True))) as z:
                        self.assertIsNone(z.testzip())
                        self.assertIn(b'Maximum OOS borrowing 3.00',z.read('report.html'))
                    pane.clear_result();self.assertIsNone(pane.report)
                    self.assertEqual(pane.sections,[])
            finally:
                w.close();w.deleteLater();self.app.processEvents()


if __name__=='__main__': unittest.main()
