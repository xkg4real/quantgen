"""Automatic chart-provider choice (owner UI-8): KIS first, then the first valid fallback.

Pure and offline: providers are fakes; any HTTP attempt fails the test.
"""
import threading
import time
import unittest
from unittest.mock import patch

from core.market.models import Candle, ChartRequest, Instrument, MarketSnapshot
from core.market import routing
from core.market.routing import (ChartRouter, KISChartProvider, ProvidersNotRun, ProvidersUnavailable,
                                 YahooChartProvider, describe, yahoo_symbols)

STOCK = ChartRequest(Instrument("domestic_stock", "005930"), "1d", 30)
US = ChartRequest(Instrument("overseas_stock", "BRK.B", "NYS"), "1d", 30)
FUTURE = ChartRequest(Instrument("domestic_future", "101W12"), "1d", 30)


def snapshot(request, n=30, close=100.0, source="KIS REST"):
    bars = tuple(Candle(f"2026-10-{1 + i:02d}" if i < 28 else f"2026-11-{i - 27:02d}", close, close + 1, close - 1, close)
                 for i in range(n))
    return MarketSnapshot(request, bars, None, "2026-11-03T00:00:00+00:00", source)


class Fake:
    def __init__(self, name, *, result=None, error=None, delay=0.0, ready=True, supports=True, block=None):
        self.name, self.result, self.error, self.delay = name, result, error, delay
        self._ready, self._supports, self.block, self.calls = ready, supports, block, []

    def ready(self):
        return self._ready, (() if self._ready else ("FAKE_KEY",))

    def supports(self, request):
        return self._supports

    def load(self, request):
        self.calls.append(request)
        if self.block is not None:
            self.block.wait()
        time.sleep(self.delay)
        if self.error:
            raise self.error
        return self.result(request) if callable(self.result) else self.result


class RouterTests(unittest.TestCase):
    def setUp(self):
        deny = patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        deny.start(); self.addCleanup(deny.stop)

    def test_kis_success_wins_and_fallbacks_are_never_asked(self):
        kis, yahoo = Fake("KIS", result=snapshot), Fake("Yahoo", result=snapshot)
        router = ChartRouter(kis, (yahoo,))
        self.assertEqual(router.load(STOCK).source, "KIS REST")
        self.assertEqual(yahoo.calls, [])
        self.assertEqual([(a.provider, a.status) for a in router.last_attempts], [("KIS", "OK")])

    def test_a_single_kis_bar_is_still_shown_but_a_fallback_needs_two(self):
        yahoo = Fake("Yahoo", result=lambda r: snapshot(r, n=1, source="Yahoo"))
        router = ChartRouter(Fake("KIS", result=lambda r: snapshot(r, n=1)), (yahoo,))
        self.assertEqual(len(router.load(STOCK).candles), 1)
        self.assertEqual(yahoo.calls, [])
        with self.assertRaises(ProvidersUnavailable):
            ChartRouter(Fake("KIS", error=RuntimeError()), (yahoo,)).load(STOCK)

    def test_kis_failure_races_fallbacks_and_first_valid_answer_wins(self):
        def bad(request):  # faster, but unusable: one bar only
            return snapshot(request, n=1, source="Fast")
        kis = Fake("KIS", error=RuntimeError("raw provider text must not surface"))
        fast_bad = Fake("Fast", result=bad)
        slow_good = Fake("Slow", result=lambda r: snapshot(r, source="Slow"), delay=0.05)
        router = ChartRouter(kis, (fast_bad, slow_good), deadline=2)
        self.assertEqual(router.load(STOCK).source, "Slow")
        record = {a.provider: (a.status, a.reason) for a in router.last_attempts}
        self.assertEqual(record["KIS"], ("FAILED", "RuntimeError"))
        self.assertEqual(record["Fast"], ("INVALID", "too_few_bars"))
        self.assertEqual(record["Slow"], ("OK", ""))
        self.assertNotIn("raw provider", repr(router.last_attempts))

    def test_wrong_instrument_unordered_or_bad_prices_are_invalid(self):
        other = ChartRequest(Instrument("domestic_stock", "000660"), "1d", 30)
        cases = {"wrong_instrument": lambda r: snapshot(other),
                 "bad_price": lambda r: MarketSnapshot(
                     r, (Candle("2026-10-01", 1, 1, 1, 1), Candle("2026-10-02", 0.0, 0.0, 0.0, 0.0)), None, "", "X"),
                 "unordered_bars": lambda r: MarketSnapshot(r, tuple(reversed(snapshot(r).candles)), None, "", "X")}
        for reason, make in cases.items():
            router = ChartRouter(Fake("KIS", result=make), (Fake("Yahoo", error=LookupError()),))
            with self.subTest(reason=reason), self.assertRaises(ProvidersUnavailable):
                router.load(STOCK)
            self.assertEqual(router.last_attempts[0].reason, reason)

    def test_a_hung_fallback_is_abandoned_on_a_daemon_thread_at_the_deadline(self):
        gate = threading.Event()
        self.addCleanup(gate.set)
        router = ChartRouter(Fake("KIS", error=RuntimeError()), (Fake("Hung", block=gate, result=snapshot),),
                             deadline=0.3)
        started = time.monotonic()
        with self.assertRaises(ProvidersUnavailable):
            router.load(STOCK)
        self.assertLess(time.monotonic() - started, 2.0)
        self.assertEqual(router.last_attempts[-1].status, "LATE")
        hung = [t for t in threading.enumerate() if t.name == "quantgen-chart-Hung"]
        self.assertTrue(hung and all(t.daemon for t in hung))

    def test_missing_credentials_name_variables_only_and_unsupported_assets_do_not_fall_back(self):
        kis = KISChartProvider(type("Service", (), {"ready": False, "load": lambda self, r: 1/0})())
        yahoo = YahooChartProvider(fetch=lambda *a: self.fail("futures have no Yahoo fallback"))
        router = ChartRouter(kis, (yahoo,))
        with self.assertRaises(ProvidersNotRun):
            router.load(FUTURE)
        self.assertEqual(router.last_attempts[0].missing, ("KIS_APP_KEY", "KIS_APP_SECRET"))
        self.assertIn("KIS_APP_KEY", describe(router.last_attempts, "en"))

    def test_primary_only_routes_keep_the_primary_error(self):
        class KISUnavailable(Exception):
            pass
        router = ChartRouter(Fake("KIS", error=KISUnavailable()))
        with self.assertRaises(KISUnavailable):
            router.load(STOCK)

    def test_kis_provider_reads_the_current_service_each_time(self):
        holder = {"service": type("A", (), {"ready": True, "load": lambda self, r: "first"})()}
        provider = KISChartProvider(lambda: holder["service"])
        self.assertEqual(provider.load(STOCK), "first")
        holder["service"] = type("B", (), {"ready": True, "load": lambda self, r: "second"})()
        self.assertEqual(provider.load(STOCK), "second")


