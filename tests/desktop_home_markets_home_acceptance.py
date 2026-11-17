"""Research Home redesign (owner request 2026-11-11, decision UI-D7 point 4; area H).

"연구 홈 화면을 표대신 이렇게 심플하고 세련되게 화살표로 휙휙 넘길수잇게 하자 (트레이딩뷰 화면 참고) 표에 종목 너무많이
때려박는거 자체의 구조적 문제인거같아. 세로로 넓게 넓게 공간 쓰고, 연구 홈에 주요차트 뿐만이 아니라 우리는 연구분석과
같은 UI들이 들어가는데, 얘들이 들어갈 공간은 스크롤 상하 범위를 넓혀서 해결해보자. 그리고 연구 홈에서 '관심종목' 차트를
직관적으로 볼수있게 유아이를 저기로 옮기고"

Checked here: market cards that page with arrows (four on a wide window, fewer when narrow), the selected
card's large chart (about half as tall as wide) fed off the UI thread from the card row's own provider, the
watchlist chart cards on Home opening the stock on Markets, the research sections below, and the quotes table
in a closed fold. Offline: HTTP, Yahoo and the KIS master download fail the test; loaders are fixtures.
"""
import os
import re
import tempfile
import threading
import time
import unittest
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from quantgen_desktop.app import ResearchWindow
    from quantgen_desktop import home_view
    from quantgen_desktop.home_view import (HOME_MARKETS, HomeView, MarketHistory, card_columns, crop,
                                            load_market_history)
    from quantgen_desktop.markets_view import WatchlistStore
from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QLabel, QMessageBox
from core.market.directory import SymbolDirectory
from core.market.models import Candle, ChartRequest, Instrument, MarketSnapshot
from core.research.watchlist import default_home_rows

SAMSUNG, APPLE = Instrument("domestic_stock", "005930"), Instrument("overseas_stock", "AAPL", "NAS")
PROVIDERS = {"^GSPC": "yfinance", "^KS11": "yfinance", "DEXKOUS": "fred", "DGS10": "fred", "VIXCLS": "fred",
             "BTC-USD": "yfinance"}


def series(symbol, source, days, *, n=300, start=100.0, step=0.5, last=date(2026, 11, 10)):
    dates = [(last - timedelta(days=n - 1 - i)).isoformat() for i in range(n)]
    return SimpleNamespace(source=source.upper(), dates=dates, values=[start + i * step for i in range(n)])


class SeriesLoader:
    """load_series stand-in: records (symbol, source, days) and the thread it ran on."""

    def __init__(self, **kwargs):
        self.calls, self.threads, self.kwargs = [], [], kwargs

    def __call__(self, symbol, *, source, days):
        self.calls.append((symbol, source, days))
        self.threads.append(threading.get_ident())
        return series(symbol, source, days, **self.kwargs)


def observed_rows():
    rows = default_home_rows()
    values = {"^GSPC": (5871.42, 0.84), "^KS11": (2587.31, -1.12), "DEXKOUS": (1387.5, 0.21),
              "DGS10": (4.31, -3.0), "VIXCLS": (15.62, 4.8), "BTC-USD": (96123.5, 2.4)}
    for row in rows:
        if row["symbol"] in values:
            value, change = values[row["symbol"]]
            row.update(value=value, change=change, status="OBSERVED", observation_date="2026-11-10")
    return rows


def snapshot(instrument, n=120):
    candles = tuple(Candle((date.today() - timedelta(days=n - 1 - i)).isoformat(), 100 + i, 102 + i, 99 + i, 101 + i,
                           1000 + i) for i in range(n))
    return MarketSnapshot(ChartRequest(instrument, "1d", n, adjusted=True), candles, None,
                          fetched_at="2026-11-10T01:00:00+00:00", source="KIS")


class FakeRouter:
    def __init__(self):
        self.calls, self.last_attempts = [], ()

    def load(self, request):
        self.calls.append(request.instrument.code)
        return snapshot(request.instrument)


class ResearchHomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ("requests.sessions.Session.request", "core.market.routing._yahoo_frame",
                       "core.ficc.data.load_series"):
            deny = patch(target, side_effect=AssertionError("Network forbidden"))
            deny.start()
            self.addCleanup(deny.stop)
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.settings = QSettings(os.path.join(folder.name, "prefs.ini"), QSettings.Format.IniFormat)
        self.store = WatchlistStore(self.settings, defaults=[SAMSUNG, APPLE])
        self.router = FakeRouter()
        self.directory = SymbolDirectory(master_loader=Mock(side_effect=AssertionError("No master download")))
        self.market_loader = Mock(side_effect=AssertionError("Automatic market refresh"))

    def window(self, language="ko", width=1440, **kwargs):
        w = ResearchWindow(auto_refresh=False, language=language, market_loader=self.market_loader,
                           symbol_directory=self.directory, watchlist_store=self.store,
                           card_router_factory=lambda: self.router, **kwargs)
        w.resize(width, 900)
        w.show()
        w.navigate("home")
        self.drain()

        def close():
            with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
                w.close()
            w.deleteLater()
        self.addCleanup(close)
        return w

    def drain(self, rounds=6):
        for _ in range(rounds):
            self.app.processEvents()
            QTest.qWait(5)

    def wait(self, predicate, seconds=5):
        end = time.monotonic() + seconds
        while time.monotonic() < end and not predicate():
            self.app.processEvents()
            time.sleep(0.01)
        self.assertTrue(predicate())

    def with_rows(self, w):
        w.session.finish_market_refresh(observed_rows())
        w.refresh_views()
        self.drain()

    # Layout ------------------------------------------------------------------------------------
    def test_home_is_cards_chart_watchlist_research_then_a_closed_quotes_table(self):
        w = self.window()
        page = w.stack.widget(w.route_indices["home"]).widget()
        top = lambda widget: widget.mapTo(page, widget.rect().topLeft()).y()
        hv = w.home_view
        order = [top(hv.strip), top(hv.chart), top(hv.grid), top(w.count_labels[0]), top(w.home_chart),
                 top(w.quotes_fold)]
        self.assertEqual(order, sorted(order))
        self.assertEqual(len(hv.cards), 6)
        self.assertEqual([c.info.symbol for c in hv.cards.values()], [info.symbol for info in HOME_MARKETS])
        # The table is the window's live-quote table, still wired, but folded away under its own title.
        self.assertIs(w.home_markets, w.watchlist.table)
        self.assertEqual(w.home_markets.rowCount(), 12)
        self.assertFalse(w.quotes_fold.expanded())
        self.assertFalse(w.watchlist.isVisible())
        self.assertEqual(w.quotes_fold.toggle.text(), "전체 시세 표")
        w.quotes_fold.toggle.click()
        self.drain()
        self.assertTrue(w.watchlist.isVisible())
        w.set_language("en")
        self.drain()
        self.assertEqual(w.quotes_fold.toggle.text(), "All quotes table")
        # Roomy: the chart is about half as tall as it is wide, never a flat strip.
        self.assertGreaterEqual(hv.chart.height(), min(home_view.CHART_MAX_HEIGHT, round(hv.chart.width() * 0.5)) - 1)
        self.assertGreaterEqual(hv.chart.height(), home_view.CHART_MIN_HEIGHT)

    def test_four_cards_on_a_wide_window_fewer_when_narrow_and_arrows_page_through_them(self):
        w = self.window(width=1440)
        hv = w.home_view
        self.assertEqual(hv.strip.visible, 4)
        self.assertEqual(hv.strip.shown(), [0, 1, 2, 3])
        self.assertFalse(hv.previous_button.isEnabled())
        self.assertTrue(hv.next_button.isEnabled())
        hv.next_button.click()
        self.wait(lambda: hv.strip.animation.state() != hv.strip.animation.State.Running)
        self.assertEqual(hv.strip.shown(), [2, 3, 4, 5])  # the last page is always full
        self.assertFalse(hv.next_button.isEnabled())
        self.assertTrue(hv.previous_button.isEnabled())
        bitcoin = hv.cards["BTC-USD"]
        self.assertGreaterEqual(bitcoin.mapTo(hv.strip, bitcoin.rect().topLeft()).x(), 0)
        self.assertLessEqual(bitcoin.mapTo(hv.strip, bitcoin.rect().bottomRight()).x(), hv.strip.width())
        hv.previous_button.click()
        self.assertEqual(hv.strip.shown(), [0, 1, 2, 3])
        w.resize(1000, 900)
        self.drain()
        self.assertLess(hv.strip.visible, 4)
        self.assertEqual(hv.strip.visible, card_columns(hv.strip.width()))
        self.assertEqual(card_columns(1200), 4)
        self.assertEqual(card_columns(500), 2)

    def test_keyboard_moves_the_selection_and_pages_to_it(self):
        w = self.window()
        hv = w.home_view
        self.assertEqual(hv.selected, "^KS11")  # KOSPI selected by default (owner's reference)
        first = hv.cards["^KS11"]
        for _ in range(3):
            QTest.keyClick(hv.cards[hv.selected], Qt.Key.Key_Right)
        self.assertEqual(hv.selected, "VIXCLS")
        self.assertIn(4, hv.strip.shown())
        self.assertTrue(hv.cards["VIXCLS"].property("selected"))
        self.assertFalse(first.property("selected"))
        QTest.keyClick(hv.cards[hv.selected], Qt.Key.Key_Home)
        self.assertEqual(hv.selected, "^GSPC")
        self.assertIn(0, hv.strip.shown())
        QTest.mouseClick(hv.cards["^KS11"], Qt.MouseButton.LeftButton)
        self.assertEqual(hv.selected, "^KS11")
        self.assertEqual(hv.chart_name.text(), "코스피 종합지수")

    # Cards -------------------------------------------------------------------------------------
    def test_cards_show_value_unit_and_signed_change_in_korean_tones(self):
        w = self.window()
        hv = w.home_view
        for card in hv.cards.values():
            self.assertEqual(card.value.text(), "—")
            self.assertEqual(card.state.text(), "조회 전")
        self.with_rows(w)
        spx, kospi, won, yield10 = (hv.cards[s] for s in ("^GSPC", "^KS11", "DEXKOUS", "DGS10"))
        self.assertEqual((spx.value.text(), spx.unit.text(), spx.change.text()), ("5,871.42", "POINT", "+0.84%"))
        self.assertEqual(spx.change.property("tone"), "up")
        self.assertEqual((kospi.name.text(), kospi.change.text(), kospi.change.property("tone")),
                         ("코스피 종합지수", "-1.12%", "down"))
        self.assertEqual((won.value.text(), won.unit.text()), ("1,387.50", "KRW"))
        self.assertEqual((yield10.unit.text(), yield10.change.text()), ("%", "-3.00 bp"))  # yields move in bp
        self.assertFalse(spx.state.isVisible())
        # Provider and observation date stay in the tooltip, not on the card.
        shown = " ".join(label.text() for label in spx.findChildren(QLabel) if label.isVisible())
        self.assertNotIn("YFINANCE", shown)
        self.assertFalse(re.search(r"\d{4}-\d{2}-\d{2}", shown))
        self.assertIn("YFINANCE", spx.toolTip())
        self.assertIn("2026-11-10", spx.toolTip())
        # The rise colour is the window's Korean rise colour.
        spx.change.ensurePolished()
        self.assertEqual(spx.change.palette().windowText().color().name(), "#c8343d")
        w.set_language("en")
        self.drain()
        self.assertEqual((spx.unit.text(), kospi.name.text()), ("PTS", "KOSPI Composite"))
        texts = [label.text() for label in hv.findChildren(QLabel)]
        self.assertFalse([t for t in texts if re.search("[가-힣]", t)], texts)

    # The chart --------------------------------------------------------------------------------
    def test_automatic_refresh_off_fetches_nothing_and_says_so(self):
        loader = SeriesLoader()
        with patch("quantgen_desktop.jobs.Jobs.start", side_effect=AssertionError("unexpected request")):
            w = self.window()
            hv = w.home_view
            hv.history_loader = loader
            hv.select("^KS11")
            hv.page(1)
            w.set_language("en")
            w.change_theme(1)
            self.drain()
        self.assertEqual(loader.calls, [])
        self.assertEqual(self.router.calls, [])
        self.market_loader.assert_not_called()
        self.assertEqual(hv.chart.values, ())
        self.assertIn("Automatic refresh is off", hv.chart.message)
        self.assertIn("press Refresh", hv.chart.message)

    def test_refresh_loads_the_selected_markets_closes_off_the_ui_thread_from_its_own_provider(self):
        loader = SeriesLoader()
        w = self.window()
        self.with_rows(w)
        hv = w.home_view
        hv.history_loader = loader
        hv.select("DEXKOUS")
        w.market_loader = lambda: observed_rows()
        hv.refresh_button.click()
        self.wait(lambda: not hv.jobs.busy and "DEXKOUS" in hv.histories and not w.jobs.busy)
        self.assertEqual(loader.calls, [("DEXKOUS", "fred", home_view.HISTORY_DAYS)])
        self.assertNotIn(threading.get_ident(), loader.threads)
        history = hv.histories["DEXKOUS"]
        self.assertTrue(history.ok)
        self.assertEqual(history.source, "FRED")
        # Six months of a year's daily closes by default; the range buttons crop without fetching.
        self.assertEqual(hv.chart.dates[-1], "2026-11-10")
        self.assertEqual(hv.chart.dates[0], "2026-05-11")
        hv.range_buttons["1m"].click()
        self.assertEqual(hv.chart.dates[0], "2026-10-10")
        hv.range_buttons["1y"].click()
        self.assertEqual(len(hv.chart.values), 300)
        self.assertEqual(len(loader.calls), 1)
        self.assertTrue(hv.chart_period.isVisible())
        self.assertIn("1년 변동 +", hv.chart_period.text())
        self.assertEqual(hv.chart_period.property("tone"), "up")
        self.assertEqual(hv.chart_value.text(), "1,387.50")
        self.assertIn("FRED", hv.chart_value.toolTip())
        hv.chart.grab()  # paints with data, hover included
        hv.chart.hover = 10
        hv.chart.grab()
        # Switching language re-renders the chart text only.
        w.set_language("en")
        self.drain()
        self.assertEqual(hv.chart_name.text(), "US dollar / Korean won")
        self.assertEqual(len(loader.calls), 1)
        # Another card: nothing loads by itself with automatic refresh off.
        hv.select("BTC-USD")
        self.drain()
        self.assertEqual(len(loader.calls), 1)
        self.assertIn("Automatic refresh is off", hv.chart.message)

    def test_failures_keep_only_authored_reasons_and_the_last_good_chart(self):
        stamp = "2026-11-10T00:00:00+00:00"
        info = HOME_MARKETS[1]
        secret = Mock(side_effect=RuntimeError("HTTP 403 https://example.invalid/?apikey=SECRET"))
        failed = load_market_history(info, loader=secret)
        self.assertEqual((failed.ok, failed.reason), (False, "access_denied"))
        self.assertNotIn("SECRET", repr(failed))
        fallback = load_market_history(info, loader=lambda s, source, days: series(s, "synthetic", days))
        self.assertEqual(fallback.reason, "invalid_response")  # a fallback is not this market's data
        unordered = lambda s, source, days: SimpleNamespace(source=source, dates=["2026-11-02", "2026-11-01"],
                                                            values=[1.0, 2.0])
        self.assertEqual(load_market_history(info, loader=unordered).reason, "invalid_response")
        empty = lambda s, source, days: SimpleNamespace(source=source, dates=[], values=[])
        self.assertEqual(load_market_history(info, loader=empty).reason, "no_observations")
        future = lambda s, source, days: series(s, source, days, last=date(2030, 1, 1))
        self.assertEqual(load_market_history(info, loader=future, today=date(2026, 11, 10)).reason, "invalid_response")
        w = self.window()
        hv = w.home_view
        hv.history_loader = secret
        hv.ensure_history(manual=True)
        self.wait(lambda: not hv.jobs.busy and hv.selected in hv.histories)
        self.assertEqual(hv.chart.values, ())
        self.assertIn("일별 종가를 불러오지 못했습니다 (권한 확인)", hv.chart.message)
        good = SeriesLoader()
        hv.history_loader = good
        hv.ensure_history(manual=True)
        self.wait(lambda: not hv.jobs.busy and hv.histories[hv.selected].ok)
        self.assertTrue(hv.chart.values)
        hv.history_loader = secret
        hv.ensure_history(manual=True)
        self.wait(lambda: not hv.jobs.busy and hv.selected in hv.failures)
        self.assertTrue(hv.chart.values)  # the last good chart stays
        self.assertTrue(hv.chart_status.isVisible())
        self.assertIn("갱신 실패 (권한 확인)", hv.chart_status.text())
        shown = " ".join(label.text() for label in hv.findChildren(QLabel)) + hv.chart.message
        self.assertNotIn("SECRET", shown)
        self.assertNotIn("example.invalid", shown)
        self.assertEqual(crop(MarketHistory("X", reason="no_observations", loaded_at=stamp), "6m"), ((), ()))

    def test_automatic_loading_reads_once_when_shown_and_again_for_each_new_card(self):
        loader = SeriesLoader()
        view = HomeView(store=WatchlistStore(None, defaults=[]), card_router_factory=lambda: self.router,
                        history_loader=loader, auto_load=True)
        self.addCleanup(view.deleteLater)
        view.resize(1200, 1400)
        view.show()
        self.wait(lambda: loader.calls and not view.jobs.busy)
        self.assertEqual(loader.calls, [("^KS11", "yfinance", home_view.HISTORY_DAYS)])  # KOSPI first
        view.select("VIXCLS")
        self.wait(lambda: len(loader.calls) == 2 and not view.jobs.busy)
        self.assertEqual(loader.calls[1][:2], ("VIXCLS", "fred"))
        view.select("^KS11")  # loaded recently: no second request
        self.drain()
        self.assertEqual(len(loader.calls), 2)
        self.assertTrue(view.chart.values)
        for symbol, provider in PROVIDERS.items():
            self.assertEqual(view.infos[symbol].provider, provider)
        view.hide()
        view.stop()

    # Watchlist on Home --------------------------------------------------------------------------
    def test_watchlist_cards_live_on_home_and_open_the_stock_on_markets(self):
        w = self.window()
        grid = w.home_view.grid
        self.assertTrue(grid.isVisible())
        self.assertIs(grid.store, w.watchlist_store)
        self.assertIs(w.markets_view.store, w.watchlist_store)
        self.assertEqual([card.instrument for card in grid.cards.values()], [SAMSUNG, APPLE])
        self.assertEqual(self.router.calls, [])  # automatic refresh off: nothing loads by itself
        self.assertTrue(grid.refresh(manual=True))
        self.wait(lambda: not grid.jobs.busy and all(c.result for c in grid.cards.values()))
        self.assertEqual(self.router.calls[:2], ["005930", "AAPL"])
        apple = grid.cards[("overseas_stock", "AAPL", "NAS")]
        QTest.mouseClick(apple, Qt.MouseButton.LeftButton)
        self.drain()
        self.assertIs(w.stack.currentWidget(), w.stack.widget(w.route_indices["markets"]))
        self.assertTrue(w.markets_view.showing_stock())
        self.assertEqual(w.markets_view.stock.instrument, APPLE)
        w.navigate("home")
        self.store.remove(SAMSUNG)
        self.assertEqual(list(grid.cards), [("overseas_stock", "AAPL", "NAS")])
        w.home_view.add_button.click()
        self.drain()
        self.assertIs(w.stack.currentWidget(), w.stack.widget(w.route_indices["markets"]))

    def test_research_sections_keep_their_attributes_and_dark_mode_follows_the_window(self):
        w = self.window()
        self.assertEqual([label.text() for label in w.count_labels], ["0", "0", "0"])
        self.assertIsNotNone(w.home_chart)
        self.assertIn("분석을 실행하면", w.home_summary.text())
        hv = w.home_view
        w.change_theme(1)
        self.drain()
        self.assertEqual(hv.colors, w.colors)
        self.assertIn(w.colors.surface, hv.styleSheet())
        self.assertTrue(hv.chart.dark)
        self.assertTrue(hv.grid.dark)
        w.change_theme(0)
        self.drain()
        self.assertFalse(hv.chart.dark)
        self.assertIn(w.colors.surface, hv.styleSheet())

    def test_quotes_fold_toggle_shows_a_focus_line_without_changing_its_look(self):
        # 2026-11-11 compliance follow-up (14-contrast, 15-keyboard): the "전체 시세 표" toggle took Tab focus but
        # its own sheet set `border: 0px` with no :focus rule, so focus was invisible. Now Home's 1px accent line.
        from PyQt6.QtGui import QColor
        from core.theme import DARK, LIGHT
        for colors in (LIGHT, DARK):
            sheet = home_view.fold_stylesheet(colors)
            rule = re.search(r"QToolButton#homeFoldToggle:focus \{([^}]*)\}", sheet)
            self.assertIsNotNone(rule)
            self.assertIn(f"border: 1px solid {colors.accent}", rule.group(1))
            self.assertIn("border: 0px", sheet.split(":focus")[0])  # unfocused: borderless, as before

        def accent_pixels(widget, colour):
            image, target = widget.grab().toImage(), QColor(colour)
            return sum(1 for x in range(image.width()) for y in range(image.height())
                       if max(abs(image.pixelColor(x, y).red() - target.red()),
                              abs(image.pixelColor(x, y).green() - target.green()),
                              abs(image.pixelColor(x, y).blue() - target.blue())) < 8)
        w = self.window()
        w.activateWindow()
        toggle = w.quotes_fold.toggle
        self.assertEqual(toggle.focusPolicy(), Qt.FocusPolicy.TabFocus)  # keyboard focus only, never on click
        for theme in (0, 1):
            w.change_theme(theme)
            self.drain()
            self.assertEqual(w.quotes_fold.colors, w.colors)  # it follows the window, though outside HomeView
            self.assertIn(w.colors.accent, toggle.styleSheet())
            w.home_view.add_button.setFocus(Qt.FocusReason.TabFocusReason)
            self.drain(2)
            plain, size = accent_pixels(toggle, w.colors.accent), toggle.size()
            self.assertEqual(plain, 0)
            toggle.setFocus(Qt.FocusReason.TabFocusReason)
            self.drain(2)
            self.assertTrue(toggle.hasFocus())
            self.assertGreater(accent_pixels(toggle, w.colors.accent), size.width() + size.height())
            self.assertEqual(toggle.size(), size)  # the line does not resize the toggle
            QTest.keyClick(toggle, Qt.Key.Key_Space)
            self.drain(2)
            self.assertTrue(w.quotes_fold.expanded())
            toggle.click()
            self.drain(2)


if __name__ == "__main__":
    unittest.main()
