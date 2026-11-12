"""Ranked lists for Markets, pure logic (owner request 2026-11-11, point 5: Toss-style "실시간 차트").

The curated universe, the ranking per category/market/sector, the provider-answer parsers and the compact
figures; and US market cap (owner 2026-11-11, "아니 미국 시총 자료 찾으세요": FMP's stated figure, else
Yahoo share counts x the row price, cached a day); domestic market cap (KIS's hts_avls only when it agrees
with listed shares x price of the same answer) and the polled-state wording (2026-11-11 compliance follow-up).
Fixture records and injected fake providers only;
nothing here touches the network or Qt, and the share-count cache writes to a temporary folder.
"""
import json
from dataclasses import replace
from pathlib import Path
import re
import tempfile
import threading
import time
import unittest
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
import unittest.mock
from unittest.mock import patch

from core.market import market_cap as MC
from core.market import rankings as R
from core.market.models import Instrument
from core.market.symbols import lookup
from data.fmp.quote_client import FMPError, FMPPlanError


def member(code):
    return next(m for m in R.DOMESTIC + R.US + R.CRYPTO if m.code == code)


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
        self.assertEqual({k for k, _e, _k in R.STATES}, {"polled", "polled_us", "closed", "stale", "daily", "none"})
        self.assertEqual(R.CAP_LABELS, (("provider", "Market cap", "시가총액"),
                                        ("computed", "Market cap (computed)", "시가총액(계산값)")))
        for table in (R.CATEGORIES, R.MARKETS, R.SECTORS, R.STATES, R.COLUMNS, R.CAP_LABELS):
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
               "lstn_stcn": "5969782550", "rprs_mrkt_kor_name": "KOSPI200"}
        r = R.parse_kis_domestic(member(SAMSUNG), out, received_at="2026-11-11T05:20:00+00:00")
        self.assertEqual((r.price, r.change, r.change_pct), (102300.0, -1500.0, -1.45))  # sign 5: down
        # hts_avls read as 100 million won, used because it agrees with listed shares x price (610.7조).
        self.assertEqual((r.volume, r.trading_value, r.market_cap), (1.49e7, 1.52e12, 6.05e14))
        self.assertEqual((r.cap_basis, r.cap_source, r.cap_as_of, r.shares),
                         ("provider", "KIS", "2026-11-11T05:20:00+00:00", 5969782550.0))
        self.assertEqual((r.mode, r.source, r.market, r.estimated_value), ("kis", "KIS", "KOSPI", False))
        self.assertEqual(R.parse_kis_domestic(member(ALTEO), {**out, "rprs_mrkt_kor_name": "KOSDAQ150"}).market,
                         "KOSDAQ")
        up = R.parse_kis_domestic(member(SAMSUNG), {**out, "prdy_vrss_sign": "2", "hts_avls": "", "acml_tr_pbmn": "x"})
        # Without KIS's figure: listed shares x price, labelled computed.
        self.assertEqual((up.change, up.market_cap, up.trading_value, up.cap_basis), (1500.0, 102300 * 5969782550,
                                                                                      None, "computed"))
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
        us = R.Batch("us", (record(APPLE),), "kis", "2026-11-11T15:00:00+00:00")
        daily = R.Batch("kr", (record(SAMSUNG, mode="daily"),), "daily", "2026-11-11T05:00:00+00:00")
        # KIS REST quotes polled during the session: "polled", never live (12-claims QG-CLAIM-KIS-20261102).
        self.assertEqual(R.source_state(kis, open_now=True), "polled")
        self.assertEqual(R.source_state(us, open_now=True), "polled_us")  # KIS's free US feed
        self.assertEqual(R.source_state(kis, open_now=False), "closed")  # KIS after the close is the last price
        self.assertEqual(R.source_state(kis, open_now=True, age_seconds=200, live_limit=135), "stale")
        self.assertEqual(R.source_state(kis, open_now=True, age_seconds=100, live_limit=135), "polled")
        self.assertEqual(R.source_state(daily, open_now=True), "daily")  # delayed bars are never live
        self.assertEqual(R.source_state(R.Batch("kr", (), "none", ""), open_now=True), "none")
        self.assertEqual(R.source_state(None, open_now=True), "none")

    def test_session_hours_follow_the_market_calendars(self):
        self.assertTrue(R.session_open("kr", datetime(2026, 11, 11, 2, 0, tzinfo=timezone.utc)))    # 11:00 KST Wed
        self.assertFalse(R.session_open("kr", datetime(2026, 11, 11, 8, 0, tzinfo=timezone.utc)))   # 17:00 KST
        self.assertFalse(R.session_open("kr", datetime(2026, 11, 14, 2, 0, tzinfo=timezone.utc)))   # Saturday
        self.assertTrue(R.session_open("us", datetime(2026, 11, 11, 16, 0, tzinfo=timezone.utc)))   # 11:00 ET
        self.assertFalse(R.session_open("us", datetime(2026, 11, 11, 2, 0, tzinfo=timezone.utc)))


# US market cap ---------------------------------------------------------------------------------------
STATED = "2026-11-11T05:19:00+00:00"
SHARES = {"AAPL": (1.484e10, "2026-10-17"), "NVDA": (2.43e10, "2026-10-31"), "MSFT": (7.43e9, "2026-10-24"),
          "JPM": (2.75e9, "2026-10-31")}


def us_record(code, price, mode="daily"):
    return R.QuoteRecord(member(code), price, 0.0, 0.0, 1e6, price * 1e6, None,
                         "KIS" if mode == "kis" else "Yahoo Finance", mode, "2026-11-10")


def us_batch(*pairs, mode="daily"):
    return R.Batch("us", tuple(us_record(code, price, mode) for code, price in pairs), mode,
                   "2026-11-11T05:20:00+00:00")


class Clock:
    def __init__(self, now=1_800_000_000.0):
        self.now = now

    def __call__(self):
        return self.now


class FakeYahoo:
    """Share counts by Yahoo symbol; `fail` raise like an unreachable host, `gate` holds every answer."""

    def __init__(self, shares=None, fail=(), gate=None, pause=0.0):
        self.shares, self.fail, self.gate, self.pause = dict(SHARES if shares is None else shares), set(fail), gate, pause
        self.calls, self.running, self.peak = [], 0, 0
        self.lock = threading.Lock()

    def __call__(self, symbol):
        with self.lock:
            self.calls.append(symbol)
            self.running += 1
            self.peak = max(self.peak, self.running)
        try:
            if self.gate is not None:
                self.gate.wait(5)
            time.sleep(self.pause)
            if symbol in self.fail:
                raise ConnectionError("SSLError: certificate verify failed")
            return self.shares.get(symbol)
        finally:
            with self.lock:
                self.running -= 1


