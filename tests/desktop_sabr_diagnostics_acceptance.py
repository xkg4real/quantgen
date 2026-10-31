import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json
import unittest
from io import BytesIO
from zipfile import ZipFile
from tests.sabr_diagnostics_acceptance import fixture
from core.research.tool_export import report_bytes
from quantgen_desktop.fx import FXPane
from PyQt6.QtWidgets import QApplication,QLabel


class NativeSABRDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_native_quote_table_warnings_and_export_preserve_evidence(self):
        p=FXPane()
        from core.theme import active
        p.colors = active()
        try:
            out=fixture('1w',-.03,.02,strike='.9');p.show_result(out);p.bind_output('FX synthetic',out)
            table=p.tables['SABR quote residuals'];self.assertEqual(table.rowCount(),3)
            self.assertTrue(any('nu upper' in x.text() and 'EXTRAPOLATION' in x.text() for x in p.findChildren(QLabel)))
            obj=json.loads(report_bytes(p.report));self.assertEqual(obj['verdict'],'NOT_RUN')
            d=next(s for s in obj['sections'] if s.get('type')=='sabr_diagnostics')
            self.assertEqual(d['active_bounds'],['nu upper']);self.assertEqual(d['independent_validation'],'NOT_RUN')
            self.assertEqual(d['arbitrage_validation'],'NOT_RUN');self.assertGreater(d['rmse_vol_points'],.7)
            self.assertEqual(len(d['residuals']),3)
            with ZipFile(BytesIO(report_bytes(p.report,bundle=True))) as z:
                self.assertIsNone(z.testzip());self.assertIn(b'EXTRAPOLATION',z.read('report.html'))
        finally:p.clear_result();p.close();p.deleteLater();self.app.processEvents()


if __name__=='__main__':unittest.main()
