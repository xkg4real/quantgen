"""Ranked lists for Markets, pure logic (owner request 2026-11-11, point 5: Toss-style "실시간 차트").

The curated universe, the ranking per category/market/sector, the provider-answer parsers and the compact
figures. Fixture records only; nothing here touches the network or Qt.
"""
import re
import unittest
from datetime import datetime, timezone

from core.market import rankings as R
from core.market.models import Instrument
from core.market.symbols import lookup


def member(code):
    return next(m for m in R.DOMESTIC + R.US if m.code == code)


def record(code, *, price=100.0, pct=0.0, volume=None, value=None, cap=None, mode="kis", as_of="2026-11-11",
           market=""):
    return R.QuoteRecord(member(code), price, price * pct / 100, pct, volume, value, cap, "KIS", mode, as_of,
                         market=market)


SAMSUNG, HYNIX, KAKAO, ECOPRO, ALTEO, APPLE, NVDA = "005930", "000660", "035720", "247540", "196170", "AAPL", "NVDA"


class UniverseTests(unittest.TestCase):
    def test_contract_keys_and_tables(self):
        self.assertEqual(R.CATEGORIES, (("value", "Trading value", "거래대금"), ("volume", "Volume", "거래량"),
                                        ("gainers", "Top gainers", "급상승"), ("losers", "Top losers", "급하락"),
                                        ("cap", "Market cap", "시가총액")))
        self.assertEqual(R.MARKET_KEYS, ("kr", "kospi", "kosdaq", "us"))
        self.assertEqual({k for k, _e, _k in R.STATES}, {"live", "closed", "stale", "daily", "none"})
        for table in (R.CATEGORIES, R.MARKETS, R.SECTORS, R.STATES, R.COLUMNS):
            for key, en, ko in table:
                self.assertFalse(re.search("[가-힣]", en), en)
                self.assertTrue(re.search("[가-힣]", ko) or ko.isascii(), ko)
                self.assertEqual(R.text(table, key, "en"), en)
                self.assertEqual(R.text(table, key, "ko"), ko)

    def test_members_are_valid_unique_and_named_in_both_languages(self):
        everyone = R.DOMESTIC + R.US
        self.assertEqual(len({m.code for m in everyone}), len(everyone))
        self.assertGreaterEqual(len(R.DOMESTIC), 60)
        self.assertGreaterEqual(len(R.US), 40)
        sectors = {k for k, _e, _k in R.SECTORS}
        for m in everyone:
            with self.subTest(code=m.code):
                self.assertIn(m.market, ("KOSPI", "KOSDAQ", "US"))
                self.assertIn(m.sector, sectors)
                self.assertTrue(m.name_ko and m.name_en)
                self.assertFalse(re.search("[가-힣]", m.name_en), m.name_en)
                self.assertIsInstance(m.instrument, Instrument)
                self.assertIs(R.member_for(m.instrument), m)
        for m in R.US:
            listed = lookup(m.code)  # the bundled overseas list carries the same KIS exchange code
            self.assertIsNotNone(listed, m.code)
            self.assertEqual(listed.exchange, m.exchange, m.code)
        self.assertTrue({"KOSPI", "KOSDAQ"} <= {m.market for m in R.DOMESTIC})

    def test_universe_filters_by_market_and_sector(self):
        self.assertEqual(R.universe("kr"), R.DOMESTIC)
        self.assertTrue(all(m.market == "KOSDAQ" for m in R.universe("kosdaq")))
        self.assertTrue(all(m.market == "KOSPI" for m in R.universe("kospi")))
        self.assertEqual(len(R.universe("kospi")) + len(R.universe("kosdaq")), len(R.DOMESTIC))
        self.assertEqual(R.universe("us"), R.US)
        self.assertTrue(all(m.sector == "semis" for m in R.universe("kr", "semis")))
        self.assertIn("battery", R.sectors_in("kr")); self.assertNotIn("battery", R.sectors_in("us"))
        self.assertEqual((R.group_of("kospi"), R.group_of("us")), ("kr", "us"))
        with self.assertRaises(ValueError):
            R.group_of("jp")


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.records = (
            record(SAMSUNG, price=102300, pct=1.5, volume=1.5e7, value=1.5e12, cap=6.05e14),
            record(HYNIX, price=520000, pct=-2.0, volume=3.0e6, value=1.6e12, cap=3.8e14),
            record(KAKAO, price=40000, pct=4.2, volume=2.0e7, value=8.0e11, cap=1.8e13),
            record(ECOPRO, price=150000, pct=-6.5, volume=1.0e6, value=1.5e11, cap=None),
            record(ALTEO, price=400000, pct=0.0, volume=0.0, value=0.0, cap=2.1e13),
            record(APPLE, price=226.1, pct=0.8, volume=4.0e7, value=9.0e9),
            record(NVDA, price=180.2, pct=-1.1, volume=2.0e8, value=3.6e10),
        )

    def codes(self, rows):
        return [row.record.member.code for row in rows]

    def test_each_category_orders_and_filters(self):
        self.assertEqual(self.codes(R.rank(self.records, "value")), [HYNIX, SAMSUNG, KAKAO, ECOPRO])  # 0 left out
        self.assertEqual(self.codes(R.rank(self.records, "volume")), [KAKAO, SAMSUNG, HYNIX, ECOPRO])
        self.assertEqual(self.codes(R.rank(self.records, "gainers")), [KAKAO, SAMSUNG])  # rising only
        self.assertEqual(self.codes(R.rank(self.records, "losers")), [ECOPRO, HYNIX])    # falling only
        self.assertEqual(self.codes(R.rank(self.records, "cap")), [SAMSUNG, HYNIX, ALTEO, KAKAO])  # no cap: out
        rows = R.rank(self.records, "value")
        self.assertEqual([row.rank for row in rows], [1, 2, 3, 4])
        self.assertEqual(rows[0].value, 1.6e12)
        self.assertEqual(R.rank(self.records, "losers")[0].value, -6.5)
        with self.assertRaises(ValueError):
            R.rank(self.records, "popular")

    def test_markets_sectors_limit_and_ties(self):
        self.assertEqual(self.codes(R.rank(self.records, "volume", market="us")), [NVDA, APPLE])
        self.assertEqual(self.codes(R.rank(self.records, "value", market="kosdaq")), [ECOPRO])
        self.assertEqual(self.codes(R.rank(self.records, "value", market="kospi")), [HYNIX, SAMSUNG, KAKAO])
        self.assertEqual(self.codes(R.rank(self.records, "value", sector="semis")), [HYNIX, SAMSUNG])
        self.assertEqual(self.codes(R.rank(self.records, "value", limit=2)), [HYNIX, SAMSUNG])
        # An observed listing market (KIS names it, or Yahoo answered under the other suffix) wins.
        moved = record(ALTEO, pct=1.0, value=5e11, market="KOSPI")
        self.assertIn(ALTEO, self.codes(R.rank((moved,), "value", market="kospi")))
        self.assertEqual(R.rank((moved,), "value", market="kosdaq"), [])
        tie = (record(KAKAO, value=1e11), record(SAMSUNG, value=1e11))
        self.assertEqual(self.codes(R.rank(tie, "value")), [SAMSUNG, KAKAO])  # stable by code

    def test_value_column_unit(self):
        self.assertEqual(R.value_unit("value", "kr"), ("value", "krw"))
        self.assertEqual(R.value_unit("gainers", "us"), ("value", "usd"))
        self.assertEqual(R.value_unit("volume", "kr"), ("volume", "shares"))
        self.assertEqual(R.value_unit("cap", "kr"), ("cap", "krw"))


