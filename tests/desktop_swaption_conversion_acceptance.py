import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json
from io import BytesIO
from zipfile import ZipFile
import unittest
from tests.swaption_conversion_acceptance import fixture
from core.research.tool_export import report_bytes
from quantgen_desktop.rates import RatesPane
from PyQt6.QtWidgets import QApplication,QLabel


class NativeSwaptionConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_valid_premium_and_unavailable_comparison_survive_native_export(self):
        p=RatesPane()
        try:
            out=fixture();p.show_result(out);p.bind_output('Swaption fixture',out)
            obj=json.loads(report_bytes(p.report));self.assertEqual(obj['verdict'],'NOT_RUN')
            section=next(s for s in obj['sections'] if s.get('type')=='comparison_volatility')
            self.assertEqual(section['status'],'UNAVAILABLE');self.assertIsNone(section['value'])
            self.assertIn('supported domain',section['reason'])
            table=p.tables['Metrics'];values={table.item(i,0).text():table.item(i,1).text() for i in range(table.rowCount())}
            self.assertNotEqual(values['Premium'],'—');self.assertEqual(values['Other-model vol'],'—')
            self.assertTrue(any('primary-model price' in x.text() for x in p.findChildren(QLabel)))
            with ZipFile(BytesIO(report_bytes(p.report,bundle=True))) as z:
                self.assertIsNone(z.testzip());self.assertIn(b'UNAVAILABLE',z.read('report.html'))
        finally:p.clear_result();p.close();p.deleteLater();self.app.processEvents()


if __name__=='__main__':unittest.main()
