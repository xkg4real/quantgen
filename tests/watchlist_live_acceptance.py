"""Offline tests for one-socket watchlist subscriptions and native event safety."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from core.market.models import Instrument, MarketSnapshot, MarketTick
from core.research.watchlist import KR_STOCK_SPECS
from data import kis_stream
from tests.kis_stream_acceptance import FakeConnection, domestic_row, frame

STOCKS = tuple(Instrument(code=code) for _, code, _ in KR_STOCK_SPECS)
NOW = datetime(2026, 11, 2, 2, 15, tzinfo=timezone.utc)


def ack(code, result="0"):
    return json.dumps({"header": {"tr_id": "H0STCNT0", "tr_key": code},
                       "body": {"rt_cd": result, "msg1": "PRIVATE_PROVIDER_MESSAGE"}})


class MultiSubscriptionTests(unittest.TestCase):
    def setUp(self):
        client = SimpleNamespace(ready=True, base_url="https://openapi.koreainvestment.com:9443", timeout_s=.2)
        self.source = kis_stream.KISStream(client)
        self.addCleanup(self.source.stop)

    def test_six_subscriptions_share_one_socket_and_route_batched_ticks(self):
        connection = FakeConnection([ack(i.code) for i in STOCKS])
        accepted, arrived = threading.Event(), threading.Event()
        statuses, ticks = [], []
        def status(value):
            statuses.append(value)
            if value == "SUBSCRIBED": accepted.set()
        def tick(value):
            ticks.append(value)
            if len(ticks) == 2: arrived.set()
        with patch.object(kis_stream, "_approval_key", return_value="PRIVATE_KEY"), \
             patch.object(kis_stream, "_connect", return_value=connection) as connect:
            self.source.start_many(STOCKS, tick, status)
            self.assertTrue(accepted.wait(1))
            self.assertEqual(statuses.count("SUBSCRIBED"), 1)
            self.assertNotIn("LIVE", statuses)
            connection.queue.put(frame("H0STCNT0", [domestic_row(code=STOCKS[0].code),
                domestic_row(code=STOCKS[1].code, price="190000")]))
            self.assertTrue(arrived.wait(1))
            self.source.stop()
            self.assertEqual(connect.call_count, 1)
            self.assertEqual([t.instrument for t in ticks], list(STOCKS[:2]))
            self.assertEqual([t.price for t in ticks], [70000, 190000])
            self.assertEqual([m["header"]["tr_type"] for m in connection.sent], ["1"]*6 + ["2"]*6)
            self.assertEqual([m["body"]["input"]["tr_key"] for m in connection.sent[:6]], [i.code for i in STOCKS])
            self.assertNotIn("PRIVATE", str(statuses) + str(ticks))

    def test_partial_and_ambiguous_ack_do_not_claim_all_subscribed(self):
        ambiguous = json.dumps({"header": {"tr_id": "H0STCNT0"}, "body": {"rt_cd": "0"}})
        connection = FakeConnection([ack(STOCKS[0].code), ambiguous, ack("999999")])
        statuses, accepted = [], threading.Event()
        def status(value):
            statuses.append(value)
            if value == "SUBSCRIBED": accepted.set()
        with patch.object(kis_stream, "_approval_key", return_value="key"), \
             patch.object(kis_stream, "_connect", return_value=connection):
            self.source.start_many(STOCKS[:2], lambda _: None, status)
            self.assertFalse(accepted.wait(.1))
            connection.queue.put(ack(STOCKS[1].code))
            self.assertTrue(accepted.wait(1))
            self.source.stop()
        self.assertEqual(statuses.count("SUBSCRIBED"), 1)

    def test_rejection_of_one_subscription_is_terminal_and_sanitized(self):
        connection = FakeConnection([ack(STOCKS[0].code), ack(STOCKS[1].code, "1")])
        failed, statuses = threading.Event(), []
        def status(value):
            statuses.append(value)
            if value.startswith("ERROR"): failed.set()
        with patch.object(kis_stream, "_approval_key", return_value="key"), \
             patch.object(kis_stream, "_connect", return_value=connection) as connect:
            self.source.start_many(STOCKS[:2], lambda _: None, status)
            self.assertTrue(failed.wait(1))
            self.source.stop()
            self.assertEqual(connect.call_count, 1)
        self.assertNotIn("SUBSCRIBED", statuses)
        self.assertNotIn("PRIVATE", str(statuses))

    def test_invalid_watchlist_is_rejected_before_provider_access(self):
        for instruments in ((), STOCKS + (Instrument(code="035420"),),
                            (STOCKS[0], STOCKS[0]), (Instrument("overseas_stock", "AAPL", "NAS"),)):
            with self.subTest(instruments=instruments), \
                 patch.object(kis_stream, "_approval_key", side_effect=AssertionError("network")):
                with self.assertRaises(ValueError):
                    self.source.start_many(instruments, lambda _: None, lambda _: None)
                self.assertFalse(self.source.running)


HAS_QT = importlib.util.find_spec("PyQt6") is not None
if HAS_QT:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication
    from quantgen_desktop.watchlist_live import WatchlistLiveController


class FakeService:
    ready = True
    def __init__(self, failures=()):
        self.calls = []
        self.threads = []
        self.failures = failures
    def load(self, request):
        self.calls.append(request)
        self.threads.append(threading.get_ident())
        if request.instrument.symbol in self.failures:
            raise RuntimeError("PRIVATE_TOKEN_IN_PROVIDER_URL")
        return MarketSnapshot(request, (), fetched_at=NOW.isoformat())


class FakeStream:
    def __init__(self):
        self.stopped = False
        self.instruments = ()
    def start_many(self, instruments, on_tick, on_status):
        self.instruments = instruments
        self.on_tick, self.on_status = on_tick, on_status
        on_status("SUBSCRIBED")
    def stop(self):
        self.stopped = True


@unittest.skipUnless(HAS_QT, "PyQt6 desktop extra is not installed")
class WatchlistControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def wait_until(self, predicate, timeout=2):
        deadline = time.monotonic() + timeout
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.002)
        self.app.processEvents()
        self.assertTrue(predicate())

    def make(self, service=None):
        self.service = service or FakeService()
        self.streams = []
        def factory():
            stream = FakeStream()
            self.streams.append(stream)
            return stream
        self.clock = NOW
        controller = WatchlistLiveController(service=self.service, stream_factory=factory,
                                             now=lambda: self.clock)
        self.addCleanup(controller.close)
        return controller

    def tick(self, instrument=STOCKS[0], **kwargs):
        return replace(MarketTick(instrument, NOW.isoformat(), 70000, 7, 10007,
                       -100, -.14, NOW.isoformat()), **kwargs)

    def test_history_runs_off_gui_and_failure_isolated_before_one_subscription(self):
        controller = self.make(FakeService(failures=(STOCKS[1].symbol,)))
        history, errors, states = [], [], []
        controller.history_ready.connect(lambda s, h: history.append((s, h, threading.get_ident())))
        controller.history_failed.connect(lambda s, c: errors.append((s, c)))
        controller.state_changed.connect(states.append)
        self.assertTrue(controller.start())
        self.wait_until(lambda: controller.state == "subscribed")
        self.assertEqual(len(self.service.calls), 6)
        self.assertTrue(all(r.adjusted and r.interval == "1d" and r.limit == 252 for r in self.service.calls))
        self.assertTrue(all(t != threading.get_ident() for t in self.service.threads))
        self.assertEqual(len(history), 5)
        self.assertTrue(all(t == threading.get_ident() for _, _, t in history))
        self.assertEqual(errors, [(STOCKS[1].symbol, "RuntimeError")])
        self.assertEqual(len(self.streams), 1)
        self.assertEqual(self.streams[0].instruments, STOCKS)
        self.assertNotIn("streaming", states)
        self.assertNotIn("PRIVATE", str(errors) + str(states))

    def test_only_fresh_ordered_real_ticks_emit_and_gap_requires_restart(self):
        controller = self.make()
        ticks = []
        controller.tick_received.connect(ticks.append)
        controller.start()
        self.wait_until(lambda: bool(self.streams))
        source = self.streams[0]
        tick = self.tick()
        source.on_tick(tick)
        self.app.processEvents()
        self.assertEqual(ticks, [tick])
        self.assertEqual(controller.state, "streaming")
        for invalid in (tick, replace(tick, cumulative_volume=10006),
                replace(tick, timestamp=(NOW-timedelta(seconds=1)).isoformat(), cumulative_volume=10008),
                replace(tick, timestamp=(NOW-timedelta(seconds=61)).isoformat()),
                replace(tick, timestamp=(NOW+timedelta(seconds=6)).isoformat()),
                replace(tick, received_at=(NOW-timedelta(seconds=61)).isoformat()),
                replace(tick, price=float("nan")), replace(tick, change_pct=float("inf")),
                replace(tick, cumulative_volume=None), replace(tick, volume=-1),
                replace(tick, source="SYNTHETIC"), replace(tick, received_at="2026-11-02T02:15:00"),
                self.tick(Instrument(code="035420"))):
            source.on_tick(invalid)
        self.app.processEvents()
        self.assertEqual(ticks, [tick])
        newer = replace(tick, cumulative_volume=10008, price=70010)
        source.on_tick(newer)
        self.app.processEvents()
        self.assertEqual(ticks, [tick, newer])
        self.clock = NOW + timedelta(seconds=16)
        controller._age()
        self.assertEqual(controller.state, "stale")
        source.on_status("RECONNECTING")
        source.on_status("SUBSCRIBED")
        source.on_tick(replace(newer, cumulative_volume=10009))
        self.app.processEvents()
        self.assertEqual(ticks, [tick, newer])
        self.assertEqual(controller.state, "stale")
        controller.stop()
        source.on_tick(replace(newer, cumulative_volume=10010))
        self.app.processEvents()
        self.assertEqual(ticks, [tick, newer])
        self.assertTrue(source.stopped)

    def test_stop_during_history_drops_late_data_and_prevents_subscription(self):
        entered, release = threading.Event(), threading.Event()
        class BlockingService(FakeService):
            def load(self, request):
                entered.set()
                release.wait(2)
                return super().load(request)
        controller = self.make(BlockingService())
        history = []
        controller.history_ready.connect(lambda *args: history.append(args))
        controller.start()
        self.assertTrue(entered.wait(1))
        self.assertFalse(controller.close())
        self.assertFalse(controller.active)
        self.assertFalse(controller.start())
        release.set()
        self.wait_until(lambda: not controller.busy)
        self.assertEqual(history, [])
        self.assertEqual(self.streams, [])
        self.assertEqual(len(self.service.calls), 1)
        self.assertTrue(controller.start())
        self.wait_until(lambda: bool(self.streams))

    def test_missing_credentials_and_errors_do_not_publish_provider_messages(self):
        service = FakeService()
        service.ready = False
        controller = self.make(service)
        errors = []
        controller.history_failed.connect(lambda s, c: errors.append(c))
        self.assertFalse(controller.start())
        self.assertEqual(controller.state, "error")
        self.assertEqual(errors, ["KISUnavailable"]*6)
        self.assertEqual(service.calls, [])
        service.ready = True
        controller.start()
        self.wait_until(lambda: bool(self.streams))
        self.streams[0].on_status("ERROR: PRIVATE_PROVIDER_TOKEN")
        self.app.processEvents()
        self.assertFalse(controller.active)
        self.assertEqual(controller.state, "error")
        self.assertTrue(self.streams[0].stopped)


if __name__ == "__main__":
    unittest.main()