def source(*, key="", fmp=None, yahoo=None, folder=None, clock=None, **kw):
    clock = clock or Clock()
    return MC.MarketCapSource(fmp_key=lambda: key, fmp_fetch=fmp or (lambda symbols, key: {}),
                              yahoo_fetch=yahoo or FakeYahoo(), cache=MC.SharesCache(folder, clock=clock),
                              clock=clock, **kw)


def by_code(batch):
    return {r.member.code: r for r in batch.records}


class MarketCapTests(unittest.TestCase):
    def test_fmp_states_the_cap_for_the_whole_universe_in_one_request(self):
        asked, clock, yahoo = [], Clock(), FakeYahoo()

        def fmp(symbols, *, key):
            asked.append((tuple(symbols), key))
            return {"AAPL": (3.4e12, STATED), "nvda": (4.4e12, STATED), "TSM": (1.5e12, STATED)}
        caps = source(key="k", fmp=fmp, yahoo=yahoo, clock=clock)
        batch = us_batch(("AAPL", 226.13), ("NVDA", 180.2), ("MSFT", 500.0), ("TSM", 290.0))
        out = caps(batch)
        got = by_code(out)
        self.assertEqual(asked, [(("AAPL", "NVDA", "MSFT", "TSM"), "k")])  # one batch request
        self.assertEqual((got["AAPL"].market_cap, got["AAPL"].cap_basis, got["AAPL"].cap_source, got["AAPL"].cap_as_of),
                         (3.4e12, "provider", "FMP", STATED))
        self.assertEqual((got["NVDA"].market_cap, got["TSM"].cap_basis), (4.4e12, "provider"))  # an ADR's stated cap
        self.assertEqual((got["MSFT"].cap_basis, got["MSFT"].market_cap), ("computed", 7.43e9 * 500.0))
        self.assertEqual(yahoo.calls, ["MSFT"])  # only what FMP did not state
        self.assertEqual((out.caps, out.cap_reasons), ("ok", ("kis_off",)))  # daily bars: KIS not in use
        self.assertEqual([r.price for r in out.records], [r.price for r in batch.records])  # quotes untouched
        clock.now += MC.PROVIDER_TTL_SECONDS - 1
        caps(batch)
        self.assertEqual(len(asked), 1)  # at most one FMP request per five minutes
        clock.now += 2
        caps(batch)
        self.assertEqual(len(asked), 2)
        domestic = R.Batch("kr", (record(SAMSUNG, cap=6e14),), "kis", "")
        self.assertIs(caps(domestic), domestic)  # the domestic path is not touched

    def test_fmp_refusals_fall_back_to_yahoo_and_are_not_retried_every_refresh(self):
        for error, reason, wait in ((FMPPlanError("HTTP 402"), "fmp_plan", MC.PLAN_RETRY_SECONDS),
                                    (FMPError("HTTP 500"), "fmp_failed", MC.FMP_RETRY_SECONDS),
                                    (None, "fmp_failed", MC.FMP_RETRY_SECONDS)):
            with self.subTest(reason=reason, error=error):
                asked, clock = [], Clock()

                def fmp(symbols, *, key):
                    asked.append(1)
                    if error is not None:
                        raise error
                    return {}  # an answer with no usable figure
                caps = source(key="k", fmp=fmp, clock=clock)
                out = caps(us_batch(("AAPL", 226.13)))
                self.assertEqual((out.caps, out.cap_reasons, out.records[0].cap_basis), ("ok", ("kis_off", reason), "computed"))
                clock.now += wait - 1
                self.assertEqual(caps(us_batch(("AAPL", 226.13))).cap_reasons, ("kis_off", reason))
                self.assertEqual(len(asked), 1)
                clock.now += 2
                caps(us_batch(("AAPL", 226.13)))
                self.assertEqual(len(asked), 2)

    def test_yahoo_share_counts_times_the_row_price_cached_for_a_day(self):
        with tempfile.TemporaryDirectory() as folder:
            clock, yahoo = Clock(), FakeYahoo()
            caps = source(yahoo=yahoo, folder=folder, clock=clock)
            out = caps(us_batch(("AAPL", 226.13), ("TSM", 290.0), mode="kis"))  # KIS last price
            apple, tsmc = out.records
            self.assertAlmostEqual(apple.market_cap, 1.484e10 * 226.13)
            self.assertEqual((apple.cap_basis, apple.cap_source, apple.cap_as_of, apple.shares),
                             ("computed", "Yahoo Finance", "2026-10-17", 1.484e10))
            self.assertEqual((tsmc.market_cap, tsmc.cap_missing), (None, "adr"))  # shares not per ADR: no figure
            self.assertEqual(yahoo.calls, ["AAPL"])
            self.assertEqual((out.caps, out.cap_reasons), ("ok", ("kis_none", "fmp_no_key")))  # KIS quotes, no KIS cap
            stored = json.loads((Path(folder) / "SHARES_YFINANCE_AAPL.json").read_text("utf-8"))
            self.assertEqual((stored["shares"], stored["as_of"], stored["source"], stored["ts"]),
                             (1.484e10, "2026-10-17", "Yahoo Finance", clock.now))
            daily = caps(us_batch(("AAPL", 210.0)))  # the daily close when that is the row's price
            self.assertAlmostEqual(daily.records[0].market_cap, 1.484e10 * 210.0)
            self.assertEqual(yahoo.calls, ["AAPL"])  # memory hit
            # A restart within 24 hours reads the file; after 24 hours the count is asked again.
            clock.now += 23 * 3600
            later = FakeYahoo()
            restarted = source(yahoo=later, folder=folder, clock=clock)
            self.assertEqual(restarted(us_batch(("AAPL", 220.0))).records[0].cap_as_of, "2026-10-17")
            self.assertEqual(later.calls, [])
            clock.now += 2 * 3600
            restarted(us_batch(("AAPL", 220.0)))
            self.assertEqual(later.calls, ["AAPL"])
        memory_only = MC.SharesCache(None, clock=Clock())
        memory_only.put("AAPL", 1e9, "2026-10-31")
        self.assertEqual((memory_only.get("aapl"), memory_only.path("AAPL")), ((1e9, "2026-10-31"), None))
        broken = Path(tempfile.mkdtemp()) / "SHARES_YFINANCE_AAPL.json"
        broken.write_text("{not json", "utf-8")
        self.assertIsNone(MC.SharesCache(broken.parent, clock=Clock()).get("AAPL"))  # unreadable: fetch again

    def test_partial_failure_keeps_the_rest_ranked_and_failed_stocks_wait(self):
        clock = Clock()
        yahoo = FakeYahoo({**SHARES, "JPM": None}, fail={"MSFT"})
        caps = source(yahoo=yahoo, clock=clock)
        batch = us_batch(("AAPL", 226.13), ("NVDA", 180.2), ("MSFT", 500.0), ("JPM", 301.5))
        out = caps(batch)
        got = by_code(out)
        self.assertEqual((got["MSFT"].market_cap, got["MSFT"].cap_missing), (None, "error"))
        self.assertEqual((got["JPM"].market_cap, got["JPM"].cap_missing), (None, "no_shares"))
        self.assertEqual(out.caps, "ok")
        rows = R.rank(out.records, "cap", market="us", missing="last")
        self.assertEqual([(r.rank, r.record.member.code) for r in rows], [(1, NVDA), (2, APPLE), (0, "MSFT"), (0, "JPM")])
        self.assertEqual([r.value for r in rows[2:]], [None, None])
        self.assertEqual([r.record.member.code for r in R.rank(out.records, "cap", market="us")], [NVDA, APPLE])
        self.assertEqual(R.rank(out.records, "gainers", market="us", missing="last"), [])  # change lists unaffected
        caps(batch)
        self.assertEqual(sorted(yahoo.calls), ["AAPL", "JPM", "MSFT", "NVDA"])  # failures wait, hits are cached
        clock.now += MC.FAILURE_RETRY_SECONDS + 1
        caps(batch)
        self.assertEqual(sorted(yahoo.calls[4:]), ["JPM", "MSFT"])

    def test_none_read_says_why(self):
        batch = us_batch(("AAPL", 226.13), ("NVDA", 180.2), ("TSM", 290.0))
        cases = (({"yahoo": FakeYahoo(fail=set(SHARES))}, ("kis_off", "fmp_no_key", "yahoo_unreachable")),
                 ({"yahoo": FakeYahoo({})}, ("kis_off", "fmp_no_key", "yahoo_empty")),
                 ({"yahoo": FakeYahoo(), "yahoo_ready": lambda: False}, ("kis_off", "fmp_no_key", "yahoo_missing")),
                 ({"key": "k", "fmp": Mock402(), "yahoo": FakeYahoo(fail=set(SHARES))}, ("kis_off", "fmp_plan", "yahoo_unreachable")))
        for kwargs, reasons in cases:
            with self.subTest(reasons=reasons):
                out = source(**kwargs)(batch)
                self.assertEqual((out.caps, out.cap_reasons), ("none", reasons))
                self.assertTrue(all(r.market_cap is None for r in out.records))
                self.assertTrue(set(reasons) <= set(R.CAP_REASONS))
                self.assertEqual(R.rank(out.records, "cap", market="us", missing="last"), [])  # empty: says why

    def test_bounded_workers_and_a_deadline_that_never_blocks_the_list(self):
        many = {m.code: (1e9 + i, "2026-10-31") for i, m in enumerate(R.US)}
        yahoo = FakeYahoo(many, pause=0.02)
        caps = source(yahoo=yahoo, workers=8)
        out = caps(R.Batch("us", tuple(us_record(m.code, 100.0) for m in R.US), "daily", ""))
        self.assertLessEqual(yahoo.peak, 4)  # never more than four requests at once
        self.assertEqual(sum(1 for r in out.records if r.market_cap), len(R.US) - len(R.ADR_CODES))
        gate = threading.Event()
        slow = FakeYahoo(gate=gate)
        caps = source(yahoo=slow, deadline=0.2)
        heard = []
        start = time.monotonic()
        out = caps(us_batch(("AAPL", 226.13)), progress=lambda done, total: heard.append((done, total)))
        self.assertLess(time.monotonic() - start, 2.0)
        self.assertEqual((out.caps, out.cap_reasons, out.records[0].cap_missing),
                         ("none", ("kis_off", "fmp_no_key", "yahoo_timeout"), "timeout"))
        self.assertEqual(caps(us_batch(("AAPL", 226.13))).records[0].cap_missing, "timeout")
        self.assertEqual(slow.calls, ["AAPL"])  # still in flight: not asked twice
        gate.set()
        end = time.monotonic() + 5
        while caps.cache.get("AAPL") is None and time.monotonic() < end:
            time.sleep(0.01)
        late = caps(us_batch(("AAPL", 226.13)))  # the late answer was kept for this refresh
        self.assertEqual((late.caps, late.records[0].cap_basis, slow.calls), ("ok", "computed", ["AAPL"]))
        self.assertEqual(heard, [])
        held = threading.Event()
        stop = source(yahoo=FakeYahoo(gate=held))
        self.assertEqual(stop(us_batch(("AAPL", 1.0)), cancelled=lambda: True).records[0].cap_missing, "timeout")
        held.set()

    def test_record_helpers_units_and_labels(self):
        apple = us_record(APPLE, 226.13)
        computed = R.computed_cap(apple, 1.6e10, source="Yahoo Finance", as_of="2026-10-17")
        self.assertAlmostEqual(computed.market_cap, 1.6e10 * 226.13)
        stated = R.with_cap(apple, 3.6e12, basis="provider", source="FMP", as_of=STATED)
        for value, ko, en in ((3.6e12, "$3.6T", "$3.6T"), (computed.market_cap, "$3.6T", "$3.6T"),
                              (4.512e11, "$451.2B", "$451.2B")):
            self.assertEqual((R.compact(value, "usd", "ko"), R.compact(value, "usd", "en")), (ko, en))
        self.assertEqual((R.compact(1.484e10, "shares", "ko"), R.compact(1.484e10, "shares", "en")),
                         ("148.4억주", "14.8B"))
        self.assertEqual((R.cap_label([computed, stated], "ko"), R.cap_label([computed], "en")),
                         ("시가총액(계산값)", "Market cap (computed)"))
        self.assertEqual((R.cap_label([stated], "ko"), R.cap_label([], "en")), ("시가총액", "Market cap"))
        self.assertEqual(R.cap_label(R.rank((computed,), "cap", market="us"), "ko"), "시가총액(계산값)")
        missing = R.without_cap(computed, "no_shares")
        self.assertEqual((missing.market_cap, missing.cap_basis, missing.shares, missing.cap_missing),
                         (None, "", None, "no_shares"))
        for bad in (0, -1, None, float("nan")):
            with self.assertRaises(ValueError):
                R.computed_cap(apple, bad, source="Yahoo Finance", as_of="")
        with self.assertRaises(ValueError):
            R.computed_cap(us_record("TSM", 290.0), 5.2e9, source="Yahoo Finance", as_of="")
        with self.assertRaises(ValueError):
            R.with_cap(apple, 1.0, basis="guess", source="")
        with self.assertRaises(ValueError):
            R.rank((computed,), "cap", missing="maybe")
        # A domestic figure that cannot be checked against a share count is not used.
        unchecked = R.parse_kis_domestic(member(SAMSUNG), {"stck_prpr": "1", "hts_avls": "5"})
        self.assertEqual((unchecked.cap_basis, unchecked.market_cap, unchecked.cap_missing), ("", None, "unverified"))


