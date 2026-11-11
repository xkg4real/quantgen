"""Pure parts of the native stock detail view (owner request 2026-11-11, UI-D8); no Qt, no network.

Owner: "검색해서 한 차트를 구체적으로 볼때에는, 해당 차트로 화면을 거의 가득채워도 가능해" and "pc기준 좌우화살표로 차트
좌우 확인할수있게". Covered: the period chips (request and window), the pan window, the intervals the routers can
deliver, an honest market state, volume against its 30-session average, the four "지금 이 차트" readings, the
exact-size chart renderer (panels fit, cropping, pointer mapping, labels, contrast) and the display text rules.
"""
from __future__ import annotations

import math
import re
import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from core.market.models import Candle, ChartRequest, Instrument, MarketSnapshot

HANGUL = re.compile("[가-힣]")
SAMSUNG = Instrument("domestic_stock", "005930")
APPLE = Instrument("overseas_stock", "AAPL", "NAS")
TENCENT = Instrument("overseas_stock", "00700", "HKS")
BOND = Instrument("bond", "KR103502GC66")


def candles(n, *, start=date(2025, 1, 2), step=1, intraday=False, volume=True):
    out = []
    for i in range(n):
        base = 100 + 10 * math.sin(i / 7) + i * .2
        stamp = ((datetime(2026, 11, 9, 9, 0) + timedelta(minutes=i)).isoformat() if intraday
                 else (start + timedelta(days=i * step)).isoformat())
        out.append(Candle(stamp, base, base + 2, base - 2, base + math.cos(i), 1000 + 10 * i if volume else None))
    return tuple(out)


class PeriodTests(unittest.TestCase):
    def test_period_requests_and_windows(self):
        from core.market.detail_model import PERIOD_KEYS, period_request, visible_for
        # Owner R-D9-2 (2026-11-11) added the yearly interval: 10Y takes the monthly candles, 전체 the yearly ones.
        self.assertEqual(PERIOD_KEYS, ("1D", "5D", "1M", "3M", "6M", "YTD", "1Y", "5Y", "10Y", "ALL"))
        requests = {key: period_request(key, SAMSUNG) for key in PERIOD_KEYS}
        self.assertEqual(requests["1D"], ("1m", 400))
        self.assertEqual(requests["5D"], ("15m", 140))
        for key in ("1M", "3M", "6M", "YTD", "1Y"):
            self.assertEqual(requests[key], ("1d", 400))  # daily periods share one request: no reload between them
        self.assertEqual(requests["5Y"], ("1w", 400))
        self.assertEqual(requests["10Y"], ("1M", 200))
        self.assertEqual(requests["ALL"], ("1Y", 50))
        for key in PERIOD_KEYS:
            self.assertEqual(period_request(key, BOND), ("1d", 100))  # KIS bond history is at most 100 bars
        with self.assertRaises(ValueError):
            period_request("2Y", SAMSUNG)
        daily = candles(400, start=date(2025, 6, 1))
        self.assertEqual([visible_for(k, daily) for k in ("1M", "3M", "6M", "1Y", "5Y")], [22, 63, 126, 252, 261])
        this_year = sum(1 for c in daily if c.timestamp.startswith(daily[-1].timestamp[:4]))
        self.assertEqual(visible_for("YTD", daily), this_year)
        self.assertEqual(visible_for("ALL", daily), 400)
        self.assertEqual(visible_for("1Y", daily[:100]), 100)          # never more than received
        january = candles(30, start=date(2026, 12, 20))                 # YTD on 7 January: still 20 bars
        self.assertEqual(visible_for("YTD", january), 20)
        minutes = candles(400, intraday=True)
        self.assertEqual(visible_for("1D", minutes), sum(1 for c in minutes if c.timestamp[:10] == minutes[-1].timestamp[:10]))

    def test_pan_window(self):
        from core.market.detail_model import window
        self.assertEqual(window(120, 30), (90, 120))
        self.assertEqual(window(120, 30, 29), (0, 30))
        self.assertEqual(window(120, 30, 5), (0, 30))       # the window never starts before the first bar
        self.assertEqual(window(120, 30, 500), (90, 120))
        self.assertEqual(window(10, 30), (0, 10))
        self.assertEqual(window(0, 30), (0, 0))

    def test_routable_intervals_follow_ready_providers(self):
        from core.market.detail_model import period_reason, routable_intervals

        class Provider:
            def __init__(self, ready, supported=None):
                self._ready, self._supported = ready, supported

            def ready(self):
                return self._ready, ()

            def supports(self, request):
                return self._supported is None or request.interval in self._supported

        class Router:
            def __init__(self, primary, fallbacks=()):
                self.primary, self.fallbacks = primary, fallbacks

        kis = ("1m", "3m", "5m", "15m", "30m", "60m", "1d", "1w", "1M")
        yahoo = Provider(True, ("1d", "1w", "1M"))
        # The yearly interval comes with the monthly one (built from it, never requested from a provider).
        self.assertEqual(routable_intervals(Router(Provider(True), (yahoo,)), SAMSUNG, supported=kis), kis + ("1Y",))
        offline = routable_intervals(Router(Provider(False), (yahoo,)), SAMSUNG, supported=kis)
        self.assertEqual(offline, ("1d", "1w", "1M", "1Y"))
        self.assertEqual(routable_intervals(Router(Provider(False)), SAMSUNG, supported=kis), ())
        self.assertEqual(period_reason("1D", SAMSUNG, offline), "needs_kis")
        self.assertEqual(period_reason("6M", SAMSUNG, offline), "")
        self.assertEqual(period_reason("ALL", SAMSUNG, offline), "")
        self.assertEqual(period_reason("5Y", BOND, ("1d",)), "bond_daily")
        self.assertEqual(period_reason("1Y", BOND, ("1d",)), "")