class ParsingTests(unittest.TestCase):
    def test_kis_domestic_quote(self):
        out = {"stck_prpr": "102,300", "prdy_vrss": "1500", "prdy_vrss_sign": "5", "prdy_ctrt": "1.45",
               "acml_vol": "14900000", "acml_tr_pbmn": "1520000000000", "hts_avls": "6050000",
               "rprs_mrkt_kor_name": "KOSPI200"}
        r = R.parse_kis_domestic(member(SAMSUNG), out, received_at="2026-11-11T05:20:00+00:00")
        self.assertEqual((r.price, r.change, r.change_pct), (102300.0, -1500.0, -1.45))  # sign 5: down
        self.assertEqual((r.volume, r.trading_value, r.market_cap), (1.49e7, 1.52e12, 6.05e14))  # 억원 -> won
        self.assertEqual((r.mode, r.source, r.market, r.estimated_value), ("kis", "KIS", "KOSPI", False))
        self.assertEqual(R.parse_kis_domestic(member(ALTEO), {**out, "rprs_mrkt_kor_name": "KOSDAQ150"}).market,
                         "KOSDAQ")
        up = R.parse_kis_domestic(member(SAMSUNG), {**out, "prdy_vrss_sign": "2", "hts_avls": "", "acml_tr_pbmn": "x"})
        self.assertEqual((up.change, up.market_cap, up.trading_value), (1500.0, None, None))
        for bad in ({}, {"stck_prpr": "0"}, None, {"stck_prpr": "nan"}):
            with self.assertRaises(ValueError):
                R.parse_kis_domestic(member(SAMSUNG), bad)

    def test_kis_overseas_quote(self):
        out = {"last": "226.13", "diff": "1.80", "sign": "2", "rate": "0.80", "tvol": "40000000",
               "tamt": "9045200000", "base": "224.33"}
        r = R.parse_kis_overseas(member(APPLE), out)
        self.assertEqual((r.price, r.change, r.change_pct, r.volume, r.trading_value, r.market_cap),
                         (226.13, 1.8, 0.8, 4.0e7, 9.0452e9, None))
        derived = R.parse_kis_overseas(member(APPLE), {"last": "220", "base": "200", "sign": ""})
        self.assertAlmostEqual(derived.change_pct, 10.0)
        with self.assertRaises(ValueError):
            R.parse_kis_overseas(member(APPLE), {"last": ""})

    def test_daily_bars_are_delayed_estimated_and_stale_ones_left_out(self):
        bars = [("2026-11-06", 1, 1, 1, 100.0, 10.0), ("2026-11-10", 1, 1, 1, 110.0, 1000.0),
                ("2026-11-07", 1, 1, 1, "bad", 5), ("2026-11-09", 1, 1, 1, 105.0, None)]
        r = R.record_from_bars(member(KAKAO), bars, market="KOSPI")
        self.assertEqual((r.price, r.as_of, r.mode, r.market), (110.0, "2026-11-10", "daily", "KOSPI"))
        self.assertAlmostEqual(r.change_pct, (110 / 105 - 1) * 100)
        self.assertEqual((r.volume, r.trading_value, r.estimated_value), (1000.0, 110000.0, True))
        self.assertEqual(r.closes, (100.0, 105.0, 110.0))
        with self.assertRaises(ValueError):
            R.record_from_bars(member(KAKAO), bars[:1])
        old = R.record_from_bars(member(SAMSUNG), [("2026-10-30", 1, 1, 1, 9.0, 1), ("2026-10-31", 1, 1, 1, 10.0, 1)])
        kept, stale = R.drop_stale((r, old))
        self.assertEqual(([k.member.code for k in kept], stale), ([KAKAO], (SAMSUNG,)))
        live = record(HYNIX, value=1.0)
        self.assertEqual(R.drop_stale((live,)), ((live,), ()))