class SourceStateWordingTests(unittest.TestCase):
    """2026-11-11 compliance follow-up (12-claims QG-CLAIM-RANK-20261111, 09): the list polls KIS REST quotes
    every 45 s, so its state is worded as the stock detail view words polling ("5초 조회", "조회 시점", US
    "무료 시세"), never "실시간"/"real-time", a word kept for received trades."""

    def test_no_state_claims_live_ticks_and_the_polled_state_names_its_interval(self):
        for key, en, ko in R.STATES:
            self.assertNotIn("실시간", ko, key)
            self.assertFalse(re.search(r"(?i)real[- ]?time|live", en), en)
        self.assertEqual(R.text(R.STATES, "polled", "ko"), "KIS 조회 · 45초마다")
        self.assertEqual(R.text(R.STATES, "polled", "en"), "KIS · polled every 45 s")
        # UI-D10 review: the US state in the domestic one's order, without the trailing "조회" that overflowed.
        self.assertEqual(R.text(R.STATES, "polled_us", "ko"), "KIS 무료 시세 · 45초마다")
        self.assertEqual(R.text(R.STATES, "polled_us", "en"), "KIS free feed · polled every 45 s")
        self.assertEqual(R.POLL_SECONDS, 45)
        stock = Path(__file__).resolve().parents[1] / "quantgen_desktop" / "owner_ui_language" / "stock.py"
        words = stock.read_text(encoding="utf-8")
        self.assertIn("'● 5초 조회'", words)  # the detail view's polling word this list follows
        self.assertIn("'● 무료 시세'", words)  # and its US free-feed word

    def test_a_round_longer_than_the_interval_is_not_called_every_45_s(self):
        # Reviewer 2026-11-11: rounds are timed from their start (market_rankings.RankingBoard.due); a round
        # that itself took longer than POLL_SECONDS cannot keep the "every 45 s" promise, so it reads delayed.
        kis = R.Batch("kr", (record(SAMSUNG),), "kis", "2026-11-11T05:00:00+00:00")
        us = R.Batch("us", (record(APPLE),), "kis", "2026-11-11T15:00:00+00:00")
        for seconds, state in ((None, "polled"), (9.6, "polled"), (R.POLL_SECONDS, "polled"),
                               (R.POLL_SECONDS + 0.5, "stale"), (120, "stale")):
            self.assertEqual(R.source_state(kis, open_now=True, round_seconds=seconds), state, seconds)
        self.assertEqual(R.source_state(us, open_now=True, round_seconds=R.POLL_SECONDS + 1), "stale")
        self.assertEqual(R.source_state(kis, open_now=False, round_seconds=120), "closed")  # the last price anyway
        daily = R.Batch("kr", (record(SAMSUNG, mode="daily"),), "daily", "2026-11-11T05:00:00+00:00")
        self.assertEqual(R.source_state(daily, open_now=True, round_seconds=120), "daily")


