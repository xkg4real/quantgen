"""Markets without tab strips, the Analysis tools page, and the chart pane's provider choice.

Owner UI-8 (2026-11-03) added asset-class tabs; the owner's 2026-11-04 request removed the scrolling
tab strip and the indicator charts from Markets: the analysis tools moved to their own page with a
visible button grid, and the price chart lives in one stock's screen.

Offline: KIS and fallback providers are fakes; any HTTP attempt fails the test.
"""
import os
import re
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from quantgen_desktop.app import ResearchWindow, TOOL_PANES
from PyQt6.QtWidgets import QApplication, QComboBox, QLabel, QTabBar, QToolButton, QWidget
from core.market.routing import ChartRouter, KISChartProvider
from tests.desktop_market_chart_acceptance import FakeService, FakeStream, fixture

KO = ['채권', '금리', '구조화 상품', '외환', '파생상품', 'ETF', 'KRX', '가상자산', '매크로 지표', '매크로 v2']
EN = ['Bonds', 'Rates', 'Structuring', 'FX', 'Derivatives', 'ETF', 'KRX', 'Crypto', 'Macro', 'Macro v2']


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

    def visible_tab_bars(self, route):
        page = self.window.stack.widget(self.window.route_indices[route]).widget()
        return [bar for bar in page.findChildren(QTabBar) if bar.isVisible()]

    def test_markets_has_no_tab_strip_and_no_indicator_board(self):
        w = self.window
        self.assertEqual(self.visible_tab_bars('markets'), [])
        self.assertFalse(hasattr(w, 'market_tabs')); self.assertFalse(hasattr(w, 'market_board'))
        page = w.stack.currentWidget().widget()
        self.assertFalse([b for b in page.findChildren(QToolButton) if b.isVisible() and b.arrowType()])
        self.assertTrue(w.markets_view.isVisible()); self.assertFalse(w.markets_view.showing_stock())
        self.assertEqual(len(w.markets_view.grid.cards), 6)  # the default watchlist: the six Home stocks
        shown = [l.text() for l in page.findChildren(QLabel) if l.isVisible()]
        self.assertFalse([t for t in shown if '공급자' in t or '관측' in t], shown)
        self.provider.assert_not_called()

    def test_every_tool_is_one_click_on_the_tools_page_in_both_languages(self):
        w = self.window
        w.navigate('tools'); self.app.processEvents()
        self.assertEqual(self.visible_tab_bars('tools'), [])
        self.assertEqual([w.tool_buttons[name].text() for name, _ in TOOL_PANES], KO)
        for name, _ in TOOL_PANES:
            w.tool_buttons[name].click(); self.app.processEvents()
            pane = getattr(w, name)
            self.assertIs(w.current_market_pane(), pane)
            self.assertTrue(pane.isVisible() and w.tool_buttons[name].isChecked(), name)
            others = [getattr(w, n) for n, _ in TOOL_PANES if n != name]
            self.assertFalse([o for o in others if o.isVisible()], name)
        w.set_language('en'); self.app.processEvents()
        texts = [w.tool_buttons[name].text() for name, _ in TOOL_PANES]
        self.assertEqual(texts, EN)
        self.assertFalse([t for t in texts if re.search('[가-힣]', t)])
        self.assertEqual(w.nav['tools'].text(), 'Analysis tools')
        with self.assertRaises(ValueError):
            w.show_market_pane(QWidget())
        self.provider.assert_not_called()

    def test_no_visible_data_source_selector_on_the_tools_page(self):
        w = self.window
        for name, _ in TOOL_PANES:
            pane = getattr(w, name)
            w.show_market_pane(pane); self.app.processEvents()
            self.assertEqual(w.stack.currentIndex(), w.route_indices['tools'])
            page = w.stack.currentWidget().widget()
            shown = [l.text() for l in page.findChildren(QLabel) if l.isVisible()]
            self.assertFalse([t for t in shown if t in ('데이터 출처', 'Data source', 'Curve source')], name)
            if hasattr(pane, 'source') and isinstance(pane.source, QComboBox) and name not in ('macro', 'macro_records'):
                self.assertTrue(pane.source.isHidden(), name)
        # The hidden combos keep their automatic value for requests and fixtures. The derivatives board
        # is chosen like the Flet page (owner issues 04/12): KIS with keys, else the labelled synthetic demo.
        import config
        self.assertEqual([w.rates.source.currentData(), w.fx.source.currentData(), w.derivatives.source.currentData(),
                          w.crypto.source.currentData(), w.krx.source.currentData(), w.bonds.source.currentData()],
                         ['auto', 'auto', 'kis' if config.kis_ready() else 'synthetic', 'live', 'gateway', 'auto'])
        self.assertTrue(w.macro.source.isHidden())
        self.assertFalse(w.macro_records.source.isHidden())  # artifact set, not a data provider
        self.assertEqual(w.macro_records.source_label.text(), '기록 묶음')

    def test_the_chart_opens_in_one_stocks_screen_on_markets(self):
        w = self.window
        w.navigate('tools'); self.app.processEvents()
        w.show_market_pane(w.market_chart); self.app.processEvents()
        self.assertEqual(w.stack.currentIndex(), w.route_indices['markets'])
        self.assertIs(w.current_market_pane(), w.market_chart)
        self.assertTrue(w.market_chart.isVisible()); self.assertTrue(w.market_chart.asset.isHidden())
        self.assertIsNone(w.market_chart.snapshot); self.assertEqual(w.market_chart._stream, None)
        self.provider.assert_not_called()

    def test_home_stock_detail_opens_that_stocks_screen(self):
        w = self.window
        w.navigate('tools'); self.app.processEvents()
        w.open_stock_chart('000660')
        for _ in range(3):
            self.app.processEvents()
        self.assertEqual(w.stack.currentIndex(), w.route_indices['markets'])
        self.assertIs(w.current_market_pane(), w.market_chart)
        self.assertEqual((w.market_chart.asset.currentData(), w.market_chart.symbol.text()), ('domestic_stock', '000660'))
        self.assertEqual(w.markets_view.stock.instrument.code, '000660')
        self.assertIsNone(w.market_chart.snapshot)  # automatic refresh is off: loading stays explicit


