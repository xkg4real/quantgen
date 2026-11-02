"""Browser market lifecycle checks using real Flet controls and injected feeds."""
from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime, timedelta
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from core.i18n import LocaleContext
from core.market.models import Candle, ChartRequest, Instrument, MarketQuote, MarketSnapshot, MarketTick
from ui.market_chart_page import MarketChartPage


def snapshot(request=None):
    request = request or ChartRequest(Instrument(), "1m", 240)
    start = datetime.fromisoformat("2026-11-02T09:00:00+09:00")
    candles = tuple(Candle((start + timedelta(minutes=i)).isoformat(), 100 + i, 102 + i,
                           99 + i, 101 + i, 10) for i in range(80))
    quote = MarketQuote(request.instrument, price=180, currency="KRW", volume=800,
                        market_time=candles[-1].timestamp, received_at=candles[-1].timestamp)
    return MarketSnapshot(request, candles, quote, candles[-1].timestamp, note="fixture")


class Page:
    width = 1000
    qg_locale = LocaleContext("ko_KR")
    qg_theme = "light"

    def __init__(self):
        self.tasks = []

    def run_task(self, handler, *args):
        task = asyncio.create_task(handler(*args))
        self.tasks.append(task)
        return task


class View(MarketChartPage):
    def _update_view(self):
        self.updates = getattr(self, "updates", 0) + 1


class Stream:
    def __init__(self):
        self.started = False
        self.stopped = False

    def start(self, instrument, on_tick, on_status):
        self.started = True
        self.instrument, self.on_tick, self.on_status = instrument, on_tick, on_status
        on_status("SUBSCRIBED")

    def stop(self):
        self.stopped = True


class WebMarketTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.page = Page()
        self.service = SimpleNamespace(load=Mock(side_effect=lambda request: snapshot(request)))
        self.streams = []
        def stream_factory():
            stream = Stream()
            self.streams.append(stream)
            return stream
        self.view = View(self.page, service=self.service, stream_factory=stream_factory)
        self.view.interval.value = "1m"
        self.view.did_mount()

    async def asyncTearDown(self):
        self.view.deactivate()
        for task in self.page.tasks:
            task.cancel()
        await asyncio.gather(*self.page.tasks, return_exceptions=True)

    async def wait_until(self, predicate):
        for _ in range(100):
            if predicate():
                return
            await asyncio.sleep(.01)
        self.fail("Timed out waiting for injected worker")

    async def test_construct_and_mount_never_query_provider(self):
        self.service.load.assert_not_called()
        self.assertEqual(self.streams, [])
        self.assertFalse(self.view.image.visible)
        self.assertEqual(self.view.current_request().limit, 240)

    async def test_load_renders_shared_chart_source_and_readout(self):
        self.assertTrue(await self.view.load_chart())
        self.assertTrue(self.view.image.src.startswith("data:image/svg+xml;base64,"))
        self.assertIn("005930", self.view.image.semantics_label)
        self.assertIn("2026-11-02", self.view.source.value)
        self.assertIn("SMA20", self.view.metrics.value)
        self.assertIn("V 10", self.view.reading.value)
        self.assertIsNone(self.view.cursor)

    async def test_current_price_keeps_small_contract_precision(self):
        request = self.view.current_request()
        data = snapshot(request)
        self.service.load.side_effect = None
        self.service.load.return_value = replace(data, quote=replace(data.quote, price=.00505))
        await self.view.load_chart()
        self.assertIn("0.00505", self.view.price.value)

    async def test_bad_input_never_calls_provider_and_errors_never_show_urls(self):
        self.view.code.value = "../.env"
        self.assertFalse(await self.view.load_chart())
        self.service.load.assert_not_called()
        self.view.code.value = "005930"
        self.service.load.side_effect = RuntimeError("https://host/?appsecret=SECRET")
        self.assertFalse(await self.view.load_chart())
        self.assertNotIn("SECRET", self.view.status.value)
        self.assertNotIn("https://", self.view.status.value)

    async def test_late_symbol_response_cannot_replace_new_selection(self):
        started, release = threading.Event(), threading.Event()
        def blocking(request):
            started.set()
            release.wait(2)
            return snapshot(request)
        self.service.load.side_effect = blocking
        task = asyncio.create_task(self.view.load_chart())
        await self.wait_until(started.is_set)
        self.view.code.value = "000660"
        self.view.inputs_changed()
        release.set()
        self.assertFalse(await task)
        self.assertIsNone(self.view.snapshot)
        self.assertFalse(self.view.image.visible)

    async def test_same_request_failure_retains_old_data_with_stale_label(self):
        await self.view.load_chart()
        prior = self.view.snapshot
        self.service.load.side_effect = RuntimeError("secret")
        await self.view.load_chart()
        self.assertIs(self.view.snapshot, prior)
        self.assertTrue(self.view._stale)
        self.assertIn("이전 결과", self.view.status.value)
        self.view.code.value = "000660"
        self.view.inputs_changed()
        await self.view.load_chart()
        self.assertIsNone(self.view.snapshot)
        self.assertNotIn("이전 결과", self.view.status.value)

    async def test_polling_cancels_on_navigation_and_does_not_resume_automatically(self):
        self.view.auto.value = True
        await self.view.toggle_auto()
        self.assertEqual(self.service.load.call_count, 1)
        future = self.view._poll_future
        self.view.deactivate()
        await asyncio.sleep(0)
        self.assertTrue(future.cancelled())
        self.assertFalse(self.view.auto.value)
        self.view.did_mount()
        self.assertIsNone(self.view._poll_future)
        self.assertEqual(self.service.load.call_count, 1)

    async def test_stream_ticks_update_snapshot_and_stale_callbacks_are_fenced(self):
        await self.view.start_live()
        stream = self.streams[-1]
        await asyncio.sleep(0)
        self.assertTrue(stream.started)
        tick = MarketTick(Instrument(), "2026-11-02T10:19:30+09:00", 190, 3, 803,
                          received_at="2026-11-02T01:19:30+00:00")
        stream.on_tick(tick)
        await asyncio.sleep(.2)
        self.assertEqual(self.view.snapshot.candles[-1].close, 190)
        self.assertEqual(self.view.snapshot.quote.price, 190)
        self.view.stop_live()
        prior = self.view.snapshot
        stream.on_tick(MarketTick(Instrument(), "2026-11-02T10:20:00+09:00", 200, 3, 806))
        stream.on_status("LIVE")
        await asyncio.sleep(.2)
        self.assertIs(self.view.snapshot, prior)
        self.assertTrue(stream.stopped)
        self.assertEqual(self.view._stream_state, "STOPPED")

    async def test_stop_while_initial_load_runs_prevents_late_stream_start(self):
        started, release = threading.Event(), threading.Event()
        def blocking(request):
            started.set()
            release.wait(2)
            return snapshot(request)
        self.service.load.side_effect = blocking
        task = asyncio.create_task(self.view.start_live())
        await self.wait_until(started.is_set)
        self.view.stop_live()
        release.set()
        await task
        self.assertEqual(self.streams, [])

    async def test_returning_cached_view_loads_fresh_history_before_subscribing(self):
        await self.view.load_chart()
        prior = self.view.snapshot
        self.view.deactivate()
        self.view.did_mount()
        await self.view.start_live()
        self.assertEqual(self.service.load.call_count, 2)
        self.assertIsNot(self.view.snapshot, prior)
        self.assertTrue(self.streams[-1].started)

    async def test_failed_fresh_history_load_cannot_subscribe_using_cached_bars(self):
        await self.view.load_chart()
        prior = self.view.snapshot
        self.view.deactivate()
        self.view.did_mount()
        self.service.load.side_effect = RuntimeError("unavailable")
        await self.view.start_live()
        self.assertEqual(self.service.load.call_count, 2)
        self.assertIs(self.view.snapshot, prior)
        self.assertTrue(self.view._stale)
        self.assertEqual(self.streams, [])

    async def test_reconnect_gap_warning_persists_after_new_ticks(self):
        await self.view.start_live()
        stream = self.streams[-1]
        before = self.view.snapshot
        stream.on_status("RECONNECTING")
        await asyncio.sleep(0)
        stream.on_status("SUBSCRIBED")
        stream.on_tick(MarketTick(Instrument(), "2026-11-02T10:20:00+09:00", 190, 3, 803))
        await asyncio.sleep(.2)
        self.assertTrue(self.view._gap_warning)
        self.assertTrue(self.view._stale)
        self.assertIs(self.view.snapshot, before)
        self.assertIn("재조회", self.view.stream_status.value)
        self.assertIn("불완전", self.view.status.value)

    async def test_duplicate_tick_does_not_reset_freshness_clock(self):
        await self.view.start_live()
        tick = MarketTick(Instrument(), "2026-11-02T10:19:30+09:00", 190, 3, 803)
        self.streams[-1].on_tick(tick)
        await asyncio.sleep(.2)
        prior = self.view.snapshot
        accepted_at = self.view._last_tick
        self.streams[-1].on_tick(tick)
        await asyncio.sleep(.2)
        self.assertIs(self.view.snapshot, prior)
        self.assertEqual(self.view._last_tick, accepted_at)

    async def test_asian_quote_delay_stays_visible_in_stream_status(self):
        self.view.asset.value = "overseas_stock"
        self.view.asset_changed()
        self.view.exchange.value = "HKS"
        self.view.code.value = "00700"
        self.view.inputs_changed()
        await self.view.start_live()
        self.assertIn("15분 지연", self.view.stream_status.value)

    async def test_cursor_selection_and_zoom_match_the_svg_viewport(self):
        await self.view.load_chart()
        self.view.zoom.value = 20
        self.view.zoom_changed()
        self.view.cursor_slider.value = 0
        self.view.cursor_changed()
        self.assertEqual(self.view.cursor, 0)
        self.assertEqual(self.view.visible_bars, 80)
        self.assertIn(self.view.snapshot.candles[0].timestamp, self.view.reading.value)
        self.view.zoom.value = 20
        self.view.zoom_changed()
        self.assertEqual(self.view.cursor, 60)
        self.assertIn(self.view.snapshot.candles[60].timestamp, self.view.reading.value)

    async def test_capability_selection_and_disconnect_cleanup(self):
        self.view.asset.value = "bond"
        self.view.asset_changed()
        self.assertEqual([option.key for option in self.view.interval.options], ["1d"])
        self.assertEqual(self.view.interval.value, "1d")
        self.assertIn("100", self.view.coverage.value)
        self.view.asset.value = "domestic_future"
        self.view.asset_changed()
        self.view.code.value = "101W12"
        self.view.exchange.value = "F"
        self.assertEqual(self.view.current_request().instrument.exchange, "F")
        self.view.deactivate()
        self.view.reconnect_session()
        self.assertTrue(self.view.mounted)
        self.assertEqual(self.streams, [])

    async def test_idle_stream_reports_absence_of_recent_trades(self):
        await self.view.start_live()
        with patch("ui.market_chart_page.time.monotonic", return_value=self.view._stream_started + 31):
            self.view._render_stream_status()
        self.assertIn("30초", self.view.stream_status.value)


if __name__ == "__main__":
    unittest.main()