class DomesticCapTests(unittest.TestCase):
    """2026-11-11 compliance follow-up (12-claims 2026-11-02 "hts_avls 단위 미검증"): KIS's hts_avls is used only
    when it agrees within 25% with listed shares x price of the same inquire-price answer, as the US path
    checks tomv; else refused ('—', unranked, with why); without hts_avls, shares x price is computed."""

    BASE = {"stck_prpr": "102300", "prdy_vrss": "0", "prdy_vrss_sign": "3", "prdy_ctrt": "0.00",
            "acml_vol": "1", "acml_tr_pbmn": "1", "hts_avls": "6050000", "lstn_stcn": "5969782550"}

    def parse(self, **fields):
        return R.parse_kis_domestic(member(SAMSUNG), {**self.BASE, **fields}, received_at="2026-11-11T05:20:00+00:00")

    def test_agreement_uses_kis_figure_within_tolerance_only(self):
        self.assertEqual(R.KIS_DOMESTIC_CAP_UNIT, 1e8)
        self.assertEqual(R.parse_kis_domestic_cap(self.BASE, 102300.0), (6.05e14, "provider", 5969782550.0, ""))
        computed = 5969782550 * 102300.0
        for ratio, used in ((1.0, True), (1.24, True), (0.76, True), (1.26, False), (0.74, False)):
            stated = str(round(computed * ratio / 1e8))
            cap, basis, _shares, missing = R.parse_kis_domestic_cap({**self.BASE, "hts_avls": stated}, 102300.0)
            self.assertEqual((cap is not None, basis, missing), (True, "provider", "") if used else
                             (False, "", "mismatch"), ratio)

    def test_refusals_are_never_rescaled(self):
        for fields, missing in (({"hts_avls": "605"}, "mismatch"),             # another unit: refused, not rescaled
                                ({"hts_avls": "605000000000000"}, "mismatch"),  # already won
                                ({"lstn_stcn": ""}, "unverified"), ({"lstn_stcn": None}, "unverified"),
                                ({"lstn_stcn": "  "}, "unverified"),
                                ({"hts_avls": "", "lstn_stcn": ""}, "absent"),
                                ({"hts_avls": None, "lstn_stcn": " "}, "absent")):
            r = self.parse(**fields)
            self.assertEqual((r.market_cap, r.cap_basis, r.cap_missing, r.shares), (None, "", missing, None), fields)
        self.assertEqual(R.parse_kis_domestic_cap(None, 1.0), (None, "", None, "absent"))
        self.assertEqual(R.parse_kis_domestic_cap(self.BASE, 0), (None, "", None, "absent"))

    def test_a_field_present_but_unusable_is_refused_with_its_own_reason(self):
        # Reviewer 2026-11-11: a share count of 0 was reported as missing, and a stated cap of 0 (or -5, 'nan',
        # 'inf') silently became the computed figure. Present but unusable is not absent.
        valid_cap, valid_shares = self.BASE["hts_avls"], self.BASE["lstn_stcn"]
        for shares in ("0", "-1", "5969782550.5", "x", "nan", "inf", True):
            for cap in (valid_cap, ""):
                with self.subTest(shares=shares, cap=cap):
                    r = self.parse(hts_avls=cap, lstn_stcn=shares)
                    self.assertEqual((r.market_cap, r.cap_basis, r.cap_missing, r.shares),
                                     (None, "", "bad_shares", None))
        for cap in ("0", "-5", "nan", "inf", "-inf", "x", True):
            for shares in (valid_shares, "", "0"):  # KIS's stated figure is refused, never replaced by shares x price
                with self.subTest(cap=cap, shares=shares):
                    r = self.parse(hts_avls=cap, lstn_stcn=shares)
                    self.assertEqual((r.market_cap, r.cap_basis, r.cap_missing, r.shares),
                                     (None, "", "bad_cap", None))
        self.assertEqual(self.parse(hts_avls=" 6,050,000 ").cap_basis, "provider")  # commas and spaces still read

    def test_computed_path_without_kis_figure(self):
        r = self.parse(hts_avls="")
        self.assertEqual((r.market_cap, r.cap_basis, r.cap_source, r.shares, r.cap_missing),
                         (5969782550 * 102300.0, "computed", "KIS", 5969782550.0, ""))
        self.assertEqual(R.cap_label(R.rank((r,), "cap"), "ko"), "시가총액(계산값)")

    def test_refused_rows_follow_the_ranked_ones_unranked(self):
        good = self.parse()
        computed = R.parse_kis_domestic(member(HYNIX), {**self.BASE, "stck_prpr": "520000", "hts_avls": "",
                                                        "lstn_stcn": "728002365"})
        refused = R.parse_kis_domestic(member(KAKAO), {**self.BASE, "stck_prpr": "40000", "hts_avls": "1",
                                                       "lstn_stcn": "442000000"})
        rows = R.rank((refused, computed, good), "cap", missing="last")
        self.assertEqual([(row.rank, row.record.member.code) for row in rows], [(1, SAMSUNG), (2, HYNIX), (0, KAKAO)])
        self.assertEqual(R.cap_label(rows, "ko"), "시가총액(계산값)")
        self.assertEqual(R.rank((refused,), "cap", missing="last"), [])  # nothing ranked: the list says why


