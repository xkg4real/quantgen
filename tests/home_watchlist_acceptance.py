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
from core.research.markets import load_markets, provider_failure_reason


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

    def test_yahoo_empty_download_and_missing_library_have_distinct_reasons_with_fred_intact(self):
        import pandas as pd
        from core.ficc import data

        def fred(ids, start):
            return {symbol: [(f"2026-10-{day}", 100 + day) for day in range(26, 31)] for symbol in ids}

        for empty_library, expected in ((False, "no_observations"), (True, "dependency_missing")):
            yahoo = None if empty_library else SimpleNamespace(download=Mock(return_value=pd.DataFrame()))
            with self.subTest(library_missing=empty_library), \
                 patch.object(data, "_yf", yahoo), patch.object(data, "_fred_fetch", side_effect=fred) as fred_fetch, \
                 patch.object(data, "_cache_get", return_value=None), patch.object(data, "_cache_put"):
                rows = load_home_markets(quote_client=SimpleNamespace(ready=False), today=NOW.date())
            for index in (0, 1, 5):
                self.assertEqual(rows[index]["reason_code"], expected)
                self.assertEqual(rows[index]["provider"], "YFINANCE")
                self.assertIsNone(rows[index]["value"])
            self.assertTrue(all(rows[index]["status"] == "OBSERVED" for index in (2, 3, 4)))
            self.assertEqual({call.args[0][0] for call in fred_fetch.call_args_list}, {"DEXKOUS", "DGS10", "VIXCLS"})
            if yahoo:
                self.assertEqual(yahoo.download.call_count, 3)
                self.assertTrue(all(call.kwargs["period"] == "3mo" for call in yahoo.download.call_args_list))

    def test_safe_reasons_survive_provider_wrappers_without_returning_secret_text(self):
        from core.ficc.common import FICCError
        from data.krx.kis_client import KISError
        cases = [
            (FICCError("YFINANCE could not serve '^GSPC': YFRateLimitError: SECRET https://host"), "rate_limited"),
            (KISError("FHKST01010100: HTTP 500 (EGW00201: SECRET https://host)"), "rate_limited"),
            (KISError("token rejected (HTTP 401) SECRET"), "access_denied"),
            (FICCError("ReadTimeout: SECRET https://host"), "network_timeout"),
            (FICCError("SSLError: SECRET https://host"), "certificate_error"),
            (FICCError("ConnectionError: SECRET https://host"), "network_error"),
            (FICCError("YFINANCE returned only 3 observations"), "insufficient_observations"),
            (FICCError("TypeError: download() got an unexpected keyword argument 'SECRET'"), "dependency_incompatible"),
            (ImportError("SECRET https://host"), "dependency_missing"),
            (RuntimeError("SECRET https://host"), "provider_unavailable"),
        ]
        for error, reason in cases:
            with self.subTest(reason=reason):
                self.assertEqual(provider_failure_reason(error), reason)
                rows = load_home_markets(loader=Mock(side_effect=error),
                         quote_client=SimpleNamespace(ready=True, quote=Mock(side_effect=error)), today=NOW.date())
                self.assertTrue(all(row["reason_code"] == reason for row in rows))
                self.assertTrue(all(row["value"] is None for row in rows))
                self.assertNotIn("SECRET", json.dumps(rows))
                self.assertNotIn("https://", json.dumps(rows))

    def test_unrecognized_or_forged_provider_reason_is_not_exposed(self):
        error = RuntimeError("https://host?token=SECRET")
        error.reason_code = "SECRET"
        self.assertEqual(provider_failure_reason(error), "provider_unavailable")
        error.reason_code = ["SECRET"]
        self.assertEqual(provider_failure_reason(error), "provider_unavailable")

    def test_missing_kis_transport_is_not_misreported_as_missing_credentials(self):
        with patch("data.krx.kis_client.requests", None), \
             patch("data.krx.kis_client.KISClient.quote", side_effect=AssertionError("provider request")):
            rows = load_home_markets(loader=series, today=NOW.date())
        self.assertTrue(all(row["reason_code"] == "dependency_missing" for row in rows[6:]))
        self.assertTrue(all(row["value"] is None for row in rows[6:]))

    def test_valid_yahoo_multiindex_close_frame_still_loads_without_provider_alias_changes(self):
        import pandas as pd
        from core.ficc import data

        def download(symbols, **_):
            return pd.DataFrame({("Close", symbols[0]): [100., 101., 102., 103., 104.]},
                                index=pd.date_range("2026-10-26", periods=5))

        with patch.object(data, "_yf", SimpleNamespace(download=Mock(side_effect=download))), \
             patch.object(data, "_cache_get", return_value=None), patch.object(data, "_cache_put"):
            def loader(symbol, *, source, days):
                return data.load_series(symbol, source=source, days=days) if source == "yfinance" else series(symbol, source=source, days=days)
            rows = load_home_markets(loader=loader, quote_client=SimpleNamespace(ready=False), today=NOW.date())
        for index in (0, 1, 5):
            self.assertEqual(rows[index]["status"], "OBSERVED")
            self.assertEqual(rows[index]["value"], 104.)
            self.assertAlmostEqual(rows[index]["change"], (104 / 103 - 1) * 100)
            self.assertIsNone(rows[index]["reason_code"])

    def test_blank_optional_kis_fields_do_not_discard_a_valid_price(self):
        from data.krx.kis_client import KISClient
        client = KISClient.__new__(KISClient)
        client.ready = True
        client._get = Mock(return_value={"output": {"stck_prpr": "70000", "prdy_vrss": "", "prdy_ctrt": "",
                          "acml_vol": "", "hts_avls": "", "stck_hgpr": "", "stck_lwpr": "", "stck_oprc": ""}})
        with patch("data.krx.kis_client._now", return_value=NOW.isoformat()):
            rows = load_home_markets(loader=series, quote_client=client, today=NOW.date())
        self.assertEqual(client._get.call_count, 6)
        self.assertTrue(all(row["status"] == "SNAPSHOT" and row["value"] == 70000 for row in rows[6:]))
        self.assertTrue(all(row["change"] is None and row["volume"] is None for row in rows[6:]))

    def test_missing_quote_and_insufficient_daily_data_do_not_guess_a_price(self):
        client = SimpleNamespace(ready=True, quote=lambda code: replace(quote(code), price=None))
        rows = load_home_markets(loader=lambda *a, **kw: SimpleNamespace(source=kw["source"], dates=[], values=[]),
                                 quote_client=client, today=NOW.date())
        self.assertTrue(all(row["reason_code"] == "no_observations" and row["value"] is None for row in rows))
        rows = load_markets(loader=lambda *a, **kw: SimpleNamespace(source=kw["source"], dates=["2026-10-30"], values=[100]),
                            today=NOW.date())
        self.assertTrue(all(row["reason_code"] == "insufficient_observations" for row in rows))

    def test_finite_observations_cannot_emit_an_infinite_change(self):
        rows = load_markets(loader=lambda *a, **kw: SimpleNamespace(source=kw["source"],
                           dates=["2026-10-29", "2026-10-30"], values=[1e-308, 1e308]), today=NOW.date())
        self.assertTrue(all(row["reason_code"] == "invalid_response" and row["change"] is None for row in rows))
        json.dumps(rows, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
