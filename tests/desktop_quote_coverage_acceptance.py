import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from io import BytesIO
from zipfile import ZipFile
import json
import unittest
from tests.quote_coverage_acceptance import output
from core.research.tool_export import report_bytes
from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication,QLabel


class NativeCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_coverage_table_and_export_preserve_missing_versus_tested_zero(self):
        w=ResearchWindow(auto_refresh=False);p=w.derivatives
        try:
            for closed in (False,True):
                out=output(closed);p.show_result(out);p.bind_output('Coverage fixture',out)
                obj=json.loads(report_bytes(p.report))
                section=next(s for s in obj['sections'] if s['type']=='quote_coverage')
                check=section['static']['call_butterfly']
                self.assertEqual(check['status'],'NOT_RUN' if closed else 'COMPUTED')
                self.assertEqual(check['violations'],None if closed else 0)
                table=p.tables['Static arbitrage checks']
                row=next(i for i in range(table.rowCount()) if table.item(i,0).text()=='call_butterfly')
                self.assertEqual(table.item(row,1).text(),'NOT_RUN' if closed else '0')
                self.assertEqual(obj['verdict'],'NOT_RUN')
                if closed:self.assertTrue(any('Put–call parity NOT_RUN' in x.text() for x in p.findChildren(QLabel)))
                with ZipFile(BytesIO(report_bytes(p.report,bundle=True))) as z:
                    self.assertIsNone(z.testzip());self.assertIn(b'quote_coverage',z.read('report.html'))
                p.clear_result()
        finally:p.clear_result();w.close();w.deleteLater();self.app.processEvents()


if __name__=='__main__':unittest.main()
