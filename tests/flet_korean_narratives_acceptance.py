"""Owner UI review 2026-11-10: the Analysis panel of every Flet page with a reviewed native Korean
narrative reads in Korean under short Korean headings in ko_KR, and in English in en_US.

For each wired page the test runs the page on synthetic data (no provider, no Anthropic call), captures
what the page hands `analysis_panel`, and checks:
  * the English `narrative` argument is unchanged (it is exactly the English twin of the inputs the
    page gave the native Korean function, so both languages describe the same result);
  * `sections(en_US)` shows that English narrative, every sentence, in order;
  * `sections(ko_KR)` shows exactly the native Korean text, every sentence, in order, under Korean
    headings, and the bullets are Korean.
Pages without a native Korean narrative (Quant Lab's Monte Carlo) pass no sections.
"""
from contextlib import ExitStack
import os
import re
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    import flet as ft
    from core.ficc import insights as fi
    from core.ficc.data import synthetic_curve_panel
    from core.ficc.macro import macro_sheet
    from core.i18n import LocaleContext
    from core.quant import insights as qi
    from core.quant.history import synthetic_history
    from core.research import crypto_workflow, derivatives_workflow, etf_workflow
    from core.research.portfolio_disclosure import portfolio_disclosure
    from quantgen_desktop import (bonds_portfolio_narrative as bpn, fx_narrative, market_narrative_language as mnl,
                                  macro_narrative_language as macro_ko, model_narrative_language as model_ko,
                                  rates_narrative)
    from ui import (bonds_page, crypto_page, derivatives_page, etf_page, fx_page, macro_page, portfolio_page,
                    quant_lab_page, rates_page, signals_page, structuring_page)
    from ui import narrative_sections as ns
    from ui import ai_panel as panel_module
    from ui.localization import translate_controls

KO, EN = LocaleContext("ko_KR"), LocaleContext("en_US")
HANGUL = re.compile(r"[가-힣]")
KO_HEADINGS = {ko for ko, _ in ns.HEADINGS.values()} | {"선물 헤지", "제약 조건"}
EN_HEADINGS = {en for _, en in ns.HEADINGS.values()} | {"Futures hedge", "Constraints"}


def squash(text: str) -> str:
    return re.sub(r"\s+", "", str(text))


def joined(sections) -> str:
    return squash("".join(line for _, lines in sections for line in lines))


def page():
    return SimpleNamespace(qg_locale=KO, update=lambda: None, run_thread=lambda fn: fn())


def walk(control, seen=None):
    seen = set() if seen is None else seen
    if not isinstance(control, ft.Control) or id(control) in seen:
        return
    seen.add(id(control))
    yield control
    for name in ("controls", "content", "title", "label", "options"):
        value = getattr(control, name, None)
        for child in (value if isinstance(value, (list, tuple)) else [value]):
            yield from walk(child, seen)


def button(root, label):
    return next(c for c in walk(root) if isinstance(c, ft.Button) and c.content == label)


def dropdown(root, label):
    return next(c for c in walk(root) if isinstance(c, ft.Dropdown) and c.label == label)


