"""Single-stock profile core (owner request 2026-11-04): offline, with fake providers only.

Every provider is a fake: the chart router runs the real ChartRouter over a fake KIS service and a fake Yahoo
fetch, the KIS quote and markets clients are fakes (or the real parsers over a fake `_get`), and any HTTP
attempt fails the test. Numbers are checked against independent hand computations on a synthetic series.
"""
from __future__ import annotations

import ast
from datetime import date, datetime, timedelta, timezone
import math
from pathlib import Path
import re
import statistics
import unittest
from unittest.mock import Mock, patch

import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    import config
    from data.krx.kis_client import KISClient, KISError, Quote

from core.market.models import Candle, ChartRequest, Instrument, MarketQuote, MarketSnapshot
from core.market.routing import ChartRouter, KISChartProvider, YahooChartProvider
from core.research import stock_profile as sp
from core.research.qscore import compute_q_score
from core.research.stock_profile import (ProfileRow, ProfileSection, SECTION_KEYS, StockProfile, build_profile,
                                         display_name, headline, load_profile, sections)

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 11, 4)
NOW = datetime(2026, 11, 4, 1, 0, tzinfo=timezone.utc)
SAMSUNG = Instrument("domestic_stock", "005930")
APPLE = Instrument("overseas_stock", "AAPL", "NAS")
HANGUL = re.compile("[ᄀ-ᇿ㄰-㆏ꥠ-꥿가-힯ힰ-퟿]")
SECRET = "appkey=SECRET-VALUE https://openapi.example/uapi"


def session_days(n, end=TODAY):
    days, day = [], end
    while len(days) < n:
        if day.weekday() < 5:
            days.append(day)
        day -= timedelta(days=1)
    return days[::-1]


def closes(n, base=50000.0, digits=0):
    """A deterministic wave with drift; integer KRW prices by default."""
    return [round(base * (1 + 0.25 * math.sin(i / 13.0)) * (1 + 0.0007 * i), digits) for i in range(n)]


def bars(n, *, end=TODAY, base=50000.0, digits=0):
    return tuple(Candle(day.isoformat(), c * 0.995, c * 1.01, c * 0.985, c, 1_000_000 + 10 * i)
                 for i, (day, c) in enumerate(zip(session_days(n, end), closes(n, base, digits))))


class FakeService:
    """The KIS MarketDataService surface the chart router uses."""

    def __init__(self, n=260, *, ready=True, error=None, end=TODAY, base=50000.0, digits=0):
        self.ready, self.error, self.calls = ready, error, []
        self.n, self.end, self.base, self.digits = n, end, base, digits

    def load(self, request):
        self.calls.append(request)
        if self.error:
            raise self.error
        candles = bars(self.n, end=self.end, base=self.base, digits=self.digits)
        quote = MarketQuote(request.instrument, price=candles[-1].close, change=500.0, change_pct=1.0,
                            volume=4321.0, open=candles[-1].open, high=candles[-1].high, low=candles[-1].low,
                            currency="KRW" if request.instrument.asset == "domestic_stock" else "USD",
                            received_at=NOW.isoformat(), source="KIS REST")
        return MarketSnapshot(request, candles, quote, NOW.isoformat(), "KIS REST", "fixture note")


class FakeYahoo:
    def __init__(self, n=260, rows=None):
        self.n, self.rows, self.calls = n, rows, []

    def __call__(self, symbol, interval, period):
        self.calls.append((symbol, interval, period))
        if self.rows is not None:
            return self.rows
        return [(day.isoformat(), c, c * 1.01, c * 0.99, c, 5000.0)
                for day, c in zip(session_days(self.n), closes(self.n, 180.0, 2))]


def router(service=None, yahoo=None):
    return ChartRouter(KISChartProvider(service or FakeService()), (YahooChartProvider(fetch=yahoo or FakeYahoo()),))


class FakeQuoteClient:
    def __init__(self, *, ready=True, error=None, ticker=None):
        self.ready, self.error, self.ticker, self.calls = ready, error, ticker, []

    def quote(self, code):
        self.calls.append(code)
        if self.error:
            raise self.error
        return Quote(self.ticker or code, "삼성전자", 61000.0, 1000.0, 1.67, 12_345_678.0, 3_600_000.0,
                     61500.0, 60100.0, 60200.0, as_of=NOW.isoformat(), per=12.5, eps=4877.0, sector="전기전자",
                     listed_shares=5_969_782_550)


def flow_rows(n=25):
    return [{"date": day.isoformat(), "close": 61000.0, "volume": 1e6,
             "foreign_net_qty": 1000.0 * (i - 12), "institution_net_qty": -250.0 * (i % 3),
             "individual_net_qty": 500.0 if i % 2 else -300.0, "raw": {}}
            for i, day in enumerate(session_days(n))]


def short_rows(n=25):
    return [{"date": day.isoformat(), "close": 61000.0, "volume": 1e6, "short_qty": 1000.0 + 10 * i,
             "short_ratio_pct": 1.0 + i / 50, "short_cum_qty": 1e7}
            for i, day in enumerate(session_days(n))]