class KISDetailTests(unittest.TestCase):
    """KIS overseas price-detail (HHDFS76200200), allowlisted with the owner's approval 2026-11-11 ("승인.")."""

    DETAIL = {"last": "226.1300", "tomv": "3355769200000", "shar": "14840000000", "curr": "USD", "perx": "34.10",
              "pbrx": "51.20", "t_xprc": "331000", "t_rate": "1463.80"}

    def test_tomv_is_used_only_when_it_agrees_with_listed_shares_times_last(self):
        self.assertEqual(R.parse_kis_overseas_detail(self.DETAIL), (3355769200000.0, 1.484e10))
        self.assertEqual(R.parse_kis_overseas_detail({**self.DETAIL, "curr": ""}), (3355769200000.0, 1.484e10))
        refused = ({**self.DETAIL, "tomv": "3355769200"},             # thousand-fold unit: refused, not rescaled
                   {**self.DETAIL, "tomv": str(3355769200000 * 1463.8)},  # won
                   {**self.DETAIL, "curr": "KRW"}, {**self.DETAIL, "shar": ""}, {**self.DETAIL, "tomv": "0"},
                   {**self.DETAIL, "last": "x"}, {}, None, "junk")
        for output in refused:
            with self.subTest(output=output):
                self.assertEqual(R.parse_kis_overseas_detail(output), (None, None))
        self.assertEqual(R.parse_kis_overseas_detail({**self.DETAIL, "tomv": "3000000000000"})[0], 3e12)  # 11% off: kept

    def test_record_gets_kis_stated_cap_but_never_for_an_adr(self):
        apple = us_record(APPLE, 226.13, "kis")
        stated = R.with_kis_detail(apple, self.DETAIL, received_at="2026-11-11T05:20:00+00:00")
        self.assertEqual((stated.market_cap, stated.cap_basis, stated.cap_source, stated.cap_as_of, stated.shares),
                         (3355769200000.0, "provider", "KIS", "2026-11-11T05:20:00+00:00", 1.484e10))
        self.assertEqual(R.cap_label([stated], "ko"), "시가총액")
        self.assertIs(R.with_kis_detail(apple, {}, received_at=""), apple)
        tsmc = us_record("TSM", 290.0, "kis")
        self.assertIs(R.with_kis_detail(tsmc, {**self.DETAIL, "last": "290", "shar": "5186000000",
                                              "tomv": str(5186000000 * 290)}), tsmc)

    def test_kis_figures_are_kept_and_only_the_rest_go_to_fmp_and_yahoo(self):
        asked, yahoo = [], FakeYahoo()

        def fmp(symbols, *, key):
            asked.append(tuple(symbols))
            return {"NVDA": (4.4e12, STATED)}
        caps = source(key="k", fmp=fmp, yahoo=yahoo)
        kis = us_batch(("AAPL", 226.13), ("NVDA", 180.2), ("MSFT", 500.0), mode="kis")
        kis = replace(kis, records=(R.with_kis_detail(kis.records[0], self.DETAIL, received_at=STATED),)
                      + kis.records[1:])
        out = caps(kis)
        got = by_code(out)
        self.assertEqual([got[c].cap_source for c in ("AAPL", "NVDA", "MSFT")], ["KIS", "FMP", "Yahoo Finance"])
        self.assertEqual((asked, yahoo.calls), ([("NVDA", "MSFT")], ["MSFT"]))
        self.assertEqual((out.caps, out.cap_reasons), ("ok", ()))
        everything = replace(kis, records=tuple(R.with_cap(r, 1e12, basis="provider", source="KIS", as_of=STATED)
                                                for r in kis.records))
        self.assertEqual((caps(everything).caps, len(asked), len(yahoo.calls)), ("ok", 1, 1))  # nothing else asked


class Mock402:
    def __call__(self, symbols, *, key):
        raise FMPPlanError("HTTP 402")


class Response:
    def __init__(self, status, payload):
        self.status_code, self.payload = status, payload

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