class SectionHelpers(unittest.TestCase):
    def test_short_text_reads_under_one_heading(self):
        self.assertEqual(ns.organise("첫 문장입니다. 둘째 문장입니다.", "ko"),
                         [("요약", ["첫 문장입니다.", "둘째 문장입니다."])])
        self.assertEqual(ns.organise("One. Two.", "en"), [("Summary", ["One.", "Two."])])
        self.assertEqual(ns.organise("", "ko"), [])

    def test_long_text_keeps_every_sentence_in_order(self):
        text = ("요약 문장 1.5%입니다. 수치 2개입니다. 수치 3.0입니다. 마지막 값은 비교 기준이 아닙니다. "
                "다시 수치 4입니다. 이 해설은 예측이 아닙니다. 투자 권고가 아닙니다.")
        sections = ns.organise(text, "ko")
        self.assertEqual([h for h, _ in sections], ["요약", "핵심 수치", "해석과 한계"])
        self.assertEqual(sections[0][1], ["요약 문장 1.5%입니다."])
        # a figure-free sentence between figures stays where it is; only the trailing run moves under limits
        self.assertIn("마지막 값은 비교 기준이 아닙니다.", sections[1][1])
        self.assertEqual(sections[2][1], ["이 해설은 예측이 아닙니다.", "투자 권고가 아닙니다."])
        self.assertEqual(joined(sections), squash(text))

    def test_korean_sentence_end_splits_before_lower_case_notes_and_signs(self):
        text = "가격은 1입니다. nelson-siegel 적합 오차는 0.1bp입니다. +1bp 이동 시 손실 2입니다."
        self.assertEqual(ns.sentences(text, "ko"),
                         ["가격은 1입니다.", "nelson-siegel 적합 오차는 0.1bp입니다.", "+1bp 이동 시 손실 2입니다."])
        self.assertEqual(ns.sentences("Spot 1.10. payer bachelier; single-curve.", "en"),
                         panel_module.split_sentences("Spot 1.10. payer bachelier; single-curve."))

    def test_missing_korean_keeps_the_panel_default(self):
        self.assertIsNone(ns.localized("English.", None))
        self.assertIsNone(ns.localized("English.", ""))
        self.assertIsNone(ns.localized("English.", "한국어.", extra=[(("제약", "Scope"), None, "Scope.")]))
        self.assertIsNone(ns.korean(lambda: 1 / 0))
        self.assertIsNone(ns.korean(lambda: None))
        sections = ns.localized("One 1. Two 2.", "하나 1입니다. 둘 2입니다.",
                                extra=[(("제약 조건", "Constraints"), ["가", "나"], "Cap 1. Bound 2.")])
        self.assertEqual(sections(KO), [("요약", ["하나 1입니다.", "둘 2입니다."]), ("제약 조건", ["가", "나"])])
        self.assertEqual(sections(EN), [("Summary", ["One 1.", "Two 2."]), ("Constraints", ["Cap 1.", "Bound 2."])])

    def test_panel_renders_korean_sections_and_returns_to_english(self):
        sections = ns.localized("Spot 1.10 today. Carry 2%. Not a forecast.", "현물 1.10입니다. 캐리 2%입니다. 예측이 아닙니다.")
        host = SimpleNamespace(qg_locale=EN)
        with patch.object(panel_module.insights, "ai_ready", return_value=False):
            panel = panel_module.analysis_panel(host, kind="fx_forward", narrative="Spot 1.10 today. Carry 2%. Not a forecast.",
                                                payload_fn=dict, sections=sections)
        translate_controls(panel, KO)
        shown = [c.value for c in walk(panel) if isinstance(c, ft.Text)]
        for text in ("요약", "현물 1.10입니다.", "캐리 2%입니다.", "예측이 아닙니다."):
            self.assertIn(text, shown)
        translate_controls(panel, EN)
        shown = [c.value for c in walk(panel) if isinstance(c, ft.Text)]
        self.assertIn("Summary", shown)
        self.assertIn("Carry 2%.", shown)
        self.assertNotIn("요약", shown)