class QuoteStateTests(unittest.TestCase):
    NOW = datetime(2026, 11, 11, 3, 0, tzinfo=timezone.utc)  # 12:00 KST, a Wednesday

    def state(self, instrument, venue=("open", "regular session"), **facts):
        from core.market.detail_model import quote_state
        return quote_state(instrument, now=self.NOW, venue_state=lambda code, moment: venue, **facts)

    def test_every_state_is_honest_and_has_text_in_both_languages(self):
        from quantgen_desktop.owner_ui_language.stock import TEXT
        recent = (self.NOW - timedelta(seconds=3)).isoformat()
        old = (self.NOW - timedelta(seconds=90)).isoformat()
        cases = {
            "live": self.state(SAMSUNG, source="KIS", mode="streaming", has_data=True, last_trade_at=recent),
            "live_quiet": self.state(SAMSUNG, source="KIS", mode="streaming", has_data=True, last_trade_at=old),
            "us_free": self.state(APPLE, source="KIS", mode="streaming", has_data=True, last_trade_at=recent),
            "delayed15": self.state(TENCENT, source="KIS", mode="snapshot", has_data=True),
            "fallback": self.state(SAMSUNG, source="Yahoo Finance", mode="snapshot", has_data=True),
            "polling": self.state(SAMSUNG, source="KIS REST", mode="polling", has_data=True),
            "snapshot": self.state(SAMSUNG, source="KIS REST", mode="snapshot", has_data=True),
            "closed": self.state(SAMSUNG, ("closed", "weekend"), source="KIS", mode="streaming", has_data=True,
                                 last_trade_at=recent),
            "holiday": self.state(SAMSUNG, ("closed", "exchange holiday (2026-11-11)"), source="KIS",
                                  mode="snapshot", has_data=True),
            "stale": self.state(SAMSUNG, source="KIS", mode="stale", has_data=True),
            "error": self.state(SAMSUNG, mode="error"),
            "loading": self.state(SAMSUNG, mode="loading"),
            "idle": self.state(SAMSUNG),
        }
        for code, state in cases.items():
            with self.subTest(code=code):
                self.assertEqual(state.code, code)
                for key in (f"state_{code}", f"state_{code}_long"):
                    en, ko = TEXT[key]
                    self.assertTrue(en and ko)
                    self.assertIsNone(HANGUL.search(en))
        self.assertEqual(cases["live"].age, 3)
        # Never "live" for a fallback, a closed market or a delayed overseas quote.
        for code in ("fallback", "closed", "holiday", "us_free", "delayed15"):
            self.assertNotEqual(cases[code].code, "live")
        self.assertIn("KIS", TEXT["state_fallback_long"][1])
        self.assertIn("지연", TEXT["state_us_free_long"][1])

    def test_closed_market_from_the_calendar(self):
        from core.market.detail_model import quote_state
        saturday = datetime(2026, 11, 14, 3, 0, tzinfo=timezone.utc)
        state = quote_state(SAMSUNG, source="KIS", mode="snapshot", has_data=True, now=saturday)
        self.assertEqual(state.code, "closed")


