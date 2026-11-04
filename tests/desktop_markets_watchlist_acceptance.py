"""Markets as the user's watchlist charts plus one screen per stock (owner request, 2026-11-04).

"'시장' UI에서 주요지표들의 실시간 차트를 제공할 필요가 없다. 해당 화면은 사용자의 선호에 따라 자신이
관심종목으로 추가해놓은 차트들을 확인할 수 있어야하고, 구체적으로 하나의 종목을 검색하였을 때 해당 종목의
모든것들을 한 화면에서 제시해줘야한다." Also: every chart search takes a code or a name, and live values
show no provider or observation-date fields.

Offline: providers are fakes; HTTP and Yahoo attempts fail the test; QSettings is a temporary file.
"""
import os
import re
import tempfile
import time
import unittest
from dataclasses import replace
from datetime import date, timedelta
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from quantgen_desktop.app import ResearchWindow
    from quantgen_desktop.markets_view import (SymbolCompleter, WatchlistStore, WATCHLIST_KEY, WATCHLIST_LIMIT,
                                               load_cards)
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton
from core.market.directory import SymbolDirectory
from core.market.models import Candle, ChartRequest, Instrument, MarketQuote, MarketSnapshot
from core.research.stock_profile import build_profile

SAMSUNG, HYNIX, APPLE = (Instrument("domestic_stock", "005930"), Instrument("domestic_stock", "000660"),
                         Instrument("overseas_stock", "AAPL", "NAS"))


def snapshot(instrument, *, source="KIS", last_day=None, start=100.0, step=1.0, n=120):
    last_day = last_day or date.today()
    candles = tuple(Candle((last_day - timedelta(days=n - 1 - i)).isoformat(), start + i * step,
                           start + i * step + 2, start + i * step - 1, start + i * step + 1, 1000 + i)
                    for i in range(n))
    request = ChartRequest(instrument, "1d", n, adjusted=True)
    return MarketSnapshot(request, candles, None, fetched_at="2026-11-04T01:00:00+00:00", source=source)


class FakeRouter:
    def __init__(self, answers):
        self.answers, self.calls, self.last_attempts = answers, [], ()

    def load(self, request):
        self.calls.append(request)
        answer = self.answers[request.instrument.code]
        if isinstance(answer, Exception):
            raise answer
        return answer


class MarketsWatchlistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ("requests.sessions.Session.request", "core.market.routing._yahoo_frame"):
            deny = patch(target, side_effect=AssertionError("Network forbidden"))
            deny.start(); self.addCleanup(deny.stop)
        folder = tempfile.TemporaryDirectory(); self.addCleanup(folder.cleanup)
        self.settings = QSettings(os.path.join(folder.name, "prefs.ini"), QSettings.Format.IniFormat)
        self.provider = Mock(side_effect=AssertionError("Provider forbidden"))
        self.directory = SymbolDirectory(master_loader=Mock(side_effect=AssertionError("No master download")))
        self.router = FakeRouter({
            "005930": snapshot(SAMSUNG, start=70000, step=10),
            "000660": snapshot(HYNIX, start=200000, step=-50, last_day=date.today() - timedelta(days=20)),
            "AAPL": snapshot(APPLE, source="Yahoo Finance", start=180, step=0.5)})
        self.profiles = []

        def profile_loader(instrument):
            self.profiles.append(instrument)
            data = self.router.answers[instrument.code]
            return build_profile(instrument, candles=data.candles, name="삼성전자" if instrument.code == "005930" else "")

        self.store = WatchlistStore(self.settings, defaults=[SAMSUNG, HYNIX, APPLE])
        self.window = ResearchWindow(auto_refresh=False, locale="ko_KR", market_loader=self.provider,
                                     connections_runner=self.provider, symbol_directory=self.directory,
                                     watchlist_store=self.store, card_router_factory=lambda: self.router,
                                     profile_loader=profile_loader)
        self.window.resize(1360, 940); self.window.show(); self.window.navigate("markets"); self.app.processEvents()
        self.view = self.window.markets_view
        self.addCleanup(self.window.deleteLater); self.addCleanup(self.window.hide)

    def wait(self, predicate, seconds=5):
        end = time.monotonic() + seconds
        while time.monotonic() < end and not predicate():
            self.app.processEvents(); time.sleep(0.01)
        self.assertTrue(predicate())

    def visible_text(self):
        page = self.window.stack.currentWidget().widget()
        return [w.text() for w in page.findChildren(QLabel) if w.isVisible() and w.text()]

    def load_cards(self):
        self.assertTrue(self.view.grid.refresh(manual=True))
        self.wait(lambda: not self.view.grid.jobs.busy and all(c.result for c in self.view.grid.cards.values()))

    def test_store_defaults_persist_and_reject_bad_entries(self):
        store = WatchlistStore(self.settings, defaults=[SAMSUNG])
        self.assertEqual(store.items(), [SAMSUNG])
        self.assertTrue(store.add(APPLE)); self.assertFalse(store.add(APPLE))
        self.assertEqual(WatchlistStore(self.settings).items(), [SAMSUNG, APPLE])  # read back from QSettings
        self.assertTrue(store.remove(SAMSUNG)); self.assertEqual(WatchlistStore(self.settings).items(), [APPLE])
        self.assertTrue(store.remove(APPLE)); self.assertEqual(WatchlistStore(self.settings, defaults=[SAMSUNG]).items(), [])
        self.settings.setValue(WATCHLIST_KEY, '[{"asset":"domestic_stock","code":"5930"},{"asset":"x","code":"1"},'
                                              '{"asset":"overseas_stock","code":"MSFT","exchange":"NAS"},7,'
                                              '{"asset":"overseas_stock","code":"MSFT","exchange":"NAS"}]')
        self.assertEqual(WatchlistStore(self.settings).items(), [Instrument("overseas_stock", "MSFT", "NAS")])
        self.settings.setValue(WATCHLIST_KEY, "not json")
        self.assertEqual(WatchlistStore(self.settings).items(), [])
        full = WatchlistStore(None, defaults=[Instrument("domestic_stock", f"{i:06d}") for i in range(30)])
        self.assertEqual(len(full.items()), WATCHLIST_LIMIT); self.assertFalse(full.add(SAMSUNG))

    def test_cards_show_price_change_and_chart_but_no_provider_or_date(self):
        self.assertEqual(self.router.calls, [])  # nothing loads with automatic refresh off
        self.load_cards()
        cards = self.view.grid.cards
        samsung = cards[("domestic_stock", "005930", "")]
        self.assertEqual(samsung.title.text(), "삼성전자")
        self.assertEqual(samsung.price.text(), f"{70000 + 119 * 10 + 1:,.0f}")
        self.assertTrue(samsung.change.text().startswith("▲")); self.assertEqual(samsung.change.property("tone"), "up")
        self.assertFalse(samsung.state.isVisible())  # KIS, fresh, loaded: nothing to flag
        hynix = cards[("domestic_stock", "000660", "")]
        self.assertTrue(hynix.change.text().startswith("▼")); self.assertEqual(hynix.change.property("tone"), "down")
        self.assertIn("오래된 자료", hynix.state.text())  # 20 days old: stale stays labelled
        apple = cards[("overseas_stock", "AAPL", "NAS")]
        self.assertEqual(apple.title.text(), "애플"); self.assertIn("지연 시세", apple.state.text())
        shown = " ".join(self.visible_text())
        for word in ("출처", "공급", "관측", "Source", "Provider", "KIS", "Yahoo"):
            self.assertNotIn(word, shown)
        self.assertFalse(re.search(r"\d{4}-\d{2}-\d{2}", shown), shown)
        self.assertIn("Yahoo Finance", apple.toolTip())  # still discoverable on hover
        self.assertEqual([r.instrument.code for r in self.router.calls], ["005930", "000660", "AAPL"])
        self.assertTrue(all(r.adjusted and r.interval == "1d" for r in self.router.calls))

    def test_a_failed_refresh_keeps_the_last_chart_and_says_so(self):
        self.load_cards()
        self.router.answers["005930"] = RuntimeError("raw provider URL")
        self.load_cards()
        card = self.view.grid.cards[("domestic_stock", "005930", "")]
        self.assertNotEqual(card.price.text(), "—")
        self.assertIn("갱신 실패, 마지막 값 표시", card.state.text())
        self.assertNotIn("raw provider", " ".join(self.visible_text()))
        self.assertEqual(load_cards(self.router, [SAMSUNG])[0].error, "RuntimeError")

    def test_a_card_or_a_search_opens_one_screen_with_everything(self):
        self.load_cards()
        card = self.view.grid.cards[("domestic_stock", "005930", "")]
        QTest.mouseClick(card, Qt.MouseButton.LeftButton)
        self.app.processEvents()
        self.assertTrue(self.view.showing_stock())
        stock = self.view.stock
        self.assertEqual(stock.instrument, SAMSUNG)
        self.assertIs(self.window.current_market_pane(), self.window.market_chart)
        self.assertFalse(self.window.market_chart.symbol.isVisible())  # the screen's header names the stock
        stock.load_profile()
        self.wait(lambda: stock.profile is not None and not stock.jobs.busy)
        self.assertEqual(stock.name.text(), "삼성전자"); self.assertEqual(stock.code.text(), "005930 · KRX")
        keys = [p.title.text() for p in stock.section_panels]
        self.assertGreaterEqual(len(keys), 4, keys)
        shown = " ".join(self.visible_text())
        self.assertNotIn("공급자", shown); self.assertNotIn("관측일", shown)
        stock.back_button.click(); self.app.processEvents()
        self.assertFalse(self.view.showing_stock())
        # Search by name, Korean initials and English name, then open.
        self.assertEqual(self.view.completer.results("삼성")[0].code, "005930")
        self.assertEqual(self.view.completer.results("ㅅㅅㅈㅈ")[0].code, "005930")
        self.assertEqual(self.view.completer.results("apple")[0].code, "AAPL")
        self.view.search.setText("애플"); self.view.submit(); self.app.processEvents()
        self.assertEqual(stock.instrument, APPLE)
        self.assertEqual(self.window.market_chart.asset.currentData(), "overseas_stock")
        self.assertEqual(self.view.search.text(), "")
        self.assertEqual(self.profiles, [SAMSUNG])  # opening never loads with automatic refresh off

    def test_unknown_text_is_not_guessed_and_codes_still_work(self):
        self.view.search.setText("없는회사이름"); self.view.submit(); self.app.processEvents()
        self.assertFalse(self.view.showing_stock()); self.assertTrue(self.view.message.isVisible())
        self.view.search.setText("123456"); self.view.submit(); self.app.processEvents()
        self.assertEqual(self.view.stock.instrument, Instrument("domestic_stock", "123456"))
        self.view.kind.setCurrentIndex(self.view.kind.findData("domestic_future"))
        self.view.search.setText("101W12"); self.view.submit(); self.app.processEvents()
        self.assertEqual(self.view.stock.instrument.asset, "domestic_future")
        self.assertEqual(self.window.market_chart.asset.currentData(), "domestic_future")
        self.assertIn("주식에만", self.view.stock.profile_status.text())
        self.assertEqual(self.profiles, [])

    def test_star_adds_and_removes_the_open_stock(self):
        self.view.open_instrument(Instrument("overseas_stock", "MSFT", "NAS"))
        stock = self.view.stock
        self.assertIn("☆", stock.watch_button.text())
        stock.watch_button.click(); self.app.processEvents()
        self.assertIn(("overseas_stock", "MSFT", "NAS"), self.view.grid.cards)
        self.assertIn("★", stock.watch_button.text())
        self.assertIn("MSFT", self.settings.value(WATCHLIST_KEY))
        stock.watch_button.click(); self.app.processEvents()
        self.assertNotIn(("overseas_stock", "MSFT", "NAS"), self.view.grid.cards)
        card = self.view.grid.cards[("domestic_stock", "000660", "")]
        card.remove_button.click(); self.app.processEvents()
        self.assertNotIn(("domestic_stock", "000660", ""), self.view.grid.cards)
        self.assertEqual([i.code for i in WatchlistStore(self.settings).items()], ["005930", "AAPL"])

    def test_every_symbol_field_searches_by_code_or_name(self):
        w = self.window
        fields = [c.edit for c in w.symbol_completers]
        self.assertIn(w.symbol, fields); self.assertIn(w.portfolio.symbols, fields)
        for pane, name in ((w.signals, "symbol"), (w.strategy, "symbols"), (w.etf, "code"), (w.krx, "code")):
            self.assertTrue(any(controls.get(name) in fields for controls in pane.fields.values()), name)
        quant = next(c for c in w.symbol_completers if c.edit is w.symbol)
        quant.apply(quant.results("삼성전자")[0]); self.app.processEvents()
        self.assertEqual(w.symbol.text(), "005930")
        portfolio = next(c for c in w.symbol_completers if c.edit is w.portfolio.symbols)
        w.portfolio.symbols.setText("AAPL, 하이닉스")
        portfolio.apply(portfolio.results(w.portfolio.symbols.text())[0]); self.app.processEvents()
        self.assertEqual(w.portfolio.symbols.text(), "AAPL, 000660")
        etf = next(c for c in w.symbol_completers if c.edit in [ctl.get("code") for ctl in w.etf.fields.values()])
        self.assertTrue(all(r.kind == "etf" for r in etf.results("삼성")))
        self.assertIsInstance(quant, SymbolCompleter)

    def test_english_mode_shows_no_hangul_on_markets(self):
        self.load_cards()
        self.view.open_instrument(SAMSUNG)
        self.view.stock.load_profile()
        self.wait(lambda: self.view.stock.profile is not None and not self.view.stock.jobs.busy)
        self.window.set_language("en"); self.app.processEvents()
        page = self.window.stack.currentWidget().widget()
        widgets = [*page.findChildren(QLabel), *page.findChildren(QPushButton)]
        hangul = [x.text() for x in widgets if x.isVisible() and re.search("[가-힣]", x.text())]
        self.assertEqual(hangul, [])
        self.assertEqual(self.view.stock.name.text(), "Samsung Electronics")
        self.view.stock.back_button.click(); self.app.processEvents()
        self.assertEqual(self.view.grid.cards[("domestic_stock", "005930", "")].title.text(), "Samsung Electronics")

    def test_nothing_loads_or_downloads_with_automatic_refresh_off(self):
        self.window.navigate("home"); self.window.navigate("markets"); self.app.processEvents()
        self.view.search.setFocus(); self.view.search.setText("삼성"); self.app.processEvents()
        self.view.open_instrument(SAMSUNG); self.app.processEvents()
        self.assertEqual(self.router.calls, []); self.assertEqual(self.profiles, [])
        self.assertIsNone(self.window.market_chart.snapshot)
        self.assertFalse(self.directory.domestic_loaded)  # no master download with automatic refresh off
        self.provider.assert_not_called()


if __name__ == "__main__":
    unittest.main()