class FakeMarkets:
    """KISMarkets' two flow methods, with its keyword-only `days`."""

    def __init__(self, *, ready=True, flows_error=None, shorts_error=None, flows=None, shorts=None):
        self.ready, self.flows_error, self.shorts_error, self.calls = ready, flows_error, shorts_error, []
        self.flows = flow_rows() if flows is None else flows
        self.shorts = short_rows() if shorts is None else shorts

    def investor_daily(self, code, *, days=60):
        self.calls.append(("investor_daily", code, days))
        if self.flows_error:
            raise self.flows_error
        return self.flows

    def short_sale_daily(self, code, *, days=60):
        self.calls.append(("short_sale_daily", code, days))
        if self.shorts_error:
            raise self.shorts_error
        return self.shorts


def signed_pct(fraction):
    """The display rule: a sign except on a value that rounds to zero."""
    text = f"{fraction * 100:+.2f}%"
    return "0.00%" if text in ("+0.00%", "-0.00%") else text


def texts(profile, lang):
    out = []
    for section in sections(profile, lang):
        out += [section.title, section.note]
        for row in section.rows:
            out += [row.label, row.value, row.hint]
    row = headline(profile, lang)
    return out + [row.label, row.value, row.hint, display_name(profile, lang)]


def by_key(profile, lang):
    return {section.key: section for section in sections(profile, lang)}


def row(section, label):
    found = [r for r in section.rows if r.label == label]
    if len(found) != 1:
        raise AssertionError(f"{label!r} not found once in {[r.label for r in section.rows]}")
    return found[0]


class Base(unittest.TestCase):
    def setUp(self):
        for target in ("requests.sessions.Session.request", "core.market.routing._yahoo_frame",
                       "core.quant.history.load_history", "core.quant.history.synthetic_history"):
            blocker = patch(target, side_effect=AssertionError(f"{target} must not run"))
            blocker.start()
            self.addCleanup(blocker.stop)

    def full(self, **overrides):
        args = dict(router=router(), quote_client=FakeQuoteClient(), markets=FakeMarkets(), today=TODAY)
        args.update(overrides)
        return load_profile(SAMSUNG, **args)