class SearchZoomTests(unittest.TestCase):
    """Owner UI-16 inside the pane: name search, no exchange/bar-count inputs, wheel zoom; since 2026-11-04 no
    provider or time lines (a delay notice only when the data is not domestic real-time)."""
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        deny = patch('requests.sessions.Session.request', side_effect=AssertionError('Network forbidden'))
        deny.start(); self.addCleanup(deny.stop)
        self.window = ResearchWindow(auto_refresh=False, locale='ko_KR', market_loader=Mock(), connections_runner=Mock())
        self.window.resize(1360, 940); self.window.show(); self.window.navigate('markets')
        self.addCleanup(self.window.deleteLater); self.addCleanup(self.window.hide)
        self.service = FakeService(); self.streams = []
        chart = self.window.market_chart
        chart.service = self.service
        chart.stream_factory = lambda: self.streams.append(FakeStream()) or self.streams[-1]
        self.window.show_market_pane(chart); chart.set_asset_class('overseas_stock'); self.app.processEvents()

    def wait(self, predicate):
        import time
        end = time.monotonic() + 5
        while time.monotonic() < end and not predicate():
            self.app.processEvents(); time.sleep(0.01)
        self.assertTrue(predicate())

    def test_choosing_a_name_loads_and_connects_without_a_button(self):
        from PyQt6.QtCore import Qt
        from PyQt6.QtTest import QTest
        p = self.window.market_chart
        for hidden in (p.exchange, p.bar_count, p.visible_bars, p.asset):
            self.assertTrue(hidden.isHidden())
        self.assertEqual(p.form_labels[1].text(), '종목 검색')
        p.symbol.setFocus(); p.symbol.setText('애플'); self.app.processEvents()
        self.assertTrue(p.symbol_suggestions.isVisible())
        self.assertEqual(p.suggestion_codes()[0], ('AAPL', 'NAS'))
        self.assertEqual(self.service.calls, [])  # typing alone never loads
        QTest.keyClick(p.symbol, Qt.Key.Key_Return)
        self.wait(lambda: p.snapshot is not None and not p.jobs.busy)
        self.assertEqual(self.service.calls[0].instrument.symbol, 'NAS:AAPL')
        self.assertEqual(self.service.calls[0].limit, 240)
        self.assertTrue(self.streams and self.streams[0].started)
        self.assertFalse(p.symbol_suggestions.isVisible())
        # Owner, 2026-11-04: no provider or time line; the US delay notice stays (12-claims), and the
        # source and times remain in the price tooltip.
        self.assertTrue(p.provenance.isVisible()); self.assertFalse(p.times.isVisible())
        self.assertIn('지연 0분', p.provenance.text())
        self.assertNotIn('출처', p.provenance.text()); self.assertNotIn('KIS', p.provenance.text())
        self.assertIn('출처', p.quote.toolTip()); self.assertIn('한국시간', p.quote.toolTip())

    def test_wheel_zooms_without_reloading_and_passes_through_at_limits(self):
        from PyQt6.QtCore import QPoint, QPointF, Qt
        from PyQt6.QtGui import QWheelEvent
        p = self.window.market_chart
        p.refresh(manual=True)
        self.wait(lambda: p.snapshot is not None and not p.jobs.busy)
        n = len(p.snapshot.candles)

        def wheel(delta):
            event = QWheelEvent(QPointF(100, 100), QPointF(100, 100), QPoint(0, 0), QPoint(0, delta),
                                Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
            self.app.sendEvent(p.chart, event)
            return event.isAccepted()

        start = p.visible_bars.value()
        self.assertTrue(wheel(120)); self.assertLess(p.visible_bars.value(), start)
        for _ in range(30):
            wheel(120)
        self.assertEqual(p.visible_bars.value(), 20)
        self.assertFalse(wheel(120))  # at the limit the page may scroll instead
        for _ in range(30):
            wheel(-120)
        self.assertEqual(p.visible_bars.value(), n)
        self.assertFalse(wheel(-120))
        self.assertEqual(len(self.service.calls), 1)
        self.assertGreaterEqual(p._cursor, n - p.visible_bars.value())

    def test_typed_listed_code_uses_its_exchange_and_suggestions_follow_language(self):
        p = self.window.market_chart
        p.symbol.setText('9984'); self.app.processEvents()
        self.assertEqual(p.request().instrument.symbol, 'TSE:9984')
        p.symbol.setText('애플'); self.app.processEvents()
        self.window.set_language('en'); self.app.processEvents()
        self.assertIn('Apple', p.symbol_suggestions.item(0).text())

    def test_domestic_derivatives_keep_a_market_selector(self):
        p = self.window.market_chart
        p.set_asset_class('domestic_future'); self.app.processEvents()
        self.assertTrue(p.exchange.isVisible()); self.assertEqual(p.form_labels[2].text(), '시장 구분')
        self.assertFalse(p.symbol_suggestions.isVisible())


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