class VolumeAndSummaryTests(unittest.TestCase):
    def test_volume_against_the_sessions_before_today(self):
        from core.market.detail_model import volume_vs_average
        bars = tuple(Candle((date(2026, 9, 1) + timedelta(days=i)).isoformat(), 1, 1, 1, 1, 100.0) for i in range(40))
        today = bars[-1].timestamp
        bars = bars[:-1] + (Candle(today, 1, 1, 1, 1, 300.0),)
        ratio = volume_vs_average(bars)
        self.assertEqual((ratio.volume, ratio.average, ratio.sessions), (300.0, 100.0, 30))
        self.assertAlmostEqual(ratio.ratio, 3.0)  # today's own bar never enters its average
        self.assertAlmostEqual(volume_vs_average(bars, 150.0).ratio, 1.5)
        short = volume_vs_average(bars[-6:])
        self.assertIsNone(short.ratio)
        self.assertEqual(short.sessions, 5)
        self.assertIsNone(volume_vs_average(()).ratio)

    def test_now_summary_has_four_plain_rows(self):
        from core.education.indicators import bars_from_candles
        from core.market.detail_model import now_summary, volume_vs_average
        data = candles(200)
        bars = bars_from_candles(data)
        rows = now_summary(bars, volume=volume_vs_average(data))
        self.assertEqual([row.topic for row in rows], ["trend", "strength", "movement", "trading"])
        self.assertIn(rows[0].code, ("above_both", "below_both", "mixed_up", "mixed_down"))
        self.assertIn(rows[1].code, STRENGTH_CODES[:-1])
        self.assertIn(rows[2].code, ("small", "usual", "large"))
        self.assertIn(rows[3].code, ("low", "usual", "high"))
        self.assertEqual([row.study for row in rows], ["sma", "rsi", "atr", "volume_ma"])
        few = bars_from_candles(data[:8])
        codes = [row.code for row in now_summary(few, volume=None)]
        self.assertEqual(codes, ["wait", "wait", "wait", "none"])

    def test_summary_text_covers_every_code_in_both_languages(self):
        from quantgen_desktop.owner_ui_language.stock import TEXT
        codes = {"trend": ("above_both", "below_both", "mixed_up", "mixed_down", "short", "wait"),
                 "strength": STRENGTH_CODES,
                 "movement": ("small", "usual", "large", "wait"),
                 "trading": ("low", "usual", "high", "short", "none")}
        for topic, names in codes.items():
            for code in names:
                en, ko = TEXT[f"now_{topic}_{code}"]
                self.assertEqual(set(re.findall(r"{(\w+)}", en)), set(re.findall(r"{(\w+)}", ko)), code)


    def test_the_now_card_and_the_rsi_panel_say_the_same_of_one_number(self):
        """Integrator 2026-11-11: at RSI 31.1 the panel said '훨씬' and the card '조금'. Both now follow the engine's
        rule: the band by the displayed value, the words by the ratio of rises to falls."""
        from core.education.indicators import bars_from_closes, compute_study
        from core.education.study_guide import study_reading
        from core.market.detail_model import now_summary
        from quantgen_desktop.owner_ui_language.stock import TEXT
        from quantgen_desktop.stock_detail_style import polite
        seen = set()
        for gain in (0.2, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 1.0, 1.3, 1.6, 2.0, 2.4, 3.0, 5.0):
            closes, price = [], 100.0
            for i in range(80):
                price *= 1 + (0.01 * gain if i % 2 == 0 else -0.01)
                closes.append(price)
            n = len(closes)
            bars = bars_from_closes(closes)
            rsi = compute_study("rsi", bars)["RSI14"][-1]
            row = now_summary(bars)[1]
            seen.add(row.code)
            reading = polite(study_reading("rsi", bars, n - 1, language="ko"))
            card = TEXT[f"now_strength_{row.code}"][1]
            self.assertIn(f"RSI {row.values['rsi']:.1f}", reading)
            if row.code in ("high", "low"):
                self.assertIn("훨씬", reading, rsi)
                self.assertIn("훨씬", card)
            elif row.code == "even":
                self.assertIn("비슷했어요", reading, rsi)
            else:
                suffix = row.code.split("_")[1] if "_" in row.code else ""
                size = {"much": "훨씬 컸어요", "more": " 더 컸어요", "": "조금 더 컸어요"}[suffix]
                self.assertIn(size, reading, (rsi, row.code))
                self.assertIn(size.strip(), card, row.code)
                if suffix == "more":
                    self.assertNotIn("조금 더", reading)
                    self.assertNotIn("훨씬", reading)
        self.assertGreaterEqual(len(seen), 5, seen)