class DomesticProfileTests(Base):
    def test_full_domestic_profile_uses_each_source_once_and_fills_every_section(self):
        service, quotes, markets = FakeService(), FakeQuoteClient(), FakeMarkets()
        profile = self.full(router=router(service), quote_client=quotes, markets=markets)
        self.assertIsInstance(profile, StockProfile)
        self.assertEqual(service.calls, [ChartRequest(SAMSUNG, "1d", 260, adjusted=True)])
        self.assertEqual(quotes.calls, ["005930"])
        self.assertEqual(markets.calls, [("investor_daily", "005930", 20), ("short_sale_daily", "005930", 20)])
        self.assertEqual((profile.name, profile.name_en), ("삼성전자", "Samsung Electronics"))
        self.assertEqual((profile.last_price, profile.change, profile.change_pct, profile.price_basis),
                         (61000.0, 1000.0, 1.67, "quote"))
        self.assertTrue(profile.adjusted and profile.live_eligible and not profile.stale)
        self.assertEqual(len(profile.candles), 260)
        self.assertEqual(profile.sources, {"history": "KIS REST", "quote": "KIS", "flows": "KIS",
                                           "short_selling": "KIS"})
        self.assertTrue(all(profile.fetched[k] for k in ("history", "quote", "flows", "short_selling")))
        for lang in ("ko", "en"):
            got = sections(profile, lang)
            self.assertEqual([s.key for s in got], list(SECTION_KEYS))
            self.assertTrue(all(isinstance(s, ProfileSection) and s.rows for s in got))
            self.assertTrue(all(isinstance(r, ProfileRow) for s in got for r in s.rows))
            self.assertTrue(all(r.tone in (None, "up", "down", "flat") for s in got for r in s.rows))
        # The same adjusted KIS bars can feed Q-SCORE without a second load.
        self.assertEqual(compute_q_score(profile.daily_snapshot(), now=NOW)["status"], "ready")

    def test_key_figures_keep_the_computed_market_cap_and_the_fundamentals_caveat(self):
        profile = self.full()
        cap = 61000.0 * 5_969_782_550
        self.assertEqual(profile.values["key_figures"]["market_cap"], cap)
        self.assertEqual(profile.values["key_figures"]["market_cap_basis"], "price_x_listed_shares")
        ko, en = by_key(profile, "ko")["key_figures"], by_key(profile, "en")["key_figures"]
        self.assertEqual([r.label for r in en.rows], ["Open", "High", "Low", "Volume", "Market cap (computed)",
                                                       "PER", "EPS", "Sector", "Listed shares"])
        self.assertEqual(row(en, "Open").value, "60,200 KRW")
        self.assertEqual(row(en, "Volume").value, "12,345,678 shares")
        self.assertEqual(row(ko, "거래량").value, "12,345,678주")
        self.assertEqual(row(en, "Market cap (computed)").value, "364.16T KRW")
        self.assertIn(f"{cap:,.0f} KRW", row(en, "Market cap (computed)").hint)
        self.assertIn("price × listed shares", row(en, "Market cap (computed)").hint)
        self.assertEqual((row(en, "PER").value, row(en, "EPS").value), ("12.50", "4,877"))
        self.assertIn("Accounting basis and reference date are unconfirmed", row(en, "PER").hint)
        self.assertIn("회계 기준과 기준일은 확인되지 않았습니다", row(ko, "EPS").hint)
        self.assertEqual((row(ko, "업종").value, row(en, "Sector").value), ("전기전자", "Electronics"))
        self.assertEqual(row(en, "Listed shares").value, "5,969,782,550 shares")
        self.assertIn("KIS", row(en, "Open").hint)

    def test_real_kis_parsers_are_called_with_allowlisted_paths_and_keyword_days(self):
        from data.kis_markets import KISMarkets
        paths = []
        days = session_days(20)

        def fake_get(path, tr_id, params, **_):
            paths.append(path)
            self.assertIn(path, config.KIS_QUOTATION_ALLOWLIST)
            if path.endswith("inquire-price"):
                return {"output": {"hts_kor_isnm": "삼성전자", "stck_prpr": "61000", "prdy_vrss": "1000",
                                   "prdy_ctrt": "1.67", "acml_vol": "12345678", "stck_oprc": "60200",
                                   "stck_hgpr": "61500", "stck_lwpr": "60100", "per": "12.50", "eps": "4877.00",
                                   "bstp_kor_isnm": "전기전자", "lstn_stcn": "5,969,782,550"}}
            if path.endswith("investor-trade-by-stock-daily"):
                return {"output2": [{"stck_bsop_date": d.strftime("%Y%m%d"), "stck_clpr": "61000",
                                     "acml_vol": "1000", "frgn_ntby_qty": "100", "prsn_ntby_qty": "-40",
                                     "orgn_ntby_qty": "-60", "frgn_reg_ntby_qty": "100"} for d in days]}
            if path.endswith("daily-short-sale"):
                return {"output2": [{"stck_bsop_date": d.strftime("%Y%m%d"), "stck_clpr": "61000",
                                     "acml_vol": "1000", "ssts_cntg_qty": "30", "ssts_vol_rlim": "3.00",
                                     "acml_ssts_cntg_qty": "999"} for d in days]}
            raise AssertionError(path)

        client = KISClient.__new__(KISClient)
        client.ready = True
        client._get = fake_get
        with patch("data.krx.kis_client._now", return_value=NOW.isoformat()):
            profile = self.full(quote_client=client, markets=KISMarkets(client=client))
        self.assertEqual(paths, ["/uapi/domestic-stock/v1/quotations/inquire-price",
                                 "/uapi/domestic-stock/v1/quotations/investor-trade-by-stock-daily",
                                 "/uapi/domestic-stock/v1/quotations/daily-short-sale"])
        flows = profile.values["flows"]["windows"]
        self.assertEqual((flows[5]["foreign"], flows[20]["individual"], flows[20]["institution"]),
                         (500.0, -800.0, -1200.0))
        self.assertEqual(profile.values["short_selling"]["average"]["short_ratio_pct"], 3.0)
        self.assertEqual(profile.values["key_figures"]["listed_shares"], 5_969_782_550)

    def test_flow_and_short_sale_numbers_match_hand_sums(self):
        flows, shorts = flow_rows(25), short_rows(25)
        profile = self.full(markets=FakeMarkets(flows=flows, shorts=shorts))
        for length in (5, 20):
            window = flows[-length:]
            for investor in ("foreign", "institution", "individual"):
                expected = sum(r[investor + "_net_qty"] for r in window)
                self.assertEqual(profile.values["flows"]["windows"][length][investor], expected)
        en = by_key(profile, "en")["flows"]
        foreign5 = sum(r["foreign_net_qty"] for r in flows[-5:])
        self.assertEqual(row(en, "Foreign · last 5 sessions").value, f"{foreign5:+,.0f} shares")
        self.assertEqual(row(en, "Foreign · last 5 sessions").tone, "up" if foreign5 > 0 else "down")
        self.assertEqual([r.label for r in en.rows][:3],
                         ["Foreign · last 5 sessions", "Institutions · last 5 sessions", "Individuals · last 5 sessions"])
        short = by_key(profile, "en")["short_selling"]
        last20 = shorts[-20:]
        self.assertEqual(row(short, "Latest short-sale share").value, f"{shorts[-1]['short_ratio_pct']:.2f}%")
        self.assertEqual(row(short, "20-session average short-sale share").value,
                         f"{statistics.fmean(r['short_ratio_pct'] for r in last20):.2f}%")
        self.assertEqual(row(short, "20-session average short-sale volume").value,
                         f"{statistics.fmean(r['short_qty'] for r in last20):,.0f} shares")
        self.assertEqual(row(by_key(profile, "ko")["short_selling"], "최근 공매도 수량").value,
                         f"{shorts[-1]['short_qty']:,.0f}주")

    def test_short_flow_history_uses_the_sessions_it_has_and_says_what_was_reported(self):
        flows = flow_rows(12)
        flows[-1]["foreign_net_qty"] = None
        profile = self.full(markets=FakeMarkets(flows=flows, shorts=short_rows(3)))
        self.assertEqual(sorted(profile.values["flows"]["windows"]), [5, 12])
        en = by_key(profile, "en")
        self.assertIn("Reported on 4 of 5 sessions", row(en["flows"], "Foreign · last 5 sessions").hint)
        self.assertIn("Individuals · last 12 sessions", [r.label for r in en["flows"].rows])
        self.assertIn("3-session average short-sale share", [r.label for r in en["short_selling"].rows])

    def test_short_sale_averages_say_how_many_sessions_reported(self):
        shorts = short_rows(25)
        for item in shorts[-20:][:15]:
            item["short_ratio_pct"] = None
        profile = self.full(markets=FakeMarkets(shorts=shorts))
        average = profile.values["short_selling"]["average"]
        self.assertEqual((average["sessions"], average["reported_ratio"], average["reported_qty"]), (20, 5, 20))
        en, ko = by_key(profile, "en")["short_selling"], by_key(profile, "ko")["short_selling"]
        share = row(en, "20-session average short-sale share")
        self.assertEqual(share.value, f"{statistics.fmean(r['short_ratio_pct'] for r in shorts[-5:]):.2f}%")
        self.assertTrue(share.hint.endswith("\nReported on 5 of 20 sessions"), share.hint)
        self.assertIn("20거래일 중 5일만 보고됨", row(ko, "20거래일 평균 공매도 비중").hint)
        # The volume average used every session, so its hint carries no such line.
        self.assertNotIn("Reported on", row(en, "20-session average short-sale volume").hint)
        self.assertNotIn("Reported on", row(by_key(self.full(), "en")["short_selling"],
                                            "20-session average short-sale share").hint)

    def test_dated_flow_rows_without_any_investor_value_read_as_no_data(self):
        flows = flow_rows(25)
        for item in flows:
            item.update(foreign_net_qty=None, institution_net_qty=None, individual_net_qty=None)
        profile = self.full(markets=FakeMarkets(flows=flows))
        self.assertNotIn("flows", profile.values)
        self.assertEqual(profile.reasons["flows"], "no_observations")
        en, ko = by_key(profile, "en"), by_key(profile, "ko")
        self.assertNotIn("flows", en)
        self.assertEqual(row(en["unavailable"], "Investor net buying").value, "No data")
        self.assertEqual(row(ko["unavailable"], sp._TITLES["flows"][0]).value, "자료 없음")
        self.assertIn("short_selling", en)
        # One investor reported on one session is still a flow section, with the gap stated.
        flows[-1]["institution_net_qty"] = -700.0
        partial = by_key(self.full(markets=FakeMarkets(flows=flows)), "en")["flows"]
        self.assertEqual([r.label for r in partial.rows],
                         ["Institutions · last 5 sessions", "Institutions · last 20 sessions"])
        self.assertIn("Reported on 1 of 20 sessions", row(partial, "Institutions · last 20 sessions").hint)


