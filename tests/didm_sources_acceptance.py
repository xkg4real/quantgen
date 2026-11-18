"""DS-4d/DS-4e: EDGAR, OpenDART, ECOS and Kalshi parsers from fixtures. No network."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

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


class KeyCheck(unittest.TestCase):
    def test_names_and_booleans_only(self):
        from tools.didm.collect_daily import KEY_NAMES, key_status
        env = {"ECOS_API_KEY": "secret-value", "FRED_API_KEY": "  ", "SEC_EDGAR_USER_AGENT": "Org x@y"}
        status = key_status(env)
        self.assertEqual(set(status), set(KEY_NAMES))
        self.assertEqual(status, {"FRED_API_KEY": False, "OPENDART_API_KEY": False,
                                  "ECOS_API_KEY": True, "SEC_EDGAR_USER_AGENT": True})
        self.assertNotIn("secret-value", repr(status))


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
