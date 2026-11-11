"""Native stock detail view (owner requests 2026-11-11, UI-D8), offscreen with offline fixtures.

Owner, verbatim: "검색해서 한 차트를 구체적으로 볼때에는, 해당 차트로 화면을 거의 가득채워도 가능해" · "스크롤로
차트좌우이동이 가능한데, 이거 그냥 막아버리고 pc기준 좌우화살표로 차트 좌우 확인할수있게 변경해줘" · "지표같은건 화살표로
접고펴고 할수잇게 해야하고, 우리는 이 ui를 기본으로 주린이들이 읽기 쉽게 하는 가이드를 화면에 잘 녹여야해" · "그냥 좌측에
존나큰차트 존나크게, 이런 공간 부족해서 스크롤이 필요한 메뉴들은 오른쪽으로 빼서 간소화" · "오른쪽의 스크롤 필요한 메뉴들은
움직이는거고, 차트쪽은 스크롤로 위아래 이동이 안되는거야. 오른쪽만 움직이는거지 스크롤이".

Covered: layout regions (large chart left, one right column), the page lock, the inert wheel over the chart, arrow
panning through `end`, the period chips, the folding indicator picker with availability reasons, beginner readings
that follow the selected candle in Korean and English, the right column scrolling by itself, focus mode, honest
market state, no fetch with automatic refresh off, and language/theme switches without a refetch (dark included).
Review fixes: an interval choice then another stock, '더 보기' through refreshes, unchecked saved settings, chart
focus on open, the loading and failed-load panels, the 전체 notice, Back's page position, the rail's search and the
side watchlist stopping when hidden.
Offline: every provider is a fake; HTTP and Yahoo attempts fail the test.
"""
from __future__ import annotations

import math
import os
import re
import tempfile
import time
import unittest
from datetime import date, timedelta
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import dotenv

with patch.object(dotenv, "load_dotenv", return_value=False):
    from quantgen_desktop.app import ResearchWindow
from PyQt6.QtCore import QPoint, QPointF, QSettings, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QAbstractButton, QApplication, QLabel
from core.market.directory import SymbolDirectory
from core.market.models import Candle, ChartRequest, Instrument, MarketQuote, MarketSnapshot
from core.research.stock_profile import build_profile

APP = QApplication.instance() or QApplication([])
SAMSUNG, HYNIX = Instrument("domestic_stock", "005930"), Instrument("domestic_stock", "000660")
KAKAO, APPLE = Instrument("domestic_stock", "035720"), Instrument("overseas_stock", "AAPL", "NAS")
HANGUL = re.compile("[가-힣]")
TAGS = re.compile("<[^>]+>")


def candles(code, n, interval="1d"):
    start = {"005930": 71000, "000660": 190000, "035720": 41000, "AAPL": 180.0}.get(code, 1000)
    out, day = [], date(2026, 11, 10)
    days = []
    while len(days) < n:
        if day.weekday() < 5:
            days.append(day)
        day -= timedelta(days=7 if interval == "1w" else 1)
    for i, d in enumerate(reversed(days)):
        base = start * (1 + 0.06 * math.sin(i / 17) + 0.02 * math.sin(i / 5) + i * 0.0004)
        o, c = base * (1 + 0.004 * math.sin(i)), base * (1 + 0.005 * math.cos(i * 1.3))
        out.append(Candle(d.isoformat(), o, max(o, c) * 1.006, min(o, c) * 0.994, c, 9e6 + 3e6 * math.sin(i / 6)))
    return tuple(out)


class Service:
    """The KIS chart service the pane reads; `source` switches the snapshots to a fallback provider."""

    def __init__(self):
        self.calls, self.source = [], "KIS REST"

    def load(self, request):
        self.calls.append(request)
        data = candles(request.instrument.code, min(400, request.limit), request.interval)
        last, prev = data[-1], data[-2]
        stamp = "2026-11-10T06:20:03+00:00"
        quote = MarketQuote(request.instrument, price=last.close, change=last.close - prev.close,
                            change_pct=(last.close / prev.close - 1) * 100, volume=last.volume, market_time=stamp,
                            received_at=stamp, source=self.source)
        return MarketSnapshot(request, data, quote, fetched_at=stamp, source=self.source)


class Stream:
    def __init__(self):
        self.started = self.stopped = False

    def start(self, instrument, on_tick, on_status):
        self.started = True
        on_status("SUBSCRIBED")

    def stop(self):
        self.stopped = True