class OverseasProfileTests(Base):
    def test_overseas_profile_has_no_fundamentals_flows_or_short_selling_and_never_asks_kis_for_them(self):
        quotes = Mock(side_effect=AssertionError("no domestic quote for overseas"))
        markets = Mock(side_effect=AssertionError("no domestic flows for overseas"))
        service = FakeService(base=180.0, digits=2)
        profile = load_profile(APPLE, router=router(service), quote_client=quotes, markets=markets, today=TODAY)
        self.assertEqual(quotes.mock_calls, [])
        self.assertEqual(markets.mock_calls, [])
        self.assertEqual(service.calls, [ChartRequest(APPLE, "1d", 260, adjusted=True)])
        self.assertEqual((profile.name, profile.name_en, profile.currency), ("애플", "Apple", "USD"))
        self.assertEqual({k: profile.reasons[k] for k in ("flows", "short_selling", "fundamentals")},
                         dict.fromkeys(("flows", "short_selling", "fundamentals"), "domestic_only"))
        en = by_key(profile, "en")
        self.assertNotIn("flows", en)
        self.assertNotIn("short_selling", en)
        self.assertEqual([r.label for r in en["key_figures"].rows], ["Open", "High", "Low", "Volume"])
        self.assertTrue(row(en["key_figures"], "Open").value.endswith(" USD"))
        self.assertRegex(row(en["key_figures"], "Open").value, r"^\d{1,3}(,\d{3})*\.\d{2} USD$")
        missing = {r.label: r.value for r in en["unavailable"].rows}
        self.assertEqual(missing["Overseas fundamentals"], "Not provided")
        self.assertEqual(missing["Investor net buying"], "Provided for Korean stocks only")
        self.assertEqual(missing["Short selling"], "Provided for Korean stocks only")
        self.assertEqual(by_key(profile, "ko")["unavailable"].rows[0].value, "국내 주식에만 제공됩니다")
        self.assertEqual(headline(profile, "en").label, "Apple · NAS:AAPL")
        self.assertEqual(display_name(profile, "ko"), "애플")


