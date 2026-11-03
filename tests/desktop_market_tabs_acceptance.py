"""Markets asset-class tabs and automatic provider choice (owner UI-8, 2026-11-03).

Offline: KIS and fallback providers are fakes; any HTTP attempt fails the test.
"""
import os
import re
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from quantgen_desktop.app import ResearchWindow, MARKET_CLASSES
from PyQt6.QtWidgets import QApplication, QComboBox, QLabel, QWidget
from core.market.routing import ChartRouter, KISChartProvider
from tests.desktop_market_chart_acceptance import FakeService, FakeStream, fixture

KO = ['국내증권', '해외증권', '국내파생상품', '해외파생상품', '채권', '금리·스왑', '외환', '가상자산', '매크로']
EN = ['Domestic securities', 'Overseas securities', 'Domestic derivatives', 'Overseas derivatives', 'Bonds',
      'Rates & swaps', 'FX', 'Crypto', 'Macro']


class MarketTabsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        deny = patch('requests.sessions.Session.request', side_effect=AssertionError('Network forbidden'))
        deny.start(); self.addCleanup(deny.stop)
        self.provider = Mock(side_effect=AssertionError('Provider forbidden'))
        self.window = ResearchWindow(auto_refresh=False, locale='ko_KR', market_loader=self.provider,
                                     connections_runner=self.provider)
        self.window.resize(1360, 940); self.window.show(); self.window.navigate('markets'); self.app.processEvents()
        self.addCleanup(self.window.deleteLater); self.addCleanup(self.window.hide)

    def titles(self):
        return [self.window.market_tabs.tabText(i) for i in range(self.window.market_tabs.count())]

    def test_nine_asset_classes_replace_the_kis_chart_tab_in_both_languages(self):
        w = self.window
        self.assertEqual(self.titles(), KO)
        w.set_language('en'); self.app.processEvents()
        self.assertEqual(self.titles(), EN)
        texts = [w.market_tabs.tabText(i) for i in range(w.market_tabs.count())]
        for entry in w.market_classes:
            if entry['inner'] is not None:
                texts += [entry['inner'].tabText(i) for i in range(entry['inner'].count())]
        self.assertFalse([t for t in texts if 'KIS' in t])
        self.assertFalse([t for t in texts if re.search('[가-힣]', t)])
        self.assertEqual(len(MARKET_CLASSES), 9)

    def test_no_visible_data_source_selector_anywhere_in_markets(self):
        w = self.window
        for index, entry in enumerate(w.market_classes):
            for pane in entry['panes']:
                w.market_tabs.setCurrentIndex(index)
                w.show_market_pane(w.market_chart if pane is entry['slot'] else pane); self.app.processEvents()
                page = w.stack.currentWidget().widget()
                shown = [l.text() for l in page.findChildren(QLabel) if l.isVisible()]
                self.assertFalse([t for t in shown if t in ('데이터 출처', 'Data source', 'Curve source')], entry['key'])
                if hasattr(pane, 'source') and isinstance(pane.source, QComboBox) and entry['key'] != 'macro':
                    self.assertTrue(pane.source.isHidden(), entry['key'])
        # The hidden combos keep their automatic value for requests and fixtures.
        self.assertEqual([w.rates.source.currentData(), w.fx.source.currentData(), w.derivatives.source.currentData(),
                          w.crypto.source.currentData(), w.krx.source.currentData(), w.bonds.source.currentData()],
                         ['auto', 'auto', 'kis', 'live', 'gateway', 'auto'])
        self.assertTrue(w.macro.source.isHidden())
        self.assertFalse(w.macro_records.source.isHidden())  # artifact set, not a data provider
        self.assertEqual(w.macro_records.source_label.text(), '기록 묶음')

    def test_every_pane_is_reachable_and_the_chart_follows_its_asset_class(self):
        w = self.window
        for index, entry in enumerate(w.market_classes):
            for pane in entry['panes']:
                target = w.market_chart if pane is entry['slot'] else pane
                if target is w.market_chart:
                    w.market_tabs.setCurrentIndex(index)  # the chart is shown in the class being viewed
                found = w.show_market_pane(target); self.app.processEvents()
                self.assertIs(w.current_market_pane(), target)
                self.assertIs(found, entry)
                if entry['asset']:
                    self.assertIs(w.market_chart.parent(), entry['slot'])
                    self.assertEqual(w.market_chart.asset.currentData(), entry['asset'])
        self.assertTrue(w.market_chart.asset.isHidden())
        # Asking for the chart keeps the chartable class being viewed.
        w.market_tabs.setCurrentIndex(1); self.app.processEvents()
        w.show_market_pane(w.market_chart); self.assertEqual(w.market_tabs.currentIndex(), 1)
        w.show_market_pane(w.fx); w.show_market_pane(w.market_chart)
        self.assertEqual(w.market_tabs.currentIndex(), 0)
        with self.assertRaises(ValueError):
            w.show_market_pane(QWidget())
        self.assertIsNone(w.market_chart.snapshot); self.assertEqual(w.market_chart._stream, None)
        self.provider.assert_not_called()

    def test_each_class_remembers_its_last_symbol(self):
        w = self.window; chart = w.market_chart
        chart.symbol.setText('000660')
        w.market_tabs.setCurrentIndex(1); self.app.processEvents()
        self.assertEqual(chart.symbol.text(), 'AAPL')
        chart.symbol.setText('MSFT')
        w.market_tabs.setCurrentIndex(0); self.app.processEvents()
        self.assertEqual((chart.asset.currentData(), chart.symbol.text()), ('domestic_stock', '000660'))
        w.market_tabs.setCurrentIndex(1); self.app.processEvents()
        self.assertEqual(chart.symbol.text(), 'MSFT')

    def test_home_stock_detail_opens_the_domestic_class(self):
        w = self.window
        w.market_tabs.setCurrentIndex(6); self.app.processEvents()
        w.open_stock_chart('000660')
        for _ in range(3):
            self.app.processEvents()
        self.assertEqual(w.market_tabs.currentIndex(), 0)
        self.assertIs(w.current_market_pane(), w.market_chart)
        self.assertEqual((w.market_chart.asset.currentData(), w.market_chart.symbol.text()), ('domestic_stock', '000660'))
        self.assertIsNone(w.market_chart.snapshot)


class FallbackDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        deny = patch('requests.sessions.Session.request', side_effect=AssertionError('Network forbidden'))
        deny.start(); self.addCleanup(deny.stop)
        from core.i18n import LocaleContext
        from quantgen_desktop.market_chart import MarketChartPane
        self.kis = FakeService(); self.kis.fail = True
        self.streams = []

        class Yahoo:
            name = 'Yahoo Finance'
            calls = []

            def ready(self):
                return True, ()

            def supports(self, request):
                return True

            def load(self, request):
                self.calls.append(request)
                from dataclasses import replace
                return replace(fixture(request), source='Yahoo Finance',
                               note='Yahoo Finance fallback: unadjusted OHLC, delayed; not a KIS quote. '
                                    'Live trade updates and Q-SCORE use KIS only.')

        self.yahoo = Yahoo()
        router = ChartRouter(KISChartProvider(lambda: self.pane.service), (self.yahoo,), deadline=3)

        def stream_factory():
            stream = FakeStream(); self.streams.append(stream); return stream

        self.pane = MarketChartPane(service=self.kis, stream_factory=stream_factory, locale=LocaleContext('ko_KR'),
                                    router=router)
        self.pane.resize(1000, 900); self.pane.show(); self.app.processEvents()
        self.addCleanup(self.pane.deleteLater); self.addCleanup(self.pane.stop)

    def wait(self, predicate):
        import time
        end = time.monotonic() + 5
        while time.monotonic() < end and not predicate():
            self.app.processEvents(); time.sleep(0.01)
        self.assertTrue(predicate())

    def test_kis_failure_shows_the_fallback_without_stream_or_polling(self):
        p = self.pane
        p.poll_button.setChecked(True)  # a user-enabled 5-second poll must not stay ticked on a fallback
        self.wait(lambda: p.snapshot is not None and not p.jobs.busy)
        self.assertFalse(p.poll_button.isChecked()); self.assertFalse(p.poll_timer.isActive())
        self.kis.calls.clear(); self.yahoo.calls.clear()
        p.refresh(manual=True)
        self.wait(lambda: p.snapshot is not None and not p.jobs.busy)
        self.assertEqual(p.snapshot.source, 'Yahoo Finance')
        self.assertEqual(len(self.kis.calls), 1); self.assertEqual(len(self.yahoo.calls), 1)
        self.assertEqual(self.streams, [])
        self.assertFalse(p.poll_timer.isActive()); self.assertFalse(p._auto_updates)
        self.assertFalse(p.poll_button.isChecked())
        self.assertEqual([a.provider for a in p._attempts], ['KIS', 'Yahoo Finance'])
        self.assertIn('Yahoo Finance 자료로 표시', p.status.text())
        self.assertIn('KIS 대신 Yahoo Finance', p.feed_notice.text())
        self.assertIn('KIS 실패 (RuntimeError)', p.feed_notice.text())
        self.assertNotIn('raw provider', p.feed_notice.text() + p.status.text())
        self.assertIn('Yahoo Finance 대체 자료', p.note.text())
        self.assertEqual(p.availability.text(), '')

    def test_kis_success_streams_as_before(self):
        p = self.pane
        self.kis.fail = False
        p.refresh(manual=True)
        self.wait(lambda: p.snapshot is not None and not p.jobs.busy)
        self.assertTrue(p.snapshot.source.startswith('KIS') or p.snapshot.source == 'KIS')
        self.assertEqual(self.yahoo.calls, [])
        self.assertTrue(self.streams and self.streams[0].started)


if __name__ == '__main__':
    unittest.main()
