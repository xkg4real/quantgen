"""Language switching preserves forms, jobs and canonical research evidence."""
import copy
import os
import re
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from quantgen_desktop.app import ResearchWindow, label, table, table_rows
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import QApplication, QAbstractButton, QComboBox, QLabel, QLineEdit, QTabWidget
from quantgen_desktop.translations import translate
from tests.desktop_acceptance import fx_fixture, portfolio_fixture, bond_fixture


class NativeLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        network = patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden'))
        network.start(); self.addCleanup(network.stop)
        self.window = self.new_window()

    def new_window(self, **kwargs):
        w = ResearchWindow(auto_refresh=False, **kwargs)
        self.addCleanup(w.deleteLater)
        return w

    def drain(self):
        for _ in range(5): self.app.processEvents()

    def test_initial_english_and_korean_chrome(self):
        w = self.window
        self.drain()
        texts = [v.text() for v in w.findChildren(QLabel)]
        texts += [v.text() for v in w.findChildren(QAbstractButton)]
        self.assertFalse([t for t in texts if re.search('[가-힣]', t)])
        self.assertEqual(w.nav['home'].text(), 'Research Home')
        self.assertIn('US 10-year yield', [w.home_markets.item(i, 0).text() for i in range(w.home_markets.rowCount())])
        self.assertEqual(w.rates.fields['option']['vol'].accessibleName(), 'Normal volatility · bp')
        w.set_language('ko')
        self.assertEqual(w.nav['home'].text(), '연구 홈')
        self.assertEqual(w.fx.run.text(), '분석 실행')
        self.assertEqual(w.rates.fields['option']['vol'].accessibleName(), '정규 변동성 · bp')

    def test_switch_twice_preserves_inputs_requests_and_canonical_ids(self):
        w = self.window
        w.fx.tool.setCurrentIndex(w.fx.tool.findData('option'))
        w.fx.fields['option']['strike'].setText('1.2345')
        request = w.fx.make_request()
        fields = [(v, v.text()) for v in w.findChildren(QLineEdit)]
        combos = [(v, v.currentData(), v.currentIndex()) for v in w.findChildren(QComboBox) if v is not w.language]
        with patch.object(w.jobs, 'start', side_effect=AssertionError('language must not start jobs')):
            for language in ('ko', 'en', 'ko', 'en'):
                w.set_language(language); self.drain()
                self.assertEqual(request, w.fx.make_request())
                for v, text in fields: self.assertEqual(v.text(), text)
                for v, data, index in combos:
                    self.assertEqual(v.currentData(), data); self.assertEqual(v.currentIndex(), index)
        self.assertIsNone(w.paper_session.runtime)
        self.assertEqual(w.nav['quant'].text(), 'Build && Test')

    def test_dynamic_results_translate_headers_metrics_status_not_reports(self):
        w = self.window
        w.set_language('ko')
        w.fx.tool.setCurrentIndex(w.fx.tool.findData('option'))
        result = fx_fixture(w.fx.make_request())
        w.fx.show_result(result); w.fx.bind_output('fx', result)
        canonical = copy.deepcopy(w.fx.report)
        self.drain()
        metrics = w.fx.tables['Metrics']
        self.assertEqual(metrics.horizontalHeaderItem(0).text(), '측정 항목')
        captions = [metrics.item(r, 0).text() for r in range(metrics.rowCount())]
        self.assertIn('행사가격', captions)
        values = [metrics.item(r, 1).text() for r in range(metrics.rowCount())]
        w.set_language('en'); self.drain()
        self.assertEqual(metrics.horizontalHeaderItem(0).text(), 'Metric')
        self.assertIn('Strike', [metrics.item(r, 0).text() for r in range(metrics.rowCount())])
        self.assertEqual(values, [metrics.item(r, 1).text() for r in range(metrics.rowCount())])
        self.assertEqual(w.fx.report, canonical)
        self.assertTrue(w.fx.status.text().startswith('Calculation complete'))
        w.fx.status.setText('입력 오류 · 숫자, 단위, 만기 및 선택한 도구의 조건을 확인하세요.')
        self.assertTrue(w.fx.status.text().startswith('Input error'))
        self.assertEqual(w.fx.charts['SABR smile']._legend_names(), ['Volatility'])
        w.set_language('ko')
        self.assertEqual(w.fx.charts['SABR smile']._legend_names(), ['변동성'])

    def test_preference_survives_restart_in_isolated_store(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'settings.ini')
            store = QSettings(path, QSettings.Format.IniFormat)
            w = self.new_window(language_store=store)
            w.language.setCurrentIndex(w.language.findData('ko'))
            store.sync()
            reopened = QSettings(path, QSettings.Format.IniFormat)
            restored = self.new_window(language=reopened.value('ui/language', 'en'), language_store=reopened)
            self.assertEqual(restored.ui_language, 'ko')
            self.assertEqual(restored.nav['markets'].text(), '시장')
            self.assertEqual(restored.language.currentData(), 'ko')

    def test_window_language_isolation_and_late_controls(self):
        en, ko = self.window, self.new_window(language='ko')
        for w in (en, ko):
            late = label('Data source'); w.fx.result_layout.addWidget(late)
            w.late_label = late
        self.drain()
        self.assertEqual(en.late_label.text(), 'Data source')
        self.assertEqual(ko.late_label.text(), '데이터 출처')
        ko.set_language('en')
        self.assertEqual(ko.late_label.source_text, 'Data source')

    def test_user_symbols_identifiers_and_unknown_narratives_preserved(self):
        w = self.window
        grid = table(['Symbol', 'Value']); w.fx.result_layout.addWidget(grid)
        table_rows(grid, [['BUY', '1,234.56'], ['English', '원문']], ids=['order-123', 'order-456'])
        source = 'Issuer source: 한글 English <b>unchanged</b>'
        original = label(source); w.fx.result_layout.addWidget(original)
        for lang in ('ko', 'en'):
            w.set_language(lang); self.drain()
            self.assertEqual(grid.item(0, 0).text(), 'BUY')
            self.assertEqual(grid.item(0, 0).data(Qt.ItemDataRole.UserRole), 'order-123')
            self.assertEqual(grid.item(0, 1).text(), '1,234.56')
            self.assertEqual(original.text(), source)
            self.assertEqual(translate('custom-symbol-시장', lang), 'custom-symbol-시장')

    def test_export_source_language_does_not_follow_display_language(self):
        from core.research.portfolio_analysis import PortfolioRequest
        from core.research.bond_analysis import BondRequest
        w = self.window
        for pane, result in ((w.portfolio, portfolio_fixture(PortfolioRequest(('TEST', 'OTHER')))),
                             (w.bonds, bond_fixture(BondRequest()))):
            pane.show_result(result)
            canonical = copy.deepcopy(pane.exports.report)
            raw = pane.notes.source_text
            for language in ('ko', 'en'):
                w.set_language(language); self.drain()
                self.assertEqual(pane.exports.report, canonical)
                self.assertEqual(pane.notes.source_text, raw)


if __name__ == '__main__':
    unittest.main()