class HistoryLengthTests(Base):
    def test_fewer_than_21_sessions_keep_only_what_the_history_supports(self):
        profile = self.full(router=router(FakeService(15)))
        en = by_key(profile, "en")
        self.assertEqual([r.label for r in en["returns"].rows], ["1W"])
        self.assertNotIn("range", en)
        self.assertNotIn("risk", en)
        self.assertNotIn("signals", en)
        self.assertEqual([r.label for r in en["indicators"].rows], ["EMA 12", "RSI 14"])
        missing = {r.label: r.value for r in en["unavailable"].rows}
        self.assertEqual(missing["52-week range"], "15 sessions · needs at least 200")
        self.assertEqual(missing["Risk"], "15 sessions · needs at least 21")
        self.assertEqual(missing["Technical signals"], "15 sessions · needs at least 34")
        ko = {r.label: r.value for r in by_key(profile, "ko")["unavailable"].rows}
        self.assertEqual(ko["위험 지표"], "15거래일 자료 · 21거래일 이상 필요")

    def test_signals_wait_until_the_indicators_show_macd_and_its_signal_line(self):
        macd_labels = ["MACD (12/26)", "MACD signal (9)"]
        for count in (21, 25, 33):
            en = by_key(self.full(router=router(FakeService(count))), "en")
            self.assertIn("risk", en)
            self.assertNotIn("signals", en)
            shown = [r.label for r in en["indicators"].rows]
            self.assertFalse(set(macd_labels) <= set(shown), (count, shown))
            self.assertEqual(row(en["unavailable"], "Technical signals").value,
                             f"{count} sessions · needs at least 34")
        en = by_key(self.full(router=router(FakeService(34))), "en")
        shown = [r.label for r in en["indicators"].rows]
        self.assertTrue(set(macd_labels) <= set(shown), shown)
        self.assertIn("MACD (12/26/9)", [r.label for r in en["signals"].rows])
        self.assertNotIn("Technical signals", [r.label for r in en["unavailable"].rows])

    def test_fewer_than_200_sessions_drop_the_range_and_the_returns_they_cannot_reach(self):
        profile = self.full(router=router(FakeService(120)))
        en = by_key(profile, "en")
        self.assertNotIn("range", en)
        self.assertEqual([r.label for r in en["returns"].rows], ["1W", "1M", "3M"])
        self.assertIn("risk", en)
        self.assertIn("signals", en)
        self.assertEqual(len(row(en["signals"], "Composite score").hint.split("\n")[0].split("·")), 2)
        self.assertEqual({r.label: r.value for r in en["unavailable"].rows}["52-week range"],
                         "120 sessions · needs at least 200")

    def test_a_range_under_52_weeks_says_so(self):
        profile = self.full(router=router(FakeService(230)))
        note = by_key(profile, "en")["range"].note
        self.assertIn("range uses 230 sessions (under 52 weeks)", note)
        self.assertIn("수정주가 일별 종가", by_key(profile, "ko")["range"].note)

    def test_fewer_than_six_sessions_leave_no_returns(self):
        profile = self.full(router=router(FakeService(3)))
        missing = {r.label: r.value for r in by_key(profile, "en")["unavailable"].rows}
        self.assertEqual(missing["Returns"], "3 sessions · needs at least 6")
        self.assertEqual(missing["Indicators"], "3 sessions · needs at least 12")


