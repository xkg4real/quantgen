import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from io import BytesIO
from zipfile import ZipFile
import json
import unittest
from tests.letf_index_acceptance import unavailable_output
from tests.letf_disclosure_acceptance import fixture
from core.research.tool_export import report_bytes
from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication,QLabel


class NativeIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_calculated_and_unavailable_index_status_survive_ui_and_exports(self):
        w=ResearchWindow(auto_refresh=False);p=w.etf
        try:
            for out,status in [(fixture(),'SYNTHETIC'),(unavailable_output(),'UNAVAILABLE')]:
                p.show_result(out);p.bind_output('Index fixture',out)
                raw=report_bytes(p.report);obj=json.loads(raw)
                section=next(s for s in obj['sections'] if s['type'] in {'letf_interpretation','letf_unavailable'})
                self.assertEqual(section['underlying_index'],'KOSDAQ150')
                self.assertEqual(section['index_status'],status)
                self.assertEqual(obj['verdict'],'NOT_RUN')
                if status=='UNAVAILABLE':
                    self.assertNotIn('AZ variance proxies · bp',p.tables)
                    self.assertTrue(any('LETF calculation NOT_RUN' in x.text() for x in p.findChildren(QLabel)))
                with ZipFile(BytesIO(report_bytes(p.report,bundle=True))) as z:
                    self.assertIsNone(z.testzip());self.assertIn(b'KOSDAQ150',z.read('report.html'))
                p.clear_result();self.assertIsNone(p.report)
        finally:p.clear_result();w.close();w.deleteLater();self.app.processEvents()


if __name__=='__main__':unittest.main()
