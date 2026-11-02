"""Watchlist provider/units/time behavior; all quotes and series are fixtures."""
from dataclasses import replace
from datetime import date, datetime, timezone
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from data.krx.kis_client import Quote
from core.research.watchlist import KR_STOCK_SPECS, default_home_rows, load_home_markets


NOW = datetime(2026, 11, 2, 2, 0, tzinfo=timezone.utc)


def series(symbol, *, source, days):
    return SimpleNamespace(source=source, dates=["2026-10-29", "2026-10-30"], values=[100, 102])


def quote(code):
    return Quote(code, "fixture", 70000, 1000, 1.45, 200000, 4200000,
                 71000, 69000, 69500, as_of=NOW.isoformat())


class HomeWatchlistTests(unittest.TestCase):
    def setUp(self):
        now = patch("core.research.watchlist._now", return_value=NOW)
        now.start(); self.addCleanup(now.stop)
        network = patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        network.start(); self.addCleanup(network.stop)

    def test_placeholders_are_complete_independent_and_do_not_access_providers(self):
        with patch("core.research.watchlist._quote_client", side_effect=AssertionError("provider construction")):
            rows = default_home_rows()
            self.assertEqual(len(rows), 12)
            self.assertEqual([r["symbol"] for r in rows[6:]], [r[1] for r in KR_STOCK_SPECS])
            self.assertTrue(all(r["status"] == "NOT_LOADED" and r["value"] is None for r in rows))
            rows[0]["value"] = 42
            self.assertIsNone(default_home_rows()[0]["value"])

    def test_existing_daily_units_and_stock_percent_are_preserved_with_one_call_each(self):
        loader = Mock(side_effect=series)
        client = SimpleNamespace(ready=True, quote=Mock(side_effect=quote))
        rows = load_home_markets(loader=loader, quote_client=client, today=NOW.date())
        self.assertEqual(loader.call_count, 6)
        self.assertEqual([call.args[0] for call in client.quote.call_args_list], [r[1] for r in KR_STOCK_SPECS])
        self.assertAlmostEqual(rows[0]["change"], 2.0)
        self.assertEqual(rows[3]["change"], 200)  # rates are bp, unchanged from load_markets
        stock = rows[6]
        self.assertEqual((stock["value"], stock["change"], stock["absolute_change"]), (70000, 1.45, 1000))
        self.assertEqual(stock["status"], "SNAPSHOT")
        self.assertEqual(stock["volume"], 200000)
        self.assertEqual(stock["received_at"], NOW.isoformat())
        self.assertEqual(stock["quote_time_kind"], "receipt")
        self.assertIsNone(stock["observation_date"])
        self.assertIsNone(stock["market_cap"])
        self.assertEqual(stock["market_cap_unit"], "UNVERIFIED")

    def test_missing_configuration_skips_quotes_but_retains_indicators(self):
        client = SimpleNamespace(ready=False, quote=Mock(side_effect=AssertionError("quote request")))
        rows = load_home_markets(loader=series, quote_client=client, today=NOW.date())
        client.quote.assert_not_called()
        self.assertTrue(all(r["status"] == "OBSERVED" for r in rows[:6]))
        self.assertTrue(all(r["reason_code"] == "connection_not_configured" for r in rows[6:]))
        self.assertTrue(all(r["value"] is None for r in rows[6:]))

    def test_failed_quote_is_not_replaced_and_does_not_hide_other_quotes(self):
        def failing(code):
            if code == "005930": raise RuntimeError("https://provider/?appsecret=SECRET")
            return quote(code)
        rows = load_home_markets(loader=series, quote_client=SimpleNamespace(ready=True, quote=failing), today=NOW.date())
        self.assertEqual(rows[6]["status"], "UNAVAILABLE")
        self.assertEqual(rows[6]["reason_code"], "provider_unavailable")
        self.assertTrue(all(r["status"] == "SNAPSHOT" for r in rows[7:]))
        self.assertNotIn("SECRET", json.dumps(rows))
        self.assertNotIn("https://", json.dumps(rows))

    def test_malformed_quote_is_not_displayed_as_valid_market_data(self):
        cases = [dict(price=float("nan")), dict(price=0), dict(price=-1), dict(price=True),
                 dict(volume=-1), dict(market_cap=float("inf")), dict(change_pct=float("nan")),
                 dict(source="synthetic"), dict(currency="USD"), dict(ticker="000000"),
                 dict(as_of="2026-11-03T02:00:00+00:00"), dict(as_of="2026-11-02T02:00:00")]
        for changes in cases:
            with self.subTest(changes=changes):
                client = SimpleNamespace(ready=True, quote=lambda code: replace(quote(code), **changes))
                rows = load_home_markets(loader=series, quote_client=client, today=NOW.date())
                self.assertTrue(all(r["status"] == "UNAVAILABLE" for r in rows[6:]))
                self.assertTrue(all(r["reason_code"] == "invalid_response" for r in rows[6:]))
                self.assertTrue(all(r["value"] is None for r in rows[6:]))

    def test_zero_optional_ohlc_is_unknown_and_old_receipt_never_becomes_observation_date(self):
        client = SimpleNamespace(ready=True, quote=lambda code: replace(quote(code), open=0, high=0, low=0,
                                  as_of="2026-10-23T02:00:00+00:00"))
        stock = load_home_markets(loader=series, quote_client=client, today=NOW.date())[6]
        self.assertIsNone(stock["open"])
        self.assertIsNone(stock["high"])
        self.assertIsNone(stock["low"])
        self.assertIsNone(stock["observation_date"])
        self.assertEqual(stock["received_at"], "2026-10-23T02:00:00+00:00")
        self.assertNotEqual(stock["status"], "LIVE")

    def test_stale_and_future_daily_observations_remain_distinct_from_quote_receipts(self):
        def mixed(symbol, *, source, days):
            dates = ["2026-10-20", "2026-10-21"] if symbol == "^GSPC" else ["2026-11-03", "2026-11-04"]
            return SimpleNamespace(source=source, dates=dates, values=[100, 101])
        rows = load_home_markets(loader=mixed, quote_client=SimpleNamespace(ready=False), today=date(2026, 11, 2))
        self.assertEqual(rows[0]["status"], "STALE")
        self.assertEqual(rows[1]["status"], "UNAVAILABLE")
        self.assertEqual(rows[1]["reason_code"], "invalid_response")


if __name__ == "__main__":
    unittest.main()