STRENGTH_CODES = ("high", "upper_much", "upper_more", "upper", "even", "lower", "lower_more", "lower_much", "low",
                  "wait")


class RendererTests(unittest.TestCase):
    def snapshot(self, n=300, interval="1d", instrument=SAMSUNG):
        data = candles(n, intraday=interval not in ("1d", "1w", "1M"))
        return MarketSnapshot(ChartRequest(instrument, interval, max(20, min(500, n))), data, None, source="KIS")

    def test_panels_fit_any_height_and_never_overlap(self):
        from core.market.detail_svg import AXIS, HEADER, PANEL_SHARE, max_panels, plan_panels, render
        self.assertEqual((max_panels(588), max_panels(788)), (3, 4))  # 1000x700 and 1440x900 charts
        keys = ("macd", "rsi", "stoch", "adx", "obv")
        for height in (588, 788):
            for n in range(6):
                with self.subTest(height=height, panels=n):
                    sizes, hidden = plan_panels(height, keys[:n])
                    self.assertEqual(len(sizes) + len(hidden), n)
                    self.assertLessEqual(sum(h for _, h in sizes), PANEL_SHARE * (height - HEADER - AXIS))
                    svg, layout = render(self.snapshot(), studies=("sma",) + keys[:n], width=900, height=height)
                    self.assertEqual((layout.width, layout.height), (900, height))
                    edges = [layout.price] + [(top, bottom) for _, top, bottom in layout.panels]
                    for (_, a_bottom), (b_top, _) in zip(edges, edges[1:]):
                        self.assertLessEqual(a_bottom, b_top)
                    self.assertLessEqual(edges[-1][1], layout.axis_top)
                    self.assertEqual(tuple(hidden), layout.hidden_panels)
                    self.assertIn(f'height="{height}"', svg[:200])

    def test_end_and_visible_crop_and_pointer_maps_bars(self):
        from core.market.detail_svg import render
        snapshot = self.snapshot(300)
        svg, layout = render(snapshot, end=199, visible=50, width=1000, height=700, cursor=180)
        self.assertEqual((layout.start, layout.stop, layout.cursor), (150, 200, 180))
        self.assertEqual(layout.index_at(layout.plot_left + 0.1), 150)
        self.assertEqual(layout.index_at(layout.plot_right - 0.1), 199)
        self.assertEqual(layout.index_at(layout.x_of(175)), 175)
        self.assertEqual(layout.index_at(-50), 150)
        self.assertIn(snapshot.candles[180].timestamp[:10], svg)  # the selected bar's date tag

    def test_labels_last_price_tag_text_size_and_languages(self):
        from core.market.detail_svg import EN_MONTHS, price_text, render
        from quantgen_desktop.owner_ui_language.stock import TEXT
        snapshot = self.snapshot(300)
        svg, _ = render(snapshot, studies=("sma", "rsi"), width=1100, height=760)
        self.assertIn(price_text(snapshot.candles[-1].close), svg)        # filled last-price tag
        self.assertTrue(any(f">{m}<" in svg for m in EN_MONTHS))
        self.assertIsNone(HANGUL.search(svg))                             # English output: no Hangul
        sizes = [int(v) for v in re.findall(r'font-size="(\d+)"', svg)]
        self.assertTrue(sizes and min(sizes) >= 12)
        ko, _ = render(snapshot, studies=("sma",), width=1100, height=760, months=TEXT["months"][1])
        self.assertTrue(any(f">{m}<" in ko for m in TEXT["months"][1]))
        intraday, layout = render(self.snapshot(300, "1m"), width=900, height=600)
        self.assertRegex(intraday, r">\d\d:\d\d<")

    def test_unavailable_studies_say_why_and_colours_contrast(self):
        from core.education.indicators import STUDIES
        from core.market.detail_svg import CANDLES, THEMES, contrast, render
        from core.market.presentation import study_colors
        _, layout = render(self.snapshot(), studies=("vwap", "investor_flow", "rsi"), width=900, height=700)
        self.assertEqual(layout.unavailable, {"vwap": "intraday_only", "investor_flow": "no_supply_data"})
        self.assertIn("investor_flow", [key for key, _, _ in layout.panels])  # a short note panel, not hidden
        for dark in (False, True):
            bg = THEMES[dark]["bg"]
            for spec in STUDIES:
                for line, color in study_colors(spec.key, dark).items():
                    self.assertGreaterEqual(contrast(color, bg), 3.0, (spec.key, line, dark))
            for color in CANDLES[dark]:
                self.assertGreaterEqual(contrast(color, bg), 3.0)

    def test_every_study_draws(self):
        from core.education.indicators import STUDIES
        from core.market.detail_svg import render
        for spec in STUDIES:
            with self.subTest(study=spec.key):
                svg, layout = render(self.snapshot(260), studies=(spec.key,), width=900, height=700)
                self.assertTrue(svg.endswith("</svg>"))


