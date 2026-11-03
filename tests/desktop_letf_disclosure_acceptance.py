import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from io import BytesIO
from zipfile import ZipFile
import json
import unittest
from tests.letf_disclosure_acceptance import fixture
from core.research.tool_export import report_bytes
from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication,QLabel

class NativeLETFTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_proxy_and_scope_exported_in_both_formats(self):
        w=ResearchWindow(auto_refresh=False)
        try:
            out=fixture();p=w.etf;p.show_result(out);p.bind_output('Synthetic LETF',out)
            self.assertIn('AZ variance proxies · bp',p.tables)
            self.assertTrue(any('not observed fund/index realised drag' in x.text() for x in p.findChildren(QLabel)))
            raw=report_bytes(p.report);self.assertEqual(json.loads(raw)['verdict'],'NOT_RUN')
            self.assertIn(b'AZ_PROXY_FROM_PRIOR_63_OBSERVATION_VARIANCE',raw)
            with ZipFile(BytesIO(report_bytes(p.report,bundle=True))) as z:
                self.assertIsNone(z.testzip());self.assertIn(b'not observed fund/index realised drag',z.read('report.html'))
            p.clear_result();self.assertIsNone(p.report)
        finally:w.etf.clear_result();w.close();w.deleteLater();self.app.processEvents()

if __name__=='__main__':unittest.main()
