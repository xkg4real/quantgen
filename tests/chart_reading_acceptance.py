"""Chart reading panels and Korean chart text (owner UI review 2026-11-10, issue 02).

Hermetic: synthetic data only, no provider or network call. Checks that
  * matplotlib draws Korean with the bundled QG Interface face (no tofu, no missing-glyph warning),
  * the macro z-score chart and the other covered charts carry reading guidance in Korean and English,
    and redraw their own text when the page language changes,
  * a chart without guidance keeps the old fallback panel (title / axes / legend / limits),
  * every public chart function in ui/fcharts, ui/qcharts and ui/xcharts returns a FigureStudy with Korean and
    English guidance, Korean text (no English-only title, axis label, legend or tick word) that fits on one line,
    no Hangul after the switch to English, and the same data, scales and colours in both languages,
  * the Macro page hides its data-source selector but keeps the control, and keeps its disclosures.
"""
import inspect
from io import BytesIO
import re
from types import SimpleNamespace
import unittest
import warnings
from unittest.mock import patch

import dotenv
import flet as ft
import numpy as np

with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.ficc.macro import macro_sheet
    from core.i18n import LocaleContext
    from core.theme import DARK, LIGHT, set_mode
    from ui import fcharts, qcharts, xcharts
    from ui.chart_study import READING_KEYS, FigureStudy
    from ui.localization import translate_controls

KO, EN = LocaleContext("ko_KR"), LocaleContext("en_US")


def walk(control, seen=None):
    seen = set() if seen is None else seen
    if not isinstance(control, ft.Control) or id(control) in seen:
        return
    seen.add(id(control))
    yield control
    for name in ("controls", "content", "title", "subtitle", "rows", "cells", "columns", "label", "options"):
        value = getattr(control, name, None)
        for child in value if isinstance(value, (list, tuple)) else [value]:
            yield from walk(child, seen)


def texts(root):
    return [c.value for c in walk(root) if isinstance(c, ft.Text) and isinstance(c.value, str)]


def figure_strings(fig):
    return [t.get_text() for t in fig.findobj(lambda a: hasattr(a, "get_text") and hasattr(a, "get_fontproperties"))
            if t.get_text()]


def has_hangul(text):
    return any("가" <= ch <= "힣" for ch in text)


def draw_without_missing_glyphs(test, fig):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig.savefig(BytesIO(), format="png")
    missing = [str(w.message) for w in caught if "missing" in str(w.message).lower()]
    test.assertEqual(missing, [], missing)


class MacroChartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        set_mode("light")
        cls.sheet = macro_sheet(source="synthetic", days=300)

    def tearDown(self):
        set_mode("light")

    def test_korean_text_uses_the_bundled_hangul_face_without_missing_glyphs(self):
        from matplotlib import font_manager
        study = fcharts.macro_z_chart(self.sheet)
        self.assertEqual(qcharts.CHART_FONT, "QG Interface")
        korean = [t for t in study.figure.findobj(lambda a: hasattr(a, "get_fontproperties") and hasattr(a, "get_text"))
                  if has_hangul(t.get_text())]
        self.assertGreater(len(korean), 10)                      # title, axis label, names, band labels, legend
        for text in korean:
            path = font_manager.findfont(text.get_fontproperties(), fallback_to_default=False)
            self.assertIn("qg-interface", path.replace("\\", "/").split("/")[-1], text.get_text())
        draw_without_missing_glyphs(self, study.figure)

    def test_chart_is_korean_by_default_and_redraws_in_english_with_the_same_data(self):
        study = fcharts.macro_z_chart(self.sheet)
        self.assertIn("주요 거시 지표", study.chart_title)
        labels_ko = [t.get_text() for t in study.figure.axes[0].get_yticklabels()]
        self.assertIn("하이일드 스프레드 (HY OAS)", labels_ko)
        bars_ko = [p.get_width() for p in study.figure.axes[0].patches if p.get_height() < 1]
        legend_ko = study.legend_text
        self.assertIn("합성 데이터 · 실제 관측 아님", legend_ko)          # synthetic rows exist -> named in the legend
        for group in ("금리", "신용", "외환", "위험선호"):
            self.assertIn(group, legend_ko)
        study.render_locale(EN)
        self.assertNotIn("주요", study.chart_title)
        self.assertFalse(any(has_hangul(s) for s in figure_strings(study.figure)))
        labels_en = [t.get_text() for t in study.figure.axes[0].get_yticklabels()]
        self.assertIn("High-yield credit spread (HY OAS)", labels_en)
        self.assertEqual([p.get_width() for p in study.figure.axes[0].patches if p.get_height() < 1], bars_ko)
        self.assertIn("Synthetic data · not observed", study.legend_text)
        draw_without_missing_glyphs(self, study.figure)

    def test_regime_read_is_out_of_the_title_and_the_x_axis_explains_the_scale(self):
        study = fcharts.macro_z_chart(self.sheet)
        ax = study.figure.axes[0]
        self.assertNotIn("\n", ax.get_title(loc="left"))
        self.assertNotIn(self.sheet.regime.curve, ax.get_title(loc="left"))
        self.assertIn("0 = 1년 평균", ax.get_xlabel())
        strings = figure_strings(study.figure)
        self.assertIn("평소 범위 (±1)", strings)
        self.assertEqual(strings.count("이례적"), 2)

    def test_no_synthetic_rows_means_no_synthetic_legend_entry(self):
        from dataclasses import replace
        real = replace(self.sheet, synthetic_ids=())
        study = fcharts.macro_z_chart(real)
        self.assertNotIn("합성", study.legend_text)
        self.assertFalse(any(p.get_hatch() for p in study.figure.axes[0].patches))

    def test_guidance_in_both_languages_follows_the_page_locale(self):
        study = fcharts.macro_z_chart(self.sheet)
        self.assertEqual(set(study.reading), set(READING_KEYS))
        for key, (ko, en) in study.reading.items():
            self.assertTrue(has_hangul(ko) and ko.strip(), key)
            self.assertTrue(en.strip() and not has_hangul(en), key)
        root = ft.Column([study])
        translate_controls(root, KO)
        shown = " ".join(texts(root))
        self.assertIn("0의 오른쪽이면 1년 평균보다 높고", shown)
        self.assertIn("P19", shown)
        translate_controls(root, EN)
        shown = " ".join(texts(root))
        self.assertIn("Bars right of 0 are above the 1-year average", shown)
        self.assertIn("not a regime model or a forecast (P19)", shown)
        self.assertNotIn("0의 오른쪽", shown)

    def test_theme_survives_a_language_switch(self):
        from matplotlib.colors import to_rgba
        study = fcharts.macro_z_chart(self.sheet)
        study.render_theme(DARK)
        study.render_locale(EN)
        np.testing.assert_allclose(study.figure.get_facecolor(), to_rgba(DARK.surface))
        self.assertEqual(study.palette, DARK)
        study.render_theme(LIGHT)
        np.testing.assert_allclose(study.figure.get_facecolor(), to_rgba(LIGHT.surface))


