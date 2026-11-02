"""Offline Q-SCORE lifecycle checks with real computation and bounded fake I/O."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import importlib.util
import math
import os
import threading
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
HAS_QT = importlib.util.find_spec("PyQt6") is not None

if HAS_QT:
    from PyQt6.QtCore import QThread
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication
    from core.market.models import Candle, ChartRequest, Instrument, MarketSnapshot, MarketTick
    from core.research.qscore import compute_q_score
    from quantgen_desktop.qscore import QScoreController

    NOW = datetime(2026, 11, 2, 2, 0, 0, tzinfo=timezone.utc)

    def history(instrument=None, *, now=NOW, fetched_at=None):
        instrument = instrument or Instrument()
        today = now.astimezone(timezone(timedelta(hours=9))).date()
        candles = []
        for i in range(252):
            price = 100 + i * .07 + math.sin(i / 6) * 2
            candles.append(Candle((today - timedelta(days=252 - i)).isoformat(),
                                  price, price + 1, price - 1, price, 1000 + i))
        return MarketSnapshot(ChartRequest(instrument, "1d", 252, adjusted=True), tuple(candles),
                              fetched_at=fetched_at or now.isoformat(), source="KIS REST")

    def tick(instrument=None, *, price=119, stamp=NOW, cumulative=1000):
        return MarketTick(instrument or Instrument(), stamp.isoformat(), price,
                          volume=10, cumulative_volume=cumulative, received_at=stamp.isoformat())

    class FakeService:
        ready = True

        def __init__(self, clock):
            self.clock = clock
            self.calls = []
            self.threads = []
            self.entered = self.release = None
            self.fail = False

        def load(self, request):
            self.calls.append(request)
            self.threads.append(QThread.currentThread())
            if self.entered is not None:
                self.entered.set()
                self.release.wait(3)
            if self.fail:
                raise RuntimeError("SECRET https://provider?key=SECRET")
            return history(request.instrument, now=self.clock())


@unittest.skipUnless(HAS_QT, "PyQt6 optional desktop dependency is unavailable")
class NativeQScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.clock = NOW
        self.service = FakeService(lambda: self.clock)
        self.controller = QScoreController(service=self.service, now=lambda: self.clock)
        self.events = []
        self.controller.score_changed.connect(lambda symbol, score: self.events.append((symbol, score)))
        guard = patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        guard.start()
        self.addCleanup(guard.stop)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.controller.stop()
        if self.service.release is not None:
            self.service.release.set()
        self.wait_idle()
        self.controller.deleteLater()
        self.app.processEvents()

    def wait_idle(self):
        for _ in range(300):
            self.app.processEvents()
            if not self.controller.jobs.busy:
                return
            QTest.qWait(10)
        self.fail("History worker did not finish")

    def prepare(self):
        self.assertTrue(self.controller.set_history("005930", history()))
        self.controller.set_feed_state("streaming")

    def score(self, symbol="005930"):
        return self.controller.scores()[symbol]

    def test_history_only_is_non_live_and_scores_are_isolated(self):
        self.assertEqual(self.service.calls, [])
        self.assertTrue(self.controller.set_history("005930", history()))
        score = self.score()
        self.assertEqual(score["status"], "ready")
        self.assertFalse(score["live"])
        self.assertEqual(score["as_of"], "2026-11-01")
        score["components"].clear()
        self.assertTrue(self.score()["components"])
        self.assertFalse(self.controller.set_history("000660", history()))
        self.assertFalse(self.controller.set_history("005930", replace(history(), source="SYNTHETIC")))

    def test_trade_burst_is_coalesced_at_one_hz_without_mutating_daily_baseline(self):
        self.prepare()
        before = self.controller._histories["005930"]
        with patch("quantgen_desktop.qscore.compute_q_score", wraps=compute_q_score) as compute:
            for number in range(10):
                self.assertTrue(self.controller.accept_tick(tick(price=118 + number / 10, cumulative=1000 + number)))
            self.assertEqual(compute.call_count, 0)
            QTest.qWait(1050)
            self.assertEqual(compute.call_count, 1)
            self.assertEqual(compute.call_args.kwargs["latest_price"], 118.9)
        self.assertTrue(self.score()["live"])
        self.assertEqual(self.score()["as_of"], NOW.isoformat())
        self.assertEqual(self.score()["last_price"], 118.9)
        self.assertIs(self.controller._histories["005930"], before)

    def test_invalid_stale_replayed_and_foreign_trades_are_not_scored(self):
        self.prepare()
        valid = tick()
        self.assertTrue(self.controller.accept_tick(valid))
        self.controller._flush_ticks()
        retained = self.score()
        invalid = [replace(valid, price=float("nan")), replace(valid, price=True),
                   replace(valid, instrument=None),
                   replace(valid, source="SYNTHETIC"), replace(valid, volume=-1),
                   replace(valid, received_at=""), replace(valid, timestamp="2026-11-02T02:00:00"),
                   tick(stamp=NOW - timedelta(seconds=121), cumulative=2000),
                   tick(stamp=NOW + timedelta(seconds=6), cumulative=2000),
                   tick(instrument=Instrument(code="000660")), valid]
        for bad in invalid:
            with self.subTest(tick=bad):
                self.assertFalse(self.controller.accept_tick(bad))
        self.controller._flush_ticks()
        self.assertEqual(self.score(), retained)

    def test_stop_and_disconnect_freeze_last_score_and_discard_pending_trades(self):
        self.prepare()
        self.controller.accept_tick(tick())
        self.controller._flush_ticks()
        last = self.score()
        self.controller.accept_tick(tick(price=120, cumulative=1010))
        self.controller.set_feed_state("stale")
        self.assertFalse(self.score()["live"])
        self.assertEqual(self.score()["feed_state"], "stale")
        self.controller._flush_ticks()
        self.assertEqual(self.score()["last_price"], last["last_price"])
        self.controller.set_feed_state("polling")
        self.assertEqual(self.score()["feed_state"], "polling")
        self.assertFalse(self.score()["live"])
        self.controller.stop()
        self.assertEqual(self.score()["feed_state"], "stopped")
        self.assertFalse(self.controller.accept_tick(tick(price=120, cumulative=1020)))
        self.assertFalse(self.controller.set_history("005930", history()))

    def test_each_symbols_live_flag_expires_without_new_trades(self):
        self.prepare()
        self.controller.accept_tick(tick())
        self.controller._flush_ticks()
        self.assertTrue(self.score()["live"])
        self.clock += timedelta(seconds=121)
        self.controller._flush_ticks()
        self.assertFalse(self.score()["live"])
        self.assertEqual(self.score()["feed_state"], "stale")
        self.assertEqual(self.score()["as_of"], NOW.isoformat())

    def test_jobs_run_off_gui_thread_and_switch_discards_the_previous_result(self):
        self.service.entered, self.service.release = threading.Event(), threading.Event()
        self.assertTrue(self.controller.request_history(Instrument()))
        self.assertTrue(self.service.entered.wait(2))
        self.assertTrue(self.controller.request_history(Instrument(code="000660")))
        self.service.release.set()
        self.wait_idle()
        self.assertNotIn("005930", self.controller.scores())
        self.assertEqual(self.score("000660")["status"], "ready")
        self.assertTrue(all(request.adjusted and request.interval == "1d" and request.limit == 252
                            for request in self.service.calls))
        self.assertTrue(all(thread is not self.app.thread() for thread in self.service.threads))

    def test_stop_invalidates_inflight_result_and_close_reports_busy(self):
        self.service.entered, self.service.release = threading.Event(), threading.Event()
        self.controller.request_history(Instrument())
        self.assertTrue(self.service.entered.wait(2))
        self.assertFalse(self.controller.close())
        self.service.release.set()
        self.wait_idle()
        self.assertEqual(self.controller.scores(), {})
        self.assertTrue(self.controller.close())

    def test_same_day_reuses_history_but_next_day_refreshes_and_missing_config_never_starts(self):
        self.controller.request_history(Instrument())
        self.wait_idle()
        self.controller.request_history(Instrument())
        self.assertEqual(len(self.service.calls), 1)
        self.clock += timedelta(days=1)
        self.controller.request_history(Instrument())
        self.wait_idle()
        self.assertEqual(len(self.service.calls), 2)
        self.service.ready = False
        self.assertFalse(self.controller.request_history(Instrument(code="000660")))
        self.assertFalse(self.controller.jobs.busy)
        self.assertEqual(len(self.service.calls), 2)
        self.assertEqual(self.score("000660")["reason"], "connection_not_configured")

    def test_history_callback_cannot_downgrade_a_fresh_live_score(self):
        self.prepare()
        self.controller.accept_tick(tick())
        self.controller._flush_ticks()
        previous = self.score()
        older = history(fetched_at=(NOW - timedelta(seconds=1)).isoformat())
        self.assertFalse(self.controller.set_history("005930", older))
        self.assertEqual(self.score(), previous)
        old_observations = history(now=NOW - timedelta(days=1), fetched_at=NOW.isoformat())
        self.assertFalse(self.controller.set_history("005930", old_observations))
        self.assertEqual(self.score(), previous)
        self.clock += timedelta(seconds=1)
        self.assertTrue(self.controller.set_history("005930", history(now=self.clock)))
        self.assertEqual(self.score(), previous)
        self.controller._flush_ticks()
        self.assertTrue(self.score()["live"])
        self.assertEqual(self.score()["as_of"], NOW.isoformat())

    def test_history_cache_is_bounded_and_provider_error_is_sanitized(self):
        for i in range(20):
            instrument = Instrument(code=f"{i:06d}")
            self.controller.set_history(instrument.symbol, history(instrument))
        self.assertEqual(len(self.controller.scores()), 16)
        self.assertNotIn("000000", self.controller.scores())
        self.service.fail = True
        self.controller.request_history(Instrument())
        self.wait_idle()
        self.assertEqual(self.score()["reason"], "history_unavailable")
        self.assertNotIn("SECRET", str(self.score()))
        self.assertEqual(len(self.controller.scores()), 16)

    def test_stopped_chart_selection_does_not_filter_the_next_home_session(self):
        self.controller.request_history(Instrument())
        self.wait_idle()
        self.controller.stop()
        self.controller.set_feed_state("loading")
        other = Instrument(code="000660")
        self.assertTrue(self.controller.set_history(other.symbol, history(other)))
        self.controller.set_feed_state("streaming")
        self.assertTrue(self.controller.accept_tick(tick(other)))
        self.controller._flush_ticks()
        self.assertTrue(self.score("000660")["live"])


if __name__ == "__main__":
    unittest.main()
