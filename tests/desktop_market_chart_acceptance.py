"""Offline native chart lifecycle tests with deterministic REST and stream fakes."""
from __future__ import annotations

import ast
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import importlib.util
import os
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
HAS_QT = importlib.util.find_spec("PyQt6") is not None
ROOT = Path(__file__).resolve().parents[1]


class NativeChartSourceChecks(unittest.TestCase):
    def test_native_view_uses_shared_contract_and_renderer(self):
        tree = ast.parse((ROOT / "quantgen_desktop/market_chart.py").read_text(encoding='utf-8'))
        imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        self.assertTrue({"core.market.models", "core.market.presentation", "core.market.live"} <= imports)
        # User-facing native features must be reachable from the real application.
        app = (ROOT / "quantgen_desktop/app.py").read_text(encoding='utf-8')
        self.assertIn("self.market_chart = MarketChartPane(locale=self.ctx)", app)
        self.assertIn("self.market_chart.stop()", app)
        self.assertIn("self.market_chart.set_locale(self.ctx)", app)


if HAS_QT:
    from PyQt6.QtCore import QThread
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication
    from core.i18n import LocaleContext
    from core.market.models import Candle, ChartRequest, MarketQuote, MarketSnapshot, MarketTick
    from quantgen_desktop.market_chart import MarketChartPane

    def fixture(request):
        now = datetime.now(timezone(timedelta(hours=9)))
        today = now.date()
        bars = tuple(Candle((today - timedelta(days=119 - i)).isoformat(),
                    100 + i, 102 + i, 99 + i, 101 + i, 1000 + i) for i in range(120))
        stamp = now.isoformat(timespec="seconds")
        quote = MarketQuote(request.instrument, price=220, change=1, change_pct=.45,
            volume=1119, market_time=stamp, received_at=stamp)
        return MarketSnapshot(request, bars, quote, fetched_at=stamp)

    class FakeService:
        def __init__(self):
            self.calls = []
            self.threads = []
            self.fail = False
            self.entered = self.release = None

        def load(self, request):
            self.calls.append(request)
            self.threads.append(QThread.currentThread())
            if self.entered is not None:
                self.entered.set()
                self.release.wait(4)
            if self.fail:
                raise RuntimeError("do not display raw provider URLs / secrets")
            return fixture(request)

    class FakeStream:
        def __init__(self):
            self.started = self.stopped = False

        def start(self, instrument, on_tick, on_status):
            self.started = True
            self.instrument = instrument
            self.on_tick, self.on_status = on_tick, on_status
            on_status("SUBSCRIBED")

        def stop(self):
            self.stopped = True


