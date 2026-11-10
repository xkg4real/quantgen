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
                                                  "Risk-free %": "무위험 금리 (%)", "Max Sharpe": "최대 샤프 지수"},
            quant_lab_page.build_quant_lab_page: {"Simulate": "모의실험 실행", "Horizon (sessions)": "기간 (거래일)",
                                                  "Target price (optional)": "목표 가격 (선택)"},
            settings_page.build_settings_page: {"Quant analysis providers": "분석용 데이터 제공처",
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
        self.assertTrue(any("선택한 목적함수(최대 샤프 지수)의 종목당 상한은 50.00%" in t for t in ko))
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
        self.assertIn("M9 검증 게이트: 미달 · FAIL", found)          # the code stays visible
        self.assertTrue(any(t.startswith("Kupiec 99% VaR: 통과 · PASS") for t in found))

    # ------------------------------------------------------------------ review findings, 2026-11-10 (second pass)
    def quant_lab_run(self, hist):
        from tests.mc_bootstrap_disclosure_acceptance import result
        from core.research.runs import SessionResearch
        with patch.object(quant_lab_page, "session_for", return_value=SessionResearch()), \
             patch.object(quant_lab_page, "load_history", return_value=hist), \
             patch.object(quant_lab_page, "run_monte_carlo", return_value=result("gbm")), \
             patch.object(quant_lab_page, "_lab_grade", return_value=None), \
             patch.object(quant_lab_page, "analysis_panel", side_effect=panel):
            root = quant_lab_page.build_quant_lab_page(page())
            root.controls[1].controls[3].value = "zero"
            button(root, "Simulate").on_click(None)
        return root

    def signals_run(self, hist):
        with patch.object(signals_page, "load_history", return_value=hist), \
             patch.object(signals_page, "analysis_panel", side_effect=panel):
            root = signals_page.build_signals_page(page())
            button(root, "Analyze").on_click(None)
        return root

    def test_synthetic_notices_keep_the_provider_message_one_keyboard_step_away(self):
        """Finding 2: the cause in both languages, the provider's own message in an ExpansionTile."""
        from ui.build_widgets import SYNTHETIC_CAUSE_EN, SYNTHETIC_CAUSE_KO
        portfolio, _ = self.optimized_portfolio()
        for name, root, note in (("signals", self.signals_run(history()), "Injected synthetic fixture"),
                                 ("quant_lab", self.quant_lab_run(history()), "Injected synthetic fixture"),
                                 ("portfolio", portfolio, None)):
            with self.subTest(page=name):
                tiles = [c for c in walk(root) if isinstance(c, ft.ExpansionTile)
                         and "Provider message" in str(getattr(c.title, "value", ""))]
                self.assertEqual(len(tiles), 1)
                folded = texts(ft.Column(tiles[0].controls))
                self.assertTrue(folded and all(t.strip() for t in folded))
                if note:
                    self.assertEqual(folded, [note])
                banner = next(c for c in walk(root) if isinstance(c, ft.Column) and tiles[0] in c.controls)
                self.assertFalse(any(getattr(c, "tooltip", None) for c in walk(banner)))   # not hover-only
                translate_controls(root, LocaleContext("ko_KR"))
                self.assertTrue(any(SYNTHETIC_CAUSE_KO in t for t in texts(root)))
                self.assertIn("제공처 메시지 (시뮬레이션 데이터로 계산한 이유)", texts(root))
                translate_controls(root, LocaleContext("en_US"))
                self.assertTrue(any(SYNTHETIC_CAUSE_EN in t for t in texts(root)))
                self.assertFalse(any("마우스" in t for t in texts(root)))

    def test_signals_summary_is_neutral_about_the_comparison_and_states_its_period(self):
        """Finding 3: beating buy-and-hold is not a gain; the period and the one-backtest caveat show."""
        from dataclasses import replace
        from core.quant.backtest import run_backtest
        from core.quant.signals import compute_signals
        from ui.components import colour_for
        hist = history()
        report = compute_signals(hist)
        real = run_backtest(hist, strategy="ma_cross", params={"fast": 20, "slow": 50}, cost_bps=10)
        for total, bench, token in ((-0.05, -0.10, "error"), (0.08, 0.12, "success"), (0.0, -0.01, "text")):
            with self.subTest(total=total, bench=bench):
                bt = replace(real, total_return=total, bench_return=bench)
                card_ = signals_page._summary(report, bt, hist)
                chips = [c for c in walk(card_) if isinstance(c, ft.Container) and isinstance(c.content, ft.Text)
                         and c.content.value in ("beats buy & hold", "trails buy & hold")]
                self.assertEqual(len(chips), 1)
                self.assertEqual(chips[0].border.top.color, colour_for("muted"))
                values = texts(card_)
                tile = next(c for c in walk(card_) if isinstance(c, ft.Column) and c.controls
                            and getattr(c.controls[0], "value", None) == "Strategy return")
                self.assertEqual(tile.controls[1].color, colour_for(token))
                self.assertIn(f"Period: {hist.first_date} to {hist.last_date}. One historical backtest; not a "
                              "statistical test or out-of-sample validation.", values)
                translate_controls(card_, LocaleContext("ko_KR"))
                self.assertIn(f"기간: {hist.first_date} ~ {hist.last_date}. 한 구간의 과거 백테스트이며 통계 검정이나 "
                              "표본 외 검증이 아닙니다.", texts(card_))

    def test_portfolio_scope_sentence_is_conditional_and_names_the_objectives_in_korean(self):
        """Findings 6 and 7."""
        out = output_fixture("max_sharpe", 1.0)
        ko = portfolio_page._scope_ko(out.portfolios, "max_sharpe")
        self.assertIn("상한이 서로 다르면 효율적 프런티어와 같은 조건의 비교가 아닙니다.", ko)
        self.assertNotIn("다르므로", ko)
        self.assertNotIn("투자선", ko)
        root = portfolio_page.build_portfolio_page(page())
        translate_controls(root, LocaleContext("ko_KR"))
        options = [o.text for o in next(c for c in walk(root) if isinstance(c, ft.Dropdown)
                                         and c.label == "목적함수").options]
        self.assertEqual(options, ["최대 샤프 지수", "최소 변동성", "리스크 패리티(위험 균등)", "동일 비중"])
        ko_text = LocaleContext("ko_KR").text
        self.assertEqual(ko_text("Efficient frontier"), "효율적 프런티어")
        optimized, _ = self.optimized_portfolio()
        translate_controls(optimized, LocaleContext("ko_KR"))
        shown = texts(optimized)
        self.assertIn("최대 샤프 지수 포트폴리오", shown)
        for name in ("최대 샤프 지수", "최소 변동성", "리스크 패리티(위험 균등)", "동일 비중"):
            self.assertIn(name, shown)                     # the comparison table

    def test_vocabulary_provider_gate_verdicts_and_igarch(self):
        """Findings 8, 9 and 11."""
        from core.ui_page_messages import build_pages
        from ui.build_widgets import SYNTHETIC_CAUSE_KO
        for word in ("제공자", "공급사", "제공업체", "관문"):
            self.assertFalse([k for k, v in build_pages.EN_TO_KO.items() if word in v], word)
            for module in (signals_page, portfolio_page, quant_lab_page, settings_page):
                self.assertNotIn(word, __import__("inspect").getsource(module), (word, module.__name__))
        self.assertIn("제공처", SYNTHETIC_CAUSE_KO)
        self.assertEqual(quant_lab_page._WORD_KO, {"PASS": "통과 · PASS", "FAIL": "미달 · FAIL",
                                                   "NOT RUN": "미실행 · NOT_RUN"})
        self.assertEqual(quant_lab_page._DECISION_KO["INSUFFICIENT_DATA"], "데이터 부족 · INSUFFICIENT_DATA")
        ko_text = LocaleContext("ko_KR").text
        self.assertEqual(ko_text("an integrated variance is not excluded at 95%: the sample cannot pin down where "
                                 "vol settles"),
                         "95% 수준에서 지속성 1(충격이 사라지지 않는 IGARCH형 분산)을 배제할 수 없습니다. "
                         "이 표본으로는 변동성이 결국 어디에 자리 잡을지 정할 수 없습니다")
        self.assertIn("게이트", ko_text("SMOKE · vendor data, not an official close, not a card run · gates nothing"))

    def test_kis_probe_says_key_not_set_without_a_request_and_shows_details(self):
        """Finding 10: no key is not a failed check; every detail is visible text, not a tooltip."""
        unavailable = {"ok": False, "detail": "KISUnavailable: Set KIS_APP_KEY and KIS_APP_SECRET to enable KIS"}
        cases = (
            ({"etf": unavailable, "bonds": unavailable},
             ["KIS: 키 미설정 (요청을 보내지 않음)"], ["KIS: Key not set (no request sent)"]),
            ({"etf": {"ok": True, "detail": "10450.2"}, "bonds": {"ok": False, "detail": "KISError: HTTP 500"}},
             ["ETF: 정상", "장내 채권: 확인 실패"], ["ETF: ok", "Bonds: Check failed"]),
        )
        for probe, ko_chips, en_chips in cases:
            with self.subTest(probe=list(probe)), patch("data.kis_markets.KISMarkets") as kis:
                kis.return_value.probe.return_value = probe
                root = settings_page.build_settings_page(page())
                button(root, "Test KIS asset domains").on_click(None)
                host = next(c for c in walk(root) if isinstance(c, ft.Row)
                            and any("KIS" in str(getattr(t, "value", "")) or "ETF" in str(getattr(t, "value", ""))
                                    for t in walk(c) if isinstance(t, ft.Text)) and c.wrap)
                translate_controls(host, LocaleContext("ko_KR"))
                shown = texts(host)
                for label in ko_chips:
                    self.assertIn(label, shown)
                details = {r["detail"] for r in probe.values()}
                for detail in details:                                 # visible, not hover-only
                    self.assertIn(LocaleContext("ko_KR").text(detail), shown)
                self.assertFalse(any(getattr(c, "tooltip", None) for c in walk(host)))
                translate_controls(host, LocaleContext("en_US"))
                for text in en_chips + sorted(details):
                    self.assertIn(text, texts(host))

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