class DisplayTests(unittest.TestCase):
    def test_compact_figures(self):
        cases = [(1.23e12, "krw", "1.2조", "₩1.2T"), (3.456e11, "krw", "3,456억", "₩345.6B"),
                 (6.05e14, "krw", "605.0조", "₩605.0T"), (2.13e7, "shares", "2,130만주", "21.3M"),
                 (1.2e8, "shares", "1.2억주", "120.0M"), (1.23e10, "usd", "$12.3B", "$12.3B"),
                 (950, "shares", "950주", "950"), (None, "krw", "—", "—"), (float("nan"), "usd", "—", "—")]
        for value, unit, ko, en in cases:
            with self.subTest(value=value, unit=unit):
                self.assertEqual(R.compact(value, unit, "ko"), ko)
                self.assertEqual(R.compact(value, unit, "en"), en)

    def test_price_change_and_state(self):
        self.assertEqual(R.price_text(102300, "KRW"), "102,300")
        self.assertEqual(R.price_text(1226.5, "USD"), "$1,226.50")
        self.assertEqual(R.change_text(1.234), ("+1.23%", "up"))
        self.assertEqual(R.change_text(-0.5), ("-0.50%", "down"))
        self.assertEqual(R.change_text(0.0), ("0.00%", "flat"))
        self.assertEqual(R.change_text(None), ("", "flat"))
        kis = R.Batch("kr", (record(SAMSUNG),), "kis", "2026-11-11T05:00:00+00:00")
        daily = R.Batch("kr", (record(SAMSUNG, mode="daily"),), "daily", "2026-11-11T05:00:00+00:00")
        self.assertEqual(R.source_state(kis, open_now=True), "live")
        self.assertEqual(R.source_state(kis, open_now=False), "closed")  # KIS after the close is not live
        self.assertEqual(R.source_state(kis, open_now=True, age_seconds=200, live_limit=135), "stale")
        self.assertEqual(R.source_state(kis, open_now=True, age_seconds=100, live_limit=135), "live")
        self.assertEqual(R.source_state(daily, open_now=True), "daily")  # delayed bars are never live
        self.assertEqual(R.source_state(R.Batch("kr", (), "none", ""), open_now=True), "none")
        self.assertEqual(R.source_state(None, open_now=True), "none")

    def test_session_hours_follow_the_market_calendars(self):
        self.assertTrue(R.session_open("kr", datetime(2026, 11, 11, 2, 0, tzinfo=timezone.utc)))    # 11:00 KST Wed
        self.assertFalse(R.session_open("kr", datetime(2026, 11, 11, 8, 0, tzinfo=timezone.utc)))   # 17:00 KST
        self.assertFalse(R.session_open("kr", datetime(2026, 11, 14, 2, 0, tzinfo=timezone.utc)))   # Saturday
        self.assertTrue(R.session_open("us", datetime(2026, 11, 11, 16, 0, tzinfo=timezone.utc)))   # 11:00 ET
        self.assertFalse(R.session_open("us", datetime(2026, 11, 11, 2, 0, tzinfo=timezone.utc)))


if __name__ == "__main__":
    unittest.main()