class DisplayTextTests(unittest.TestCase):
    BANNED = ("사세요", "파세요", "매수하세요", "매도하세요", "추천", "목표가", "진입", "청산")

    def test_stock_text_is_paired_without_advice(self):
        from quantgen_desktop import owner_ui_language
        from quantgen_desktop.owner_ui_language.stock import PAIRS, TEXT
        self.assertIn("stock", owner_ui_language.AREAS)
        self.assertEqual(PAIRS, {})
        owner_ui_language.pairs()  # no conflicts with the other areas
        for key, (en, ko) in TEXT.items():
            with self.subTest(key=key):
                if isinstance(en, tuple):
                    self.assertEqual(len(en), len(ko))
                    self.assertFalse([e for e in en if HANGUL.search(e)])
                    continue
                self.assertIsNone(HANGUL.search(en))
                self.assertEqual(set(re.findall(r"{(\w+)}", en)), set(re.findall(r"{(\w+)}", ko)))
                for word in self.BANNED:
                    self.assertNotIn(word, ko)
                self.assertNotRegex(en, r"(?i)\b(you should|time to) (buy|sell)\b")


class ProfileRowsTests(unittest.TestCase):
    def test_profile_keeps_the_supply_rows_for_the_chart(self):
        from core.education.indicators import Supply, bars_from_candles, compute_study
        from core.research.stock_profile import build_profile
        data = candles(260, start=date(2025, 11, 1))
        days = [c.timestamp[:10] for c in data[-20:]]
        flows = [{"date": d, "foreign_net_qty": 100 * i, "institution_net_qty": -50, "individual_net_qty": None}
                 for i, d in enumerate(days)]
        shorts = [{"date": d, "short_qty": 10 + i, "short_ratio_pct": 2.5, "volume": 1000} for i, d in enumerate(days)]
        profile = build_profile(SAMSUNG, candles=data, flows=flows, shorts=shorts, today=date.fromisoformat(days[-1]))
        daily = profile.values["flows"]["daily"]
        self.assertEqual(len(daily), 20)
        self.assertEqual(daily[1], (days[1], 100.0, -50.0, None))
        self.assertEqual(profile.values["short_selling"]["daily"][-1], (days[-1], 2.5, 29.0))
        self.assertIn(5, profile.values["flows"]["windows"])  # the existing figures are unchanged
        nan = lambda v: math.nan if v is None else v
        supply = Supply(tuple((d, nan(f), nan(i), nan(p)) for d, f, i, p in daily),
                        tuple((d, nan(r), nan(q)) for d, r, q in profile.values["short_selling"]["daily"]))
        values = compute_study("short_ratio", bars_from_candles(data), supply=supply)
        self.assertAlmostEqual(values["SHORT_RATIO"][-1], 2.5)


