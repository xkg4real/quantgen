"""A chart is visible before paging/quote completion, without inventing live data."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from dataclasses import replace
import threading
import time
import unittest
from unittest.mock import patch

from tests.kis_workspace_acceptance import Client, NOW, domestic_row, no_quote
from data.kis_workspace import MarketDataService
from core.market.models import ChartRequest
from core.market.routing import ChartRouter, KISChartProvider


class ProgressiveHistoryTests(unittest.TestCase):
    def test_first_history_page_precedes_remaining_requests_and_quote(self):
        previews = []
        def handler(path, tr, params):
            if no_quote(path):
                self.assertGreaterEqual(len(previews), 2)
                return {"output": {"stck_prpr": "100"}}
            if params["FID_INPUT_DATE_2"] == "20261102":
                return {"output2": [domestic_row("20261102"), domestic_row("20261030")]}
            self.assertTrue(previews, "Do not wait for the next network page to paint")
            return {"output2": [domestic_row("20261029")]}
        service = MarketDataService(Client(handler), now=lambda: NOW)
        router = ChartRouter(KISChartProvider(service))
        final = router.load_progressive(ChartRequest(limit=20), previews.append)
        self.assertEqual(len(previews[0].candles), 2)
        self.assertIsNone(previews[0].quote)
        self.assertEqual(previews[-1].candles, final.candles)
        self.assertEqual(final.quote.price, 100)
        self.assertEqual(len(service.client.calls), 3)  # two bounded pages + one quote
        self.assertEqual(router.last_attempts[-1].status, "OK")

    def test_minute_previews_keep_forming_volume_unknown(self):
        def handler(path, tr, params):
            if no_quote(path): return {"output": {}}
            return {"output2": [domestic_row("20261102", time="150000", volume="999"),
                                domestic_row("20261102", time="145900", volume="3")]}
        service = MarketDataService(Client(handler), now=lambda: NOW)
        previews = []
        final = service.load_progressive(ChartRequest(interval="1m", limit=20), previews.append)
        self.assertIsNone(previews[0].candles[-1].volume)
        self.assertEqual(previews[0].candles, final.candles)

    def test_native_paints_before_worker_finishes_and_ignores_old_selection(self):
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtTest import QTest
        from quantgen_desktop.market_chart import MarketChartPane
        from tests.desktop_market_chart_acceptance import fixture, FakeStream
        from tests.qt_fixture_cleanup import delete_owned_widget
        app = QApplication.instance() or QApplication([])
        release = threading.Event()
        class Service:
            ready = True
            def load_progressive(self, request, callback):
                full = fixture(request)
                callback(replace(full, candles=full.candles[-20:], quote=None))
                # This proves ordering, not CI machine speed. Hold the final
                # response until the GUI has inspected the partial one.
                if not release.wait(30): raise TimeoutError("Fixture release was not signalled")
                return full
        streams = []
        def stream():
            value = FakeStream(); streams.append(value); return value
        with patch("requests.sessions.Session.request", side_effect=AssertionError("Network forbidden")):
            pane = MarketChartPane(service=Service(), stream_factory=stream)
            pane.resize(900, 700); pane.show()
            try:
                pane.refresh(manual=True)
                end = time.monotonic() + 20
                while pane.snapshot is None and time.monotonic() < end: QTest.qWait(10)
                self.assertIsNotNone(pane.snapshot)
                self.assertTrue(pane.jobs.busy)
                self.assertTrue(pane.chart.isVisible())
                self.assertEqual(len(pane.snapshot.candles), 20)
                self.assertEqual(streams, [])
                before = pane.snapshot
                pane._history_preview(pane._epoch - 1, pane.request(), fixture(pane.request()))
                self.assertIs(pane.snapshot, before)
                release.set()
                end = time.monotonic() + 20
                while pane.jobs.busy and time.monotonic() < end: QTest.qWait(10)
                self.assertFalse(pane.jobs.busy)
                self.assertEqual(len(pane.snapshot.candles), 120)
            finally:
                release.set(); pane.stop(); pane.jobs.pool.waitForDone(6000)
                app.processEvents(); delete_owned_widget(pane)


if __name__ == "__main__": unittest.main()
