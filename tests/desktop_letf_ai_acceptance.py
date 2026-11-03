"""Real native LETF request/report to preview and consent; no external AI or stores."""
from copy import deepcopy
from io import BytesIO
import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch
from zipfile import ZipFile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.quant.history import synthetic_history
    from core.quant.insights import Analysis
    from core.research.tool_export import report_bytes
    from quantgen_desktop.app import ResearchWindow
from PyQt6.QtCore import QEvent, QSettings
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMessageBox


class NativeLETFAiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='quantgen-letf-ai-')
        self.addCleanup(self.temp.cleanup)
        for target in ('socket.socket.connect', 'requests.sessions.Session.request',
                       'core.quant.validate.load_cards', 'core.research.etf_workflow.load_cards',
                       'core.quant.gate_ledger.family_ledger'):
            guard = patch(target, side_effect=AssertionError('No live provider, card or ledger'))
            guard.start()
            self.addCleanup(guard.stop)

        def history(symbol, *, source, days):
            self.assertEqual(source, 'synthetic')
            return synthetic_history(symbol, days=days)

        history_guard = patch('core.research.etf_workflow.load_history', side_effect=history)
        history_guard.start()
        self.addCleanup(history_guard.stop)
        self.runner = Mock(return_value=Analysis('Synthetic scenario commentary', 'fixture-model'))
        self.paper = Mock(side_effect=AssertionError('Paper store must stay unopened'))
        self.window = ResearchWindow(auto_refresh=False, commentary_runner=self.runner,
            paper_factory=self.paper, language_store=QSettings(
                self.temp.name + '/preferences.ini', QSettings.Format.IniFormat))
        self.addCleanup(self.close_window)

    def wait(self, jobs):
        for _ in range(1000):
            self.app.processEvents()
            if not jobs.busy:
                return
            QTest.qWait(10)
        self.fail('Synthetic worker did not finish')

    def close_window(self):
        self.wait(self.window.jobs)
        self.wait(self.window.commentary.jobs)
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            self.window.close()
        self.window.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_actual_scenario_report_preview_and_send_preserve_assumptions_and_consent(self):
        pane = self.window.etf
        pane.source.setCurrentIndex(pane.source.findData('synthetic'))
        fields = pane.fields['etf']
        fields['code'].setText('252670')
        fields['days'].setText('60')
        fields['letf_benchmark'].setCurrentIndex(fields['letf_benchmark'].findData('price_return'))
        for name, value in [('letf_funding_rate', '3.21'), ('letf_annual_fee', '.64'),
                            ('letf_dividend_yield', '1.23')]:
            fields[name].setText(value)
        pane.run.click()  # Real validation, window callback, Qt worker and report binding.
        self.wait(self.window.jobs)
        self.assertIsNotNone(pane.report, pane.status.text())
        self.assertEqual(pane.report['execution_status'], 'COMPLETED')
        self.assertEqual(pane.report['verdict'], 'NOT_RUN')
        # Explicit report serialisation stays entirely in memory, including its ZIP.
        self.assertEqual(json.loads(report_bytes(pane.report)), pane.report)
        with ZipFile(BytesIO(report_bytes(pane.report, bundle=True))) as bundle:
            self.assertEqual(json.loads(bundle.read('analysis.json')), pane.report)
        # Synthetic private markers exercise filtering without reading any account or key.
        pane.report['parameters']['api_key'] = 'synthetic-private-marker'
        pane.report['parameters']['account_balance'] = 'synthetic-private-marker'
        original = deepcopy(pane.report)
        self.runner.assert_not_called()

        commentary = self.window.commentary
        commentary.reload.click()
        self.assertEqual(commentary.source.count(), 1)
        self.assertEqual(commentary.source.currentText(), 'etf')
        commentary.preview_button.click()
        preview = json.loads(commentary.preview.toPlainText())
        self.assertEqual(preview['tool'], 'etf')
        self.assertEqual(preview['official_verdict'], 'NOT_RUN')
        self.assertNotIn('synthetic-private-marker', json.dumps(preview))
        self.assertEqual(preview['parameters']['letf_benchmark'], 'price_return')
        self.assertAlmostEqual(preview['parameters']['letf_funding_rate'], .0321)
        self.assertAlmostEqual(preview['parameters']['letf_annual_fee'], .0064)
        self.assertAlmostEqual(preview['parameters']['letf_dividend_yield'], .0123)
        interpretation = next(s for s in preview['sections'] if s['type'] == 'letf_interpretation')
        self.assertEqual(interpretation['index_status'], 'SYNTHETIC')
        self.assertEqual(interpretation['current_proxy_validation'], 'NOT_RUN')
        self.assertEqual(interpretation['assumptions']['funding_source'], 'USER_ASSUMPTION_NOT_MARKET_DATA')
        self.assertEqual(interpretation['assumptions']['benchmark'], 'price_return')
        table = next(s for s in preview['sections'] if s.get('name') == 'AZ variance proxies · bp')
        row = next(r for r in table['rows'] if r[0] == 63)
        self.assertAlmostEqual(float(row[3]), 240.75)
        self.assertAlmostEqual(float(row[4]), -16.)
        self.assertAlmostEqual(float(row[5]), -61.5)
        self.assertEqual(len(row), 7)

        self.assertFalse(commentary.consent.isChecked())
        # Owner B3: the button always answers; it is marked ready only once consent is ticked.
        self.assertFalse(commentary.send.property('primary'))
        commentary.submit()  # Even direct invocation cannot bypass the consent guard.
        self.runner.assert_not_called()
        self.assertIn('전송 동의', commentary.status.text())
        commentary.consent.setChecked(True)
        self.assertTrue(commentary.send.property('primary'))
        self.runner.assert_not_called()
        commentary.send.click()
        self.wait(commentary.jobs)
        self.runner.assert_called_once_with('etf', preview, question='')
        self.assertEqual(commentary.output.toPlainText(), 'Synthetic scenario commentary')
        self.assertEqual(commentary.report_actions.report['verdict'], 'NOT_RUN')
        self.assertEqual(pane.report, original)
        self.paper.assert_not_called()


if __name__ == '__main__':
    unittest.main()