class YearlyIntervalTests(unittest.TestCase):
    """Owner 2026-11-11 (R-D9-2): "몇분, 일, 주 월, 년" — yearly candles from the monthly history, no new endpoint."""

    def monthly(self, first=(2023, 3), last=(2026, 11), missing_volume=None):
        out, (year, month) = [], first
        i = 0
        while (year, month) <= last:
            base = 100 + i
            volume = None if (year, month) == missing_volume else 1000.0 + i
            out.append(Candle(f"{year}-{month:02d}-01", base, base + 5 + (i % 3), base - 4, base + 1, volume))
            i += 1
            year, month = (year + 1, 1) if month == 12 else (year, month + 1)
        return tuple(out)

    def test_yearly_candles_fold_the_months_and_say_which_years_are_partial(self):
        from core.market.detail_model import load_chart, yearly_span
        months = self.monthly()

        class Router:
            requests = []

            def load(self, request):
                self.requests.append(request)
                return MarketSnapshot(request, months, None, "2026-11-10T06:00:00+00:00", "KIS REST",
                                      "Partial history: 45/500 requested bars (provider window or paging limit).")
        router = Router()
        request = ChartRequest(SAMSUNG, "1Y", 50)
        snapshot = load_chart(router, request)
        self.assertEqual(router.requests, [ChartRequest(SAMSUNG, "1M", 500)])   # the monthly history only
        self.assertIs(snapshot.request, request)
        self.assertEqual([c.timestamp for c in snapshot.candles], ["2023-01-01", "2024-01-01", "2025-01-01", "2026-01-01"])
        year = [c for c in months if c.timestamp.startswith("2024")]
        candle = snapshot.candles[1]
        self.assertEqual((candle.open, candle.close), (year[0].open, year[-1].close))
        self.assertEqual((candle.high, candle.low), (max(c.high for c in year), min(c.low for c in year)))
        self.assertEqual(candle.volume, sum(c.volume for c in year))
        # Honest about partial years: the history starts in March 2023, and 2026 runs to November.
        self.assertEqual(yearly_span(snapshot), {2023: (3, 12), 2026: (1, 11)})
        self.assertIn("requested monthly bars", snapshot.note)
        # A month without volume leaves its year's volume unknown, never a smaller invented sum.
        router2 = Router()
        months = self.monthly(missing_volume=(2025, 6))
        self.assertIsNone(load_chart(router2, request).candles[2].volume)
        # Other intervals pass straight through.
        daily = ChartRequest(SAMSUNG, "1d", 400)
        self.assertEqual(load_chart(router2, daily).request, daily)

    def test_yearly_live_bucket_and_axis_label(self):
        from core.market.detail_svg import cursor_label, render
        from core.market.live import bucket
        self.assertEqual(bucket("2026-11-10T10:00:00+09:00", "1Y"), "2026-01-01")
        self.assertEqual(cursor_label("2026-01-01", False, "1Y"), "2026")
        self.assertEqual(cursor_label("2026-11-01", False, "1M"), "2026-11")
        years = tuple(Candle(f"{y}-01-01", 100 + y % 7, 110 + y % 7, 95, 104, 1e6) for y in range(1990, 2027))
        svg, layout = render(MarketSnapshot(ChartRequest(SAMSUNG, "1Y", 50), years), studies=("sma", "rsi"),
                             width=900, height=600)
        self.assertIn(">2026<", svg)
        self.assertEqual(layout.stop - layout.start, len(years))