class SourceFailureTests(Base):
    def assert_no_secret(self, profile):
        for lang in ("ko", "en"):
            blob = "\n".join(texts(profile, lang))
            self.assertNotIn("SECRET", blob)
            self.assertNotIn("https://", blob)

    def test_history_failure_empties_only_the_history_sections(self):
        failing = router(FakeService(error=RuntimeError(SECRET)), FakeYahoo(rows=[]))
        profile = self.full(router=failing)
        self.assertEqual(profile.candles, ())
        en = by_key(profile, "en")
        self.assertEqual(set(en), {"key_figures", "flows", "short_selling", "unavailable"})
        missing = {r.label: r for r in en["unavailable"].rows}
        for title in ("52-week range", "Returns", "Risk", "Technical signals", "Indicators"):
            self.assertEqual(missing[title].value, "Request failed")
            self.assertIn("ProvidersUnavailable", missing[title].hint)
            self.assertIn("KIS failed (RuntimeError)", missing[title].hint)
        self.assertEqual(profile.errors["range"], "ProvidersUnavailable")
        self.assertIn("PER", [r.label for r in en["key_figures"].rows])
        self.assertEqual(headline(profile, "en").value, "61,000 KRW  +1,000 (+1.67%)")
        self.assert_no_secret(profile)

    def test_quote_failure_keeps_the_chart_quote_and_names_the_missing_fundamentals(self):
        profile = self.full(quote_client=FakeQuoteClient(error=KISError(SECRET)))
        en = by_key(profile, "en")
        self.assertEqual([r.label for r in en["key_figures"].rows], ["Open", "High", "Low", "Volume"])
        self.assertEqual(profile.sources["quote"], "KIS REST")
        fundamentals = row(en["unavailable"], "Fundamentals (PER, EPS, sector, listed shares, market cap)")
        self.assertEqual(fundamentals.value, "Request failed")
        self.assertIn("KISError", fundamentals.hint)
        self.assertEqual(profile.name, "삼성전자")  # the bundled name, since the quote carried none
        for key in ("range", "returns", "risk", "signals", "indicators", "flows", "short_selling"):
            self.assertIn(key, en)
        self.assert_no_secret(profile)

    def test_flow_failure_and_short_sale_failure_are_independent(self):
        for broken, kept in (("flows", "short_selling"), ("short_selling", "flows")):
            markets = FakeMarkets(**{("flows_error" if broken == "flows" else "shorts_error"): KISError(SECRET)})
            profile = self.full(markets=markets)
            en = by_key(profile, "en")
            self.assertNotIn(broken, en)
            self.assertIn(kept, en)
            self.assertEqual(profile.errors[broken], "KISError")
            title = sp._TITLES[broken][1]
            self.assertEqual(row(en["unavailable"], title).value, "Request failed")
            self.assert_no_secret(profile)

    def test_missing_or_unready_clients_read_as_not_configured(self):
        for kwargs in (dict(quote_client=None, markets=None),
                       dict(quote_client=FakeQuoteClient(ready=False), markets=FakeMarkets(ready=False))):
            profile = self.full(**kwargs)
            self.assertEqual({k: profile.reasons[k] for k in ("fundamentals", "flows", "short_selling")},
                             dict.fromkeys(("fundamentals", "flows", "short_selling"), "connection_not_configured"))
            missing = {r.label: r.value for r in by_key(profile, "en")["unavailable"].rows}
            self.assertEqual(missing["Investor net buying"], "KIS connection not configured")
            self.assertEqual(missing["Fundamentals (PER, EPS, sector, listed shares, market cap)"],
                             "KIS connection not configured")
        unready = FakeQuoteClient(ready=False)
        self.full(quote_client=unready)
        self.assertEqual(unready.calls, [])

    def test_a_quote_for_another_code_is_rejected(self):
        profile = self.full(quote_client=FakeQuoteClient(ticker="000660"))
        self.assertEqual(profile.reasons["fundamentals"], "invalid_response")
        self.assertEqual(profile.sources["quote"], "KIS REST")

    def test_nothing_at_all_still_answers_with_plain_reasons(self):
        profile = load_profile(SAMSUNG, router=None, today=TODAY)
        en = by_key(profile, "en")
        self.assertEqual(list(en), ["unavailable"])
        missing = {r.label: r.value for r in en["unavailable"].rows}
        self.assertEqual(missing["Key figures"], "KIS connection not configured")
        self.assertEqual(missing["News"], "Not provided")
        self.assertEqual(headline(profile, "en"), ProfileRow("Samsung Electronics · 005930", "—", None,
                                                             "KIS connection not configured"))
        self.assertIsNone(profile.daily_snapshot())

    def test_a_router_that_answers_for_another_instrument_is_refused(self):
        class Wrong:
            last_attempts = ()

            def load(self, request):
                return FakeService().load(ChartRequest(Instrument("domestic_stock", "000660"), "1d", 260, True))

        profile = self.full(router=Wrong())
        self.assertEqual(profile.reasons["range"], "invalid_response")
        self.assertEqual(profile.candles, ())

    def test_non_stock_instruments_are_a_programming_error(self):
        future = Instrument("domestic_future", "101W12")
        with self.assertRaises(ValueError):
            build_profile(future, candles=())
        with self.assertRaises(ValueError):
            load_profile(future, router=router())
        with self.assertRaises(TypeError):
            build_profile("005930", candles=())


class YahooProfileTests(Base):
    def test_a_yahoo_snapshot_is_named_unadjusted_and_never_live(self):
        yahoo = FakeYahoo()
        profile = self.full(router=router(FakeService(ready=False), yahoo), quote_client=FakeQuoteClient(ready=False))
        self.assertEqual(yahoo.calls, [("005930.KS", "1d", "2y")])
        self.assertEqual(profile.sources["history"], "Yahoo Finance")
        self.assertFalse(profile.adjusted)
        self.assertFalse(profile.live_eligible)
        self.assertEqual(profile.price_basis, "quote")
        snapshot = profile.daily_snapshot()
        self.assertFalse(snapshot.request.adjusted)
        self.assertEqual(compute_q_score(snapshot, now=NOW)["status"], "unavailable")
        for lang, words in (("en", "Yahoo Finance daily closes (unadjusted, delayed)"),
                            ("ko", "Yahoo Finance 일별 종가 (수정 전·지연)")):
            got = by_key(profile, lang)
            for key in ("range", "returns", "risk", "indicators"):
                self.assertIn(words, got[key].note)
            for key in ("key_figures", "range", "returns", "risk", "signals", "indicators"):
                for item in got[key].rows:
                    self.assertIn("Yahoo Finance", item.hint, (key, item.label))
            self.assertNotIn("수정주가", got["range"].note)
        en = by_key(profile, "en")
        live = row(en["unavailable"], "Live trades")
        self.assertEqual(live.value, "KIS data only")
        self.assertIn("KIS not configured (KIS_APP_KEY, KIS_APP_SECRET)", live.hint)
        self.assertIn("Yahoo Finance · delayed, unadjusted daily bar", headline(profile, "en").hint)
        self.assertNotIn("Live trades", [r.label for r in by_key(self.full(), "en")["unavailable"].rows])

    def test_a_yahoo_source_is_never_called_adjusted_even_if_the_caller_says_so(self):
        profile = build_profile(SAMSUNG, candles=bars(30), source="Yahoo Finance", adjusted=True, today=TODAY)
        self.assertFalse(profile.adjusted)


