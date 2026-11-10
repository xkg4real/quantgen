"""Screen routing without a source selector: `best` asks keyless Yahoo before simulating.

Hermetic: every provider is patched. `auto` keeps its documented no-Yahoo invariant.
"""
import contextlib
import unittest

import config
from core.quant import history as H


def _rows(n=60):
    return [(f"2026-{(i // 28) % 12 + 1:02d}-{i % 28 + 1:02d}", 100.0 + i) for i in range(n)]


@contextlib.contextmanager
def _env(*, fmp=False, kis=False, yahoo=None):
    calls = []

    def fake_yf(symbol, *, days=504):
        calls.append(symbol)
        if yahoo is None or symbol not in yahoo:
            raise H.HistoryError(f"Yahoo Finance failed for {symbol!r}: offline")
        dates, closes = zip(*_rows())
        return H.History(symbol=symbol.upper(), source="YFINANCE", dates=dates, closes=closes,
                         note="Yahoo adjusted close", adjustment="total")

    saved = (config.fmp_ready, config.fmp_key, config.kis_ready, H.yf_history, H._cached)
    config.fmp_ready = lambda: fmp
    config.fmp_key = lambda: "k" if fmp else ""
    config.kis_ready = lambda: kis
    H.yf_history = fake_yf
    H._cached = lambda provider, fetch, symbol, days: fetch(symbol, days=days)
    try:
        yield calls
    finally:
        config.fmp_ready, config.fmp_key, config.kis_ready, H.yf_history, H._cached = saved


class BestSourceTests(unittest.TestCase):
    def test_auto_keeps_no_yahoo_invariant(self):
        with _env(yahoo={"AAPL"}) as calls:
            self.assertEqual(H.load_history("AAPL", source="auto").source, "SYNTHETIC")
        self.assertEqual(calls, [])

    def test_best_uses_yahoo_when_fmp_key_missing(self):
        with _env(yahoo={"AAPL"}) as calls:
            h = H.load_history("AAPL", source="best")
        self.assertEqual((h.source, calls), ("YFINANCE", ["AAPL"]))
        self.assertIn("FMP_API_KEY is not configured", h.note)

    def test_best_maps_krx_code_to_yahoo_when_kis_missing(self):
        with _env(yahoo={"005930.KS"}) as calls:
            h = H.load_history("005930", source="best")
        self.assertEqual((h.source, h.symbol, calls), ("YFINANCE", "005930.KS", ["005930.KS"]))

    def test_best_tries_kosdaq_suffix_second(self):
        with _env(yahoo={"035720.KQ"}) as calls:
            h = H.load_history("035720", source="best")
        self.assertEqual(calls, ["035720.KS", "035720.KQ"])
        self.assertEqual(h.symbol, "035720.KQ")

    def test_best_falls_back_to_labeled_synthetic_when_yahoo_fails(self):
        with _env(yahoo=set()):
            h = H.load_history("AAPL", source="best")
        self.assertEqual(h.source, "SYNTHETIC")
        self.assertIn("Yahoo Finance also failed", h.note)

    def test_best_does_not_replace_a_configured_provider(self):
        with _env(fmp=True, yahoo={"AAPL"}) as calls:
            saved = H.fmp_history
            dates, closes = zip(*_rows())
            H.fmp_history = lambda s, *, days=504: H.History(s, "FMP", dates, closes)
            try:
                h = H.load_history("AAPL", source="best")
            finally:
                H.fmp_history = saved
        self.assertEqual((h.source, calls), ("FMP", []))

    def test_best_is_a_listed_source(self):
        self.assertIn("best", H.SOURCES)


if __name__ == "__main__":
    unittest.main()
