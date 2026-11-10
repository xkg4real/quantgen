"""Chart reading panels and Korean chart text (owner UI review 2026-11-10, issue 02).

Hermetic: synthetic data only, no provider or network call. Checks that
  * matplotlib draws Korean with the bundled QG Interface face (no tofu, no missing-glyph warning),
  * the macro z-score chart and the other covered charts carry reading guidance in Korean and English,
    and redraw their own text when the page language changes,
  * a chart without guidance keeps the old fallback panel (title / axes / legend / limits),
  * the Macro page hides its data-source selector but keeps the control, and keeps its disclosures.
"""
from io import BytesIO
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