@unittest.skipUnless(HAS_QT, "PyQt6 optional desktop dependency is unavailable")
class NativeChartLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        no_network = patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        no_network.start()
        self.addCleanup(no_network.stop)
        self.service = FakeService()
        self.streams = []

        def stream_factory():
            stream = FakeStream()
            self.streams.append(stream)
            return stream

        self.pane = MarketChartPane(service=self.service, stream_factory=stream_factory,
                                    locale=LocaleContext("ko_KR"))
        self.pane.resize(1080, 950)
        self.pane.show()
        self.app.processEvents()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.pane.stop()
        if self.service.release is not None:
            self.service.release.set()
        self.wait_idle()
        self.pane.close()
        self.pane.deleteLater()
        self.app.processEvents()

    def wait_idle(self):
        for _ in range(400):
            self.app.processEvents()
            if not self.pane.jobs.busy:
                return
            QTest.qWait(10)
        self.fail("REST worker did not finish")

    def wait_for_ui(self, predicate):
        # Assert the rendered outcome, not an OS-specific timer scheduling time.
        for _ in range(100):
            self.app.processEvents()
            if predicate():
                return
            QTest.qWait(10)
        self.assertTrue(predicate(), 'UI did not render the accepted tick within 1 second')

    def load(self):
        self.assertTrue(self.pane.refresh(manual=True))
        self.wait_idle()
        self.assertIsNotNone(self.pane.snapshot)

    def connect_stream(self):
        self.pane.start_stream()
        self.wait_idle()
        self.app.processEvents()

    def test_construction_never_fetches_and_input_validation_precedes_provider(self):
        self.assertEqual(self.service.calls, [])
        self.assertEqual(self.pane.request().interval, "1d")
        self.assertFalse(self.pane.exchange.isEnabled())
        self.pane.symbol.setText("../../.env")
        self.assertFalse(self.pane.refresh(manual=True))
        self.assertEqual(self.service.calls, [])
        self.assertIn("코드", self.pane.status.text())

    def test_rest_runs_off_gui_thread_and_renders_shared_chart_and_cursor(self):
        self.load()
        p = self.pane
        self.assertIsNot(self.service.threads[0], self.app.thread())
        self.assertTrue(p.chart.renderer().isValid())
        self.assertIn("005930", p.reading.text())
        self.assertIn("SMA20", p.indicator_reading.text())
        self.assertEqual(p.cursor_slider.maximum(), 119)
        p.visible_bars.setValue(30)
        p.move_cursor(0)
        self.assertEqual(p.visible_bars.value(), 120)
        self.assertIn(p.snapshot.candles[0].timestamp, p.reading.text())
        before = p.snapshot
        p.set_locale(LocaleContext("en_US"))
        self.assertEqual(p.load_button.text(), "Load / refresh")
        self.assertIs(p.snapshot, before)
        self.assertEqual(len(self.service.calls), 1)

    def test_connect_from_empty_chart_loads_history_before_subscribing(self):
        self.assertIsNone(self.pane.snapshot)
        self.assertTrue(self.pane.stream_button.isEnabled())
        self.pane.stream_button.click()
        self.wait_idle()
        self.app.processEvents()
        self.assertEqual(len(self.service.calls), 1)
        self.assertTrue(self.streams[-1].started)
        self.assertTrue(self.pane.chart.renderer().isValid())

    def test_missing_kis_settings_has_actionable_message_without_raw_exception(self):
        from data.krx.kis_client import KISUnavailable
        with patch.object(self.service, 'load', side_effect=KISUnavailable('SECRET')):
            self.pane.stream_button.click()
            self.wait_idle()
        self.assertIn('KIS_APP_KEY', self.pane.status.text())
        self.assertIn('.env', self.pane.status.text())
        self.assertNotIn('SECRET)', self.pane.status.text())
        self.assertFalse(self.streams)
        self.assertTrue(self.pane.stream_button.isEnabled())

    def test_old_request_result_cannot_overwrite_new_symbol(self):
        self.service.entered, self.service.release = threading.Event(), threading.Event()
        self.assertTrue(self.pane.refresh(manual=True))
        self.assertTrue(self.service.entered.wait(2))
        self.pane.symbol.setText("000660")
        self.service.release.set()
        self.wait_idle()
        self.assertIsNone(self.pane.snapshot)
        self.assertEqual(self.pane.request().instrument.code, "000660")
        self.assertEqual(self.pane.quote.text(), "")

    def test_stream_callbacks_are_queued_and_stop_discards_late_ticks(self):
        self.load()
        p = self.pane
        self.connect_stream()
        stream = self.streams[-1]
        self.assertTrue(stream.started)
        self.assertIn("첫 체결 대기", p.status.text())
        tick = MarketTick(p.snapshot.request.instrument,
                          datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"),
                          225, volume=2, cumulative_volume=1121,
                          received_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        # A real stream calls from a non-GUI thread, just like this fixture.
        worker = threading.Thread(target=lambda: stream.on_tick(tick))
        worker.start()
        worker.join()
        self.app.processEvents()
        # The coalescing timer is 200ms; CI may schedule its paint later under
        # load. Require the visible quote to arrive within a bounded deadline.
        self.wait_for_ui(lambda: '225' in p.quote.text())
        self.assertEqual(p.snapshot.quote.price, 225)
        self.assertIn("225", p.quote.text())
        retained = p.snapshot
        p.stop()
        self.assertTrue(stream.stopped)
        stream.on_tick(replace(tick, price=900, cumulative_volume=1122))
        self.app.processEvents()
        self.assertIs(p.snapshot, retained)

    def test_old_market_timestamp_is_labelled_stale_despite_fresh_transport(self):
        self.load()
        p = self.pane
        self.connect_stream()
        old = datetime.now(timezone(timedelta(hours=9))) - timedelta(minutes=16)
        tick = MarketTick(p.snapshot.request.instrument, old.isoformat(timespec="seconds"), 225,
                          volume=2, cumulative_volume=1121,
                          received_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        self.streams[-1].on_tick(tick)
        self.app.processEvents()
        self.wait_for_ui(lambda: '지연·오래된 체결' in p.status.text())
        self.assertIn("지연·오래된 체결", p.status.text())

    def test_reconnect_gap_requires_authoritative_reload_before_merging(self):
        self.load()
        p = self.pane
        self.connect_stream()
        stream = self.streams[-1]
        retained = p.snapshot
        stream.on_status("RECONNECTING")
        stream.on_status("SUBSCRIBED")
        stream.on_tick(MarketTick(p.snapshot.request.instrument,
            datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds"), 900,
            volume=300, cumulative_volume=1419,
            received_at=datetime.now(timezone.utc).isoformat(timespec="seconds")))
        self.app.processEvents()
        self.assertIs(p.snapshot, retained)
        self.assertIn("연결 공백", p.status.text())
        p.stop()
        count = len(self.service.calls)
        self.connect_stream()
        self.assertEqual(len(self.service.calls), count + 1)
        self.assertTrue(stream.stopped)
        self.assertFalse(p._stream_gap)
        self.assertTrue(self.streams[-1].started)

    def test_hide_stops_stream_and_polling_and_does_not_restart_on_show(self):
        self.load()
        p = self.pane
        p.poll_button.setChecked(True)
        self.wait_idle()
        self.assertTrue(p.poll_timer.isActive())
        self.connect_stream()
        self.assertFalse(p.poll_timer.isActive())
        stream = self.streams[-1]
        p.hide()
        self.app.processEvents()
        self.assertTrue(stream.stopped)
        self.assertFalse(p.poll_timer.isActive())
        self.assertFalse(p.age_timer.isActive())
        count = len(self.service.calls)
        p.show()
        self.app.processEvents()
        self.assertEqual(len(self.service.calls), count)
        self.assertIsNone(p._stream)

    def test_each_new_stream_synchronizes_history_before_subscribing(self):
        self.load()
        p = self.pane
        old = replace(p.snapshot, fetched_at=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat())
        p.snapshot = old
        self.service.entered, self.service.release = threading.Event(), threading.Event()
        p.start_stream()
        self.assertTrue(self.service.entered.wait(2))
        self.assertEqual(self.streams, [])
        self.assertIs(p.snapshot, old)
        self.service.release.set()
        self.wait_idle()
        self.assertEqual(len(self.service.calls), 2)
        self.assertIsNot(p.snapshot, old)
        self.assertTrue(self.streams[-1].started)
        p.stop()
        p.hide()
        p.show()
        self.app.processEvents()
        self.connect_stream()
        self.assertEqual(len(self.service.calls), 3)
        self.assertEqual(len(self.streams), 2)

    def test_hide_cancels_subscription_pending_history_sync(self):
        self.load()
        p = self.pane
        retained = p.snapshot
        self.service.entered, self.service.release = threading.Event(), threading.Event()
        p.start_stream()
        self.assertTrue(self.service.entered.wait(2))
        p.hide()
        self.service.release.set()
        self.wait_idle()
        self.assertEqual(self.streams, [])
        self.assertIs(p.snapshot, retained)
        self.assertIsNone(p._pending_stream_epoch)
        p.show()
        self.app.processEvents()
        self.assertEqual(self.streams, [])

    def test_live_ticks_pin_historical_cursor_by_timestamp_and_only_follow_latest(self):
        self.load()
        p = self.pane
        self.connect_stream()
        p.move_cursor(40)
        selected = p.snapshot.candles[p._cursor].timestamp
        tomorrow = datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)
        first = MarketTick(p.snapshot.request.instrument, tomorrow.isoformat(timespec="seconds"), 225,
                           volume=2, cumulative_volume=1121,
                           received_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        self.streams[-1].on_tick(first)
        self.app.processEvents()
        self.wait_for_ui(lambda: p.chart.snapshot is p.snapshot)
        self.assertEqual(p.snapshot.candles[p._cursor].timestamp, selected)
        self.assertIn(selected, p.reading.text())
        p.move_cursor(len(p.snapshot.candles) - 1)
        second = replace(first, timestamp=(tomorrow + timedelta(days=1)).isoformat(timespec="seconds"),
                         cumulative_volume=1123)
        self.streams[-1].on_tick(second)
        self.app.processEvents()
        self.wait_for_ui(lambda: p.chart.snapshot is p.snapshot)
        self.assertEqual(p._cursor, len(p.snapshot.candles) - 1)
        self.assertIn(second.timestamp[:10], p.reading.text())

    def test_failure_preserves_same_snapshot_marks_stale_and_redacts_details(self):
        self.load()
        retained = self.pane.snapshot
        self.service.fail = True
        self.pane.refresh(manual=True)
        self.wait_idle()
        self.assertIs(self.pane.snapshot, retained)
        self.assertIn("오래된", self.pane.status.text())
        self.assertNotIn("secrets", self.pane.status.text())
        self.assertNotIn("URLs", self.pane.status.text())

    def test_capability_selector_disables_unsupported_bond_timeframes(self):
        p = self.pane
        p.asset.setCurrentIndex(p.asset.findData("bond"))
        for index in range(p.interval.count()):
            self.assertEqual(p.interval.model().item(index).isEnabled(),
                             p.interval.itemData(index) == "1d")
        self.assertEqual(p.interval.currentData(), "1d")
        self.assertIn("10,000", p.availability.text())
        p.asset.setCurrentIndex(p.asset.findData("domestic_future"))
        self.assertTrue(p.exchange.isEnabled())
        p.exchange.setCurrentIndex(p.exchange.findData("CF"))
        self.assertEqual(p.request().instrument.exchange, "CF")
        future_index = p.asset.findData("overseas_future")
        self.assertEqual(p.asset.itemText(future_index), "해외선물")
        p.set_locale(LocaleContext("en_US"))
        self.assertEqual(p.asset.itemText(future_index), "Overseas futures")

    def test_derivative_and_tiny_option_quotes_preserve_precision_and_correct_unit(self):
        p = self.pane
        p.asset.setCurrentIndex(p.asset.findData("domestic_future"))
        self.load()
        for price, expected in ((123.456789, "123.456789"), (.00505, "0.00505")):
            with self.subTest(price=price):
                p.snapshot = replace(p.snapshot, quote=replace(p.snapshot.quote, price=price))
                p.render()
                self.assertIn(expected, p.quote.text())
        self.assertIn("계약 시세 단위", p.quote.text())
        self.assertNotIn("KRW", p.quote.text())


if __name__ == "__main__":
    unittest.main()