class ProviderCallTests(unittest.TestCase):
    def test_fmp_batch_quote_request_and_answers(self):
        asked = []
        stamp = int(datetime(2026, 11, 11, 5, 19, tzinfo=timezone.utc).timestamp())

        def get(url, params, timeout):
            asked.append((url, dict(params), timeout))
            return Response(200, [{"symbol": "AAPL", "marketCap": 3.4e12, "price": 226.1, "timestamp": stamp},
                                  {"symbol": "XYZ", "marketCap": None}, {"symbol": "BAD", "marketCap": -5}, "junk"])
        out = MC.fmp_batch(["AAPL", "XYZ", "BAD"], key="sekret", base_url="https://fmp.test/stable/", timeout=3, get=get)
        self.assertEqual(out, {"AAPL": (3.4e12, STATED)})
        self.assertEqual(asked, [("https://fmp.test/stable/batch-quote", {"symbols": "AAPL,XYZ,BAD", "apikey": "sekret"}, 3)])
        for status, payload, error in ((402, [], FMPPlanError), (403, [], FMPPlanError), (429, [], FMPError),
                                       (200, {"Error Message": "Restricted Endpoint: upgrade"}, FMPPlanError),
                                       (200, {"Error Message": "Invalid API KEY"}, FMPError),
                                       (200, ValueError("html"), FMPError), (200, "text", FMPError)):
            with self.subTest(status=status, payload=payload):
                with self.assertRaises(error):
                    MC.fmp_batch(["AAPL"], key="k", get=lambda url, params, timeout: Response(status, payload))

        def down(url, params, timeout):
            raise ConnectionError("https://fmp.test/stable/batch-quote?apikey=sekret failed")
        with self.assertRaises(FMPError) as caught:
            MC.fmp_batch(["AAPL"], key="sekret", get=down)
        self.assertNotIn("sekret", str(caught.exception))

    def test_yahoo_share_count_through_the_yfinance_handle(self):
        import pandas as pd
        index = pd.to_datetime(["2026-07-31", "2026-10-17", "2026-10-31"]).tz_localize("America/New_York")
        series = pd.Series([1.49e10, 1.484e10, float("nan")], index=index)
        asked = []

        class Ticker:
            def __init__(self, symbol):
                asked.append(symbol)

            def get_shares_full(self, start=None, end=None):
                asked.append(start)
                return series
        with patch("core.ficc.data._yf", SimpleNamespace(Ticker=Ticker)):
            self.assertEqual(MC.yahoo_shares("AAPL"), (1.484e10, "2026-10-17"))  # the newest valid count
            self.assertTrue(MC._yahoo_installed())
        self.assertEqual(asked[0], "AAPL")
        start = date.fromisoformat(asked[1])
        self.assertEqual((datetime.now(timezone.utc).date() - start).days, MC.SHARES_WINDOW_DAYS)
        self.assertEqual(MC.latest_shares(series.to_frame("shares")), (1.484e10, "2026-10-17"))
        for empty in (None, pd.Series(dtype=float), pd.DataFrame(), pd.Series([0.0, float("nan")], index=index[:2])):
            self.assertIsNone(MC.latest_shares(empty))
        with patch("core.ficc.data._yf", None):
            with self.assertRaises(ModuleNotFoundError):
                MC.yahoo_shares("AAPL")
            self.assertFalse(MC._yahoo_installed())
            caps = MC.MarketCapSource(fmp_key=lambda: "", cache=MC.SharesCache(None))
            self.assertEqual(caps(us_batch(("AAPL", 1.0))).cap_reasons, ("kis_off", "fmp_no_key", "yahoo_missing"))

    def test_production_cache_is_the_history_cache_directory_never_the_repository(self):
        import config
        repository = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(config, "ficc_cache_dir", return_value=Path(folder)), \
                patch.object(config, "FICC_CACHE_TTL_SECONDS", 6 * 3600.0):
            caps = MC.MarketCapSource(fmp_key=lambda: "", yahoo_fetch=FakeYahoo())
            caps(us_batch(("AAPL", 226.13)))
            self.assertTrue((Path(folder) / "SHARES_YFINANCE_AAPL.json").is_file())
            with patch.object(config, "FICC_CACHE_TTL_SECONDS", 0.0):
                self.assertIsNone(MC._default_directory())  # the history cache switched off: memory only
        self.assertFalse(list(repository.glob("SHARES_YFINANCE_*.json")))
        self.assertNotIn(str(repository), str(config.ficc_cache_dir().resolve()))  # ~/.nextgen/ficc_cache


class CoinUniverseTests(unittest.TestCase):
    """Owner ruling UI-D10: coins from the data the app already uses (keyless Yahoo daily), in US dollars."""

    def test_coins_are_a_market_of_their_own_with_no_stock_instrument(self):
        self.assertGreaterEqual(len(R.CRYPTO), 10)
        self.assertEqual(R.CRYPTO[0].code, "BTC")
        self.assertEqual(len({m.code for m in R.CRYPTO}), len(R.CRYPTO))
        for m in R.CRYPTO:
            with self.subTest(code=m.code):
                self.assertEqual((m.group, m.currency, m.instrument, m.place("ko"), m.sector),
                                 ("crypto", "USD", None, "", ""))
                self.assertEqual(R.crypto_symbol(m), f"{m.code}-USD")
                self.assertTrue(m.name_ko and m.name_en)
                self.assertFalse(re.search("[가-힣]", m.name_en))
        self.assertEqual((R.group_of("crypto"), R.members_of("crypto"), R.universe("crypto")),
                         ("crypto", R.CRYPTO, R.CRYPTO))
        self.assertEqual(R.sectors_in("crypto"), ())
        self.assertEqual(R.value_unit("value", "crypto"), ("value", "usd"))
        self.assertTrue(R.session_open("crypto"))  # coins trade every day
        self.assertEqual(R.MARKET_KEYS, ("kr", "kospi", "kosdaq", "us"))  # the earlier list keys are unchanged
        self.assertIsNone(R.member_for(Instrument("overseas_stock", "BTC", "NAS")))

    def test_yahoo_coin_volume_is_dollar_trading_value_never_a_unit_count(self):
        btc = R.CRYPTO[0]
        record = R.record_from_bars(btc, [("2026-11-09", 1, 1, 1, 95000.0, 3.0e10),
                                          ("2026-11-10", 1, 1, 1, 96123.5, 4.1e10)])
        self.assertEqual((record.trading_value, record.volume, record.estimated_value), (4.1e10, None, False))
        self.assertAlmostEqual(record.change_pct, (96123.5 / 95000 - 1) * 100)
        self.assertEqual(record.closes, (95000.0, 96123.5))
        self.assertEqual([r.record.member.code for r in R.rank((record,), "value", market="crypto")], ["BTC"])
        self.assertEqual(R.rank((record,), "volume", market="crypto"), [])  # no count, never ranked by it
        stock = R.record_from_bars(member(SAMSUNG), [("2026-11-09", 1, 1, 1, 100.0, 10.0),
                                                    ("2026-11-10", 1, 1, 1, 101.0, 20.0)])
        self.assertEqual((stock.trading_value, stock.volume, stock.estimated_value), (2020.0, 20.0, True))
        self.assertEqual((R.price_text(0.38124, "USD"), R.price_text(96123.5, "USD")), ("$0.3812", "$96,123.50"))

    def test_daily_path_asks_yahoo_for_the_dollar_pair_and_never_kis(self):
        from quantgen_desktop.market_rankings import ProductionRankingLoader
        asked = []

        def fetch(symbol):
            asked.append(symbol)
            if symbol == "ETH-USD":
                return []
            return [("2026-11-09", 1, 1, 1, 10.0, 5.0), ("2026-11-10", 1, 1, 1, 11.0, 6.0)]
        factory = unittest.mock.Mock(side_effect=AssertionError("KIS is never constructed for coins"))
        batch = ProductionRankingLoader(service_factory=factory, fetch=fetch,
                                        caps=unittest.mock.Mock(side_effect=AssertionError("no caps")))(
            "crypto", R.CRYPTO[:3])
        self.assertEqual(sorted(asked), ["BTC-USD", "ETH-USD", "XRP-USD"])
        self.assertEqual((batch.group, batch.mode), ("crypto", "daily"))
        self.assertEqual([r.member.code for r in batch.records], ["BTC", "XRP"])
        self.assertEqual(batch.failures, (("ETH", "LookupError"),))  # degraded per coin, said in the footnote
        factory.assert_not_called()
        self.assertEqual(R.source_state(batch, open_now=True), "daily")


