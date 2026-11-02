"""Q-SCORE behavior with deterministic prices; never requests market data."""
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from core.market.models import Candle, ChartRequest, Instrument, MarketSnapshot
from core.quant.history import History
from core.research.qscore import compute_q_score, q_score_help


NOW = datetime(2026, 11, 2, 2, 0, tzinfo=timezone.utc)


def fixture(*, trend=0.001, noise=0.003, count=252, end=date(2026, 10, 30)):
    days = []
    while len(days) < count:
        if end.weekday() < 5:
            days.append(end.isoformat())
        end -= timedelta(days=1)
    days.reverse()
    increments = trend + noise * np.sin(np.arange(count) * 0.7)
    prices = 50000 * np.exp(np.cumsum(increments))
    return History("005930", "KIS", tuple(days), tuple(prices), adjustment="split")


def snapshot(history=None):
    history = history or fixture()
    candles = tuple(Candle(day, price, price, price, price, 10) for day, price in zip(history.dates, history.closes))
    return MarketSnapshot(ChartRequest(Instrument(), "1d", 252, adjusted=True), candles, source="KIS REST")


class QScoreTests(unittest.TestCase):
    def setUp(self):
        network = patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        network.start()
        self.addCleanup(network.stop)

    def test_deterministic_json_safe_score_uses_existing_engine_components(self):
        first = compute_q_score(fixture(), now=NOW)
        self.assertEqual(first, compute_q_score(fixture(), now=NOW))
        self.assertEqual(first["status"], "ready")
        self.assertFalse(first["live"])
        self.assertEqual(first["as_of"], "2026-10-30")
        self.assertEqual(first["sessions"], 252)
        self.assertEqual(first["methodology"], "Q-SCORE v0.1")
        self.assertEqual(set(first["components"]["technical"]["signals"]),
                         {"trend50", "trend200", "momentum", "rsi", "macd", "vol"})
        self.assertEqual(first["components"]["drawdown"]["engine"], "core.quant.risk.analyze_history")
        recombined = sum(c["score"] * c["weight"] for c in first["components"].values())
        self.assertAlmostEqual(first["score"], recombined, places=2)
        self.assertGreaterEqual(first["stars"], 1)
        self.assertLessEqual(first["stars"], 5)
        json.dumps(first, allow_nan=False)

    def test_direction_and_worse_drawdown_change_the_score(self):
        up = compute_q_score(fixture(trend=0.002), now=NOW)
        down = compute_q_score(fixture(trend=-0.002), now=NOW)
        self.assertGreater(up["score"], down["score"])
        self.assertGreater(up["components"]["drawdown"]["score"], down["components"]["drawdown"]["score"])
        self.assertGreater(up["stars"], down["stars"])

    def test_displayed_boundary_score_and_stars_cannot_disagree(self):
        # A composite at 79.999 rounds to 80.00 for display, so it must also
        # cross the documented 80-point boundary rather than show four stars.
        signals = SimpleNamespace(composite=42.85428571428571, components=())
        risk = SimpleNamespace(max_drawdown=0, cvar_1d=0, engine="local")
        with patch("core.research.qscore.compute_signals", return_value=signals), \
                patch("core.research.qscore.analyze_history", return_value=risk):
            result = compute_q_score(fixture(), now=NOW)
        self.assertEqual((result["score"], result["stars"]), (80.0, 5))

    def test_actual_tick_reprices_one_daily_observation_without_mutating_baseline(self):
        baseline = snapshot(fixture(count=230))
        original = baseline.candles
        higher = compute_q_score(baseline, baseline.candles[-1].close * 1.04, NOW,
                                 now=NOW)
        lower = compute_q_score(baseline, baseline.candles[-1].close * 0.96, NOW,
                                now=NOW)
        self.assertEqual((higher["status"], higher["sessions"], higher["live"]), ("ready", 231, True))
        self.assertEqual(higher["price_basis"], "provisional_daily")
        self.assertGreater(higher["score"], lower["score"])
        self.assertEqual(baseline.candles, original)
        # Intraday calls all rebuild today's one provisional close from the
        # same immutable baseline, rather than turn ticks into daily history.
        for seconds in (1, 2, 30):
            later = NOW + timedelta(seconds=seconds)
            score = compute_q_score(baseline, original[-1].close * 1.01, later, now=later)
            self.assertEqual(score["sessions"], 231)
        same_day = snapshot(fixture(count=230, end=NOW.date()))
        self.assertEqual(compute_q_score(same_day, same_day.candles[-1].close, NOW, now=NOW)["sessions"], 230)

    def test_snapshot_and_explicit_candles_agree_but_metadata_cannot_be_overridden(self):
        baseline = snapshot()
        expected = compute_q_score(baseline, now=NOW)
        actual = compute_q_score(baseline.candles, source="KIS REST", adjusted=True, symbol="005930", now=NOW)
        self.assertEqual(expected, actual)
        raw = replace(baseline, request=replace(baseline.request, adjusted=False))
        self.assertEqual(compute_q_score(raw, adjusted=True, now=NOW)["reason"], "adjusted_history_required")
        intraday = replace(baseline, request=replace(baseline.request, interval="1m"))
        self.assertEqual(compute_q_score(intraday, now=NOW)["reason"], "daily_history_required")
        synthetic = replace(fixture(), source="SYNTHETIC")
        self.assertEqual(compute_q_score(synthetic, source="KIS", now=NOW)["reason"], "unverified_source")

    def test_missing_short_flat_and_invalid_history_never_get_stars(self):
        base = fixture()
        cases = [None, fixture(count=199), replace(base, closes=(50000,) * 252),
                 replace(base, closes=base.closes[:-1]),
                 replace(base, dates=base.dates[:-1] + (base.dates[-2],)),
                 replace(base, closes=base.closes[:-1] + (float("nan"),)),
                 replace(base, closes=base.closes[:-1] + (0,)),
                 replace(base, closes=base.closes[:-1] + (-1,)),
                 replace(base, closes=base.closes[:-1] + (True,))]
        for history in cases:
            with self.subTest(history=type(history).__name__):
                result = compute_q_score(history, source="KIS", adjusted=True, now=NOW)
                self.assertNotEqual(result["status"], "ready")
                self.assertIsNone(result["stars"])
                self.assertIsNone(result["score"])
                json.dumps(result, allow_nan=False)

    def test_stale_future_and_irregular_daily_history_are_explicitly_rejected(self):
        self.assertEqual(compute_q_score(fixture(end=date(2026, 10, 20)), now=NOW)["reason"], "stale_history")
        self.assertEqual(compute_q_score(fixture(end=date(2026, 11, 3)), now=NOW)["reason"], "future_history")
        base = fixture()
        days = list(base.dates)
        days[:30] = [(date.fromisoformat(day) - timedelta(days=30)).isoformat() for day in days[:30]]
        self.assertEqual(compute_q_score(replace(base, dates=tuple(days)), now=NOW)["reason"], "invalid_history_dates")

    def test_bad_stale_future_out_of_order_or_wrong_scale_ticks_cannot_refresh_stars(self):
        base = fixture()
        cases = [
            ({"latest_price": 0, "as_of": NOW}, "invalid_quote"),
            ({"latest_price": True, "as_of": NOW}, "invalid_quote"),
            ({"latest_price": float("inf"), "as_of": NOW}, "invalid_quote"),
            ({"latest_price": base.last}, "invalid_quote"),
            ({"latest_price": base.last, "as_of": NOW.replace(tzinfo=None)}, "invalid_quote"),
            ({"latest_price": base.last, "as_of": NOW - timedelta(seconds=121)}, "stale_quote"),
            ({"latest_price": base.last, "as_of": NOW + timedelta(seconds=6)}, "future_quote"),
            ({"latest_price": base.last, "as_of": NOW - timedelta(seconds=1), "previous_as_of": NOW}, "out_of_order_quote"),
            ({"latest_price": base.last * 0.5, "as_of": NOW}, "adjustment_mismatch"),
            ({"latest_price": base.last * 2, "as_of": NOW}, "adjustment_mismatch"),
        ]
        for keywords, reason in cases:
            with self.subTest(reason=reason):
                result = compute_q_score(base, now=NOW, **keywords)
                self.assertEqual(result["reason"], reason)
                self.assertIsNone(result["stars"])
                self.assertFalse(result["live"])

    def test_lookback_is_bounded_and_help_discloses_experimental_method_in_both_languages(self):
        result = compute_q_score(fixture(count=500), now=NOW)
        self.assertEqual(result["sessions"], 252)
        self.assertEqual(result["status"], "ready")
        self.assertIn("예측력은 검증되지", q_score_help("ko"))
        self.assertIn("unvalidated predictive power", q_score_help("en"))
        for lang in ("ko", "en"):
            for requirement in ("70%", "15%", "200", "252", "120", "CVaR"):
                self.assertIn(requirement, q_score_help(lang))


if __name__ == "__main__":
    unittest.main()