class ShortGuideTests(unittest.TestCase):
    """Owner 2026-11-11 (R-D9-3): the guide is a short card; its texts are short in both languages."""
    INTERVALS = ("1m", "5m", "60m", "1d", "1w", "1M", "1Y")

    def bars(self, interval, n=260):
        from core.education.indicators import Bars
        if interval.endswith("m"):
            stamps = tuple((datetime(2026, 11, 9, 9, 0) + timedelta(minutes=i)).isoformat() for i in range(n))
        else:
            stamps = tuple((date(2020, 1, 2) + timedelta(days=i)).isoformat() for i in range(n))
        close = tuple(100 + 10 * math.sin(i / 9) + i * .05 for i in range(n))
        return Bars(stamps, close, tuple(c + 1 for c in close), tuple(c - 1 for c in close), close,
                    tuple(1e6 + 1e4 * math.sin(i) for i in range(n)), interval)

    def test_every_study_has_short_fields_within_their_limits(self):
        from core.education.indicators import STUDIES, study
        from core.education.study_guide import (CAUTION_MAX, CUE_MAX, CUES_MAX, GAUGES, ONE_LINER_MAX, SHORT,
                                                short_guide)
        self.assertEqual(set(SHORT), {spec.key for spec in STUDIES})
        for spec in STUDIES:
            for language in ("ko", "en"):
                with self.subTest(study=spec.key, language=language):
                    short = short_guide(spec.key, language)
                    self.assertTrue(0 < len(short.one_liner) <= ONE_LINER_MAX, short.one_liner)
                    self.assertTrue(1 <= len(short.cues) <= CUES_MAX)
                    for cue in short.cues:
                        self.assertTrue(0 < len(cue) <= CUE_MAX, cue)
                    self.assertTrue(0 < len(short.caution) <= CAUTION_MAX, short.caution)
                    if language == "ko":
                        self.assertNotIn("니다", short.one_liner + short.caution)   # 해요체 on the screen
                        self.assertNotIn("봉", short.one_liner + short.caution + "".join(short.cues))
                    else:
                        self.assertIsNone(HANGUL.search(short.one_liner + short.caution + "".join(short.cues)))
        for key, gauge in GAUGES.items():
            lines = {line.id for line in study(key).lines}
            names = [name for name in gauge[1:] if isinstance(name, str)]
            self.assertTrue(set(names) <= lines, (key, names))

    def test_readings_and_guides_never_say_bong_and_read_every_interval(self):
        from core.education.indicators import STUDIES, Supply, compute_study
        from core.education.study_guide import gauge_value, guide, short_reading, study_reading
        days = [(date(2020, 1, 2) + timedelta(days=i)).isoformat() for i in range(260)]
        supply = Supply(tuple((d, 1000.0 * (i % 5 - 2), -500.0, 300.0) for i, d in enumerate(days)),
                        tuple((d, 2.0 + i % 3, 1000.0) for i, d in enumerate(days)))
        for interval in self.INTERVALS:
            bars = self.bars(interval)
            for spec in STUDIES:
                with self.subTest(interval=interval, study=spec.key):
                    text = guide(spec.key, "ko", interval)
                    self.assertNotIn("봉", text.what + text.how + text.caution)
                    self.assertNotRegex(text.what + text.how + text.caution, r"\{\w+")   # every unit word filled
                    values = compute_study(spec.key, bars, supply=supply)
                    for index in (5, -1):
                        long = study_reading(spec.key, bars, index, language="ko", values=values, supply=supply)
                        brief = short_reading(spec.key, bars, index, language="ko", values=values, supply=supply)
                        self.assertNotIn("봉", long + brief)
                        self.assertNotIn("니다", brief)
                        self.assertLessEqual(len(brief), 44, brief)
                        english = short_reading(spec.key, bars, index, language="en", values=values, supply=supply)
                        self.assertIsNone(HANGUL.search(english), english)
                    gauge = gauge_value(spec.key, values, bars)
                    if gauge is not None:
                        self.assertIn(gauge[0], ("scale", "band", "offset", "zero", "ratio"))
                        self.assertTrue(math.isfinite(gauge[1]))
        # The words follow the interval.
        rsi = lambda interval: study_reading("rsi", self.bars(interval), -1, language="ko")
        self.assertIn("최근 14일 동안", rsi("1d"))
        self.assertIn("최근 14주 동안", rsi("1w"))
        self.assertIn("최근 14개월 동안", rsi("1M"))
        self.assertIn("최근 14년 동안", rsi("1Y"))
        self.assertIn("최근 14분 동안", rsi("1m"))
        self.assertIn("최근 14개 5분 구간 동안", rsi("5m"))
        self.assertIn("최근 20주", guide("sma", "ko", "1w").what)


if __name__ == "__main__":
    unittest.main()