class EtfUniverseTests(unittest.TestCase):
    """Owner ruling UI-D11 (2026-11-12, "ETF라해야지"): ETF lists on the stocks' data paths and ranking page."""

    def test_domestic_etfs_are_liquid_krx_etfs_apart_from_the_stocks(self):
        self.assertEqual(len(R.ETF_KR), 20)
        codes = [m.code for m in R.ETF_KR]
        self.assertEqual(len(set(codes)), 20)
        self.assertFalse(set(codes) & {m.code for m in R.DOMESTIC})
        for name in ("KODEX 200", "TIGER 200", "KODEX 레버리지", "KODEX 인버스", "KODEX 200선물인버스2X",
                     "TIGER 미국S&P500", "TIGER 미국나스닥100", "KODEX 미국S&P500TR", "KODEX 코스닥150",
                     "TIGER 2차전지테마"):
            self.assertIn(name, [m.name_ko for m in R.ETF_KR])
        # Codes the app already trades or studies as KRX ETFs (paper_live/config.py, the ETF tool's default).
        for code in ("069500", "229200", "114800", "251340", "132030", "261240", "122630"):
            self.assertIn(code, codes)
        for m in R.ETF_KR:
            with self.subTest(code=m.code):
                self.assertTrue(re.fullmatch(r"\d{6}", m.code))
                self.assertEqual((m.group, m.currency, m.sector, m.place("ko")), ("etf_kr", "KRW", "", ""))
                self.assertEqual(m.instrument, Instrument("domestic_stock", m.code))  # opens the stock screen
                self.assertIs(R.member_for(m.instrument), m)
                self.assertTrue(m.name_ko.startswith(("KODEX", "TIGER")) and m.name_en)
                self.assertFalse(re.search("[가-힣]", m.name_en))
                self.assertTrue(re.search("코덱스|타이거", m.aliases[0]))  # the brand typed in Hangul finds it

    def test_us_etfs_are_those_the_symbol_directory_lists_as_etfs(self):
        from unittest.mock import Mock
        from core.market.directory import SymbolDirectory
        directory = SymbolDirectory(master_loader=Mock(side_effect=AssertionError("No master download")))
        self.assertGreaterEqual(len(R.ETF_US), 10)
        self.assertEqual(R.ETF_US[0].code, "SPY")
        for m in R.ETF_US:
            with self.subTest(code=m.code):
                listing = directory.lookup("overseas_stock", m.code, m.exchange)
                self.assertIsNotNone(listing)
                self.assertEqual(listing.kind, "etf")
                self.assertEqual((m.group, m.currency, m.sector, m.place("en")), ("etf_us", "USD", "", ""))
                self.assertEqual(m.instrument, Instrument("overseas_stock", m.code, m.exchange))
                self.assertIs(R.member_for(m.instrument), m)
        for missing in ("VTI", "SMH", "XLK", "JEPI", "ARKK"):  # not in the bundled directory: not offered
            self.assertNotIn(missing, [m.code for m in R.ETF_US])

    def test_etf_groups_rank_as_stocks_without_market_cap(self):
        from core.market import screen as S
        self.assertEqual(R.GROUPS, ("kr", "us", "crypto", "etf_kr", "etf_us"))
        self.assertEqual(R.MARKET_KEYS, ("kr", "kospi", "kosdaq", "us"))  # the earlier list keys are unchanged
        for group, members, money in (("etf_kr", R.ETF_KR, "krw"), ("etf_us", R.ETF_US, "usd")):
            self.assertEqual((R.group_of(group), R.members_of(group), R.universe(group)), (group, members, members))
            self.assertEqual(R.sectors_in(group), ())
            self.assertEqual(R.value_unit("value", group), ("value", money))
            self.assertTrue(S.category_note(group, "cap"))
            self.assertFalse(any(S.category_note(group, key) for key in ("value", "volume", "gainers", "losers")))
            self.assertEqual([c.key for c in S.Screen(group).conditions()], ["change", "value"])
        bars = [("2026-11-09", 1, 1, 1, 30000.0, 1000.0), ("2026-11-10", 1, 1, 1, 30300.0, 2000.0)]
        leverage = R.record_from_bars(R.ETF_KR[2], bars)
        self.assertEqual((leverage.trading_value, leverage.volume, leverage.estimated_value), (30300.0 * 2000, 2000.0,
                                                                                               True))
        records = (leverage, R.record_from_bars(R.ETF_KR[0], [bars[0], ("2026-11-10", 1, 1, 1, 29000.0, 5000.0)]))
        self.assertEqual([r.record.member.code for r in S.Screen("etf_kr", "value").apply(records)],
                         ["069500", "122630"])
        self.assertEqual(S.Screen("etf_kr", "cap").apply(records), [])  # no market-cap ranking for ETFs
        self.assertEqual([m.code for m in S.Screen("etf_kr", text="레버리지").members()], ["122630", "233740"])
        self.assertEqual([m.code for m in S.Screen("etf_us", text="레버리지").members()], ["TQQQ", "SOXL"])
        self.assertEqual(S.threshold_text(1e10, "money", "etf_kr", "ko"), "100억")
        self.assertEqual(S.threshold_text(1e9, "money", "etf_us", "ko"), "$1B")
        us = R.Batch("etf_us", (R.QuoteRecord(R.ETF_US[0], 600.0, 1.0, 0.2, 1e6, 6e8, None, "KIS", "kis", "x"),),
                     "kis", "2026-11-11T05:20:00+00:00")
        self.assertEqual(R.source_state(us, open_now=True), "polled_us")  # KIS's free US feed, as US stocks
        for hour in (16, 2):  # 11:00 New York, then 11:00 Seoul
            moment = datetime(2026, 11, 11, hour, 0, tzinfo=timezone.utc)
            self.assertEqual(R.session_open("etf_us", moment), R.session_open("us", moment))
            self.assertEqual(R.session_open("etf_kr", moment), R.session_open("kr", moment))