class LanguageAndLabelTests(Base):
    def profiles(self):
        return [self.full(), load_profile(APPLE, router=router(FakeService(base=180.0, digits=2)), today=TODAY),
                self.full(router=router(FakeService(ready=False))),
                self.full(router=router(FakeService(15))),
                self.full(router=router(FakeService(error=KISError(SECRET)), FakeYahoo(rows=[])),
                          quote_client=FakeQuoteClient(error=KISError(SECRET)),
                          markets=FakeMarkets(flows_error=RuntimeError(), shorts_error=ValueError())),
                load_profile(SAMSUNG, router=None, today=TODAY),
                load_profile(Instrument("domestic_stock", "123456"), router=router(), quote_client=FakeQuoteClient(),
                             today=TODAY)]

    def test_english_output_contains_no_hangul(self):
        for profile in self.profiles():
            for text in texts(profile, "en"):
                self.assertIsNone(HANGUL.search(text), text)
            self.assertTrue(any(HANGUL.search(t) for t in texts(profile, "ko")))
        unknown = self.profiles()[-1]
        self.assertEqual(display_name(unknown, "en"), "123456")
        self.assertEqual(display_name(unknown, "ko"), "삼성전자")  # the fake quote's name

    def test_no_row_is_a_provider_or_observation_date_column(self):
        banned = ("provider", "공급자", "observation date", "관측일")
        for profile in self.profiles():
            for lang in ("ko", "en"):
                for section in sections(profile, lang):
                    for item in section.rows:
                        self.assertFalse(any(word in item.label.lower() for word in banned), item.label)

    def test_signal_wording_and_korean_labels_match_the_existing_catalogue(self):
        from quantgen_desktop.model_narrative_language import SIGNAL_STANCES
        from quantgen_desktop.translations import translate
        self.assertEqual(set(sp._STANCES_KO), set(SIGNAL_STANCES))
        for english, korean in list(sp._STANCES_KO.items()) + list(sp._COMPONENTS_KO.items()):
            self.assertEqual(translate(english, "ko"), korean)
        self.assertEqual(translate(sp.SIGNALS_CONTEXT[1], "ko"), sp.SIGNALS_CONTEXT[0])
        self.assertIn(repr(sp.SIGNALS_CONTEXT[1]), (ROOT / "quantgen_desktop/signals.py").read_text(encoding="utf-8"))
        tree = ast.parse((ROOT / "quantgen_desktop/watchlist.py").read_text(encoding="utf-8"))
        sectors = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                       and getattr(node.targets[0], "id", "") == "_SECTORS_EN")
        self.assertEqual(sp._SECTORS_EN, sectors)
        profile = self.full()
        for lang in ("ko", "en"):
            note = by_key(profile, lang)["signals"].note
            self.assertTrue(note.startswith(sp.SIGNALS_CONTEXT[0 if lang == "ko" else 1]))
        self.assertIn("Not a buy or sell recommendation.", by_key(profile, "en")["signals"].note)
        self.assertEqual(row(by_key(profile, "ko")["signals"], "판단").value,
                         translate(profile.values["signals"]["stance"], "ko"))