class OtherChartTests(unittest.TestCase):
    def tearDown(self):
        set_mode("light")

    def test_covered_charts_have_bilingual_guidance_and_korean_text(self):
        from core.quant.backtest import run_backtest
        from core.quant.history import synthetic_history
        from core.ficc import data, fx
        h = synthetic_history("AAPL")
        bt = run_backtest(h)
        dates = list(h.dates)
        eq = np.cumprod(1 + np.full(len(dates), 0.0005))
        pairs = ("EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "USDKRW")
        spots = {p: data.synthetic_fx(p, days=300) for p in pairs}
        rates = {c: data.synthetic_series(f"RATE_{c}", days=300, kind="rate") for c in data.G10_KRW}
        charts = {
            "price": qcharts.price_chart(h),
            "equity": qcharts.equity_chart(bt),
            "lab_equity": xcharts.equity_chart(dates, eq, eq * 0.99, title="S_X: out-of-sample equity"),
            "curve_history": fcharts.curve_history_chart(data.synthetic_curve_panel(days=60)),
            "fx_spot": fcharts.fx_spot_chart(spots["EURUSD"], 1.1),
            "carry_bar": fcharts.carry_bar_chart(fx.carry_table(spots, rates)),
        }
        for name, study in charts.items():
            with self.subTest(chart=name):
                self.assertTrue(study.src.startswith("data:image/png;base64,"))
                self.assertEqual(set(study.reading), set(READING_KEYS))
                self.assertTrue(has_hangul(study.chart_title), study.chart_title)
                draw_without_missing_glyphs(self, study.figure)
                study.render_locale(EN)
                self.assertFalse(has_hangul(study.chart_title), study.chart_title)
        self.assertEqual(xcharts.equity_chart(dates, eq, None, title="S_X: out-of-sample equity").chart_title,
                         "S_X: 표본 외(OOS) 누적 성과")

    def test_a_chart_without_guidance_keeps_the_fallback_panel(self):
        fig, ax = qcharts._fig(4, 3, LIGHT)
        ax.plot([0, 1, 2], [1, 2, 3], label="Series A")
        ax.set_title("Observed data", loc="left"); ax.set_xlabel("Date"); ax.set_ylabel("Price")
        ax.legend()
        study = qcharts._to_image(fig)
        self.assertEqual(study.reading, {})
        study.render_locale(EN)
        shown = texts(study)
        self.assertIn("Observed data", shown)
        self.assertIn("Date · Price", shown)
        self.assertIn("Series A", shown)
        self.assertIn(EN.t("chart_limits"), shown)


def chart_fixtures():
    """name -> builder for every public chart, on synthetic data, with the titles the pages pass.
    A name after ':' is a second case of the same function (another caller title)."""
    from core.ficc import data, fx, ratesim, swaps
    from core.ficc.bonds import Bond, analyze_bond, scenario_pnl
    from core.ficc.curves import analyze_curve, curve_pca
    from core.ficc.structured import dual_currency_deposit, principal_protected_note, reverse_convertible
    from core.quant.backtest import run_backtest
    from core.quant.history import synthetic_history
    from core.quant.montecarlo import run_monte_carlo
    from core.quant.optimize import efficient_frontier, optimize_portfolio
    from core.quant.risk import align_histories
    from core.research.crypto_workflow import analyze as crypto_analyze
    from core.research.derivatives_workflow import snapshot

    panel = data.synthetic_curve_panel(days=120)
    report = analyze_curve(panel, method="nelson_siegel")
    curve = report.curve
    bond = Bond(coupon=0.04, maturity=10.0, name="4% 10y")
    ba = analyze_bond(bond, ytm=0.045, curve=curve)
    pts = fx.smile_from_quotes(fx.SmileQuote(0.5, 0.10, 0.01, 0.003), 1.10, 0.045, 0.03)
    F = fx.forward(1.10, 0.045, 0.03, 0.5)
    sabr = fx.calibrate_sabr(F, 0.5, [p.strike for p in pts], [p.vol for p in pts])
    ks = np.linspace(pts[0].strike * 0.97, pts[-1].strike * 1.03, 60)
    sim = ratesim.simulate(ratesim.calibrate(data.load_short_rate("USD", source="synthetic", days=300)),
                           horizon=1.0, n_paths=200, threshold=0.05)
    hpv = ratesim.horizon_pv_distribution(sim.params, sim, kind="bond", bond=bond, curve=curve)
    pairs = ("EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "USDKRW")
    spots = {p: data.synthetic_fx(p, days=300) for p in pairs}
    rates = {c: data.synthetic_series(f"RATE_{c}", days=300, kind="rate") for c in data.G10_KRW}
    h = synthetic_history("AAPL")
    mc = run_monte_carlo(h, n_paths=200, horizon_days=20)
    bt = run_backtest(h)
    stats = align_histories([synthetic_history(s) for s in ("AAPL", "MSFT", "NVDA", "TLT")])
    deriv = snapshot(source="synthetic", n_paths=200)
    crypto = crypto_analyze(source="synthetic", card_loader=lambda path: [], include_balances=False)
    kp, funding, btc = crypto["kimchi"], crypto["funding"], crypto["btc"]
    sma = {n: np.concatenate([np.full(n - 1, np.nan), np.convolve(btc, np.ones(n) / n, mode="valid")])
           for n in (50, 200)}
    dates = list(h.dates)
    eq = np.cumprod(1 + np.full(len(dates), 0.0005))
    rng = np.random.default_rng(4)
    nav = 10000 * np.exp(np.cumsum(rng.normal(0, 0.01, 250)))
    prem = rng.normal(0, 0.15, 250)
    from core.ficc.macro import macro_sheet
    return {
        "fcharts.curve_chart": lambda: fcharts.curve_chart(report),
        "fcharts.curve_history_chart": lambda: fcharts.curve_history_chart(panel),
        "fcharts.pca_chart": lambda: fcharts.pca_chart(curve_pca(panel)),
        "fcharts.krd_chart": lambda: fcharts.krd_chart(ba.krd, title="Key-rate DV01, z-spread +12.3bp held"),
        "fcharts.krd_chart:swap": lambda: fcharts.krd_chart(ba.krd, "Key-rate DV01 — 1y5y payer"),
        "fcharts.krd_chart:default": lambda: fcharts.krd_chart(ba.krd),
        "fcharts.scenario_chart": lambda: fcharts.scenario_chart(scenario_pnl(bond, curve, ba.price)),
        "fcharts.price_yield_chart": lambda: fcharts.price_yield_chart(bond, ba.ytm),
        "fcharts.caplet_chart": lambda: fcharts.caplet_chart(swaps.price_cap_floor(curve, 5.0, None, vol=0.008)),
        "fcharts.smile_chart": lambda: fcharts.smile_chart(ks, fx.smile_curve(sabr, F, 0.5, ks), pts, F),
        "fcharts.fx_spot_chart": lambda: fcharts.fx_spot_chart(spots["EURUSD"], ((0.25, 1.105), (1.0, 1.12))),
        "fcharts.carry_equity_chart": lambda: fcharts.carry_equity_chart(fx.carry_backtest(spots, rates)),
        "fcharts.carry_bar_chart": lambda: fcharts.carry_bar_chart(fx.carry_table(spots, rates)),
        "fcharts.payoff_chart": lambda: fcharts.payoff_chart(
            principal_protected_note(curve, spot=100.0, vol=0.2, maturity=3.0)),
        "fcharts.payoff_chart:rc": lambda: fcharts.payoff_chart(
            reverse_convertible(curve, spot=100.0, vol=0.25, maturity=1.0, underlying="EQ")),
        "fcharts.payoff_chart:dcd": lambda: fcharts.payoff_chart(
            dual_currency_deposit(curve, spot=1.10, strike=1.08, vol=0.08, maturity=0.25, r_for=0.03,
                                  base_ccy="EUR", quote_ccy="USD")),
        "fcharts.rate_fan_chart": lambda: fcharts.rate_fan_chart(sim),
        "fcharts.horizon_pv_hist": lambda: fcharts.horizon_pv_hist(hpv),
        "fcharts.macro_z_chart": lambda: fcharts.macro_z_chart(macro_sheet(source="synthetic", days=300)),
        "qcharts.price_chart": lambda: qcharts.price_chart(h),
        "qcharts.fan_chart": lambda: qcharts.fan_chart(h, mc),
        "qcharts.terminal_histogram": lambda: qcharts.terminal_histogram(mc),
        "qcharts.equity_chart": lambda: qcharts.equity_chart(bt),
        "qcharts.frontier_chart": lambda: qcharts.frontier_chart(
            efficient_frontier(stats, points=6, n_cloud=100),
            [optimize_portfolio(stats, objective=o) for o in ("max_sharpe", "min_vol")]),
        "qcharts.corr_heatmap": lambda: qcharts.corr_heatmap(stats.corr, stats.symbols),
        "qcharts.cond_vol_chart": lambda: qcharts.cond_vol_chart(h, mc.garch),
        "xcharts.lines_chart": lambda: xcharts.lines_chart(
            kp.dates, {"kimchi premium %": kp.premium_pct},
            title="Kimchi premium (Upbit KRW-BTC vs Binance × USD/KRW)", hlines={"0": 0.0}, pct=True),
        "xcharts.lines_chart:funding": lambda: xcharts.lines_chart(
            funding.dates, {"funding (ann. %)": funding.carry_ann_pct},
            title="Perpetual funding, 7-day mean annualised", hlines={"0": 0.0}, pct=True),
        "xcharts.lines_chart:btc": lambda: xcharts.lines_chart(
            crypto["btc_dates"], {"BTCUSDT": btc, "SMA50": sma[50], "SMA200": sma[200]},
            title="BTCUSDT with 50/200-day averages"),
        "xcharts.smile_chart": lambda: xcharts.smile_chart(deriv["points"], deriv["svi"], deriv["F"],
                                                           title=f"KOSPI200 {deriv['expiry']} smile"),
        "xcharts.density_chart": lambda: xcharts.density_chart(
            deriv["rnd"], p_samples=1126.0 * np.exp(np.random.default_rng(3).normal(0, 0.05, 3000))),
        "xcharts.equity_chart": lambda: xcharts.equity_chart(dates, eq, eq * 0.99, title="S_X: out-of-sample equity"),
        "xcharts.bars_chart": lambda: xcharts.bars_chart(["Trend", "Value", "Quality"], [82.0, 55.0, 21.0],
                                                         title="Scores", title_ko="점수",
                                                         labels_ko=["추세", "가치", "품질"]),
        "xcharts.premium_chart": lambda: xcharts.premium_chart(dates[:250], nav * (1 + prem / 100), nav, prem,
                                                               title="069500 price vs NAV"),
    }


def public_charts():
    return {f"{module.__name__.split('.')[-1]}.{name}" for module in (fcharts, qcharts, xcharts)
            for name, fn in vars(module).items()
            if inspect.isfunction(fn) and fn.__module__ == module.__name__ and not name.startswith("_")}


def plotted(fig):
    """Everything the figure plots, for comparing languages: limits, scales, lines, bars, collections, colours."""
    from matplotlib.colors import to_rgba
    out = []
    for ax in fig.axes:
        out.append((ax.get_xlim(), ax.get_ylim(), ax.get_xscale(), ax.get_yscale()))
        for line in ax.get_lines():
            out.append((np.asarray(line.get_xdata(), float), np.asarray(line.get_ydata(), float),
                        to_rgba(line.get_color()), line.get_linestyle()))
        for p in ax.patches:
            if hasattr(p, "get_width"):
                out.append((p.get_x(), p.get_y(), p.get_width(), p.get_height(), to_rgba(p.get_facecolor())))
        for c in ax.collections:
            out.append((np.asarray(c.get_offsets(), float), [np.asarray(q.vertices, float) for q in c.get_paths()],
                        np.asarray(c.get_facecolor(), float)))
    return out


def assert_same_plot(test, a, b, where=""):
    if isinstance(a, (list, tuple)):
        test.assertEqual(len(a), len(b), where)
        for i, (x, y) in enumerate(zip(a, b)):
            assert_same_plot(test, x, y, f"{where}/{i}")
    elif isinstance(a, (np.ndarray, float, np.floating)):
        np.testing.assert_allclose(np.asarray(a, float), np.asarray(b, float), equal_nan=True, err_msg=where)
    else:
        test.assertEqual(a, b, where)


ENGLISH_WORD = re.compile(r"\b[a-z]{3,}")          # an ordinary lower-case English word (names/acronyms start upper)


class EveryChartTests(unittest.TestCase):
    """Every public chart reads in Korean by default and in English after the switch, with the same plot."""

    @classmethod
    def setUpClass(cls):
        set_mode("light")
        with patch("requests.sessions.Session.request", side_effect=AssertionError("No provider API")):
            cls.fixtures = chart_fixtures()

    def tearDown(self):
        set_mode("light")

    def test_every_public_chart_function_has_a_case(self):
        self.assertEqual(public_charts() - {k.split(":")[0] for k in self.fixtures}, set())

    def test_every_chart_is_korean_then_english_with_guidance_and_the_same_plot(self):
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        for name, make in self.fixtures.items():
            with self.subTest(chart=name):
                with patch("requests.sessions.Session.request", side_effect=AssertionError("No provider API")):
                    study = make()
                self.assertIsInstance(study, FigureStudy)
                self.assertTrue(study.src.startswith("data:image/png;base64,"))
                self.assertEqual(set(study.reading), set(READING_KEYS))
                for key, (ko, en) in study.reading.items():
                    self.assertTrue(has_hangul(ko), (key, ko))
                    self.assertTrue(en.strip() and not has_hangul(en), (key, en))
                ko_limit, en_limit = study.reading["limit"]
                self.assertRegex(ko_limit, "예측|보장|전망|권유")       # a chart is not a forecast
                self.assertRegex(en_limit, "forecast|guarantee|recommendation")

                # Korean: the title is Korean, on one line, inside the figure; no English-only wording.
                self.assertTrue(has_hangul(study.chart_title), study.chart_title)
                fig = study.figure
                canvas = FigureCanvasAgg(fig)
                canvas.draw()
                renderer = canvas.get_renderer()
                for ax in fig.axes:
                    for title in (ax.title, ax._left_title, ax._right_title):
                        if title.get_text():
                            self.assertNotIn("\n", title.get_text())
                            box = title.get_window_extent(renderer)
                            self.assertLessEqual(box.x1, fig.bbox.x1 + 0.5, title.get_text())
                            self.assertGreaterEqual(box.x0, fig.bbox.x0 - 0.5, title.get_text())
                english = [s for s in figure_strings(fig) if not has_hangul(s) and ENGLISH_WORD.search(s)]
                self.assertEqual(english, [], name)
                draw_without_missing_glyphs(self, fig)
                ko_plot = plotted(fig)

                study.render_locale(EN)
                self.assertFalse(any(has_hangul(s) for s in figure_strings(study.figure)), name)
                self.assertFalse(has_hangul(study.chart_title), study.chart_title)
                assert_same_plot(self, ko_plot, plotted(study.figure), name)
                shown = " ".join(texts(study))
                self.assertIn(en_limit, shown)
                study.render_locale(KO)
                self.assertTrue(has_hangul(study.chart_title))
                self.assertIn(ko_limit, " ".join(texts(study)))

    def test_titles_the_pages_pass_read_in_korean(self):
        cases = {
            "fcharts.krd_chart": "만기별 DV01 (z-스프레드 +12.3bp 고정) — 합계",
            "fcharts.krd_chart:swap": "만기별 DV01 — 1년 후 시작 5년 고정금리 지급 스왑, 합계",
            "fcharts.payoff_chart": "원금보장형 노트 (외환) — 공정가치",
            "fcharts.payoff_chart:rc": "역전환형 노트 (주식) — 공정가치",
            "fcharts.payoff_chart:dcd": "이중통화예금 EURUSD (행사가격 1.08) — 공정가치",
            "fcharts.price_yield_chart": "쿠폰 4% · 10년 만기 채권 — 가격과 수익률",
            "xcharts.lines_chart": "김치 프리미엄 (업비트 KRW-BTC 대 바이낸스 × 달러/원 환율)",
            "xcharts.lines_chart:btc": "BTCUSDT와 50일·200일 이동평균",
            "xcharts.smile_chart": "KOSPI200 DEMO 변동성 스마일",
            "xcharts.premium_chart": "069500 시장가격과 순자산가치(NAV)",
        }
        for name, title in cases.items():
            with self.subTest(chart=name):
                self.assertTrue(self.fixtures[name]().chart_title.startswith(title))
        study = self.fixtures["fcharts.payoff_chart"]()
        ax = study.figure.axes[0]
        self.assertEqual((ax.get_xlabel(), ax.get_ylabel()), ("만기 시 기초자산 가격", "액면 100당"))
        self.assertEqual(study.legend_text, "만기 지급액 (액면 100당) · 발행가 100")
        study.render_locale(EN)
        self.assertTrue(study.chart_title.startswith("Principal-protected note (FX) — fair "))
        self.assertEqual(study.legend_text, "Payoff at maturity (per 100) · Issue price 100")


class MacroPageTests(unittest.TestCase):
    def build(self):
        from ui import macro_page
        page = SimpleNamespace(qg_locale=KO, update=lambda: None, run_thread=lambda fn: fn())
        with patch.object(macro_page, "analysis_panel", side_effect=lambda *a, **k: ft.Text("analysis fixture")), \
                patch("requests.sessions.Session.request", side_effect=AssertionError("No provider API")):
            root = macro_page.build_macro_page(page)
            source = next(c for c in walk(root) if isinstance(c, ft.Dropdown) and c.label == "Data source")
            source.value = "synthetic"
            next(c for c in walk(root) if isinstance(c, ft.Button) and c.content == "Refresh").on_click(None)
        return root, source

    def test_the_data_source_selector_is_hidden_but_kept(self):
        root, source = self.build()
        self.assertFalse(source.visible)
        self.assertIn("auto", [o.key for o in source.options])
        from ui import macro_page
        fresh = macro_page.build_macro_page(SimpleNamespace(qg_locale=KO, update=lambda: None,
                                                            run_thread=lambda fn: None))
        dd = next(c for c in walk(fresh) if isinstance(c, ft.Dropdown) and c.label == "Data source")
        self.assertEqual(dd.value, "auto")

    def test_summary_disclosures_and_names_read_in_korean_and_english(self):
        root, _ = self.build()
        translate_controls(root, KO)
        shown = texts(root)
        joined = " ".join(shown)
        for caption in ("시장 요약", "현재 상태를 설명하는 해석 — 국면 모형 아님 (P19)", "금리 곡선 (20거래일)",
                        "위험선호", "미 국채 2년 금리 (UST 2y)"):
            self.assertIn(caption, shown)
        self.assertIn("새로고침", [b.content for b in walk(root) if isinstance(b, ft.Button)])
        self.assertIn("합성 데이터 사용 중", joined)                      # the synthetic notice stays loud
        translate_controls(root, EN)
        shown = texts(root)
        joined = " ".join(shown)
        self.assertIn("Descriptive read — not a regime model (P19)", shown)
        self.assertIn("Synthetic data: ", joined)
        self.assertIn("US Treasury 2-year yield (UST 2y)", shown)
        self.assertNotIn("시장 요약", shown)
        self.assertIn("Refresh", [b.content for b in walk(root) if isinstance(b, ft.Button)])


if __name__ == "__main__":
    unittest.main()