class ScreenTests(unittest.TestCase):
    """Owner ruling UI-D10: the categories are each market's ranking and search criteria (core.market.screen)."""

    def setUp(self):
        from core.market import screen as S
        self.S = S
        self.records = (
            record(SAMSUNG, price=102300, pct=1.5, volume=1.5e7, value=1.5e12, cap=6.05e14),
            record(HYNIX, price=520000, pct=-2.0, volume=3.0e6, value=1.6e12, cap=3.8e14),
            record("042700", price=135400, pct=3.8, volume=1.0e6, value=5.7e11, cap=1.3e13),
            record(KAKAO, price=40000, pct=4.2, volume=2.0e7, value=8.0e11, cap=1.8e13),
            record(ECOPRO, price=150000, pct=-6.5, volume=1.0e6, value=1.5e11, cap=None),
            record("240810", price=40000, pct=5.3, volume=2.0e6, value=3.2e10, cap=2.0e12, market="KOSDAQ"),
            record(APPLE, price=226.1, pct=0.8, volume=4.0e7, value=9.0e9, cap=3.4e12),
            record("JPM", price=301.5, pct=2.7, volume=9.0e6, value=2.7e9, cap=8.3e11),
        )

    def codes(self, rows):
        return [row.record.member.code for row in rows]

    def test_pages_and_sub_markets(self):
        S = self.S
        # Owner ruling UI-D11: the coin market is 크립토 (never 코인), and two ETF pages follow.
        self.assertEqual(S.PAGES, (("kr", "Korean stocks", "국내 주식"), ("us", "US stocks", "미국 주식"),
                                   ("crypto", "Crypto", "크립토"), ("etf_kr", "Korean ETFs", "국내 ETF"),
                                   ("etf_us", "US ETFs", "미국 ETF")))
        self.assertEqual([k for k, _e, _k in S.SUBS["kr"]], ["", "kospi", "kosdaq"])
        self.assertEqual([k for k, _e, _k in S.SUBS["us"]], ["", "NAS", "NYS"])
        self.assertEqual((S.SUBS["crypto"], S.SUBS["etf_kr"], S.SUBS["etf_us"]), ((), (), ()))
        self.assertEqual({m.exchange for m in R.US}, {"NAS", "NYS"})  # the data has these two exchanges
        self.assertEqual((S.page_text("crypto", "ko"), S.sub_text("us", "NAS", "ko")), ("크립토", "나스닥"))

    def test_text_category_sub_market_sector_and_conditions_combine(self):
        S = self.S
        screen = S.Screen("kr", "gainers", text="반도체")  # a sector's name finds its stocks
        self.assertEqual(self.codes(screen.apply(self.records)), ["240810", "042700", SAMSUNG])
        self.assertEqual(self.codes(replace(screen, category="value").apply(self.records)),
                         [HYNIX, SAMSUNG, "042700", "240810"])
        self.assertEqual(self.codes(replace(screen, sub="kospi").apply(self.records)), ["042700", SAMSUNG])
        narrowed = screen.with_limit("change", 2, None).with_limit("value", 1e11)
        self.assertEqual(self.codes(narrowed.apply(self.records)), ["042700"])
        self.assertEqual(narrowed.limits, (("change", 2.0, None), ("value", 1e11, None)))
        self.assertEqual(self.codes(narrowed.without("value").apply(self.records)), ["240810", "042700"])
        self.assertEqual(narrowed.cleared().limits, ())
        self.assertEqual(self.codes(S.Screen("kr", "value", text="ㅅㅅㅈㅈ").apply(self.records)), [SAMSUNG])
        self.assertEqual(self.codes(S.Screen("kr", "value", text="hynix").apply(self.records)), [HYNIX])
        self.assertEqual(self.codes(S.Screen("kr", "value", text="035720").apply(self.records)), [KAKAO])
        self.assertEqual(self.codes(S.Screen("kr", "cap", sector="battery").apply(self.records)), [])  # no cap
        self.assertEqual(self.codes(S.Screen("kr", "cap").with_limit("cap", 1e14).apply(self.records)),
                         [SAMSUNG, HYNIX])
        # A missing figure never passes a condition on it (unknown is not "at least").
        self.assertNotIn(ECOPRO, self.codes(S.Screen("kr", "value").with_limit("cap", 1).apply(self.records)))
        self.assertEqual(self.codes(S.Screen("kr", "losers").with_limit("change", None, -3).apply(self.records)),
                         [ECOPRO])
        us = S.Screen("us", "value")
        self.assertEqual(self.codes(us.apply(self.records)), [APPLE, "JPM"])  # only the market's own records
        self.assertEqual(self.codes(replace(us, sub="NYS").apply(self.records)), ["JPM"])
        self.assertEqual(self.codes(replace(us, text="애플").apply(self.records)), [APPLE])
        self.assertEqual(len(S.Screen("kr", text="반도체").members()), len(R.universe("kr", "semis")))

    def test_a_new_condition_is_a_row_of_data(self):
        S = self.S
        extra = S.Condition("volume", "Volume", "거래량", "min", "money", lambda r: r.volume, pages=("kr",),
                            steps={"kr": (1e7,)})
        with patch.object(S, "CONDITIONS", S.CONDITIONS + (extra,)), \
                patch.object(S, "CONDITION_KEYS", S.CONDITION_KEYS + ("volume",)):
            screen = S.Screen("kr", "value").with_limit("volume", 1e7).with_limit("change", 0)
            self.assertEqual(screen.limits, (("change", 0.0, None), ("volume", 1e7, None)))  # table order
            self.assertEqual(self.codes(screen.apply(self.records)), [SAMSUNG, KAKAO])
            self.assertEqual([c.key for c in screen.conditions()], ["change", "value", "cap", "volume"])
            self.assertEqual([c.key for c in S.Screen("crypto").conditions()], ["change", "value"])
            with self.assertRaises(ValueError):
                S.Screen("us").with_limit("volume", 1)  # its table says Korea only

    def test_what_a_market_cannot_do_is_refused_or_said(self):
        S = self.S
        for bad in (dict(page="jp"), dict(page="kr", category="popular"), dict(page="kr", sub="NAS"),
                    dict(page="crypto", sector="semis"), dict(page="crypto", limits=(("cap", 1.0, None),)),
                    dict(page="kr", limits=(("change", 5.0, 1.0),)), dict(page="kr", limits=(("change", None, None),))):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                S.Screen(**bad)
        self.assertTrue(S.category_note("crypto", "volume") and S.category_note("crypto", "cap"))
        self.assertEqual((S.category_note("crypto", "value"), S.category_note("kr", "cap")), ("", ""))
        coin = R.record_from_bars(R.CRYPTO[0], [("2026-11-09", 1, 1, 1, 1.0, 5.0), ("2026-11-10", 1, 1, 1, 2.0, 6.0)])
        self.assertEqual(S.Screen("crypto", "cap").apply((coin,)), [])
        self.assertEqual(len(S.Screen("crypto", "gainers").apply((coin,))), 1)

    def test_thresholds_read_as_people_say_them(self):
        t = self.S.threshold_text
        self.assertEqual([t(v, "money", "kr", "ko") for v in (1e10, 5e10, 1e11, 5e11, 1e12, 1e13, 1e14)],
                         ["100억", "500억", "1,000억", "5,000억", "1조", "10조", "100조"])
        self.assertEqual([t(v, "money", "kr", "en") for v in (1e11, 1e12)], ["₩100B", "₩1T"])
        self.assertEqual([t(v, "money", "us", "ko") for v in (1e8, 5e8, 1e9, 1e12)], ["$100M", "$500M", "$1B", "$1T"])
        self.assertEqual([t(v, "pct", "kr", "ko") for v in (-3, 0, 2.5)], ["−3%", "0%", "+2.5%"])


if __name__ == "__main__":
    unittest.main()