class HandComputationTests(Base):
    """Independent arithmetic on the synthetic series, against both raw values and display text."""

    def setUp(self):
        super().setUp()
        self.candles = bars(260)
        self.closes = [c.close for c in self.candles]
        self.days = [c.timestamp for c in self.candles]
        self.profile = build_profile(SAMSUNG, candles=self.candles, today=TODAY, source="KIS REST",
                                     fetched_at=NOW.isoformat())
        self.en = by_key(self.profile, "en")

    def test_returns(self):
        last = self.closes[-1]
        for label, offset in (("1W", 5), ("1M", 21), ("3M", 63), ("6M", 126), ("1Y", 252)):
            expected = last / self.closes[-1 - offset] - 1
            self.assertNotEqual(round(expected * 100, 2), 0)
            self.assertAlmostEqual(self.profile.values["returns"][label]["value"], expected, places=12)
            shown = row(self.en["returns"], label)
            self.assertEqual(shown.value, f"{expected * 100:+.2f}%")
            self.assertEqual(shown.tone, "up" if expected > 0 else "down")
            self.assertIn(f"{self.closes[-1 - offset]:,.0f} KRW", shown.hint)

    def test_range(self):
        window = self.closes[-252:]
        high, low, last = max(window), min(window), self.closes[-1]
        data = self.profile.values["range"]
        self.assertEqual((data["high"], data["low"], data["sessions"]), (high, low, 252))
        self.assertEqual(data["high_date"], self.days[-252:][len(window) - 1 - window[::-1].index(high)])
        self.assertEqual(row(self.en["range"], "52-week high").value, f"{high:,.0f} KRW")
        self.assertEqual(row(self.en["range"], "52-week low").value, f"{low:,.0f} KRW")
        self.assertEqual(row(self.en["range"], "Position in range").value, f"{(last - low) / (high - low) * 100:.2f}%")
        self.assertEqual(row(self.en["range"], "From 52-week high").value, signed_pct(last / high - 1))
        self.assertEqual(row(self.en["range"], "From 52-week low").value, signed_pct(last / low - 1))
        self.assertEqual(self.en["range"].note, "Adjusted daily closes · 260 sessions · today's bar may be provisional")

    def test_risk_against_hand_statistics(self):
        logs = [math.log(b / a) for a, b in zip(self.closes, self.closes[1:])]
        data = self.profile.values["risk"]
        self.assertEqual(data["sessions"], 260)
        self.assertAlmostEqual(data["best_day"], max(logs), places=12)
        self.assertAlmostEqual(data["worst_day"], min(logs), places=12)
        self.assertAlmostEqual(data["positive_days"], sum(1 for r in logs if r > 0) / len(logs), places=12)
        vol = statistics.stdev(logs) * math.sqrt(252)
        self.assertAlmostEqual(data["ann_vol"], vol, places=9 if data["engine"] == "local" else 4)
        peak, drawdown = self.closes[0], 0.0
        for close in self.closes:
            peak = max(peak, close)
            drawdown = min(drawdown, close / peak - 1)
        self.assertAlmostEqual(data["max_drawdown"], drawdown, places=9 if data["engine"] == "local" else 4)
        self.assertEqual(row(self.en["risk"], "Best day").value, f"{max(logs) * 100:+.2f}%")
        self.assertEqual(row(self.en["risk"], "Worst day").tone, "down")
        self.assertEqual(row(self.en["risk"], "Max drawdown").value, f"{data['max_drawdown'] * 100:+.2f}%")

    def test_indicators_and_signals_come_from_the_existing_engines(self):
        from core.market.presentation import indicator_values
        from core.quant.history import History
        from core.quant.signals import compute_signals
        expected = indicator_values(MarketSnapshot(ChartRequest(SAMSUNG, "1d", 260, adjusted=True), self.candles))
        self.assertEqual(row(self.en["indicators"], "SMA 20").value, f"{expected['SMA20']:,.0f} KRW")
        self.assertEqual(row(self.en["indicators"], "RSI 14").value, f"{expected['RSI14']:.1f}")
        self.assertAlmostEqual(statistics.fmean(self.closes[-20:]), expected["SMA20"], places=6)
        report = compute_signals(History("005930", "KIS REST", tuple(self.days), tuple(self.closes), adjustment="split"))
        self.assertEqual(row(self.en["signals"], "Composite score").value, f"{report.composite:+.1f}")
        self.assertEqual(row(self.en["signals"], "Stance").value, report.stance)
        self.assertEqual(len(self.en["signals"].rows), 2 + len(report.components))

    def test_daily_close_price_and_tones_when_no_quote_is_given(self):
        last, previous = self.closes[-1], self.closes[-2]
        self.assertEqual((self.profile.last_price, self.profile.price_basis), (last, "daily_close"))
        self.assertAlmostEqual(self.profile.change_pct, (last / previous - 1) * 100, places=12)
        head = headline(self.profile, "en")
        self.assertEqual(head.value, f"{last:,.0f} KRW  {last - previous:+,.0f} ({(last / previous - 1) * 100:+.2f}%)")
        figures = by_key(self.profile, "en")["key_figures"]
        self.assertIn("Last daily bar", row(figures, "Open").hint)
        flat = build_profile(SAMSUNG, candles=[Candle(c.timestamp, 100, 100, 100, 100) for c in self.candles[-30:]],
                             today=TODAY)
        self.assertEqual({r.tone for r in by_key(flat, "en")["returns"].rows}, {"flat"})
        self.assertEqual(row(by_key(flat, "en")["returns"], "1W").value, "0.00%")
        self.assertEqual(headline(flat, "en").tone, "flat")

    def test_stale_and_future_histories_are_labelled_or_refused(self):
        stale = build_profile(SAMSUNG, candles=bars(260, end=TODAY - timedelta(days=12)), today=TODAY)
        self.assertTrue(stale.stale)
        self.assertIn("stale", by_key(stale, "en")["returns"].note)
        future = build_profile(SAMSUNG, candles=bars(260, end=TODAY + timedelta(days=3)), today=TODAY)
        self.assertEqual(future.candles, ())
        self.assertEqual({r.label: r.value for r in by_key(future, "en")["unavailable"].rows}["Returns"],
                         "Price history is dated after today")


class PurityTests(unittest.TestCase):
    def test_the_module_reads_no_endpoint_no_synthetic_history_and_no_qt(self):
        from tests.acceptance import _code_only
        code = _code_only(ROOT / "core/research/stock_profile.py")
        for token in ("/uapi/", "load_history", "synthetic", "PyQt6", "quantgen_desktop", "requests", "open("):
            self.assertNotIn(token, code)
        self.assertIn("ChartRequest(instrument, '1d', HISTORY_BARS, adjusted=True)", code)
        self.assertEqual(sp.HISTORY_BARS, 260)


if __name__ == "__main__":
    unittest.main()
