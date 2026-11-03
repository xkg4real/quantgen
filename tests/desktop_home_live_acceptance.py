"""Complete native Home -> detail -> live chart paths, with fake provider I/O."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import importlib.util
import os
import threading
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
HAS_QT = importlib.util.find_spec("PyQt6") is not None

if HAS_QT:
    import dotenv
    with patch.object(dotenv, "load_dotenv", return_value=False):
        from quantgen_desktop.app import ResearchWindow
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from core.market.models import Instrument, MarketQuote
    from tests.desktop_qscore_acceptance import history, tick


    class Service:
        ready = True

        def __init__(self, now):
            self.now = now
            self.calls = []

        def load(self, request):
            self.calls.append(request)
            data = history(request.instrument, now=self.now())
            bars = data.candles[-request.limit:]
            # REST quote has a receipt time, not a fabricated exchange time.
            quote = MarketQuote(request.instrument, price=bars[-1].close, volume=900,
                                received_at=self.now().isoformat(), source="KIS REST")
            return replace(data, request=request, candles=bars, quote=quote)


    class Stream:
        def __init__(self):
            self.stopped = False

        def start_many(self, instruments, on_tick, on_status):
            self.instruments = tuple(instruments)
            self.on_tick, self.on_status = on_tick, on_status
            on_status("SUBSCRIBED")

        def start(self, instrument, on_tick, on_status):
            self.start_many((instrument,), on_tick, on_status)

        def stop(self):
            self.stopped = True


@unittest.skipUnless(HAS_QT, "PyQt6 optional desktop dependency is unavailable")
class HomeLiveIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        no_network = patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        self.network = no_network.start()
        self.addCleanup(no_network.stop)
        self.clock = datetime.now(timezone.utc)
        self.home_service, self.chart_service, self.score_service = [Service(lambda: self.clock) for _ in range(3)]
        self.home_streams, self.chart_streams = [], []
        self.window = ResearchWindow(auto_refresh=False, language="ko", market_loader=lambda: [])
        w = self.window
        w.home_feed.service = self.home_service
        w.home_feed._now = lambda: self.clock
        w.home_feed.stream_factory = lambda: self.new_stream(self.home_streams)
        w.market_chart.service = self.chart_service
        w.market_chart.stream_factory = lambda: self.new_stream(self.chart_streams)
        w.q_scores.service = self.score_service
        w.q_scores._now = lambda: self.clock
        w.chart_scores.service = self.score_service
        w.chart_scores._now = lambda: self.clock
        w.show()
        self.app.processEvents()
        self.addCleanup(self.cleanup)

    @staticmethod
    def new_stream(collection):
        stream = Stream()
        collection.append(stream)
        return stream

    def wait_until(self, predicate, timeout=4):
        deadline = time.monotonic() + timeout
        while not predicate() and time.monotonic() < deadline:
            self.app.processEvents()
            QTest.qWait(10)
        self.app.processEvents()
        self.assertTrue(predicate())

    def cleanup(self):
        w = self.window
        w.home_feed.stop()
        w.market_chart.stop()
        w.q_scores.stop()
        w.chart_scores.stop()
        self.wait_until(lambda: not (w.home_feed.busy or w.market_chart.jobs.busy or
                                    w.q_scores.jobs.busy or w.chart_scores.jobs.busy))
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            w.close()
        w.deleteLater()
        self.app.processEvents()
        self.network.assert_not_called()

    def start_home(self):
        self.window.watchlist.live_button.click()
        self.wait_until(lambda: self.window.home_feed.state == "subscribed")
        self.assertEqual(len(self.home_streams), 1)

    def publish(self, stream, event):
        worker = threading.Thread(target=lambda: stream.on_tick(event))
        worker.start()
        worker.join(timeout=1)
        self.assertFalse(worker.is_alive())
        self.app.processEvents()

    def test_home_button_streams_six_stocks_and_tick_changes_visible_score_without_http(self):
        w = self.window
        self.assertEqual(self.home_service.calls, [])
        self.assertEqual(self.chart_service.calls, [])
        self.assertEqual(self.score_service.calls, [])
        self.start_home()
        self.assertEqual(len(self.home_service.calls), 6)
        self.assertEqual(len(self.home_streams[0].instruments), 6)
        self.assertEqual(w.watchlist.table.rowCount(), 12)
        initial = w.q_scores.scores()["005930"]
        self.assertEqual(initial["status"], "ready")
        self.assertFalse(initial["live"])
        self.assertIn("★", w.watchlist.table.item(6, w.watchlist.table.columnCount() - 1).text())
        self.publish(self.home_streams[0], tick(price=121, stamp=self.clock))
        self.wait_until(lambda: w.q_scores.scores()["005930"].get("live"))
        live = w.q_scores.scores()["005930"]
        self.assertEqual(live["last_price"], 121)
        self.assertNotEqual(live["score"], initial["score"])
        self.assertIn("121", w.watchlist.table.item(6, 1).text())
        self.assertIn("★", w.watchlist.table.item(6, w.watchlist.table.columnCount() - 1).text())
        self.assertEqual(w.watchlist.rows[6]["q_score"]["as_of"], self.clock.isoformat())
        self.publish(self.home_streams[0], tick(price=116, stamp=self.clock, cumulative=1010))
        self.wait_until(lambda: w.q_scores.scores()["005930"].get("last_price") == 116)
        self.assertNotEqual(w.q_scores.scores()["005930"]["score"], live["score"])
        self.assertEqual(len(self.home_service.calls), 6)
        self.assertEqual(self.chart_service.calls, [])
        self.assertEqual(self.score_service.calls, [])

    def test_details_selects_chart_stops_home_and_updates_candles_and_score_from_same_tick(self):
        w = self.window
        self.start_home()
        w.watchlist.table.cellWidget(6, w.watchlist.table.columnCount() - 2).click()
        self.app.processEvents()
        dialog = w.watchlist.detail_dialog
        self.assertTrue(dialog.isVisible())
        dialog.chart_button.click()
        self.app.processEvents()
        self.assertTrue(self.home_streams[0].stopped)
        self.assertFalse(w.home_feed.active)
        self.assertEqual(w.stack.currentIndex(), w.route_indices["markets"])
        self.assertIs(w.current_market_pane(), w.market_chart)
        self.assertEqual(w.market_chart.symbol.text(), "005930")
        self.assertEqual(self.chart_service.calls, [])
        self.assertEqual(self.score_service.calls, [])
        p = w.market_chart
        p.load_button.click()
        self.wait_until(lambda: p.snapshot is not None and not p.jobs.busy and not w.chart_scores.jobs.busy)
        self.assertEqual(len(self.chart_service.calls), 1)
        self.assertEqual(len(self.score_service.calls), 1)
        self.wait_until(lambda: bool(self.chart_streams) and not p.jobs.busy)
        self.assertEqual(len(self.chart_streams), 1)
        self.assertEqual(len(self.chart_service.calls), 1)  # Load automatically subscribes.
        self.assertEqual(len(self.score_service.calls), 1)  # Reuse same-day score history.
        self.publish(self.chart_streams[0], tick(price=121, stamp=self.clock, cumulative=1000))
        self.wait_until(lambda: w.chart_scores.scores().get("005930", {}).get("live"))
        self.assertEqual(p.snapshot.quote.price, 121)
        self.assertEqual(p.snapshot.candles[-1].close, 121)
        self.assertTrue(p.chart.renderer().isValid())
        self.assertIn("121", p.quote.text())
        self.assertTrue(p.q_score_label.isVisible())
        self.assertIn("★", p.q_score_label.text())
        self.assertEqual(w.chart_scores.scores()["005930"]["last_price"], 121)
        self.assertEqual(w.watchlist.rows[6]["q_score"]["last_price"], 121)
        self.assertEqual(len(self.home_service.calls), 6)
        self.assertEqual(len(self.chart_service.calls), 1)
        self.assertEqual(len(self.score_service.calls), 1)

    def test_page_exit_stops_both_price_and_score_and_late_callbacks_cannot_restart(self):
        w = self.window
        self.start_home()
        event = tick(price=121, stamp=self.clock)
        self.publish(self.home_streams[0], event)
        self.wait_until(lambda: w.q_scores.scores()["005930"].get("live"))
        w.nav["guide"].click()
        self.app.processEvents()
        frozen = w.q_scores.scores()["005930"]
        self.assertFalse(frozen["live"])
        self.assertEqual(frozen["feed_state"], "stopped")
        self.assertTrue(w.indicator_guide.isVisible())
        self.assertTrue(self.home_streams[0].stopped)
        self.publish(self.home_streams[0], replace(event, price=120, cumulative_volume=1010))
        self.home_streams[0].on_status("SUBSCRIBED")
        self.app.processEvents()
        self.assertEqual(w.q_scores.scores()["005930"], frozen)
        self.assertEqual(w.watchlist.rows[6]["value"], 121)
        self.assertEqual(w.watchlist.rows[6]["status"], "STALE")
        w.nav["home"].click()
        self.app.processEvents()
        self.assertFalse(w.home_feed.active)
        self.assertEqual(len(self.home_streams), 1)
        self.assertEqual(len(self.home_service.calls), 6)


if __name__ == "__main__":
    unittest.main()
