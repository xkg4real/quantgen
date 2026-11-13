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

    def ctrl_wheel(self, widget, x, dy, y=None, modifiers=Qt.KeyboardModifier.ControlModifier):
        """A wheel turn at chart x (Ctrl held by default); returns whether the widget took it."""
        y = widget.height() / 2 if y is None else y
        event = QWheelEvent(QPointF(x, y), QPointF(widget.mapToGlobal(QPoint(int(x), int(y)))), QPoint(0, 0),
                            QPoint(0, dy), Qt.MouseButton.NoButton, modifiers, Qt.ScrollPhase.NoScrollPhase, False)
        APP.sendEvent(widget, event)
        return event.isAccepted()

    def mouse(self, widget, kind, x, y, held=True):
        """A left-button press, move or release at (x, y) sent straight to `widget`."""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QMouseEvent
        left, none = Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton
        kind = {"press": QEvent.Type.MouseButtonPress, "move": QEvent.Type.MouseMove,
                "release": QEvent.Type.MouseButtonRelease}[kind]
        button = none if kind == QEvent.Type.MouseMove else left
        buttons = left if (kind == QEvent.Type.MouseButtonPress or (kind == QEvent.Type.MouseMove and held)) else none
        event = QMouseEvent(kind, QPointF(x, y), QPointF(widget.mapToGlobal(QPoint(int(x), int(y)))), button, buttons,
                            Qt.KeyboardModifier.NoModifier)
        APP.sendEvent(widget, event)
        return event.isAccepted()

    def visible_texts(self, root):
        out = []
        for widget in [*root.findChildren(QLabel), *root.findChildren(QAbstractButton)]:
            if widget.isVisible() and widget.text():
                out.append(TAGS.sub("", widget.text()))
        return out

    # Layout --------------------------------------------------------------------------------------
    def test_the_right_column_never_moves_sideways_with_seven_digit_prices(self):
        """Owner's PC, 2026-11-12: SK하이닉스 at 1,255,000 KRW put price and change side by side wider than the column, the
        column shifted sideways and both edges were cut. The change now drops under the price and the column stays put."""
        global candles
        real = candles

        def big(code, n, interval="1d"):
            rows = real(code, n, interval)
            scale = 1255000 / 190000 if code == "000660" else 1
            return tuple(Candle(c.timestamp, c.open * scale, c.high * scale, c.low * scale, c.close * scale, c.volume)
                         for c in rows)
        candles = big
        self.addCleanup(lambda: globals().__setitem__("candles", real))
        for size in ((1440, 900), (1280, 800), (1000, 700)):
            self.window.resize(*size); self.settle()
            self.open(HYNIX); self.settle()
            scroll = self.view.side.current_scroll()
            page, bar = scroll.widget(), scroll.horizontalScrollBar()
            self.assertLessEqual(page.minimumSizeHint().width(), scroll.viewport().width(), size)
            self.assertEqual((page.width(), bar.maximum()), (scroll.viewport().width(), 0), size)
            bar.setValue(30); scroll.ensureWidgetVisible(self.view.side.card.change); self.settle(2)
            self.assertEqual(bar.value(), 0, size)  # nothing can shift the column sideways
            card = self.view.side.card
            for label in (card.price, card.change, card.name):
                right = label.mapTo(scroll.viewport(), label.rect().topRight()).x()
                self.assertLessEqual(right, scroll.viewport().width(), (size, label.text()))
                self.assertGreaterEqual(label.mapTo(scroll.viewport(), label.rect().topLeft()).x(), 0, size)

    def test_large_chart_left_one_right_column_and_the_page_never_scrolls(self):
        self.open()
        view, body = self.view, self.view.body
        page = self.window.stack.currentWidget()
        chart, side = view.chart_column.geometry(), view.side.geometry()
        self.assertTrue(view.side.isVisible())
        self.assertGreaterEqual(side.x(), chart.right() + 12)          # the column sits beside the chart
        # Owner 2026-11-12 "차트 가로넓이 살짝만 더넓혀보자": column 335-360 (was 340-380) and page sides 16 (was 24).
        self.assertTrue(335 <= side.width() <= 360, side.width())
        self.assertGreaterEqual(chart.width(), 800)
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
        # 1000x700 (owner R-D9-1, replacing the overlay column): the column stays beside the chart and never over
        # it; the rail folds while the stock is shown to make room and comes back as it was.
        self.assertFalse(self.window.sidebar_collapsed)
        self.window.resize(1000, 700); self.settle(); self.settle()
        self.assertTrue(view.side.isVisible())
        self.assertFalse(view.side.geometry().intersects(view.chart_column.geometry()))
        self.assertGreaterEqual(view.side.x(), view.chart_column.geometry().right() + 12)
        self.assertTrue(self.window.sidebar_collapsed)
        self.assertGreaterEqual(view.chart_column.width(), 540)
        view.side_button.click(); self.settle()                         # hidden: the chart takes the width
        self.assertFalse(view.side.isVisible())
        self.assertEqual(view.chart_column.width(), body.width())
        view.side_button.click(); self.settle()
        self.assertTrue(view.side.isVisible())
        self.assertEqual(view.height(), page.viewport().height())
        # Leaving the stock restores the list's own scrolling and the owner's rail.
        view.back_button.click(); self.settle()
        self.assertEqual(page.verticalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.assertEqual(view.lock.scroll, None)
        self.assertFalse(self.window.sidebar_collapsed)

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
    def test_arrows_pan_through_end_and_ctrl_wheel_zooms(self):
        """Arrows, Shift+arrows, Home/End and 0 as before. Owner R-D12-1 (2026-11-12, "차트 확대를 +-로 하지말고
        컨트롤 + 마우스 휠 이렇게 하자"): the zoom steps that + and - gave until then now come from Ctrl + wheel, and
        the keys no longer zoom."""
        self.open(profile=False)
        p, chart = self.pane, self.pane.chart
        n = len(p.snapshot.candles)
        self.assertEqual((p.period, p.visible_bars.value(), p._end, p._cursor), ("6M", 126, None, n - 1))
        self.assertTrue(self.view.periods.buttons["6M"].isChecked())
        chart.setFocus()
        # Owner: "좌우화살표로 차트 좌우 확인할수있게" (review 2026-11-11: at 6개월 nothing moved until the 126th
        # press). Each ← moves the chart itself one step at once, the selection with it.
        QTest.keyClick(chart, Qt.Key.Key_Left)
        self.assertEqual((p._cursor, p._end, chart.end, p.visible_bars.value()), (n - 2, n - 2, n - 2, 126))
        self.assertEqual(chart.layout_info.stop - 1, n - 2)
        self.assertFalse(self.view.periods.buttons["6M"].isChecked())  # a manual pan leaves the period's view
        QTest.keyClick(chart, Qt.Key.Key_Left, Qt.KeyboardModifier.ShiftModifier)   # Shift: ten steps
        self.assertEqual((p._end, p._cursor), (n - 12, n - 12))
        self.assertEqual(chart.layout_info.stop - 1, n - 12)
        QTest.keyClick(chart, Qt.Key.Key_Right)
        self.assertEqual((p._end, p._cursor), (n - 11, n - 11))
        QTest.keyClick(chart, Qt.Key.Key_Home)
        self.assertEqual((p._cursor, p.window()), (0, (0, 126)))
        QTest.keyClick(chart, Qt.Key.Key_Left)                          # at the start: nothing further left
        self.assertEqual((p._cursor, p.window()), (0, (0, 126)))
        QTest.keyClick(chart, Qt.Key.Key_End)
        self.assertEqual((p._cursor, p._end), (n - 1, None))
        for key in (Qt.Key.Key_Plus, Qt.Key.Key_Minus, Qt.Key.Key_Equal, Qt.Key.Key_Underscore):
            QTest.keyClick(chart, key)
            self.assertEqual((p.visible_bars.value(), p._end), (126, None))
        middle = chart.layout_info.x_of(n - 10)
        self.ctrl_wheel(chart, middle, 120)
        self.assertEqual(p.visible_bars.value(), round(126 * 0.8))
        self.ctrl_wheel(chart, middle, -120); self.ctrl_wheel(chart, middle, -120)
        self.assertGreater(p.visible_bars.value(), 126)
        QTest.keyClick(chart, Qt.Key.Key_0)
        self.assertEqual((p.visible_bars.value(), p._end), (126, None))
        self.assertTrue(self.view.periods.buttons["6M"].isChecked())
        self.view.periods.left.click()
        self.assertEqual(p._end, n - 11)
        self.view.overlays.latest_button.click()
        self.assertIsNone(p._end)
        self.assertEqual(len(self.service.calls), 1)  # moving never reloads

    # Pointer: Ctrl + wheel zooms, a left-drag pans (owner R-D12-1/2, 2026-11-12) --------------------------------
    def test_ctrl_wheel_zooms_on_the_bar_under_the_pointer(self):
        """Owner R-D12-1: "차트 확대를 +-로 하지말고 컨트롤 + 마우스 휠 이렇게 하자". Over the chart, Ctrl + wheel up zooms
        in and down out, one notch one step (0.8 / 1.25 times the bars), on the bar under the pointer, which stays
        under it; 20 bars and every loaded bar are the limits. The plain wheel and + - = _ change nothing, Ctrl +
        wheel over the right column does not zoom the chart, and the page never moves."""
        from PyQt6.QtGui import QNativeGestureEvent, QPointingDevice
        self.open()
        p, chart, view = self.pane, self.pane.chart, self.view
        n = len(p.snapshot.candles)
        page = self.window.stack.currentWidget().verticalScrollBar()
        state = lambda: (p.visible_bars.value(), p._end, p._cursor, page.value())
        chart.setFocus()
        for _ in range(3):
            QTest.keyClick(chart, Qt.Key.Key_Left, Qt.KeyboardModifier.ShiftModifier)   # room on both sides
        self.settle(2)
        self.assertEqual((p.visible_bars.value(), p._end), (126, n - 31))
        before = state()
        layout = chart.layout_info
        bar = layout.start + 40
        x, y = layout.x_of(bar) + layout.step * 0.3, sum(layout.price) / 2     # off the bar's centre, still on it
        # The plain wheel either way, and the keys that zoomed until R-D12-1: nothing.
        for dy in (120, -120):
            self.assertTrue(self.ctrl_wheel(chart, x, dy, y, Qt.KeyboardModifier.NoModifier))
        for key in (Qt.Key.Key_Plus, Qt.Key.Key_Minus, Qt.Key.Key_Equal, Qt.Key.Key_Underscore):
            QTest.keyClick(chart, key)
        self.settle(2)
        self.assertEqual(state(), before)
        # One notch up: one step in; the bar stays under the pointer and becomes the selected one.
        self.assertTrue(self.ctrl_wheel(chart, x, 120, y))
        self.assertEqual(p.visible_bars.value(), round(126 * 0.8))
        self.assertEqual((chart.layout_info.index_at(x), p._cursor), (bar, bar))
        self.assertFalse(view.periods.buttons["6M"].isChecked())          # a manual zoom leaves the period's view
        # A two-notch turn down: two steps out, past the first view; the bar is still under the pointer.
        self.assertTrue(self.ctrl_wheel(chart, x, -240, y))
        self.assertEqual(p.visible_bars.value(), round(round(126 * 0.8) * 1.25 ** 2))
        self.assertEqual(chart.layout_info.index_at(x), bar)
        self.assertIsNotNone(p._end)
        # A high-resolution wheel: two half notches make one step.
        shown = p.visible_bars.value()
        self.ctrl_wheel(chart, x, 60, y)
        self.assertEqual(p.visible_bars.value(), shown)
        self.ctrl_wheel(chart, x, 60, y)
        self.assertEqual(p.visible_bars.value(), round(shown * 0.8))
        self.assertEqual(chart.layout_info.index_at(x), bar)
        # The limits: 20 bars in, every loaded bar out; a turn past a limit changes nothing.
        for _ in range(30):
            self.ctrl_wheel(chart, x, 120, y)
        self.assertEqual(p.visible_bars.value(), 20)
        held = state()
        self.ctrl_wheel(chart, x, 120, y)
        self.assertEqual(state(), held)
        for _ in range(30):
            self.ctrl_wheel(chart, x, -120, y)
        self.assertEqual((p.visible_bars.value(), p.window()), (n, (0, n)))
        # A trackpad pinch zooms too.
        pinch = QNativeGestureEvent(Qt.NativeGestureType.ZoomNativeGesture, QPointingDevice.primaryPointingDevice(), 2,
                                    QPointF(x, y), QPointF(x, y), QPointF(chart.mapToGlobal(QPoint(int(x), int(y)))),
                                    0.25, QPointF(0, 0))
        APP.sendEvent(chart, pinch)
        self.assertEqual(p.visible_bars.value(), round(n * 0.8))
        # Ctrl + wheel over the right column does not zoom (nor pan) the chart.
        before = state()
        side = view.side.stock_scroll
        sideways = side.horizontalScrollBar().value()
        for dy in (120, -120):
            self.ctrl_wheel(side.viewport(), 40, dy, 40)
        self.settle(2)
        self.assertEqual(state(), before)
        self.assertEqual(side.horizontalScrollBar().value(), sideways)
        self.assertEqual(page.value(), view.lock.target)
        self.assertEqual(len(self.service.calls), 1)                      # zooming never reloads

    def test_left_drag_pans_the_chart_and_a_click_still_selects_a_bar(self):
        """Owner R-D12-2: "차트 화면 좌클릭해서 좌우로 끌면 좌우도 움직일수잇게 !! 화살표도 유지하고". A left-drag on the
        plot pans by the bars dragged (the grabbed bar follows the pointer), stops at the first and the latest bar,
        keeps the zoom and never moves the page; an open hand over the plot, a closed one while dragging; a click
        without a drag still selects the bar under it; the arrows still pan."""
        self.open()
        p, chart, view = self.pane, self.pane.chart, self.view
        n = len(p.snapshot.candles)
        page = self.window.stack.currentWidget().verticalScrollBar()
        layout = chart.layout_info
        self.assertEqual((layout.start, layout.stop, p._end, p.visible_bars.value()), (n - 126, n, None, 126))
        step, y = layout.step, sum(layout.price) / 2
        grabbed = n - 60
        x0 = layout.x_of(grabbed)
        # Hover: the open hand over the plot, the arrow over the price axis.
        self.mouse(chart, "move", x0, y, held=False)
        self.assertEqual(chart.pointer_shape(), Qt.CursorShape.OpenHandCursor)
        self.mouse(chart, "move", layout.plot_right + 10, y, held=False)
        self.assertEqual(chart.pointer_shape(), Qt.CursorShape.OpenHandCursor)
        # Drag right by ten bars: ten older bars come in and the grabbed bar stays under the pointer.
        self.assertTrue(self.mouse(chart, "press", x0, y))
        self.mouse(chart, "move", x0 + 1, y)                              # within the drag distance: nothing yet
        self.assertEqual((p._end, chart.layout_info.start), (None, n - 126))
        x1 = x0 + 10 * step
        self.assertTrue(self.mouse(chart, "move", x1, y))
        self.assertEqual(chart.pointer_shape(), Qt.CursorShape.ClosedHandCursor)
        self.assertEqual((chart.layout_info.start, p._end, p.visible_bars.value()), (n - 136, n - 11, 126))
        self.assertEqual((chart.layout_info.index_at(x1), p._cursor), (grabbed, grabbed))
        self.assertEqual(page.value(), view.lock.target)
        self.assertFalse(view.periods.buttons["6M"].isChecked())          # a manual pan leaves the period's view
        # Far past the first bar the window stops at it; far past the latest it stops there and follows live data.
        self.mouse(chart, "move", x0 + 400 * step, y)
        self.assertEqual((p.window(), p.visible_bars.value()), ((0, 126), 126))
        self.assertEqual(page.value(), view.lock.target)
        self.mouse(chart, "move", x0 - 400 * step, y)
        self.assertEqual((p.window(), p._end), ((n - 126, n), None))
        x2 = x0 + 5 * step
        self.mouse(chart, "move", x2, y)
        self.assertTrue(self.mouse(chart, "release", x2, y))
        self.assertEqual(chart.pointer_shape(), Qt.CursorShape.OpenHandCursor)
        self.assertEqual((p.window(), p._end, p._cursor), ((n - 131, n - 5), n - 6, grabbed))
        self.assertEqual(page.value(), view.lock.target)
        # After the release the selection follows the pointer again.
        self.mouse(chart, "move", chart.layout_info.x_of(n - 100), y, held=False)
        self.assertEqual(p._cursor, n - 100)
        # A click (press and release, or a jitter within the drag distance) selects the bar under it, no pan.
        window = p.window()
        for target, jitter in ((n - 120, 0), (n - 20, 1)):
            p.move_cursor(n - 50)
            x = chart.layout_info.x_of(target)
            self.mouse(chart, "press", x, y)
            if jitter:
                self.mouse(chart, "move", x + jitter, y)
            self.mouse(chart, "release", x + jitter, y)
            self.assertEqual((p._cursor, p.window()), (target, window))
        # A press over the price axis grabs nothing.
        self.mouse(chart, "press", layout.plot_right + 10, y)
        self.mouse(chart, "move", layout.plot_right - 200, y)
        self.mouse(chart, "release", layout.plot_right - 200, y)
        self.assertEqual(p.window(), window)
        # The arrows still pan.
        chart.setFocus()
        QTest.keyClick(chart, Qt.Key.Key_Left)
        self.assertEqual(p._end, window[1] - 2)
        self.assertEqual(page.value(), view.lock.target)
        self.assertEqual(len(self.service.calls), 1)                      # dragging never reloads

    def test_a_drag_against_an_end_keeps_the_selection_under_the_pointer(self):
        """Review of R-D12-2 ("the crosshair/readout follows after release"): when the window cannot follow the drag
        (it is stopped at the latest or the first bar, or every loaded bar is shown) the selection and the OHLC strip
        stay on the bar under the pointer, during the drag and after the release; with every bar shown the pointer
        is the arrow, not the hand, and the hand comes back when a zoom lets the window move."""
        self.open()
        p, chart, view = self.pane, self.pane.chart, self.view
        n = len(p.snapshot.candles)
        layout = chart.layout_info
        step, y = layout.step, sum(layout.price) / 2
        self.assertEqual((layout.start, layout.stop), (n - 126, n))
        # At the latest bar a drag toward newer bars moves nothing; the selection follows the pointer all the same.
        x0 = layout.x_of(n - 60)
        self.mouse(chart, "move", x0, y, held=False)
        self.mouse(chart, "press", x0, y)
        x1 = x0 - 30 * step
        self.mouse(chart, "move", x1, y)
        self.assertEqual((p.window(), p._end, p._cursor), ((n - 126, n), None, n - 90))
        self.mouse(chart, "release", x1 - 2 * step, y)                     # released two bars further on
        self.settle(2)
        self.assertEqual((p.window(), p._end, p._cursor), ((n - 126, n), None, n - 92))
        self.assertEqual(view.overlays.ohlc.date.text(), p.snapshot.candles[n - 92].timestamp[:10])
        # At the first bar, a drag toward older bars: the same.
        QTest.keyClick(chart, Qt.Key.Key_Home)
        self.assertEqual(p.window(), (0, 126))
        x0 = chart.layout_info.x_of(30)
        self.mouse(chart, "press", x0, y)
        self.mouse(chart, "move", x0 + 40 * step, y)
        self.assertEqual((p.window(), p._cursor), ((0, 126), 70))
        self.mouse(chart, "release", x0 + 40 * step, y)
        self.settle(2)
        self.assertEqual((p.window(), p._cursor), ((0, 126), 70))
        self.assertEqual(view.overlays.ohlc.date.text(), p.snapshot.candles[70].timestamp[:10])
        # Every loaded bar shown: no hand (nothing to drag), and a press-and-move only moves the selection.
        for _ in range(30):
            self.ctrl_wheel(chart, x0, -120, y)
        self.assertEqual(p.window(), (0, n))
        xa = chart.layout_info.x_of(200)
        self.mouse(chart, "move", xa, y, held=False)
        self.assertEqual(chart.pointer_shape(), Qt.CursorShape.OpenHandCursor)
        self.mouse(chart, "press", xa, y)
        self.mouse(chart, "move", xa + 80, y)
        under = chart.layout_info.index_at(xa + 80)
        self.assertGreater(under, 200)
        self.assertEqual(chart.pointer_shape(), Qt.CursorShape.ClosedHandCursor)
        self.assertEqual((p.window(), p._cursor), ((0, n), under))
        self.mouse(chart, "release", xa + 80, y)
        self.assertEqual((p.window(), p._cursor), ((0, n), under))
        # One Ctrl + wheel step in: the window can move again and the hand shows without a mouse move.
        self.ctrl_wheel(chart, xa + 80, 120, y)
        self.assertLess(p.visible_bars.value(), n)
        self.assertEqual(chart.pointer_shape(), Qt.CursorShape.OpenHandCursor)
        self.assertEqual(len(self.service.calls), 1)

    def test_a_zoom_a_key_or_a_live_bar_during_a_drag_is_not_undone(self):
        """Review of R-D12-2: Ctrl + wheel, Shift+arrow, 0 or a new live bar while the left button is held are kept by
        the next mouse move: the drag goes on from the bar under the pointer at that moment (and, at the latest bar,
        keeps following live data)."""
        from dataclasses import replace
        self.open()
        p, chart = self.pane, self.pane.chart
        n = len(p.snapshot.candles)
        layout = chart.layout_info
        step, y = layout.step, sum(layout.price) / 2
        x0 = layout.x_of(n - 60)

        def hold_still(x):
            """A move to the middle of the bar under chart x (the same bar: a held drag must not pan)."""
            current = chart.layout_info
            centre = current.x_of(current.index_at(x))
            self.mouse(chart, "move", centre, y)
            return centre

        self.mouse(chart, "press", x0, y)
        x1 = x0 + 10 * step
        self.mouse(chart, "move", x1, y)
        self.assertEqual(p.window(), (n - 136, n - 10))
        # Ctrl + wheel at the pointer: the bar under it stays there through the next moves, at the new bar width.
        self.ctrl_wheel(chart, x1, 120, y)
        zoomed = p.window()
        self.assertEqual((p.visible_bars.value(), chart.layout_info.index_at(x1)), (round(126 * 0.8), n - 60))
        x = hold_still(x1)
        self.assertEqual((p.window(), chart.layout_info.index_at(x)), (zoomed, n - 60))
        x += 5 * chart.layout_info.step + 1
        self.mouse(chart, "move", x, y)
        self.assertEqual((p.visible_bars.value(), chart.layout_info.index_at(x)), (round(126 * 0.8), n - 60))
        # Shift+← during the drag: kept.
        QTest.keyClick(chart, Qt.Key.Key_Left, Qt.KeyboardModifier.ShiftModifier)
        shifted, held = p.window(), chart.layout_info.index_at(x)
        x = hold_still(x)
        self.assertEqual((p.window(), chart.layout_info.index_at(x)), (shifted, held))
        # 0 during the drag: the default view, following the latest bar, is kept.
        QTest.keyClick(chart, Qt.Key.Key_0)
        self.assertEqual((p.window(), p._end, p.visible_bars.value()), ((n - 126, n), None, 126))
        x = hold_still(x)
        self.assertEqual((p.window(), p._end), ((n - 126, n), None))
        # A new live bar while the press is held at the latest bar: the window keeps following live data.
        last = p.snapshot.candles[-1]
        p.snapshot = replace(p.snapshot, candles=p.snapshot.candles + (
            Candle("2026-11-11", last.close, last.close * 1.01, last.close * 0.99, last.close * 1.005, last.volume),))
        p.render()
        self.assertEqual((p.window(), p._end), ((n - 125, n + 1), None))
        x = hold_still(x)
        self.assertEqual((p.window(), p._end), ((n - 125, n + 1), None))
        # Dragging on from there pans as usual.
        held = chart.layout_info.index_at(x)
        self.mouse(chart, "move", x + 4 * chart.layout_info.step, y)
        self.assertEqual(chart.layout_info.index_at(x + 4 * chart.layout_info.step), held)
        self.assertEqual(p.window(), (n - 129, n - 3))
        self.mouse(chart, "release", x + 4 * chart.layout_info.step, y)
        self.assertEqual(len(self.service.calls), 1)

    def test_overlay_pointer_shapes_and_the_chart_name(self):
        """Review of R-D12-2: the panel header's ⓘ and × show the pointing hand (a press there clicks, never drags);
        the labels over the chart show the drag hand over the plot and the arrow over the price axis however the
        pointer reached them. The chart's accessible name says how to move and zoom it after every load (a render
        no longer replaces it with the data source), in Korean and English."""
        from quantgen_desktop.stock_detail_style import text
        self.open()
        p, chart, view = self.pane, self.pane.chart, self.view
        self.assertEqual(chart.accessibleName(), text("ko", "chart_name"))
        p.set_indicators(("rsi",))
        self.settle()
        layout = chart.layout_info
        head = view.overlays.heads["rsi"]
        handle = self.window.windowHandle()
        at = lambda x, y: chart.mapTo(self.window, QPoint(round(x), round(y)))
        price_y = sum(layout.price) / 2
        # The header's title sits over the plot. Reached from the price axis (the arrow), it shows the hand.
        title = head.title.mapTo(chart, head.title.rect().center())
        self.assertLess(title.x(), layout.plot_right)
        QTest.mouseMove(handle, at(layout.plot_right + 20, price_y))
        self.assertEqual(chart.pointer_shape(), Qt.CursorShape.OpenHandCursor)
        QTest.mouseMove(handle, at(title.x(), title.y()))
        self.assertIs(self.window.childAt(at(title.x(), title.y())), head.title)
        self.assertEqual(head.title.cursor().shape(), Qt.CursorShape.OpenHandCursor)
        # From the plot onto the ⓘ and × buttons: the pointing hand.
        for button in (head.info, head.off):
            QTest.mouseMove(handle, at(layout.x_of(layout.start + 50), price_y))
            self.assertEqual(chart.pointer_shape(), Qt.CursorShape.OpenHandCursor)
            centre = button.mapTo(self.window, button.rect().center())
            QTest.mouseMove(handle, centre)
            self.assertIs(self.window.childAt(centre), button)
            self.assertEqual(button.cursor().shape(), Qt.CursorShape.PointingHandCursor)
        # Over the header's part above the price axis (left of the buttons): the arrow, though reached from the plot.
        spot = QPoint(round(layout.plot_right) + 2, title.y())
        under = self.window.childAt(chart.mapTo(self.window, spot))
        self.assertTrue(under is not chart and chart.isAncestorOf(under))
        self.assertNotIn(under, (head.info, head.off))
        QTest.mouseMove(handle, at(layout.x_of(layout.start + 50), price_y))
        QTest.mouseMove(handle, chart.mapTo(self.window, spot))
        self.assertEqual(under.cursor().shape(), Qt.CursorShape.OpenHandCursor)
        # The accessible name after a reload, in English too.
        self.window.set_language("en")
        self.settle()
        p.refresh(manual=True)
        self.wait(lambda: not p.jobs.busy)
        self.settle()
        self.assertEqual(len(self.service.calls), 2)
        self.assertEqual(chart.accessibleName(), text("en", "chart_name"))

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
        # ⓘ unfolds the beginner guide as a short card (owner R-D9-3): the reading now first, the long texts
        # behind 자세히.
        from core.education.study_guide import short_guide, short_reading, study_reading
        rows["rsi"].info.click(); self.settle(2)
        card = rows["rsi"].guide
        self.assertTrue(card.isVisible())
        bars = view.engine_bars()
        self.assertEqual(card.headline.text(), short_reading("rsi", bars, -1, language="ko", supply=self.pane.supply))
        self.assertEqual(card.one_liner.text(), short_guide("rsi", "ko").one_liner)
        self.assertFalse(card.details.isVisible())
        self.assertEqual(card.long_texts[0], polite(study_reading("rsi", bars, -1, language="ko", supply=self.pane.supply)))
        self.assertIn(polite(guide("rsi", "ko").caution), card.long_texts)
        card.more.click(); self.settle(2)
        self.assertTrue(card.details.isVisible())
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
        self.assertEqual(self.view.back_button.text(), "←" if self.view._level >= 2 else "← Real-time charts")
        self.assertNotRegex(self.view.back_button.accessibleName(), "[가-힣]")
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

    def test_back_in_a_narrow_window_and_the_owners_own_rail_choice(self):
        """Review of UI-D9: at 1000x700 the screen folds the rail for the chart, yet Back still returns the list to
        where it was; a rail the owner opened or closed meanwhile is left as they last set it (and saved)."""
        from PyQt6.QtWidgets import QWidget
        from quantgen_desktop import shell_rail
        w = self.window
        w.language_store = self.settings          # the shell saves the owner's rail choice here
        page = w.stack.currentWidget()
        filler = QWidget(); filler.setFixedHeight(3000)            # a long ranking list
        w.markets_view.layout().addWidget(filler); self.settle()
        bar = page.verticalScrollBar()
        w.resize(1000, 700); self.settle(); self.settle()
        bar.setValue(600); self.settle()
        self.assertEqual(bar.value(), 600)
        self.assertFalse(w.sidebar_collapsed)
        self.open(load=False, profile=False); self.settle()
        self.assertTrue(w.sidebar_collapsed)                       # folded to give the chart its room
        self.assertEqual(bar.value(), self.view.lock.target)
        self.view.back_button.click(); self.settle(); self.settle()
        self.assertEqual(bar.value(), 600)
        self.assertFalse(w.sidebar_collapsed)                      # and given back
        # The owner opens the rail with its own button while the screen holds it folded: it stays open, also
        # after a resize; they close it again: Back leaves it closed, as saved.
        self.open(load=False, profile=False); self.settle()
        self.assertTrue(w.sidebar_collapsed)
        w.sidebar_show.click(); self.settle()
        self.assertFalse(w.sidebar_collapsed)
        w.resize(1010, 700); self.settle(); self.settle()
        self.assertFalse(w.sidebar_collapsed)
        w.sidebar_hide.click(); self.settle()
        self.view.back_button.click(); self.settle()
        self.assertTrue(w.sidebar_collapsed)
        self.assertTrue(shell_rail.stored_flag(self.settings))
        # A saved choice made any other way counts too.
        w.set_sidebar_collapsed(False); self.settle()
        self.open(load=False, profile=False); self.settle()
        self.assertTrue(w.sidebar_collapsed)
        w.set_sidebar_collapsed(False); w.set_sidebar_collapsed(True); self.settle()
        self.view.back_button.click(); self.settle()
        self.assertTrue(w.sidebar_collapsed)
        self.assertTrue(shell_rail.stored_flag(self.settings))

    def test_the_data_notes_follow_the_chart_and_menu_intervals_load_enough_bars(self):
        """Review of UI-D9: the notes box beside the chart never keeps another stock's or interval's notes; ages read
        in plain units; an interval chosen after the 전체 chip asks for 400 bars again; Yahoo's monthly note and
        the running year read in Korean."""
        from core.market.detail_model import yearly_snapshot
        from quantgen_desktop.stock_detail import plain_age, plain_ages, year_label
        view, pane = self.view, self.pane
        self.open(APPLE, profile=False)
        view._show_notes(); self.settle()
        self.assertTrue(view.notes.isVisible())
        apple = view.notes.body.text()
        self.assertIn("Nasdaq", apple)
        view.side.watchlist.render()
        row = view.side.watchlist.watch.rows[("domestic_stock", "005930", "")]
        QTest.mouseClick(row, Qt.MouseButton.LeftButton); self.settle()
        pane.refresh(manual=True); self.wait(lambda: not pane.jobs.busy); self.settle()
        self.assertEqual(view.instrument.code, "005930")
        self.assertTrue(view.notes.isVisible())
        self.assertNotIn("Nasdaq", view.notes.body.text())
        shown = view.notes.body.text()
        view.notes.refresh()
        self.assertEqual(view.notes.body.text(), shown)             # already the chart shown now
        self.assertEqual(view.notes.poll.text(), "5초마다 새로 불러오기")
        self.assertTrue(view.notes.poll.toolTip() and view.notes.stream.toolTip())
        # Ages in plain units.
        self.assertEqual([plain_age(s, "ko") for s in (40, 300, 7200, 108294)], ["40초", "5분", "2시간", "1일"])
        self.assertEqual(plain_ages("수신 중지 · 마지막 수신 108294초 전", "ko"), "수신 중지 · 마지막 수신 1일 전")
        self.assertEqual(plain_ages("Updates stopped · last received 3700s ago", "en"),
                         "Updates stopped · last received 1 h ago")
        # 전체 asks for the yearly chart (50 years from the monthly history); a menu interval after it, for 400.
        view.periods.buttons["ALL"].click(); self.wait(lambda: not pane.jobs.busy); self.settle()
        self.assertEqual((self.service.calls[-1].interval, self.service.calls[-1].limit), ("1M", 500))
        for interval in ("1d", "1w"):
            combo = view.interval_combo
            index = combo.findData(interval)
            combo.setCurrentIndex(index); view._interval_chosen(index)
            self.wait(lambda: not pane.jobs.busy); self.settle()
            self.assertEqual((self.service.calls[-1].interval, self.service.calls[-1].limit), (interval, 400))
            self.assertEqual(len(pane.snapshot.candles), 400)
            shown = view.notes.body.text()
            view.notes.refresh()
            self.assertEqual(view.notes.body.text(), shown, interval)   # the open notes follow the interval
            view.periods.buttons["ALL"].click(); self.wait(lambda: not pane.jobs.busy); self.settle()
        # Yahoo's partial monthly history (no KIS paging remark) reads in Korean in the yearly chart's notes.
        monthly = MarketSnapshot(ChartRequest(SAMSUNG, "1M", 500), candles("005930", 30), None,
                                 "2026-11-10T06:20:03+00:00", "Yahoo Finance",
                                 "Partial history: 234/500 requested bars.")
        note = pane._data_note(yearly_snapshot(monthly, ChartRequest(SAMSUNG, "1Y", 50)).note, SAMSUNG)
        self.assertNotIn("Partial history", note)
        self.assertIn("요청한 500개월 중 234개월", note)
        self.assertIn("연 단위", note)
        # The yearly candle's date says which year is still running, by the calendar.
        self.assertEqual(year_label(2025, None, "ko"), "2025")
        self.assertEqual(year_label(2026, (1, 12, True), "ko"), "2026년 · 12월까지 (진행 중)")
        self.assertEqual(year_label(2026, (10, 11, True), "ko"), "2026년 · 10~11월 (진행 중)")
        self.assertEqual(year_label(2026, (11, 11, True), "ko"), "2026년 · 11월 (진행 중)")
        self.assertEqual(year_label(2013, (1, 2, False), "ko"), "2013년 · 1~2월 값")
        self.assertEqual(year_label(2024, (3, 3, False), "ko"), "2024년 · 3월 값")
        self.assertEqual(year_label(2026, (1, 12, True), "en"), "2026 so far (to Dec)")

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

    # UI-D9 (owner 2026-11-11 ~19:45/19:55 KST): nothing covers the chart, plain time words, short guide cards --------
    def visible_widgets(self, root):
        from PyQt6.QtWidgets import QWidget
        return [w for w in [root, *root.findChildren(QWidget)] if w.isVisible() and w.width() > 0 and w.height() > 0]

    def all_texts(self, root):
        """Every text the screen can show under `root`: labels, buttons, tooltips, accessible names, placeholders
        and every item of the interval menu (shown or in its list)."""
        from PyQt6.QtWidgets import QComboBox, QLineEdit
        out = []
        for widget in self.visible_widgets(root):
            for value in (widget.toolTip(), widget.accessibleName()):
                if value:
                    out.append(TAGS.sub("", value))
            if isinstance(widget, (QLabel, QAbstractButton)) and widget.text():
                out.append(TAGS.sub("", widget.text()))
            if isinstance(widget, QLineEdit) and widget.placeholderText():
                out.append(widget.placeholderText())
            if isinstance(widget, QComboBox):
                out += [widget.itemText(i) for i in range(widget.count())]
        from quantgen_desktop.stock_detail_style import text
        out += [text("ko", key) for key in ("group_minutes", "group_daily")]
        return out

    def assert_plain_korean(self, root, where):
        """No '봉' (owner R-D9-2) and one register, 해요체 (no 합니다체, no '…음' sentence endings)."""
        # Owner D13 explicitly chose this short disclaimer; other prose keeps 해요체.
        texts = [t for t in self.all_texts(root) if t != "실험적 지표 · 투자 권유 아님"]
        self.assertTrue(texts, where)
        self.assertEqual([t for t in texts if "봉" in t], [], where)
        self.assertEqual([t for t in texts if "니다" in t], [], where)
        self.assertEqual([t for t in texts if re.search(r"(수 있음|아님|없었음|높음|낮음)(\s*[.)]|\s·|$)", t)], [], where)
        # Review of UI-D9: the particle fits the unit word ('120일과', not '120일와'), the trend row names no fixed
        # span of months, 年 starts a word as 연, and ages read in plain units.
        self.assertEqual([t for t in texts if re.search(r"(\d일|구간|개월|\d년)와 ", t)], [], where)
        self.assertEqual([t for t in texts if "1~3개월" in t or re.search(r"(^|[^\d])년 단위", t)], [], where)
        self.assertEqual([t for t in texts if re.search(r"\d{3,}초", t) or "을(를)" in t], [], where)

    def test_nothing_covers_the_chart_at_any_size_or_column_state(self):
        """R-D9-1: for each window size and right-column state, no widget but the chart's own band texts meets the
        chart below its header band; the band texts stay in their bands; the column never meets the chart."""
        from core.market.detail_svg import HEADER, PANEL_HEAD
        from PyQt6.QtCore import QRect
        self.open()
        view, chart = self.view, self.pane.chart
        view.set_studies(("sma", "bb", "volume_ma", "rsi", "macd", "stoch", "adx", "cci")); self.settle()
        overlays = view.overlays
        band_widgets = [overlays.ohlc, overlays.legend, overlays.notice]

        def check(where):
            self.settle(3)
            layout = chart.layout_info
            self.assertIsNotNone(layout, where)
            origin = chart.mapTo(self.window, QPoint(0, 0))
            protected = QRect(origin.x(), origin.y() + HEADER, chart.width(), chart.height() - HEADER)
            heads = [h for h in overlays.heads.values() if h.isVisible()]
            own = set(band_widgets) | set(heads)
            for widget in self.visible_widgets(self.window):
                if widget is chart or widget.isAncestorOf(chart) or widget.window() is not self.window:
                    continue
                if any(widget is o or o.isAncestorOf(widget) for o in own):
                    continue
                rect = QRect(widget.mapTo(self.window, QPoint(0, 0)), widget.size())
                self.assertFalse(rect.intersects(protected), (where, type(widget).__name__, widget.objectName(),
                                                              widget.property("sd"), rect, protected))
            for widget in band_widgets:
                if widget.isVisible():
                    self.assertLessEqual(widget.geometry().bottom(), HEADER, (where, widget.geometry()))
            panels = {key: (top, bottom) for key, top, bottom in layout.panels}
            for key, head in overlays.heads.items():
                if head.isVisible():
                    top, _ = panels[key]
                    self.assertGreaterEqual(head.geometry().top(), top, where)
                    self.assertLessEqual(head.geometry().bottom(), top + PANEL_HEAD, where)
                    self.assertLessEqual(head.geometry().right(), layout.width, where)
            if view.side.isVisible():
                self.assertFalse(view.side.geometry().intersects(view.chart_column.geometry()), where)

        for size in ((1000, 700), (1280, 800), (1440, 900), (1920, 1080)):
            self.window.resize(*size); self.settle(); self.settle()
            view.set_side_shown(False); check((size, "hidden"))
            view.set_side_shown(True); view.side.set_page(0); check((size, "stock tab"))
            view.explain("rsi"); check((size, "indicator tab with a guide"))
            view.picker.rows()["rsi"].guide.set_open(True); check((size, "guide unfolded"))
            self.pane.pan(-15); check((size, "panned: the latest button"))
            self.pane.follow_latest()
            view.set_focus_mode(True); check((size, "focus"))
            view.set_focus_mode(False)
            self.assertGreaterEqual(view.chart_column.width(), 540, size)

    def test_intervals_are_plain_time_words_with_a_yearly_one(self):
        """R-D9-2: the menu reads 1분 … 60분, 일, 주, 월, 년; 년 is built from the monthly history."""
        from core.market.detail_model import yearly_span
        self.open(profile=False)
        combo = self.view.interval_combo
        names = [combo.itemText(i) for i in range(combo.count())]
        self.assertEqual(names, ["1분", "3분", "5분", "15분", "30분", "60분", "일", "주", "월", "년"])
        self.assertEqual(combo.currentText(), "일")
        index = combo.findData("1Y")
        combo.setCurrentIndex(index); self.view._interval_chosen(index)
        self.wait(lambda: not self.pane.jobs.busy and self.pane.snapshot is not None
                  and self.pane.snapshot.request.interval == "1Y")
        self.settle()
        self.assertEqual((self.service.calls[-1].interval, self.service.calls[-1].limit), ("1M", 500))
        self.assertEqual(combo.currentText(), "년")
        years = self.pane.snapshot.candles
        self.assertEqual(len({c.timestamp[:4] for c in years}), len(years))
        self.assertTrue(all(c.timestamp.endswith("-01-01") for c in years))
        last = int(years[-1].timestamp[:4])
        self.assertTrue(yearly_span(self.pane.snapshot)[last][2])          # 2026 is this year (fetched 2026-11-10)
        self.assertIn("진행 중", self.view.overlays.ohlc.date.text())       # the running year says so
        self.assertIn("연 단위", self.view.overlays.ohlc.title.text())      # 年 at a word's start is 연
        self.window.set_language("en"); self.settle()
        self.assertEqual([combo.itemText(i) for i in range(combo.count())],
                         ["1 min", "3 min", "5 min", "15 min", "30 min", "60 min", "Day", "Week", "Month", "Year"])
        self.window.set_language("ko"); self.settle()
        # 전체 draws the yearly candles, 10년 the monthly ones.
        self.view.periods.buttons["10Y"].click(); self.wait(lambda: not self.pane.jobs.busy); self.settle()
        self.assertEqual(self.pane.snapshot.request.interval, "1M")
        self.view.periods.buttons["ALL"].click(); self.wait(lambda: not self.pane.jobs.busy); self.settle()
        self.assertEqual(self.pane.snapshot.request.interval, "1Y")

    def test_no_bong_and_one_register_on_the_korean_screen_in_every_state(self):
        """R-D9-2: '봉' appears in no Korean text of the stock screen: each interval, the picker with guides open
        and unfolded, many studies, the notes, every folded section opened, and the empty, loading and failed
        chart."""
        from core.education.indicators import STUDIES
        from core.market.detail_model import routable_intervals
        view = self.view
        self.window.markets_view.open_instrument(SAMSUNG); self.settle()
        self.assert_plain_korean(view, "not loaded")
        self.open()
        for key in ("key_figures", "range", "risk", "technical", "supply"):
            section = view.side.sections[key]
            section.set_open(True)
            if section.more.isVisible() and not section.expanded:
                section.more.click()
        view.side.watchlist.recent_group.set_open(True)
        self.settle()
        self.assert_plain_korean(view, "loaded, every section open")
        view._show_notes(); self.settle()
        self.assertTrue(view.notes.isVisible())
        self.assert_plain_korean(view, "data notes")
        combo = view.interval_combo
        for index in range(combo.count()):
            if not combo.model().item(index).isEnabled():
                continue
            combo.setCurrentIndex(index); view._interval_chosen(index)
            self.wait(lambda: not self.pane.jobs.busy); self.settle()
            self.assert_plain_korean(view, combo.itemData(index))
        view.choose_period("6M"); self.wait(lambda: not self.pane.jobs.busy); self.settle()
        view.set_studies(tuple(spec.key for spec in STUDIES)); self.settle()
        self.assert_plain_korean(view, "every study on")
        for key in ("rsi", "bb", "macd", "investor_flow", "vwap"):
            view.explain(key); self.settle(2)
            view.picker.rows()[key].guide.set_open(True); self.settle(2)
        self.assert_plain_korean(view, "picker with guides open and unfolded")
        view.side.set_page(0)
        tech = view.side.sections["technical"]
        for entry in tech._entries:
            card = getattr(entry, "findChild", None) and entry.findChildren(QAbstractButton)
            for button in card or ():
                if button.isCheckable() and button.isVisible():
                    button.setChecked(True)
        self.settle()
        self.assert_plain_korean(view, "reading rows unfolded")
        self.pane.pan(-20); self.chart_wheel(); self.settle()
        self.assert_plain_korean(view, "notices")

        def offline(request):
            raise RuntimeError("offline")
        self.service.load = offline
        self.window.markets_view.open_instrument(KAKAO); self.settle()
        self.pane.refresh(manual=True); self.wait(lambda: not self.pane.jobs.busy); self.settle()
        self.assertTrue(self.pane.empty_retry.isVisible())
        self.assert_plain_korean(view, "failed load")

    def chart_wheel(self):
        self.wheel(self.pane.chart)

    def test_guide_cards_are_short_and_the_column_explains_its_figures(self):
        """R-D9-3: a folded guide card shows the reading, the pill, a gauge, one line, cue chips and one caution,
        about three lines of text and none of the old section headings; reviewer findings on the column."""
        from core.education.study_guide import short_guide
        from quantgen_desktop.stock_detail_style import text
        self.open()
        view = self.view
        old_heads = ("무엇인가요", "어떻게 보나요", "주의", "지금 읽기", "설정")
        for key in ("rsi", "bb", "macd", "sma", "volume_ma"):
            view.explain(key); self.settle(2)
            card = view.picker.rows()[key].guide
            self.assertTrue(card.isVisible(), key)
            shown = [t for t in self.visible_texts(card)]
            self.assertFalse([t for t in shown if t.strip() in old_heads], key)
            self.assertTrue(card.headline.text(), key)
            self.assertTrue(card.gauge.isVisible(), key)
            self.assertEqual([c.text() for c in card.cues.chips if c.text()], list(short_guide(key, "ko").cues))
            lines = sum(round(w.height() / w.fontMetrics().lineSpacing()) for w in (card.headline, card.one_liner,
                                                                                   card.caution) if w.isVisible())
            self.assertLessEqual(lines, 4, key)
            self.assertFalse(card.details.isVisible())
        # Picker rows keep the whole name in a 320px column; the place moves to line 2 instead.
        self.window.resize(1000, 700); self.settle(); self.settle()
        view.show_indicators(); self.settle()
        for group in view.picker.groups.values():
            group.set_open(True)
        self.settle(3)
        for key, row in view.picker.rows().items():
            if row.isVisible():
                self.assertEqual(row.name.fitted(), row.name.text(), key)   # rows out of view are not painted
        self.window.resize(1440, 900); self.settle()
        # 기술 지표: the studies' rows and one composite score with its scale, no sub-scores or verdict.
        tech = view.side.sections["technical"]
        rows = [e for e in tech._entries if hasattr(e, "label")]
        self.assertEqual([r.label for r in rows], [text("ko", "signals_label")])
        self.assertIn("−100~100", rows[0].hint)
        # Figures explain themselves; no internal engine name.
        hints = {row.label: row.hint for key in ("key_figures", "risk")
                 for row in view.side.sections[key]._entries if hasattr(row, "label")}
        for label_text, start in (("PER", "PER —"), ("EPS", "EPS —"), ("1일 VaR 95%", "위험가치(VaR)"),
                                  ("1일 CVaR 95%", "조건부 VaR(CVaR)")):
            self.assertTrue(hints[label_text].startswith(start), (label_text, hints[label_text]))
        self.assertFalse([h for h in hints.values() if "gs_quant" in h or "계산 엔진" in h])
        # Register and pointers: the full watchlist, the Q-SCORE chip, the key hint.
        self.assertEqual(text("ko", "watch_full", limit=20), "관심종목은 20개까지 담을 수 있어요.")
        self.assertNotIn("?", text("ko", "qscore_tip"))
        self.assertEqual(view.periods.hint.text(), "← → · 끌기 이동 · Ctrl+휠 확대·축소")   # owner R-D12-1/2
        self.assertNotIn("⤢", text("ko", "picker_panel_limit", count=3) + text("ko", "hidden_panels_tip", names="x"))
        # The English legend shows the volume average in the strip's unit.
        self.window.set_language("en"); self.settle()
        legend = TAGS.sub("", view.overlays.legend_label.text())
        self.assertRegex(legend, r"Volume MA 20 [\d.]+M")
        self.window.set_language("ko"); self.settle()
        self.assertRegex(TAGS.sub("", view.overlays.legend_label.text()), r"거래량 평균 20 [\d,]+만")


    def test_guide_cards_say_each_thing_once_and_the_keys_stay_with_the_chart(self):
        """Review of UI-D9 (R-D9-3: "글밥이 너무 많아"): an open guide's row and card say each thing once, the reading
        first; the pill names the zone by its edges and the caution speaks of the side the value is on; ADX, which
        has no direction, gets neutral colours on a 0-100 track and a two-part reading; the 기술 지표 rows are a
        name, a reading with its pill and a gauge. Owner: the PC arrows move the chart, also after a click on a
        switch, a fold header or a toolbar button."""
        from core.education import indicators as engine
        from core.education.study_guide import CAUTION_LOW, short_guide
        self.open()
        view, picker, p = self.view, self.view.picker, self.pane
        view.set_studies(("sma", "bb", "rsi", "adx", "stoch", "vwap")); self.settle()
        for key in ("rsi", "adx", "stoch", "bb", "macd", "sma"):
            view.explain(key); self.settle(2)
            row = picker.rows()[key]
            texts = [t.strip() for t in self.visible_texts(row) if t.strip()]
            self.assertEqual(len(texts), len(set(texts)), (key, texts))
            self.assertFalse(row.desc.isVisible(), key)           # the one-liner is said by the card
            self.assertFalse(row.value.isVisible(), key)          # the value, by the card's reading
            self.assertTrue(row.guide.headline.isVisible(), key)
            self.assertLess(row.guide.pill.y(), row.guide.one_liner.y(), key)   # pill and reading come first
            self.assertNotIn("보통", texts, key)
            row.open_guide(False); self.settle(2)
            self.assertTrue(row.desc.isVisible(), key)
        rsi = float(engine.compute_study("rsi", view.engine_bars())["RSI14"][-1])
        view.explain("rsi"); self.settle(2)
        card = picker.rows()["rsi"].guide
        if 30 < round(rsi, 1) < 70:
            self.assertEqual(card.pill.text(), "30~70 사이")
        self.assertEqual(card.caution.text(), CAUTION_LOW["rsi"][0] if rsi < 50 else short_guide("rsi", "ko").caution)
        view.explain("adx"); self.settle(2)
        card = picker.rows()["adx"].guide
        self.assertEqual(card.gauge.kind, "level")
        self.assertEqual([round(m[0], 2) for m in card.gauge.marks], [0.2, 0.25])
        self.assertEqual(card.headline.text().count(" · "), 1, card.headline.text())
        # 기술 지표: the name alone heads each block; a study that cannot be drawn is one muted line.
        view.side.set_page(0)
        tech = view.side.sections["technical"]
        tech.set_open(True); view.render_sections(); self.settle(2)
        for key, (block, head, card) in view._technical_blocks.items():
            name = engine.study(key).name("ko")
            plain = TAGS.sub("", head.text()).replace("&ensp;", "").replace("●", "").strip()
            if key == "vwap":
                self.assertEqual(plain, f"{name} · 분 단위 차트 전용")
                self.assertTrue(card.isHidden() and card.more.isHidden())       # (some blocks sit behind 더 보기)
            else:
                self.assertEqual(plain, name)                       # no readouts in front of the reading
                self.assertTrue(head.toolTip())                     # they sit in the tooltip
                self.assertFalse(card.isHidden() or card.headline.isHidden() or card.gauge.isHidden(), key)
                self.assertIs(card.more.parentWidget(), block)      # 자세히 › ends the name's line
        # The keys: after a click on a picker switch, a fold header or the toolbar's 지표, ← still pans the chart;
        # a text input keeps its arrows.
        n = len(p.snapshot.candles)
        view.show_indicators(); self.settle()
        switch_row = picker.rows()["cci"]
        picker.groups["momentum"].set_open(True); view._reveal(switch_row); self.settle(2)
        QTest.mouseClick(switch_row.switch, Qt.MouseButton.LeftButton); self.settle(2)
        self.assertIn("cci", view.studies)
        focused = APP.focusWidget()
        self.assertTrue(focused is not None and view.isAncestorOf(focused) and focused is not p.chart, focused)
        QTest.keyClick(focused, Qt.Key.Key_Left); self.settle(2)
        self.assertEqual(p._end, n - 2)
        view.side.set_page(0); self.settle()
        head = view.side.sections["risk"].head
        view.side.stock_scroll.ensureWidgetVisible(head); self.settle()
        QTest.mouseClick(head, Qt.MouseButton.LeftButton); self.settle(2)
        self.assertIs(APP.focusWidget(), head)
        QTest.keyClick(head, Qt.Key.Key_Left); self.settle(2)
        self.assertEqual(p._end, n - 3)
        view.indicators_button.setFocus(); self.settle()
        QTest.keyClick(view.indicators_button, Qt.Key.Key_End); self.settle(2)
        self.assertIsNone(p._end)
        view.search.setFocus(); view.search.setText("삼성"); self.settle()
        QTest.keyClick(view.search, Qt.Key.Key_Left); self.settle(2)
        self.assertIsNone(p._end)                                   # the search box moved its own cursor
        self.assertEqual(view.search.cursorPosition(), 1)


if __name__ == "__main__":
    unittest.main()
