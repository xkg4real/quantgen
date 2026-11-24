"""DS-4d/DS-4e: EDGAR, OpenDART, ECOS and Kalshi parsers from fixtures. No network."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import call, patch

from core.didm.ingest import ecos, filings, kalshi
from core.didm.store import PointInTimeStore

RECEIVED = datetime(2026, 11, 18, 1, 0, tzinfo=timezone.utc)

SUBMISSIONS = {
    "cik": "0000320193", "name": "Example Corp", "tickers": ["EXMP"],
    "filings": {"recent": {
        "accessionNumber": ["0000320193-26-000101", "0000320193-26-000100"],
        "form": ["8-K", "4"],
        "filingDate": ["2026-11-14", "2026-11-13"],
        "acceptanceDateTime": ["2026-11-14T16:05:12.000Z", "2026-11-13T18:00:00.000Z"],
        "primaryDocument": ["ex8k.htm", "form4.xml"],
        "items": ["2.02,9.01", ""],
    }},
}
DART = {"status": "000", "total_page": 1, "list": [
    {"corp_code": "00126380", "corp_name": "예시전자", "stock_code": "005930", "corp_cls": "Y",
     "report_nm": "주요사항보고서(자기주식취득결정)", "rcept_no": "20261117000123", "flr_nm": "예시전자",
     "rcept_dt": "20261117", "rm": "유"},
]}
ECOS = {"StatisticSearch": {"list_total_count": 2, "row": [
    {"STAT_CODE": "722Y001", "STAT_NAME": "한국은행 기준금리", "ITEM_CODE1": "0101000",
     "ITEM_NAME1": "기준금리", "UNIT_NAME": "연%", "TIME": "202610", "DATA_VALUE": "2.50"},
    {"STAT_CODE": "200Y001", "STAT_NAME": "GDP", "ITEM_CODE1": "10111", "ITEM_NAME1": "GDP",
     "UNIT_NAME": "십억원", "TIME": "2026Q3", "DATA_VALUE": "1,234.5"},
]}}
MARKETS = {"markets": [
    {"ticker": "KXFED-26DEC-T4.25", "event_ticker": "KXFED-26DEC", "title": "Fed rate above 4.25%?",
     "status": "open", "close_time": "2026-12-16T19:00:00Z",
     "yes_bid": 61, "yes_ask": 63, "last_price": 62, "volume": 52000, "open_interest": 9000},
    {"ticker": "KXFED-26DEC-T5.00", "event_ticker": "KXFED-26DEC", "title": "thin",
     "status": "open", "yes_bid": None, "yes_ask": None, "last_price": 3, "volume": 40},
]}
CANDLES = {"candlesticks": [
    {"end_period_ts": 1763337600, "price": {"close": 58}, "volume": 3000, "open_interest": 8000},
    {"end_period_ts": 1763424000, "price": {"close": None}, "volume": 0, "open_interest": 8000},
]}


class Edgar(unittest.TestCase):
    def test_rows(self):
        rows = filings.edgar_rows(SUBMISSIONS, RECEIVED)
        self.assertEqual([r["item_id"] for r in rows], ["0000320193-26-000101"])  # form 4 filtered
        r = rows[0]
        self.assertEqual(r["published_at"], datetime(2026, 11, 14, 16, 5, 12, tzinfo=timezone.utc))
        self.assertEqual(r["payload"]["items"], "2.02,9.01")
        self.assertEqual(r["payload"]["cik"], "320193")

    def test_all_forms(self):
        self.assertEqual(len(filings.edgar_rows(SUBMISSIONS, RECEIVED, forms=None)), 2)

    def test_ragged_columns_rejected(self):
        bad = {**SUBMISSIONS, "filings": {"recent": {**SUBMISSIONS["filings"]["recent"], "form": ["8-K"]}}}
        with self.assertRaises(filings.FilingError):
            filings.edgar_rows(bad, RECEIVED)


class OpenDart(unittest.TestCase):
    def test_rows(self):
        r = filings.opendart_rows(DART, RECEIVED)[0]
        self.assertEqual(r["item_id"], "20261117000123")
        self.assertEqual(r["published_at"].isoformat(), "2026-11-17T00:00:00+09:00")
        self.assertEqual(r["payload"]["time_precision"], "date")

    def test_no_data(self):
        self.assertEqual(filings.opendart_rows({"status": "013"}, RECEIVED), [])

    def test_bad_receipt(self):
        with self.assertRaises(filings.FilingError):
            filings.opendart_rows({"list": [{"rcept_no": "x", "rcept_dt": "20261117"}]}, RECEIVED)


class Ecos(unittest.TestCase):
    def test_rows(self):
        rows = ecos.rows(ECOS, RECEIVED)
        self.assertEqual(rows[0]["item_id"], "722Y001:0101000:202610")
        self.assertEqual(rows[1]["payload"]["value"], 1234.5)
        self.assertEqual(rows[1]["valid_at"].isoformat(), "2026-07-01T00:00:00+09:00")
        self.assertTrue(all(r["published_at"] == RECEIVED for r in rows))
        self.assertFalse(rows[0]["payload"]["release_time_known"])

    def test_no_data_and_error(self):
        self.assertEqual(ecos.rows({"RESULT": {"CODE": "INFO-200"}}, RECEIVED), [])
        with self.assertRaises(ecos.EcosError):
            ecos.rows({"RESULT": {"CODE": "ERROR-100"}}, RECEIVED)

    def test_bad_time(self):
        with self.assertRaises(ecos.EcosError):
            ecos.period_start("26-10")


class Kalshi(unittest.TestCase):
    def test_snapshot(self):
        rows = kalshi.market_snapshot_rows(MARKETS, RECEIVED)
        self.assertAlmostEqual(rows[0]["payload"]["p_yes"], 0.62)
        self.assertTrue(rows[0]["payload"]["liquid"])
        self.assertEqual(rows[1]["payload"]["p_yes"], 0.03)  # last price when no quotes
        self.assertFalse(rows[1]["payload"]["liquid"])
        self.assertTrue(rows[0]["item_id"].endswith("@20261118T010000Z"))

    def test_current_dollar_and_fp_fields(self):
        payload = {"markets": [{"ticker": "KXFED-26DEC-H0", "yes_bid_dollars": "0.6100",
                                "yes_ask_dollars": "0.6300", "last_price_dollars": "0.6200",
                                "volume_fp": "52000.00", "volume_24h_fp": "1200.00",
                                "open_interest_fp": "9000.00"}]}
        r = kalshi.market_snapshot_rows(payload, RECEIVED)[0]["payload"]
        self.assertAlmostEqual(r["p_yes"], 0.62)
        self.assertEqual(r["volume"], 52000.0)
        self.assertTrue(r["liquid"])
        self.assertEqual(r["parser"], kalshi.PARSER)

    def test_missing_volume_is_missing_not_zero(self):
        r = kalshi.market_snapshot_rows({"markets": [{"ticker": "X", "last_price_dollars": "0.1000"}]},
                                        RECEIVED)[0]["payload"]
        self.assertIsNone(r["volume"])
        self.assertFalse(r["liquid"])
        self.assertAlmostEqual(r["p_yes"], 0.10)

    def test_bad_dollar_string(self):
        with self.assertRaises(kalshi.KalshiError):
            kalshi.market_snapshot_rows({"markets": [{"ticker": "X", "yes_bid_dollars": "abc"}]}, RECEIVED)

    def test_dollar_price_rejected_before_rounding_to_probability(self):
        invalid = (True, False, "1.000000004", "-0.000000004", "1.00000000000000000001",
                   "-1e-1000", "NaN", float("inf"), "-Infinity", "bad", 10**400)
        for value in invalid:
            for field in ("last_price", "yes_bid", "yes_ask"):
                with self.subTest(value=value, field=field), self.assertRaises(kalshi.KalshiError):
                    market = {"ticker": "X", field: 50, field + "_dollars": value}
                    kalshi.market_snapshot_rows({"markets": [market]}, RECEIVED)
            with self.subTest(value=value, field="close"), self.assertRaises(kalshi.KalshiError):
                candle = {"end_period_ts": 1763337600, "price": {"close": 50, "close_dollars": value}}
                kalshi.candlestick_rows("X", {"candlesticks": [candle]}, RECEIVED)

    def test_valid_dollars_keep_cent_rounding_and_legacy_fallback(self):
        for value in (0, 1, "0.0000", "1.0000", 0.61, "0.123456789", "0.99999999999999999999", "0.000000004"):
            with self.subTest(value=value):
                cents = round(float(value) * 100, 6)
                market = {"ticker": "X", "last_price_dollars": value, "last_price": 37}
                snapshot = kalshi.market_snapshot_rows({"markets": [market]}, RECEIVED)[0]["payload"]
                candle = {"end_period_ts": 1763337600, "price": {"close_dollars": value, "close": 37}}
                closed = kalshi.candlestick_rows("X", {"candlesticks": [candle]}, RECEIVED)[0]["payload"]
                self.assertEqual((snapshot["last_price"], closed["close"]), (cents, cents))
                self.assertEqual((snapshot["p_yes"], closed["p_yes"]), (cents / 100, cents / 100))
        for blank in (None, ""):
            market = {"ticker": "X", "last_price_dollars": blank, "last_price": 37}
            self.assertEqual(kalshi.market_snapshot_rows({"markets": [market]}, RECEIVED)[0]["payload"]["p_yes"], 0.37)

    def test_candles_current_fields(self):
        payload = {"candlesticks": [{"end_period_ts": 1763337600, "price": {"close_dollars": "0.5800"},
                                     "volume_fp": "3000.00", "open_interest_fp": "8000.00"}]}
        r = kalshi.candlestick_rows("T", payload, RECEIVED)[0]["payload"]
        self.assertEqual(r["p_yes"], 0.58)
        self.assertEqual(r["volume"], 3000.0)

    def test_candles(self):
        rows = kalshi.candlestick_rows("KXFED-26DEC-T4.25", CANDLES, RECEIVED)
        self.assertEqual(rows[0]["published_at"], datetime.fromtimestamp(1763337600, tz=timezone.utc))
        self.assertEqual(rows[0]["payload"]["p_yes"], 0.58)
        self.assertIsNone(rows[1]["payload"]["p_yes"])

    def test_price_out_of_range(self):
        with self.assertRaises(kalshi.KalshiError):
            kalshi.market_snapshot_rows({"markets": [{"ticker": "X", "yes_bid": 150}]}, RECEIVED)

    def test_naive_received(self):
        with self.assertRaises(kalshi.KalshiError):
            kalshi.candlestick_rows("X", CANDLES, datetime(2026, 11, 18))

    def test_invalid_counts_rejected_in_snapshots_and_candles(self):
        invalid = (True, False, float("nan"), "Infinity", "-Infinity", 10**400, "1e-1000", "-1e-1000")
        for name in ("volume", "open_interest", "volume_24h"):
            for key in (name, name + "_fp"):
                for value in invalid:
                    with self.subTest(key=key, value=value):
                        market = {"ticker": "X", name: 12, key: value}
                        with self.assertRaises(kalshi.KalshiError):
                            kalshi.market_snapshot_rows({"markets": [market]}, RECEIVED)
                        if name != "volume_24h":
                            candle = {"end_period_ts": 1763337600, name: 12, key: value}
                            with self.assertRaises(kalshi.KalshiError):
                                kalshi.candlestick_rows("X", {"candlesticks": [candle]}, RECEIVED)

    def test_fixed_point_and_legacy_counts_at_liquidity_threshold(self):
        markets = [
            {"ticker": "A", "volume_fp": "999.75", "volume": 1001, "open_interest_fp": "0.00"},
            {"ticker": "B", "volume_fp": "", "volume": 1000},
            {"ticker": "C", "volume_24h_fp": None, "volume_24h": 3},
        ]
        rows = kalshi.market_snapshot_rows({"markets": markets}, RECEIVED)
        self.assertEqual([(r["payload"]["volume"], r["payload"]["liquid"]) for r in rows],
                         [(999.75, False), (1000, True), (None, False)])
        self.assertEqual(rows[0]["payload"]["open_interest"], 0)
        self.assertEqual(rows[2]["payload"]["volume_24h"], 3)


class KalshiPagination(unittest.TestCase):
    def setUp(self):
        from data.didm import kalshi as client
        self.client = client

    def test_bad_envelopes_do_not_complete_a_partial_batch(self):
        for invalid in (None, [], {}, {"markets": None}, {"markets": {}}, {"markets": "x"}, {"markets": [1]}):
            with self.subTest(invalid=invalid):
                pages = [{"markets": [{"ticker": "A"}], "cursor": "next"}, invalid]
                with patch.object(self.client, "fetch_markets", side_effect=pages) as fetch:
                    with self.assertRaises(self.client.SourceError):
                        self.client.fetch_all_markets("SERIES")
                    self.assertEqual(fetch.call_count, 2)

    def test_invalid_cursor_types_never_mean_complete(self):
        for token in (False, 0, 1, [], {}, True):
            with self.subTest(token=token), patch.object(self.client, "fetch_markets",
                                                        return_value={"markets": [], "cursor": token}):
                with self.assertRaises(self.client.SourceError):
                    self.client.fetch_all_markets("SERIES", max_pages=1)

    def test_repeated_cursor_is_an_error_even_at_the_cap(self):
        pages = [{"markets": [], "cursor": token} for token in ("x", "y", "x")]
        with patch.object(self.client, "fetch_markets", side_effect=pages) as fetch:
            with self.assertRaises(self.client.SourceError):
                self.client.fetch_all_markets("SERIES", max_pages=3)
            self.assertEqual(fetch.call_count, 3)

    def test_empty_page_continues_and_repeated_markets_keep_order(self):
        row_a, row_b = {"ticker": "A"}, {"ticker": "B"}
        for terminal in ({}, {"cursor": None}, {"cursor": ""}):
            with self.subTest(terminal=terminal):
                pages = [{"markets": [row_a], "cursor": " first "}, {"markets": [], "cursor": "second"},
                         {"markets": [row_b, row_a], **terminal}]
                with patch.object(self.client, "fetch_markets", side_effect=pages) as fetch:
                    result = self.client.fetch_all_markets("SERIES", "closed", max_pages=3)
                    self.assertEqual(result, {"markets": [row_a, row_b, row_a], "pages": 3, "complete": True})
                    self.assertEqual(fetch.call_args_list, [call("SERIES", "closed", cursor=token)
                                                           for token in (None, " first ", "second")])

    def test_new_cursor_at_the_cap_keeps_partial_results(self):
        row = {"ticker": "A"}
        with patch.object(self.client, "fetch_markets", return_value={"markets": [row], "cursor": "next"}) as fetch:
            result = self.client.fetch_all_markets("SERIES", max_pages=1)
            self.assertEqual(result, {"markets": [row], "pages": 1, "complete": False})
            fetch.assert_called_once_with("SERIES", "open", cursor=None)


class KeyCheck(unittest.TestCase):
    def test_names_and_booleans_only(self):
        from tools.didm.collect_daily import KEY_NAMES, key_status
        env = {"ECOS_API_KEY": "secret-value", "FRED_API_KEY": "  ", "SEC_EDGAR_USER_AGENT": "Org x@y"}
        status = key_status(env)
        self.assertEqual(set(status), set(KEY_NAMES))
        self.assertEqual({k: v for k, v in status.items() if v}, {"ECOS_API_KEY": True, "SEC_EDGAR_USER_AGENT": True})
        self.assertNotIn("secret-value", repr(status))


class EnvFile(unittest.TestCase):
    def test_env_file_loads_without_override(self):
        import os
        from unittest import mock
        from tools.didm.collect_daily import key_status, load_env_file
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"ECOS_API_KEY": "kept"}, clear=False):
            os.environ.pop("OPENDART_API_KEY", None)
            env = Path(tmp) / ".env"
            env.write_text("OPENDART_API_KEY=from-file\nECOS_API_KEY=ignored\n", encoding="utf-8")
            load_env_file(str(env))
            self.assertTrue(key_status()["OPENDART_API_KEY"])
            self.assertEqual(os.environ["ECOS_API_KEY"], "kept")
            os.environ.pop("OPENDART_API_KEY", None)

    def test_missing_env_file(self):
        from tools.didm.collect_daily import load_env_file
        with self.assertRaises(SystemExit):
            load_env_file("/nonexistent/.env")


class EcosSpec(unittest.TestCase):
    def test_leading_zero_loss_refused(self):
        from tools.didm.collect_daily import ecos_spec
        self.assertEqual(ecos_spec("722Y001,M,202401,202610,0101000")[4], ["0101000"])
        with self.assertRaises(SystemExit):
            ecos_spec("722Y001,M,202401,202610,101000")


class IntoStore(unittest.TestCase):
    def test_all_sources_as_of(self):
        rows = (filings.edgar_rows(SUBMISSIONS, RECEIVED) + filings.opendart_rows(DART, RECEIVED)
                + ecos.rows(ECOS, RECEIVED) + kalshi.market_snapshot_rows(MARKETS, RECEIVED)
                + kalshi.candlestick_rows("KXFED-26DEC-T4.25", CANDLES, RECEIVED))
        with tempfile.TemporaryDirectory() as tmp, PointInTimeStore(Path(tmp) / "s.sqlite") as st:
            self.assertEqual(st.append_many(rows), len(rows))
            a = st.as_of("2026-11-18T02:00:00Z")
            self.assertEqual(len(a), len(rows))
            self.assertEqual(a, st.as_of("2026-11-18T02:00:00Z"))
            self.assertEqual(st.as_of("2026-11-18T00:59:59Z"), [])


if __name__ == "__main__":
    unittest.main()