class PageWiring(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for target in ("socket.socket.connect", "requests.sessions.Session.request"):
            self.stack.enter_context(patch(target, side_effect=AssertionError("network forbidden")))
        self.panel = synthetic_curve_panel(days=60, seed=42)

    def capture(self, module):
        panels = []

        def panel(_page, **kw):
            kw["payload_fn"]()
            panels.append(kw)
            return ft.Text("analysis fixture")
        self.stack.enter_context(patch.object(module, "analysis_panel", side_effect=panel))
        return panels

    def spy(self, module, name):
        return self.stack.enter_context(patch.object(module, name, wraps=getattr(module, name)))

    def assert_bilingual(self, kw, korean_text, *, extra_ko=()):
        """`extra_ko`: the Korean lines of each extra part shown after the main read, in order (in English
        the extra parts are part of the narrative argument, checked as a whole)."""
        sections = kw.get("sections")
        self.assertTrue(callable(sections), kw.get("kind"))
        self.assertTrue(korean_text and HANGUL.search(korean_text))
        ko, en = sections(KO), sections(EN)
        # English: exactly the narrative argument, every sentence, in order.
        self.assertEqual(joined(en), squash(kw["narrative"]), kw["kind"])
        self.assertTrue({h for h, _ in en} <= EN_HEADINGS, en)
        # Korean: exactly the native text (+ the extra parts), under Korean headings.
        self.assertEqual(joined(ko), squash(korean_text) + "".join(squash("".join(k)) for k in extra_ko), kw["kind"])
        self.assertTrue({h for h, _ in ko} <= KO_HEADINGS, ko)
        self.assertEqual(ko[0][0], "요약")
        lines = [line for _, items in ko for line in items]
        korean_share = sum(bool(HANGUL.search(line)) for line in lines) / len(lines)
        self.assertGreaterEqual(korean_share, 0.6, (kw["kind"], lines))

    # ---------------------------------------------------------------- Rates (five tools)
    def test_rates_every_tool(self):
        panels = self.capture(rates_page)
        self.stack.enter_context(patch.object(rates_page, "load_treasury_curve", return_value=self.panel))
        spies = {n: self.spy(rates_page, n) for n in ("curve_korean", "swap_korean", "swaption_korean",
                                                       "cap_floor_korean", "simulation_korean")}
        p = page()
        rates_page._run_curve(p, source="synthetic", method="bootstrap", lookback=20)
        rates_page._run_swap(p, source="synthetic", tenor_text="10y", fixed_pct=None, notional=1e6, pay_fixed=True)
        rates_page._run_option(p, source="synthetic", kind="swaption", expiry_text="1y", tenor_text="10y",
                               strike_pct=None, payer=True, model="bachelier", vol_in=80, notional=1e6)
        rates_page._run_option(p, source="synthetic", kind="cap", expiry_text="1y", tenor_text="5y",
                               strike_pct=None, payer=True, model="black", vol_in=20, notional=1e6)
        rates_page._run_sim(p, source="synthetic", model="vasicek", horizon=1.0, n_paths=200, threshold_pct=4.0,
                            instrument="bond", instr_tenor_text="5y", coupon_pct=4.0)
        self.assertEqual([kw["kind"] for kw in panels], ["rates_curve", "rates_swap", "rates_swaption",
                                                        "rates_cap_floor", "rates_simulation"])
        twins = [("curve_korean", fi.narrate_curve), ("swap_korean", fi.narrate_swap),
                 ("swaption_korean", fi.narrate_swaption), ("cap_floor_korean", fi.narrate_cap_floor),
                 ("simulation_korean", fi.narrate_ratesim)]
        for kw, (name, english) in zip(panels, twins):
            with self.subTest(kind=kw["kind"]):
                args = spies[name].call_args.args
                self.assertEqual(kw["narrative"], english(*args))
                self.assert_bilingual(kw, getattr(rates_narrative, name)(*args))

    # ---------------------------------------------------------------- FX (three tools)
    def test_fx_every_tool(self):
        panels = self.capture(fx_page)
        fx_text = self.spy(fx_page, "fx_text")
        carry = self.spy(fx_page, "carry_korean")
        root = fx_page.build_fx_page(page())
        dropdown(root, "Data source").value = "synthetic"
        for tool in ("forward", "option", "carry"):
            dropdown(root, "Tool").value = tool
            button(root, "Run").on_click(None)
        self.assertEqual([kw["kind"] for kw in panels], ["fx_forward", "fx_option", "fx_carry"])
        fwd, opt, car = panels
        tool, d = fx_text.call_args_list[0].args
        self.assertEqual(tool, "forward")
        self.assertEqual(fwd["narrative"], fi.narrate_fx_forward(d["pair"], d["S"], d["forward"], d["points"],
                                                                 d["carry"], d["basis"]))
        self.assert_bilingual(fwd, fx_narrative.fx_korean(SimpleNamespace(request=SimpleNamespace(tool=tool), data=d)))
        tool, d = fx_text.call_args_list[1].args
        self.assertEqual(tool, "option")
        # any non-None fit: with the diagnostics given, the English twin only appends their text
        self.assertEqual(opt["narrative"], fi.narrate_fx_option(d["report"], d["points"], object(),
                                                                diagnostics=d["sabr_diagnostics"]))
        self.assert_bilingual(opt, fx_narrative.fx_korean(SimpleNamespace(request=SimpleNamespace(tool=tool), data=d)))
        rows, bt = carry.call_args.args
        self.assertEqual(car["narrative"], fi.narrate_carry(rows, bt))
        self.assert_bilingual(car, fx_narrative.carry_korean(rows, bt))

    # ---------------------------------------------------------------- Bonds (three tools)
    def test_bonds_every_tool(self):
        panels = self.capture(bonds_page)
        self.stack.enter_context(patch.object(bonds_page, "load_treasury_curve", return_value=self.panel))
        bond = self.spy(bonds_page, "bond_korean")
        root = bonds_page.build_bonds_page(page())
        for tool in ("calc", "scenarios", "hedge"):
            dd = dropdown(root, "Tool")
            dd.value = tool
            dd.on_select(None)
            button(root, "Run").on_click(None)
        self.assertEqual([kw["kind"] for kw in panels], ["bond_calc", "bond_scenarios", "bond_hedge"])
        for kw, call in zip(panels, bond.call_args_list):
            with self.subTest(kind=kw["kind"]):
                a, rows = call.args
                english = fi.narrate_bond(a, list(rows) or None)
                korean = bpn.bond_korean(a, rows)
                if kw["kind"] == "bond_hedge":
                    payload = kw["payload_fn"]()["hedge"]
                    hedge = (payload["position_dv01"], payload["ctd_dv01_per_contract"],
                             payload["conversion_factor"], payload["contracts"])
                    self.assertTrue(kw["narrative"].startswith(english + " Hedging "))
                    ko_hedge = bpn.hedge_text(hedge, "ko").splitlines()
                    self.assert_bilingual(kw, korean, extra_ko=[ko_hedge])
                    self.assertEqual(kw["sections"](KO)[-1], ("선물 헤지", ko_hedge))
                    self.assertEqual(kw["sections"](EN)[-1][0], "Futures hedge")
                else:
                    self.assertEqual(kw["narrative"], english)
                    self.assert_bilingual(kw, korean)
        self.assertEqual(len(bond.call_args_list[1].args[1]), 9)      # the scenarios reached the Korean read

    # ---------------------------------------------------------------- Portfolio
    def test_portfolio(self):
        panels = self.capture(portfolio_page)
        self.stack.enter_context(patch.object(portfolio_page, "load_history",
                                              side_effect=lambda s, **kw: synthetic_history(s, days=400)))
        read = self.spy(portfolio_page, "portfolio_korean")
        scope = self.spy(portfolio_page, "portfolio_scope_korean")
        root = portfolio_page.build_portfolio_page(page())
        next(c for c in walk(root) if isinstance(c, ft.TextField) and c.label == "Symbols (comma separated)").value = \
            "AAA, BBB, CCC"
        button(root, "Optimize").on_click(None)
        (kw,) = panels
        chosen = read.call_args.args[0]
        ports, objective = scope.call_args.args
        summary = portfolio_disclosure(ports, objective)["summary"]
        self.assertEqual(kw["narrative"], qi.narrate_portfolio(chosen) + " " + summary)
        ko_scope = bpn.portfolio_scope_korean(ports, objective)
        self.assert_bilingual(kw, bpn.portfolio_korean(chosen), extra_ko=[ns.sentences(ko_scope, "ko")])
        self.assertEqual(kw["sections"](KO)[-1][0], "제약 조건")
        self.assertEqual(kw["sections"](EN)[-1], ("Constraints", ns.sentences(summary, "en")))

    # ---------------------------------------------------------------- Macro (sheet, daily, weekly)
    def test_macro_sheet_daily_weekly(self):
        sheet = macro_sheet(source="synthetic")
        panels = self.capture(macro_page)
        self.stack.enter_context(patch.object(macro_page, "macro_sheet", return_value=sheet))
        self.stack.enter_context(patch.object(macro_page.config, "ficc_provider_status", return_value=[]))
        self.stack.enter_context(patch.object(macro_page.fcharts, "macro_z_chart",
                                              side_effect=lambda *a, **k: ft.Text("chart")))
        root = macro_page.build_macro_page(page())
        button(root, "Refresh").on_click(None)
        button(root, "Daily market commentary").on_click(None)
        button(root, "Weekly rates and FX note").on_click(None)
        self.assertEqual([kw["kind"] for kw in panels],
                         ["macro_sheet", "daily_market_commentary", "weekly_fi_fx_strategy"])
        for kw, tool, english in zip(panels, ("sheet", "daily", "weekly"),
                                     (fi.narrate_macro, fi.narrate_daily_brief, fi.narrate_weekly_strategy)):
            with self.subTest(tool=tool):
                self.assertEqual(kw["narrative"], english(sheet))
                out = SimpleNamespace(sheet=sheet, request=SimpleNamespace(tool=tool), narrative=kw["narrative"])
                self.assert_bilingual(kw, macro_ko.macro_korean(out))

    # ---------------------------------------------------------------- ETF, Crypto, Derivatives
    def test_etf_crypto_derivatives(self):
        etf = etf_workflow.analyze("122630", days=504, source="synthetic")
        crypto = crypto_workflow.analyze(source="synthetic")
        board = derivatives_workflow.snapshot(source="synthetic", n_paths=400)
        cases = ((etf_page, "analyze", etf, "Analyze", etf_workflow.narrative, mnl.etf_korean),
                 (crypto_page, "analyze", crypto, "Refresh", crypto_workflow.narrative, mnl.crypto_korean),
                 (derivatives_page, "snapshot", board, "Load", derivatives_workflow.narrative, mnl.derivatives_korean))
        for module, loader, data, label, english, korean in cases:
            with self.subTest(page=module.__name__):
                panels = self.capture(module)
                self.stack.enter_context(patch.object(module, loader, return_value=data))
                root = getattr(module, "build_" + module.__name__.split(".")[-1])(page())
                button(root, label).on_click(None)
                (kw,) = panels
                self.assertEqual(kw["narrative"], english(data))
                self.assert_bilingual(kw, korean(data))
                # the native app's own variant check accepts this narrative for this data
                kind = {"etf_page": "etf", "crypto_page": "crypto", "derivatives_page": "derivatives"}[
                    module.__name__.split(".")[-1]]
                self.assertEqual(mnl.market_variants(SimpleNamespace(narrative=kw["narrative"], data=data), kind)["ko"],
                                 korean(data))

    # ---------------------------------------------------------------- Signals, Structuring
    def test_signals(self):
        panels = self.capture(signals_page)
        self.stack.enter_context(patch.object(signals_page, "load_history",
                                              return_value=synthetic_history("AAPL", days=504)))
        spy = self.spy(signals_page, "signals_korean")
        root = signals_page.build_signals_page(page())
        button(root, "Analyze").on_click(None)
        (kw,) = panels
        report, bt = spy.call_args.args
        self.assertEqual(kw["narrative"], qi.narrate_signals(report) + " " + qi.narrate_backtest(bt))
        self.assert_bilingual(kw, model_ko.signals_korean(report, bt))

    def test_structuring_every_product(self):
        panels = self.capture(structuring_page)
        self.stack.enter_context(patch.object(structuring_page, "load_treasury_curve", return_value=self.panel))
        self.stack.enter_context(patch.object(structuring_page.fcharts, "payoff_chart",
                                              side_effect=lambda *a, **k: ft.Text("chart")))
        spy = self.spy(structuring_page, "structured_korean")
        root = structuring_page.build_structuring_page(page())
        products = ("ppn", "rc", "dcd", "steep")
        for product in products:
            dd = dropdown(root, "Product")
            dd.value = product
            dd.on_select(None)
            button(root, "Price").on_click(None)
        self.assertEqual(len(panels), len(products))
        for kw, call in zip(panels, spy.call_args_list):
            with self.subTest(product=call.args[0].product):
                self.assertEqual(kw["narrative"], fi.narrate_structured(call.args[0]))
                self.assert_bilingual(kw, model_ko.structured_korean(call.args[0]))

    # ---------------------------------------------------------------- not wired
    def test_quant_lab_has_no_native_korean_narrative_and_keeps_the_default(self):
        import inspect
        self.assertNotIn("sections=", inspect.getsource(quant_lab_page))
        self.assertFalse(any("monte" in name.lower() for name in dir(model_ko) + dir(mnl)))


if __name__ == "__main__":
    unittest.main()