class YahooFallbackTests(unittest.TestCase):
    def test_symbol_mapping_and_supported_requests(self):
        self.assertEqual(yahoo_symbols(STOCK.instrument), ("005930.KS", "005930.KQ"))
        self.assertEqual(yahoo_symbols(US.instrument), ("BRK-B",))
        self.assertEqual(yahoo_symbols(Instrument("overseas_stock", "00700", "HKS")), ("0700.HK",))
        self.assertEqual(yahoo_symbols(Instrument("overseas_stock", "7203", "TSE")), ("7203.T",))
        self.assertEqual(yahoo_symbols(Instrument("overseas_stock", "VIC", "HSX")), ())
        provider = YahooChartProvider(fetch=lambda *a: ())
        self.assertTrue(provider.supports(STOCK))
        self.assertFalse(provider.supports(ChartRequest(STOCK.instrument, "5m", 30)))
        self.assertFalse(provider.supports(FUTURE))

    def test_rows_become_a_labelled_unadjusted_snapshot_and_kosdaq_is_tried_second(self):
        asked = []

        def fetch(symbol, interval, period):
            asked.append((symbol, interval))
            if symbol.endswith(".KS"):
                return ()
            return [("2026-10-30", 10, 12, 9, 11, 100), ("2026-10-31", 11, 13, 10, 12, None),
                    ("bad", "x", 1, 1, 1, 1), ("2026-11-03", 12, 14, 11, 13, float("nan"))]

        result = YahooChartProvider(fetch=fetch).load(STOCK)
        self.assertEqual(asked, [("005930.KS", "1d"), ("005930.KQ", "1d")])
        self.assertEqual([c.close for c in result.candles], [11, 12, 13])
        self.assertIsNone(result.candles[-1].volume)
        self.assertEqual((result.source, result.quote.currency, result.quote.price), ("Yahoo Finance", "KRW", 13))
        self.assertIn("not a KIS quote", result.note)
        self.assertIn("Partial history: 3/30", result.note)
        with self.assertRaises(LookupError):
            YahooChartProvider(fetch=lambda *a: [("2026-10-30", 1, 1, 1, 1, 1)]).load(STOCK)

    def test_description_line_is_bilingual_and_carries_no_values(self):
        attempts = (routing.Attempt("KIS", "NOT_RUN", "not_configured", ("KIS_APP_KEY",)),
                    routing.Attempt("Yahoo Finance", "FAILED", "ConnectionError"))
        self.assertEqual(describe(attempts, "ko"), "KIS 미설정 (KIS_APP_KEY) · Yahoo Finance 실패 (ConnectionError)")
        self.assertEqual(describe(attempts, "en"), "KIS not configured (KIS_APP_KEY) · Yahoo Finance failed (ConnectionError)")


if __name__ == "__main__":
    unittest.main()