class StockDetailTests(unittest.TestCase):
    def setUp(self):
        for target in ("requests.sessions.Session.request", "core.market.routing._yahoo_frame"):
            deny = patch(target, side_effect=AssertionError("Network forbidden"))
            deny.start(); self.addCleanup(deny.stop)
        folder = tempfile.TemporaryDirectory(); self.addCleanup(folder.cleanup)
        self.settings = QSettings(os.path.join(folder.name, "prefs.ini"), QSettings.Format.IniFormat)
        self.provider = Mock(side_effect=AssertionError("Provider forbidden"))
        self.directory = SymbolDirectory(master_loader=Mock(side_effect=AssertionError("No master download")))
        self.card_calls, self.profiles = [], []

        test = self

        class CardRouter:
            last_attempts = ()

            def load(self, request):
                test.card_calls.append(request)
                return Service().load(request)

        def profile_loader(instrument):
            self.profiles.append(instrument)
            data = candles(instrument.code, 260)
            last = data[-1]
            days = [c.timestamp[:10] for c in data[-20:]]
            flows = [{"date": d, "foreign_net_qty": 1000 * (i - 10), "institution_net_qty": -400 * i,
                      "individual_net_qty": 300} for i, d in enumerate(days)]
            shorts = [{"date": d, "short_qty": 2000 + i, "short_ratio_pct": 2 + i / 10, "volume": 1e7}
                      for i, d in enumerate(days)]
            from data.krx.kis_client import Quote
            quote = Quote(instrument.code, "삼성전자", last.close, last.close - data[-2].close,
                          (last.close / data[-2].close - 1) * 100, last.volume, None, last.high, last.low, last.open,
                          as_of="2026-11-10T06:00:00+00:00", source="KIS", per=13.2, eps=6120.0, sector="전기전자",
                          listed_shares=5_969_782_550)
            return build_profile(instrument, candles=data, quote=quote, flows=flows, shorts=shorts,
                                 name="삼성전자" if instrument.code == "005930" else "",
                                 today=date(2026, 11, 10), source="KIS")

        from quantgen_desktop.markets_view import WatchlistStore
        self.store = WatchlistStore(self.settings, defaults=[SAMSUNG, HYNIX, APPLE])
        self.window = ResearchWindow(auto_refresh=False, locale="ko_KR", market_loader=self.provider,
                                     connections_runner=self.provider, symbol_directory=self.directory,
                                     watchlist_store=self.store, card_router_factory=CardRouter,
                                     profile_loader=profile_loader)
        self.window.resize(1440, 900); self.window.show(); self.window.navigate("markets")
        self.service, self.streams = Service(), []
        self.pane = self.window.market_chart
        self.pane.service = self.service
        self.pane.stream_factory = lambda: self.streams.append(Stream()) or self.streams[-1]
        self.view = self.window.markets_view.stock
        self.addCleanup(self.close)
        self.settle()

    def close(self):
        self.pane.stop()
        self.window.hide()
        self.window.deleteLater()
        APP.processEvents()

    def settle(self, rounds=6):
        for _ in range(rounds):
            APP.processEvents()
            QTest.qWait(10)

    def wait(self, predicate, seconds=6):
        end = time.monotonic() + seconds
        while time.monotonic() < end and not predicate():
            APP.processEvents(); time.sleep(0.01)
        self.assertTrue(predicate())

    def open(self, instrument=SAMSUNG, *, load=True, profile=True):
        self.window.markets_view.open_instrument(instrument)
        self.settle()
        if load:
            self.pane.refresh(manual=True)
            self.wait(lambda: self.pane.snapshot is not None and not self.pane.jobs.busy)
        if profile:
            self.view.load_profile()
            self.wait(lambda: self.view.profile is not None and not self.view.jobs.busy)
        self.settle()

    def wheel(self, widget, dx=0, dy=-120):
        event = QWheelEvent(QPointF(20, 20), QPointF(widget.mapToGlobal(QPoint(20, 20))), QPoint(0, 0), QPoint(dx, dy),
                            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
        APP.sendEvent(widget, event)
        return event.isAccepted()

    def visible_texts(self, root):
        out = []
        for widget in [*root.findChildren(QLabel), *root.findChildren(QAbstractButton)]:
            if widget.isVisible() and widget.text():
                out.append(TAGS.sub("", widget.text()))
        return out

    # Layout --------------------------------------------------------------------------------------
    def test_large_chart_left_one_right_column_and_the_page_never_scrolls(self):
        self.open()
        view, body = self.view, self.view.body
        page = self.window.stack.currentWidget()
        chart, side = view.chart_column.geometry(), view.side.geometry()
        self.assertTrue(view.side.isVisible())
        self.assertGreaterEqual(side.x(), chart.right() + 12)          # the column sits beside the chart
        self.assertTrue(340 <= side.width() <= 380, side.width())
        self.assertGreaterEqual(chart.width(), 780)
        self.assertGreaterEqual(self.pane.chart.height(), 700)          # most of the window height
        self.assertEqual(chart.height(), body.height())
        self.assertLess(view.toolbar.geometry().bottom(), body.geometry().top())
        self.assertGreater(view.periods.mapTo(view, QPoint()).y(), self.pane.chart.mapTo(view, QPoint()).y())
        # No card grid under the chart: the profile sections live in the right column.
        for section in view.section_panels:
            self.assertTrue(view.side.isAncestorOf(section))
        # Page lock: no page scroll bar, the view is the viewport's height and the page is held at its top.
        self.assertEqual(page.verticalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.assertEqual(view.height(), page.viewport().height())
        self.assertEqual(page.verticalScrollBar().value(), view.lock.target)
        page.verticalScrollBar().setValue(0)                            # e.g. a deferred scroll-to-top
        self.assertEqual(page.verticalScrollBar().value(), view.lock.target)
        # 1000x700: the column opens over the chart from the toolbar instead of squeezing it.
        self.window.resize(1000, 700); self.settle()
        self.assertFalse(view.side.isVisible())
        self.assertEqual(view.chart_column.width(), body.width())
        view.side_button.click(); self.settle()
        self.assertTrue(view.side.isVisible())
        self.assertTrue(view.side.geometry().intersects(view.chart_column.geometry()))
        QTest.keyClick(self.pane.chart, Qt.Key.Key_Escape); self.settle()
        self.assertFalse(view.side.isVisible())
        self.assertEqual(view.height(), page.viewport().height())
        # Leaving the stock restores the list's own scrolling.
        view.back_button.click(); self.settle()
        self.assertEqual(page.verticalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.assertEqual(view.lock.scroll, None)

    def test_wheel_over_the_chart_does_nothing_and_only_the_right_column_scrolls(self):
        self.open()
        page = self.window.stack.currentWidget().verticalScrollBar()
        state = lambda: (self.pane.visible_bars.value(), self.pane._end, self.pane._cursor, page.value())
        before = state()
        for dx, dy in ((0, -120), (0, 120), (-120, 0), (120, 0)):
            self.assertTrue(self.wheel(self.pane.chart, dx, dy))
            self.settle(2)
            self.assertEqual(state(), before)
        for widget in (self.view.toolbar, self.view.periods, self.view.interval_combo):
            self.wheel(widget)
            self.settle(2)
            self.assertEqual(page.value(), self.view.lock.target)
        side = self.view.side.stock_scroll
        self.assertGreater(side.verticalScrollBar().maximum(), 0)
        start = side.verticalScrollBar().value()
        self.wheel(side.viewport(), dy=-240)
        self.settle(2)
        self.assertGreater(side.verticalScrollBar().value(), start)
        self.assertEqual(state(), before)

    # Keyboard ------------------------------------------------------------------------------------
    def test_arrows_pan_through_end_and_keys_zoom(self):
        self.open(profile=False)
        p, chart = self.pane, self.pane.chart
        n = len(p.snapshot.candles)
        self.assertEqual((p.period, p.visible_bars.value(), p._end, p._cursor), ("6M", 126, None, n - 1))
        self.assertTrue(self.view.periods.buttons["6M"].isChecked())
        chart.setFocus()
        p.move_cursor(n - 126)                     # the window's first candle
        QTest.keyClick(chart, Qt.Key.Key_Left)     # one more to the left pans the window by one bar
        self.assertEqual((p._cursor, p._end, chart.end, p.visible_bars.value()), (n - 127, n - 2, n - 2, 126))
        self.assertFalse(self.view.periods.buttons["6M"].isChecked())  # a manual pan leaves the period's view
        QTest.keyClick(chart, Qt.Key.Key_Left, Qt.KeyboardModifier.ShiftModifier)
        self.assertEqual((p._end, p._cursor), (n - 12, n - 137))
        self.assertEqual(chart.layout_info.stop - 1, n - 12)
        QTest.keyClick(chart, Qt.Key.Key_Home)
        self.assertEqual((p._cursor, p.window()), (0, (0, 126)))
        QTest.keyClick(chart, Qt.Key.Key_End)
        self.assertEqual((p._cursor, p._end), (n - 1, None))
        QTest.keyClick(chart, Qt.Key.Key_Plus)
        self.assertEqual(p.visible_bars.value(), round(126 * 0.8))
        QTest.keyClick(chart, Qt.Key.Key_Minus); QTest.keyClick(chart, Qt.Key.Key_Minus)
        self.assertGreater(p.visible_bars.value(), 126)
        QTest.keyClick(chart, Qt.Key.Key_0)
        self.assertEqual((p.visible_bars.value(), p._end), (126, None))
        self.assertTrue(self.view.periods.buttons["6M"].isChecked())
        self.view.periods.left.click()
        self.assertEqual(p._end, n - 11)
        self.view.overlays.latest_button.click()
        self.assertIsNone(p._end)
        self.assertEqual(len(self.service.calls), 1)  # moving never reloads

    def test_daily_periods_share_one_request_and_five_years_reload_weekly(self):
        self.open(profile=False)
        self.assertEqual((self.service.calls[0].interval, self.service.calls[0].limit), ("1d", 400))
        for key, shown in (("1M", 22), ("3M", 63), ("1Y", 252), ("YTD", None)):
            self.view.periods.buttons[key].click(); self.settle(2)
            self.assertEqual(len(self.service.calls), 1, key)
            if shown:
                self.assertEqual(self.pane.visible_bars.value(), shown)
            self.assertTrue(self.view.periods.buttons[key].isChecked())
        self.view.periods.buttons["5Y"].click()
        self.wait(lambda: len(self.service.calls) == 2 and not self.pane.jobs.busy)
        self.assertEqual((self.service.calls[-1].interval, self.service.calls[-1].limit), ("1w", 400))
        self.assertEqual(self.settings.value("markets/detail/period"), "5Y")

    def test_intraday_periods_need_a_ready_provider(self):
        from core.market.routing import ChartRouter

        class Offline:
            name = "KIS"

            def ready(self):
                return False, ("KIS_APP_KEY",)

            def supports(self, request):
                return True

        class Yahoo:
            name = "Yahoo Finance"

            def ready(self):
                return True, ()

            def supports(self, request):
                return request.interval in ("1d", "1w", "1M")

        self.pane.router = ChartRouter(Offline(), (Yahoo(),))
        self.open(load=False, profile=False)
        for key in ("1D", "5D"):
            button = self.view.periods.buttons[key]
            self.assertFalse(button.isEnabled())
            self.assertIn("KIS", button.toolTip())
        self.assertTrue(self.view.periods.buttons["1Y"].isEnabled())
        self.assertFalse(self.view.choose_period("1D"))

    # Indicators ----------------------------------------------------------------------------------
    def test_indicator_picker_folds_toggles_and_explains_availability(self):
        from core.education.indicators import STUDIES, CATEGORIES
        from core.education.study_guide import availability_text, guide
        from quantgen_desktop.stock_detail_style import polite
        self.open(profile=False)
        view, picker = self.view, self.view.picker
        view.show_indicators(); self.settle()
        self.assertTrue(picker.isVisible())
        self.assertEqual(tuple(picker.groups), CATEGORIES)
        rows = picker.rows()
        self.assertEqual(set(rows), {s.key for s in STUDIES})
        self.assertEqual(len(rows), 27)
        momentum = picker.groups["momentum"]
        self.assertTrue(momentum.is_open)                    # it holds RSI, which is on
        QTest.mouseClick(momentum.head, Qt.MouseButton.LeftButton); self.settle(2)
        self.assertFalse(momentum.body.isVisible())
        momentum.head.setFocus()
        QTest.keyClick(momentum.head, Qt.Key.Key_Space); self.settle(2)
        self.assertTrue(momentum.body.isVisible())
        self.assertGreaterEqual(rows["rsi"].height(), 56)
        rows["stoch"].switch.click(); self.settle(2)
        self.assertIn("stoch", view.studies)
        self.assertIn("stoch", self.pane.selected_indicators())
        self.assertIn("stoch", [key for key, _, _ in self.pane.chart.layout_info.panels])
        self.assertIn("stoch", self.settings.value("markets/detail/indicators"))
        # Availability: VWAP on a daily chart, supply/demand before the profile's KIS rows arrive.
        self.assertEqual(rows["vwap"].reason, "intraday_only")
        self.assertFalse(rows["vwap"].switch.isEnabled())
        # The view shows the engine's formal reasons in 해요체 (owner wording rule, spec 6).
        self.assertEqual(rows["vwap"].desc.toolTip(), polite(availability_text("intraday_only", "ko")))
        self.assertTrue(rows["vwap"].desc.toolTip().endswith("표시해요."))
        self.assertEqual(rows["investor_flow"].reason, "no_supply_data")
        view.load_profile()
        self.wait(lambda: view.profile is not None and not view.jobs.busy)
        self.settle()
        self.assertEqual(rows["investor_flow"].reason, "")
        # ⓘ unfolds the beginner guide with the reading now.
        rows["rsi"].info.click(); self.settle(2)
        self.assertTrue(rows["rsi"].guide.isVisible())
        texts = [body.text() for _, body in rows["rsi"].guide_parts]
        self.assertEqual(texts[:3], [polite(guide("rsi", "ko").what), polite(guide("rsi", "ko").how),
                                     polite(guide("rsi", "ko").caution)])
        self.assertTrue(texts[3])
        # A panel's x turns it off; its info button opens that guide.
        view.overlays.heads["stoch"].off.click(); self.settle(2)
        self.assertNotIn("stoch", view.studies)
        self.assertFalse(rows["stoch"].is_checked())
        picker._emit(())
        self.assertEqual(self.pane.selected_indicators(), ())
        picker.starter_button.click()
        self.assertEqual(view.studies, ("sma", "volume_ma", "rsi"))
        picker.search.setText("일목"); self.settle(2)
        self.assertTrue(rows["ichimoku"].isVisible())
        self.assertFalse(rows["rsi"].isVisible())
        picker.search.setText("없는지표"); self.settle(2)
        self.assertTrue(picker.no_match.isVisible())

    def test_readings_follow_the_selected_candle_in_both_languages(self):
        from core.education.study_guide import study_reading
        from quantgen_desktop.stock_detail_style import polite
        self.open()
        p, view = self.pane, self.view
        bars = view.engine_bars()
        head = view.overlays.heads["rsi"]
        self.assertTrue(head.isVisible())
        n = len(bars)
        # The engine writes 합니다체; the view shows its readings in 해요체 (owner wording rule, spec 6). English as is.
        self.assertEqual(head.full, polite(study_reading("rsi", bars, n - 1, language="ko", supply=p.supply)))
        self.assertNotIn("니다", head.full)
        p.move_cursor(n - 40); self.settle(2)
        self.assertEqual(head.full, polite(study_reading("rsi", bars, n - 40, language="ko", supply=p.supply)))
        self.assertIn(p.snapshot.candles[n - 40].timestamp[:10], view.overlays.ohlc.date.text())
        self.assertIn("시가", view.overlays.ohlc.keys["o"].text())
        self.assertIn("처음 거래된 가격", view.overlays.ohlc.keys["o"].toolTip())
        from quantgen_desktop.stock_detail import korean_amount
        volume = p.snapshot.candles[n - 40].volume
        self.assertEqual(view.overlays.ohlc.values["v"].text(), korean_amount(volume))     # 만, as the legend
        calls = len(self.service.calls)
        self.window.set_language("en"); self.settle()
        self.assertRegex(view.overlays.ohlc.values["v"].text(), r"^[\d.,]+[KMB]?$")
        self.assertEqual(head.full, study_reading("rsi", bars, n - 40, language="en", supply=p.supply))
        overlay_texts = [view.overlays.ohlc, view.overlays.legend, head]
        hangul = [t for w in overlay_texts for t in self.visible_texts(w) if HANGUL.search(t)]
        self.assertEqual(hangul, [])
        self.assertEqual(len(self.service.calls), calls)
        # The right column's 지금 이 차트 and 기술 지표 blocks read the latest candle.
        now = view.side.now
        self.assertEqual([row.topic.text() for row in now.rows], ["Trend", "Strength", "Movement", "Trading"])
        self.assertIn("not a signal to buy or sell", now.disclaimer.text())

    # Right column -------------------------------------------------------------------------------
    def test_symbol_card_sections_and_honest_state(self):
        self.open()
        view, card = self.view, self.view.side.card
        profile = view.profile
        self.assertEqual(view.price.text(), f"{self.pane.snapshot.quote.price:,.0f}")
        self.assertTrue(view.change.text().startswith(("▲", "▼", "–")))
        self.assertAlmostEqual(card.range_bar.position, profile.values["range"]["position"])
        self.assertIn("30일 평균", card.volume_ratio.text())
        self.assertTrue(card.volume_bar.isVisible())
        titles = [section.title.text() for section in view.section_panels]
        self.assertEqual(titles, ["주요 지표", "가격 범위·기간 수익률", "위험", "기술 지표", "공매도·수급"])
        for section in view.section_panels:
            shown = [w for w in section._widgets if w.isVisibleTo(section) and section.body.isVisibleTo(section)]
            rows = len([w for w in shown if w.property("sd") == "rowValue"]) or len(shown)
            self.assertLessEqual(rows, 4, section.title.text())
        risk = view.side.sections["risk"]
        self.assertFalse(risk.is_open)                                  # folded with a digest
        self.assertTrue(risk.head.digest.text())
        risk.head.toggle(); self.settle(2)
        self.assertTrue(risk.more.isVisible())
        self.assertTrue(view.side.unavailable.text().startswith("이 화면에서 제공하지 않는 정보"))
        self.assertEqual(len(view.side.now.rows), 4)
        # Clicking the strength row turns RSI on when it is off.
        view.set_studies(("sma",)); self.settle(2)
        strength = view.side.now.rows[1]
        self.assertEqual(strength.study, "rsi")
        QTest.mouseClick(strength, Qt.MouseButton.LeftButton); self.settle(2)
        self.assertIn("rsi", view.studies)
        # State: a closed market is said so; a fallback snapshot is never presented as KIS.
        with patch("core.markets.trading_state", return_value=("closed", "weekend")):
            view._render_state()
            self.assertEqual(view.state_chip.text(), "○ 장 마감")
        self.service.source = "Yahoo Finance"
        self.pane.refresh(manual=True)
        self.wait(lambda: self.pane.snapshot is not None and self.pane.snapshot.source == "Yahoo Finance"
                  and not self.pane.jobs.busy)
        self.settle()
        self.assertEqual(view.state_chip.text(), "● 지연 자료")
        self.assertIn("KIS 시세가 아니에요", card.state.text())

    def test_watchlist_rows_fold_and_open_a_stock(self):
        self.open(KAKAO, load=False, profile=False)
        watch = self.view.side.watchlist
        self.assertEqual(list(watch.watch.rows), [("domestic_stock", "005930", ""), ("domestic_stock", "000660", ""),
                                                  ("overseas_stock", "AAPL", "NAS")])
        self.assertEqual(self.card_calls, [])                          # nothing loads with automatic refresh off
        watch.refresh(manual=True)
        self.wait(lambda: not watch.jobs.busy and watch.results)
        row = watch.watch.rows[("domestic_stock", "000660", "")]
        self.assertNotEqual(row.price.text(), "—")
        QTest.mouseClick(row, Qt.MouseButton.LeftButton); self.settle()
        self.assertEqual(self.view.instrument, HYNIX)
        self.assertEqual(list(watch.recent_group.rows), [("domestic_stock", "035720", "")])
        self.assertEqual(row.property("current"), "true")
        watch.watch.head.toggle(); self.settle(2)
        self.assertFalse(watch.watch.body.isVisible())

    def test_focus_mode_collapses_the_rail_and_hides_the_column(self):
        self.open(load=False, profile=False)
        w, view = self.window, self.view
        calls = []
        original = w.set_sidebar_collapsed
        w.set_sidebar_collapsed = lambda collapsed, remember=True: (calls.append((collapsed, remember)),
                                                                      original(collapsed, remember=remember))[1]
        view.focus_button.click(); self.settle()
        self.assertTrue(w.sidebar_collapsed)
        self.assertFalse(view.side.isVisible())
        self.assertEqual(view.chart_column.width(), view.body.width())
        self.assertEqual(self.window.stack.currentWidget().verticalScrollBar().value(), view.lock.target)
        view.chart.chart.setFocus()
        QTest.keyClick(view.chart.chart, Qt.Key.Key_F, Qt.KeyboardModifier.ShiftModifier); self.settle()
        self.assertFalse(w.sidebar_collapsed)
        self.assertTrue(view.side.isVisible())
        view.set_focus_mode(True); self.settle()
        view.back_button.click(); self.settle()                         # leaving restores the rail too
        self.assertFalse(w.sidebar_collapsed)
        self.assertEqual(calls, [(True, False), (False, False), (True, False), (False, False)])

    # Data and switching --------------------------------------------------------------------------
    def test_nothing_is_fetched_with_automatic_refresh_off(self):
        self.window.markets_view.open_instrument(SAMSUNG)
        for _ in range(20):
            APP.processEvents(); QTest.qWait(10)
        self.view.choose_period("1Y"); self.view.choose_period("5Y")
        self.view.show_indicators(); self.settle()
        self.assertEqual(self.service.calls, [])
        self.assertEqual(self.card_calls, [])
        self.assertEqual(self.profiles, [])
        self.assertIsNone(self.pane.snapshot)
        self.assertTrue(self.pane.empty_state.isVisible())
        self.assertIn("↺", self.pane.empty_state.text())
        self.assertEqual(self.view.state_chip.text(), "불러오기 전")
        self.provider.assert_not_called()

    def test_language_and_theme_switch_without_a_refetch(self):
        from core.theme import DARK
        self.open()
        self.view.watch_button.click(); self.view.watch_button.click()
        # The column's cards load once with automatic loading on, so a refetch on the switch would be counted.
        watchlist = self.view.side.watchlist
        watchlist.auto_load = True
        self.assertTrue(watchlist.refresh(manual=True))
        self.wait(lambda: not watchlist.jobs.busy); self.settle()
        self.assertGreater(len(self.card_calls), 0)
        counts = (len(self.service.calls), len(self.profiles), len(self.card_calls))
        svg_before = self.pane.chart.layout_info
        self.window.set_language("en"); self.settle()
        self.window.theme.setCurrentIndex(1); self.settle()
        self.assertEqual((len(self.service.calls), len(self.profiles), len(self.card_calls)), counts)
        self.assertTrue(self.view.dark)
        self.assertEqual(self.pane.chart.theme["bg"], DARK.bg)
        self.assertIn(DARK.surface, self.view.styleSheet())
        self.assertIsNot(self.pane.chart.layout_info, svg_before)       # redrawn, not reloaded
        hangul = [t for t in self.visible_texts(self.view) if HANGUL.search(t)]
        self.assertEqual(hangul, [])
        self.assertEqual(self.view.back_button.text(), "← Real-time charts")
        self.assertEqual(self.view.side.sections["key_figures"].title.text(), "Key figures")
        self.view.show_indicators(); self.settle()
        hangul = [t for t in self.visible_texts(self.view.side) if HANGUL.search(t)]
        self.assertEqual(hangul, [])
        self.window.set_language("ko"); self.window.theme.setCurrentIndex(0); self.settle()
        self.assertEqual(self.view.side.sections["key_figures"].title.text(), "주요 지표")
        self.assertEqual((len(self.service.calls), len(self.profiles), len(self.card_calls)), counts)

    # Review fixes (2026-11-11): crash paths, focus, empty states, notices, page position, search ----------------
    def slot_errors(self):
        """Exceptions raised inside Qt slots (PyQt6 aborts the app on them): collected instead, for the test."""
        errors = []
        hook = patch("sys.excepthook", side_effect=lambda kind, value, tb: errors.append(f"{kind.__name__}: {value}"))
        hook.start(); self.addCleanup(hook.stop)
        return errors

    def test_an_interval_choice_then_another_stock_opens_with_the_last_period_chip(self):
        errors = self.slot_errors()
        self.open(profile=False)
        combo = self.view.interval_combo
        index = combo.findData("1w")
        combo.setCurrentIndex(index); self.view._interval_chosen(index); self.settle()
        self.assertIsNone(self.pane.period)                 # the chart left its period: no chip is lit
        self.assertEqual(self.view.period, "6M")            # the last chip is kept for the next stock
        self.window.markets_view.open_instrument(HYNIX); self.settle()
        self.assertEqual((self.view.instrument, self.pane.period), (HYNIX, "6M"))
        self.view.side.watchlist.render()
        row = self.view.side.watchlist.watch.rows[("domestic_stock", "005930", "")]
        QTest.mouseClick(row, Qt.MouseButton.LeftButton); self.settle()
        self.assertEqual(self.view.instrument, SAMSUNG)
        self.assertEqual(errors, [])

    def test_more_in_a_section_keeps_its_reading_blocks_through_every_refresh(self):
        from PyQt6 import sip
        errors = self.slot_errors()
        self.open()
        self.view.set_studies(("sma", "volume_ma", "rsi", "macd", "stoch", "adx")); self.settle()
        tech = self.view.side.sections["technical"]
        tech.set_open(True); self.settle(2)
        self.assertTrue(tech.more.isVisible())
        blocks = [entry for entry in tech._entries if not hasattr(entry, "label")]
        tech.more.click(); self.settle()
        self.assertFalse(any(sip.isdeleted(block) for block in blocks))
        self.assertTrue(all(block.isVisibleTo(tech) for block in blocks))
        self.view._refresh_side(force=True); self.settle()      # a new snapshot or tick
        self.view.side.set_page(1); self.settle(); self.view.side.set_page(0); self.settle()
        self.view.picker.rows()["cci"].switch.click(); self.settle()
        self.window.set_language("en"); self.settle(); self.window.set_language("ko"); self.settle()
        tech = self.view.side.sections["technical"]
        if tech.more.isVisible():
            tech.more.click(); self.settle()                   # 접기
        self.window.markets_view.open_instrument(HYNIX); self.settle()
        self.view.set_studies(()); self.settle()
        self.view.set_studies(("rsi",)); self.settle()
        self.assertEqual(errors, [])

    def test_saved_settings_from_another_build_are_checked(self):
        from quantgen_desktop.stock_detail import StockDetailView
        errors = self.slot_errors()
        view = self.view
        for raw, expected in (('["sma", "renamed_study"]', ("sma",)), ("5", ("sma", "volume_ma", "rsi")),
                              ("not json", ("sma", "volume_ma", "rsi")), ('["gone"]', ("sma", "volume_ma", "rsi"))):
            self.settings.setValue("markets/detail/indicators", raw)
            self.assertEqual(view._stored_studies(), expected, raw)
        for raw in ("bogus", "5", None):
            self.settings.setValue("markets/detail/period", raw)
            self.assertEqual(view._stored_period(), "6M", raw)
        self.settings.setValue("markets/detail/sections", "[1, 2]")
        self.assertTrue(view._section_open("risk", True))
        # A window built over the worst of them still opens stocks.
        self.settings.setValue("markets/detail/indicators", "5")
        self.settings.setValue("markets/detail/period", "bogus")
        other = StockDetailView(self.pane, store=self.store, auto_load=False)
        self.assertEqual((other.studies, other.period), (("sma", "volume_ma", "rsi"), "6M"))
        other.deleteLater(); self.settle()
        self.settings.setValue("markets/detail/indicators", '["sma", "renamed_study"]')
        self.view.studies = self.view._stored_studies()
        self.open()
        self.assertEqual(self.pane.period, "6M")
        self.assertEqual(errors, [])

    def test_opening_a_stock_gives_the_chart_the_keys(self):
        markets = self.window.markets_view
        markets.search.setFocus(); self.settle()
        self.view.auto_load = True
        markets.open_instrument(SAMSUNG); self.settle()
        self.assertIn(APP.focusWidget(), (self.view.chart_column, self.pane.chart))   # even while loading
        self.wait(lambda: self.pane.snapshot is not None and not self.pane.jobs.busy and not self.view.jobs.busy)
        self.settle()
        self.assertIs(APP.focusWidget(), self.pane.chart)
        before = self.pane._cursor
        QTest.keyClick(APP.focusWidget(), Qt.Key.Key_Left); self.settle(2)
        QTest.keyClick(APP.focusWidget(), Qt.Key.Key_Plus); self.settle(2)
        self.assertEqual(self.pane._cursor, before - 1)
        self.assertEqual(markets.search.text(), "")             # nothing was typed into the hidden search box
        self.view.search.setFocus(); self.settle()
        self.view.side.watchlist.render()
        row = self.view.side.watchlist.watch.rows[("domestic_stock", "000660", "")]
        row.setFocus(); QTest.keyClick(row, Qt.Key.Key_Return); self.settle()
        self.assertEqual(self.view.instrument, HYNIX)
        self.assertIn(APP.focusWidget(), (self.view.chart_column, self.pane.chart))
        self.wait(lambda: not self.pane.jobs.busy and not self.view.jobs.busy
                  and not self.view.side.watchlist.jobs.busy)

    def test_loading_and_a_failed_load_show_their_own_chart_panel(self):
        import threading
        self.window.markets_view.open_instrument(SAMSUNG); self.settle()
        self.assertIn("↺", self.pane.empty_state.text())
        gate, load = threading.Event(), self.service.load
        self.service.load = lambda request: (gate.wait(5), load(request))[1]
        self.pane.refresh(manual=True); self.settle()
        self.assertEqual(self.pane.empty_state.text(), "차트를 불러오는 중…")
        self.assertEqual(self.view.state_chip.text(), "불러오는 중…")
        gate.set(); self.wait(lambda: not self.pane.jobs.busy); self.pane.stop(); self.settle()

        def offline(request):
            raise RuntimeError("offline")
        self.service.load = offline
        self.window.markets_view.open_instrument(KAKAO); self.settle()
        self.pane.refresh(manual=True); self.wait(lambda: not self.pane.jobs.busy); self.settle()
        self.assertEqual(self.pane.empty_state.text(), "시세를 불러오지 못했어요.")
        self.assertTrue(self.pane.empty_retry.isVisible())
        self.assertEqual(self.pane.empty_retry.text(), "다시 시도")
        self.assertIn("KIS", self.pane.empty_tried.text())         # what was tried
        self.assertNotIn("불러오지 않았어요", self.pane.empty_state.text())
        self.service.load = load
        self.pane.empty_retry.click(); self.wait(lambda: not self.pane.jobs.busy); self.settle()
        self.assertIsNotNone(self.pane.snapshot)
        self.assertFalse(self.pane.empty_actions.isVisible())

    def test_the_all_period_hides_the_partial_history_notice(self):
        from dataclasses import replace
        load = self.service.load
        self.service.load = lambda request: replace(load(request), note="Partial history: 120 of 400")
        self.open(profile=False)
        self.assertIn("요청한", self.pane.feed_notice.text())         # other periods keep it
        self.view.periods.buttons["ALL"].click(); self.wait(lambda: not self.pane.jobs.busy); self.settle()
        self.assertEqual(self.pane.period, "ALL")
        self.assertNotIn("요청한", self.pane.feed_notice.text())

    def test_back_returns_the_list_to_where_it_was(self):
        from PyQt6.QtWidgets import QWidget
        page = self.window.stack.currentWidget()
        filler = QWidget(); filler.setFixedHeight(3000)            # a long ranking list
        self.window.markets_view.layout().addWidget(filler); self.settle()
        bar = page.verticalScrollBar()
        bar.setValue(600); self.settle()
        self.assertEqual(bar.value(), 600)
        self.open(load=False, profile=False)
        self.assertEqual(bar.value(), self.view.lock.target)
        self.view.back_button.click(); self.settle()
        self.assertEqual(bar.value(), 600)

    def test_the_rail_search_reaches_a_visible_search_while_a_stock_is_open(self):
        self.open(load=False, profile=False)
        markets = self.window.markets_view
        scroll = self.window.stack.currentWidget()
        for size in ((1440, 900), (1000, 700)):
            self.window.resize(*size); self.settle()
            self.view.chart_column.setFocus(); self.settle()
            self.assertTrue(markets.show_category("search")); self.settle()
            focused = APP.focusWidget()
            self.assertTrue(markets.showing_stock())
            self.assertIs(focused, self.view.search, size)
            rect = focused.rect().translated(focused.mapTo(scroll.viewport(), QPoint()))
            self.assertTrue(scroll.viewport().rect().contains(rect), (size, rect))

    def test_the_side_watchlist_stops_loading_when_hidden(self):
        watch = self.view.side.watchlist
        self.open(load=False, profile=False)
        import threading
        watch._cancel = threading.Event()
        cancel = watch._cancel
        self.view.back_button.click(); self.settle()
        self.assertTrue(cancel.is_set())


if __name__ == "__main__":
    unittest.main()
