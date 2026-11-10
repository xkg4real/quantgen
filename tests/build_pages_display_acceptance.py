"""Owner UI review 2026-11-10, area F: Portfolio, Signals, Quant Lab, Settings, Execution, Rules.

Hermetic: no provider, store or network. Checks the three owner complaints this area fixes:
13 the Portfolio page must lay out (no `expand` child inside a wrapping row: Flutter paints a
grey box), 04/12 no visible data-source selector (the hidden one keeps a valid value and the
loads ask `source="best"`), and 14 Korean captions in ko_KR with English intact in en_US.
"""
from __future__ import annotations

from dataclasses import fields
from datetime import date, timedelta
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import dotenv
import flet as ft

with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.i18n import LocaleContext
    from core.quant.history import History
    from ui import portfolio_page, quant_lab_page, rules_page, settings_page, signals_page, trading_page
    from ui.build_widgets import localize_tree
    from ui.localization import translate_controls
    from tests.portfolio_scope_acceptance import output_fixture


def walk(value, seen=None):
    seen = set() if seen is None else seen
    if not isinstance(value, ft.Control) or id(value) in seen:
        return
    seen.add(id(value))
    yield value
    for f in fields(value):
        if f.name.startswith("_"):
            continue
        child = getattr(value, f.name)
        if isinstance(child, ft.Control):
            yield from walk(child, seen)
        elif isinstance(child, list):
            for item in child:
                yield from walk(item, seen)


def texts(root) -> list[str]:
    return [str(c.value) for c in walk(root) if isinstance(c, ft.Text) and c.value]


def captions(root) -> set[str]:
    out = set(texts(root))
    for c in walk(root):
        for name in ("label", "hint_text", "tooltip", "text"):
            v = getattr(c, name, None)
            if isinstance(v, str):
                out.add(v)
        if isinstance(c, ft.Button) and isinstance(c.content, str):
            out.add(c.content)
    return out


def expand_in_wrap(root) -> list[str]:
    bad = []
    for c in walk(root):
        if isinstance(c, (ft.Row, ft.Column)) and getattr(c, "wrap", False):
            for child in c.controls or []:
                if getattr(child, "expand", None) not in (None, False, 0):
                    bad.append(f"{type(child).__name__} label={getattr(child, 'label', None)!r}")
    return bad


def history(symbol="FIXTURE", n=320):
    dates = tuple((date(2025, 1, 1) + timedelta(days=i)).isoformat() for i in range(n))
    closes = tuple(100 + 10 * ((i % 40) / 40) + i * 0.05 for i in range(n))
    return History(symbol, "SYNTHETIC", dates, closes, note="Injected synthetic fixture")


def page():
    p = Mock()
    p.width = 1360
    p.qg_locale = LocaleContext("en_US")
    p.qg_theme = "light"
    p.run_thread.side_effect = lambda work: work()
    return p


def source_dropdown(root) -> ft.Dropdown:
    return next(c for c in walk(root) if isinstance(c, ft.Dropdown) and c.label == "Data source")


def button(root, label) -> ft.Button:
    return next(c for c in walk(root) if isinstance(c, ft.Button) and c.content == label)


def panel(_page, **kw):
    kw["payload_fn"]()
    return ft.Text("injected AI panel")


