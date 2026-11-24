"""D7: Kalshi daily candles of closed/settled markets over a date range. No network."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from core.didm.store import PointInTimeStore
from data.didm import kalshi
from data.didm.keys import SourceError
from tools.didm import collect_daily as cd


def ts(day: str) -> int:
    return int(datetime.fromisoformat(day + "T00:00:00+00:00").timestamp())


MARKETS = {
    "settled": [{"ticker": "KXFED-22DEC-T4.00", "open_time": "2022-11-01T00:00:00Z",
                 "close_time": "2022-12-14T19:00:00Z"}],
    "closed": [{"ticker": "KXFED-23JAN-T4.50", "open_time": "2025-06-01T00:00:00Z",   # opens after the range
                "close_time": "2025-07-01T00:00:00Z"}],
    "open": [],
}


def candles(start, end):
    """One candle per day ending at each midnight in [start, end]."""
    out, t = [], (start // 86_400 + 1) * 86_400
    while t <= end:
        out.append({"end_period_ts": t, "price": {"close_dollars": "0.6000"}, "volume_fp": "1500.00"})
        t += 86_400
    return {"candlesticks": out}


class Collector(unittest.TestCase):
    def run_collect(self, start="2022-01-01", end="2022-12-31", statuses=("settled", "closed", "open"),
                    max_markets=200, window_days=365, list_markets=None):
        listed, asked = [], []

        def lm(series, status, max_pages, *, min_close_ts):
            listed.append((series, status, min_close_ts))
            return {"markets": MARKETS[status], "pages": 1, "complete": True}

        def fc(series, ticker, a, b, period):
            asked.append((ticker, a, b, period))
            return candles(a, b)
        with tempfile.TemporaryDirectory() as tmp, PointInTimeStore(Path(tmp) / "s.sqlite") as st, \
                mock.patch("builtins.print") as pr:
            out = cd.collect_kalshi_history(st, ["KXFED"], start, end, list(statuses), max_markets,
                                            list_markets=list_markets or lm, fetch_candles=fc,
                                            window_days=window_days)
            stored = st.as_of("2100-01-01T00:00:00Z", source_id="kalshi")
        return out[0], listed, asked, stored, pr.call_args.args[0]

    def test_settled_market_candles_in_window(self):
        out, listed, asked, stored, line = self.run_collect()
        self.assertEqual([s for _, s, _ in listed], ["settled", "closed", "open"])
        self.assertEqual({m for _, _, m in listed}, {ts("2022-01-01")})
        self.assertEqual(len(asked), 1)                                  # 2025 market skipped
        ticker, a, b, period = asked[0]
        self.assertEqual((ticker, period), ("KXFED-22DEC-T4.00", 1440))
        self.assertEqual(a, ts("2022-11-01"))
        self.assertEqual(b, int(datetime(2022, 12, 14, 19, tzinfo=timezone.utc).timestamp()))
        self.assertEqual(out["candles"], 43)                       # 11-02..11-30 (29) + 12-01..12-14 (14)
        self.assertTrue(all(i.kind == "kalshi_candle" and i.payload["p_yes"] == 0.6 for i in stored))
        self.assertIn("first 2022-11-02, last 2022-12-14", line)

    def test_windows_split(self):
        _, _, asked, _, _ = self.run_collect(window_days=10)
        self.assertEqual(len(asked), 5)
        self.assertTrue(all(b - a < 10 * 86_400 for _, a, b, _ in asked))
        self.assertEqual(asked[0][1], ts("2022-11-01"))
        self.assertTrue(all(asked[i + 1][1] == asked[i][2] + 1 for i in range(len(asked) - 1)))

    def test_cap_and_incomplete_reported(self):
        def lm(series, status, max_pages, *, min_close_ts):
            ms = [{"ticker": f"T{i}", "open_time": "2022-01-01T00:00:00Z", "close_time": "2022-01-03T00:00:00Z"}
                  for i in range(3)] if status == "settled" else []
            return {"markets": ms, "pages": max_pages, "complete": status != "settled"}
        out, _, asked, _, line = self.run_collect(max_markets=2, list_markets=lm)
        self.assertEqual((out["markets"], out["read"], out["complete"]), (3, 2, False))
        self.assertEqual(len(asked), 2)
        self.assertIn("complete False, capped at 2", line)

    def test_reversed_range(self):
        with self.assertRaises(SystemExit):
            self.run_collect(start="2023-01-01", end="2022-01-01")


class Client(unittest.TestCase):
    def test_status_and_close_window_params(self):
        with self.assertRaises(ValueError):
            kalshi.fetch_markets("KXFED", "finalized")
        with mock.patch.object(kalshi, "_get", return_value={"markets": [], "cursor": ""}) as g:
            got = kalshi.fetch_all_markets("KXFED", "settled", min_close_ts=100, max_close_ts=200)
        self.assertEqual(got["complete"], True)
        params = g.call_args.args[1]
        self.assertEqual((params["status"], params["min_close_ts"], params["max_close_ts"]), ("settled", 100, 200))

    def test_repeated_cursor_still_refused(self):
        with mock.patch.object(kalshi, "_get", return_value={"markets": [], "cursor": "same"}):
            with self.assertRaises(SourceError):
                kalshi.fetch_all_markets("KXFED", "closed", min_close_ts=1)


class Cli(unittest.TestCase):
    def test_history_needs_from(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                cd.main(["--data-dir", tmp, "--no-gdelt", "--kalshi-history", "KXFED"])


if __name__ == "__main__":
    unittest.main()