class BuildPagesDisplayTests(unittest.TestCase):
    def setUp(self):
        for target in ("socket.socket.connect", "requests.sessions.Session.request"):
            p = patch(target, side_effect=AssertionError("network forbidden"))
            p.start()
            self.addCleanup(p.stop)

    # ------------------------------------------------------------------ 13: Portfolio grey box
    def optimized_portfolio(self):
        out = output_fixture("max_sharpe", .5)
        with patch.object(portfolio_page, "load_history", side_effect=out.histories) as loader, \
             patch.object(portfolio_page, "align_histories", return_value=out.stats), \
             patch.object(portfolio_page, "convention_warning", return_value=""), \
             patch.object(portfolio_page, "analysis_panel", side_effect=panel):
            root = portfolio_page.build_portfolio_page(page())
            root.controls[1].controls[0].value = "ONE, TWO, THREE"
            root.controls[1].controls[3].value = "0.5"     # per-asset cap of the selected objective
            button(root, "Optimize").on_click(None)
        return root, loader

    def test_portfolio_lays_out_with_no_expand_inside_a_wrapping_row(self):
        root = portfolio_page.build_portfolio_page(page())
        self.assertEqual(expand_in_wrap(root), [])
        symbols = root.controls[1].controls[0]
        self.assertIsInstance(symbols, ft.TextField)
        self.assertFalse(symbols.expand)
        self.assertTrue(symbols.width)
        optimized, _ = self.optimized_portfolio()
        self.assertEqual(expand_in_wrap(optimized), [])
        found = texts(optimized)
        self.assertIn("Weights and risk contributions", found)
        self.assertIn("All four objectives compared", found)
        self.assertTrue(any(t.startswith("Largest weights:") for t in found))

    def test_every_owned_page_builds_without_expand_inside_wrap(self):
        from core.engine.feed import QuoteFeed
        from core.engine.runtime import EngineRuntime
        from core.rules.store import RuleStore
        from data.krx import KRXGateway
        import tempfile
        roots = [signals_page.build_signals_page(page()), quant_lab_page.build_quant_lab_page(page()),
                 settings_page.build_settings_page(page())]
        with tempfile.TemporaryDirectory() as tmp, patch("config.trading_dir", return_value=__import__("pathlib").Path(tmp)):
            store = RuleStore()
            roots.append(trading_page.build_trading_page(page(), EngineRuntime(store, QuoteFeed(KRXGateway()))))
            rules = rules_page.build_rules_page(page(), store)
            button(rules, "New rule").on_click(None)
            roots.append(rules)
            for root in roots:
                with self.subTest(root=type(root).__name__):
                    self.assertEqual(expand_in_wrap(root), [])

    # ------------------------------------------------------------------ 04/12: no visible source selector
    def test_source_selectors_are_hidden_valid_and_loads_ask_best(self):
        for build in (signals_page.build_signals_page, portfolio_page.build_portfolio_page,
                      quant_lab_page.build_quant_lab_page):
            with self.subTest(page=build.__name__):
                dd = source_dropdown(build(page()))
                keys = [o.key for o in dd.options]
                self.assertFalse(dd.visible)
                self.assertEqual(dd.value, "best")
                self.assertIn("best", keys)
                self.assertIn("synthetic", keys)       # tests and self-checks still pick it
                self.assertIn("auto", keys)
                self.assertEqual(next(o.text for o in dd.options if o.key == "best"), "Auto")
        self.assertEqual(LocaleContext("ko_KR").text("Auto"), "자동")

        _, loader = self.optimized_portfolio()
        self.assertTrue(loader.call_args_list)
        self.assertTrue(all(c.kwargs["source"] == "best" for c in loader.call_args_list))

        with patch.object(signals_page, "load_history", return_value=history()) as loader, \
             patch.object(signals_page, "analysis_panel", side_effect=panel):
            root = signals_page.build_signals_page(page())
            button(root, "Analyze").on_click(None)
        self.assertEqual(loader.call_args.kwargs["source"], "best")
        self.assertTrue(any(t.startswith("FIXTURE: SYNTHETIC") for t in texts(root)))   # provenance stays

        from tests.mc_bootstrap_disclosure_acceptance import result
        from core.research.runs import SessionResearch
        with patch.object(quant_lab_page, "session_for", return_value=SessionResearch()), \
             patch.object(quant_lab_page, "load_history", return_value=history()) as loader, \
             patch.object(quant_lab_page, "run_monte_carlo", return_value=result("gbm")) as mc, \
             patch.object(quant_lab_page, "_lab_grade", return_value=None), \
             patch.object(quant_lab_page, "analysis_panel", side_effect=panel):
            root = quant_lab_page.build_quant_lab_page(page())
            inputs = root.controls[1].controls
            inputs[3].value = "zero"                      # no risk-free fetch
            self.assertEqual(inputs[6].value, "5,000")    # paths read with a thousands separator
            button(root, "Simulate").on_click(None)
        self.assertEqual(loader.call_args.kwargs["source"], "best")
        self.assertEqual(mc.call_args.kwargs["n_paths"], 5000)

    # ------------------------------------------------------------------ 14: Korean captions
    def test_key_captions_are_korean_in_ko_and_english_in_en(self):
        expected = {
            signals_page.build_signals_page: {"Analyze": "분석 실행", "Backtest strategy": "백테스트 전략",
                                              "Fast/lookback": "단기·관찰 기간", "Cost (bps)": "거래비용 (bp)",
                                              "Signals": "기술적 분석"},
            portfolio_page.build_portfolio_page: {"Optimize": "최적화 실행",
                                                  "Symbols (comma separated)": "종목 (쉼표로 구분)",
                                                  "Max weight/asset": "종목당 최대 비중 (0~1)",
                                                  "Risk-free %": "무위험 금리 (%)", "Max Sharpe": "샤프 지수 최대화"},
            quant_lab_page.build_quant_lab_page: {"Simulate": "모의실험 실행", "Horizon (sessions)": "기간 (거래일)",
                                                  "Target price (optional)": "목표 가격 (선택)"},
            settings_page.build_settings_page: {"Quant analysis providers": "분석용 데이터 제공자",
                                                "Test FICC data access": "FICC 데이터 연결 확인"},
        }
        for build, pairs in expected.items():
            with self.subTest(page=build.__name__):
                root = build(page())
                translate_controls(root, LocaleContext("ko_KR"))
                ko = captions(root)
                for english, korean in pairs.items():
                    self.assertIn(korean, ko, english)
                    self.assertNotIn(english, ko)
                translate_controls(root, LocaleContext("en_US"))
                en = captions(root)
                for english in pairs:
                    self.assertIn(english, en)

    def test_result_sentences_switch_language_and_keep_codes(self):
        root, _ = self.optimized_portfolio()
        translate_controls(root, LocaleContext("ko_KR"))
        ko = texts(root)
        self.assertTrue(any(t.startswith("비중이 큰 종목은") for t in ko))
        self.assertTrue(any("선택한 목적함수(샤프 지수 최대화)의 종목당 상한은 50.00%" in t for t in ko))
        self.assertIn("50.00%", ko)                      # the cap column in the comparison table
        translate_controls(root, LocaleContext("en_US"))
        en = texts(root)
        self.assertTrue(any(t.startswith("Selected max_sharpe: per-asset cap 50.00%.") for t in en))
        self.assertFalse(any("비중이 큰 종목은" in t for t in en))

        from tests.macro_ui_views import texts as flat_texts
        from ui.quant_lab_page import _grade_blocks, _lab_grade
        blocks = ft.Column(_grade_blocks(_lab_grade("SPY")))
        translate_controls(blocks, LocaleContext("ko_KR"))
        found = flat_texts([blocks])
        self.assertIn("M9 검증 관문: 불합격 · FAIL", found)          # the code stays visible
        self.assertTrue(any(t.startswith("Kupiec 99% VaR: 통과 · PASS") for t in found))

    def test_execution_and_rules_sentences_with_numbers(self):
        from core.rules import Comparator, OrderKind, PriceCondition, Rule, Side, SizeMode
        from decimal import Decimal
        rule = Rule(name="r", symbol="005930", side=Side.BUY, size_mode=SizeMode.QUANTITY,
                    size_value=Decimal(10), order_kind=OrderKind.LIMIT, limit_price=Decimal(70000),
                    conditions=(PriceCondition(Comparator.AT_OR_BELOW, Decimal(70000)),))
        self.assertEqual(rules_page._summary_ko(rule),
                         "005930: 현재가가 70,000 이하일 때, 70,000 지정가 주문으로 10주를 매수합니다.")
        self.assertIn("70,000", rule.summary())
        box = ft.Column([ft.Text("Evaluating every 5s · last pass 10:00:00"), ft.Text("DISARMED"),
                         ft.Text("of 3 saved"), ft.Text("Exchange calendar data runs out in 12 days (KRX first). "
                                                        "Regenerate with pkg_tools/generate_calendars.py.")])
        localize_tree(box, trading_page.TRADING_KO)
        translate_controls(box, LocaleContext("ko_KR"))
        self.assertEqual(texts(box)[:3], ["5초마다 평가 · 마지막 평가 10:00:00", "작동 해제 · DISARMED", "저장된 규칙 3개 중"])
        self.assertTrue(texts(box)[3].startswith("거래소 휴장일 자료가 12일 뒤 끝납니다"))
        translate_controls(box, LocaleContext("en_US"))
        self.assertEqual(texts(box)[1], "DISARMED")


if __name__ == "__main__":
    unittest.main()
