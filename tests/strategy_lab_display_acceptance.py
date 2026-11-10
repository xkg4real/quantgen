"""Strategy Lab display (owner UI review 2026-11-10): every study card reads in plain Korean and English,
no raw field name reaches the screen, pass/fail marks follow validate.GATE, and the run result leads with a
verdict. Synthetic inputs only: no network, no ledger, no Anthropic call."""
from datetime import date, timedelta
from functools import lru_cache
import json
from pathlib import Path
import re
import unittest
from unittest.mock import Mock, patch

import dotenv
import flet as ft
import numpy as np

with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.quant.history import History
    from core.research import strategy_workflow as flow
    from core.research import strategy_display as D
    from ui import strategy_lab_page as page_module
    from ui import ai_panel as panel_module
from core.i18n import LocaleContext
from core.quant import validate as V
from core.research.strategy_exposure import EXPOSURE_HELP, exposure_lines
from ui.localization import translate_controls

ROOT = Path(__file__).resolve().parents[1]
CARD_FILES = sorted((ROOT / "docs" / "asset_expansion" / "cards").glob("*.json"))
HANGUL = re.compile(r"[가-힣]")
RAW_KEY = re.compile(r"[A-Za-z0-9]+_[A-Za-z0-9_]+")       # snake_case field names such as kupiec95_p or cc_p


def walk(c, seen=None):
    seen = set() if seen is None else seen
    if not isinstance(c, ft.Control) or id(c) in seen:
        return
    seen.add(id(c))
    yield c
    for name in ("controls", "content", "title", "leading", "label", "options"):
        v = getattr(c, name, None)
        for child in (v if isinstance(v, (list, tuple)) else [v]):
            yield from walk(child, seen)


def texts(root) -> list[str]:
    return [str(c.value) for c in walk(root) if isinstance(c, ft.Text) and c.value]


@lru_cache
def fixture(family="trend_switch", cost=None):
    symbols = ("SPY", "QQQ", "TLT")
    rng = np.random.default_rng(1107)
    prices = 100 * np.exp(np.vstack([np.zeros(3), np.cumsum(rng.normal(.0004, .01, (1499, 3)), axis=0)]))
    dates = tuple((date(2020, 1, 1) + timedelta(days=i)).isoformat() for i in range(len(prices)))

    def loader(symbol, **kw):
        return History(symbol, "SYNTHETIC", dates, tuple(prices[:, symbols.index(symbol)]), note="synthetic fixture")
    with patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden")), \
         patch("core.quant.gate_ledger.family_ledger", side_effect=AssertionError("ledger forbidden")):
        return flow.run_family(family, list(symbols), history_loader=loader, source="synthetic", cost_bps=cost,
                               bootstrap_B=40)


class CardCatalogueTests(unittest.TestCase):
    def setUp(self):
        self.cards = [flow._study_card(json.loads(p.read_text(encoding="utf-8"))) for p in CARD_FILES]

    def test_every_card_file_has_a_reviewed_display_entry(self):
        self.assertEqual(len(CARD_FILES), 34)
        ids = {c["card_id"] for c in self.cards}
        self.assertEqual(ids - set(D.CARDS), set(), "a card file without a display entry")
        self.assertEqual(set(D.CARDS) - ids, set(), "a display entry without a card file")

    def test_names_reasons_and_numbers_are_plain_in_both_languages(self):
        for c in self.cards:
            with self.subTest(card=c["card_id"]):
                t = D.card_text(c)
                (reason, _) = D.reason_text(c["decision_reason"], c)
                for ko in (t.name[0], t.what[0], reason[0], D.kind_label(c["kind"])[0]):
                    self.assertRegex(ko, HANGUL)
                for en in (t.name[1], t.what[1], reason[1], D.kind_label(c["kind"])[1]):
                    self.assertNotRegex(en, HANGUL)
                self.assertNotEqual(reason[0], c["decision_reason"], "the recorded reason is rendered, not echoed")
                for language in ("ko", "en"):
                    shown = " ".join([D.pick(t.name, language), D.pick(reason, language),
                                      D.key_numbers(c, language)])
                    self.assertIsNone(RAW_KEY.search(shown), (language, shown))
                    self.assertNotIn("nan", shown.lower().split())
                target = D.revise_target_text(c.get("revise_target"))
                if target:
                    self.assertRegex(target[0], HANGUL)
                ko_verdict, en_verdict = D.verdict_label(c["decision"])
                self.assertIn(c["decision"], ko_verdict, "the verdict code stays visible next to its meaning")
                self.assertEqual(en_verdict, c["decision"])

    def test_unknown_cards_and_reasons_fall_back_to_the_recorded_wording(self):
        odd = flow._study_card({"card_id": "FUTURE_X", "decision": "PASS", "kind": "strategy", "hypothesis": "h",
                                "decision_reason": "a new reason", "stats": {"sr_oos": 1.0}})
        self.assertEqual(D.card_text(odd).name, ("FUTURE_X", "FUTURE_X"))
        self.assertEqual(D.reason_text("a new reason")[0], ("a new reason", "a new reason"))
        self.assertIn("1.00", D.key_numbers(odd, "ko"))
        foreign = flow._study_card({"card_id": "MACRO-R06-KR-ETF", "class": "CARD-P", "verdict": "PASS"})
        self.assertEqual(D.verdict_label(foreign["decision"]), ("판정 없음 · UNKNOWN", "UNKNOWN"))

    def test_checklist_agrees_with_every_recorded_strategy_verdict(self):
        """Pass/fail marks come from the card's own fields and validate.GATE, never from parsing its text."""
        linked = {"deflated Sharpe below 0.95": "dsr", "execution check failed (execution)": "stress"}
        for c in self.cards:
            if not isinstance(c["stats"].get("sr_oos"), float):
                continue
            with self.subTest(card=c["card_id"]):
                checks = {k.key: k for k in D.strategy_checks({**c["stats"], "ci90": c["tests"].get("ci90")})}
                gated = [k for k in checks.values() if k.gated]
                if c["decision"] == "PASS":
                    self.assertTrue(all(k.status == "pass" for k in gated), [(k.key, k.status) for k in gated])
                elif c["decision_reason"].startswith("does not beat its benchmark"):
                    self.assertEqual(checks["bench"].status, "fail")
                elif c["decision_reason"] in linked:
                    self.assertEqual(checks[linked[c["decision_reason"]]].status, "fail")
                self.assertEqual(checks["dsr"].threshold[1], f"≥ {V.GATE['dsr_min']}")


class RunResultTests(unittest.TestCase):
    def test_verdict_banner_reasons_and_tiles_from_score_fields(self):
        r = fixture()
        v = D.run_verdict(r)
        sc = r["score"]
        self.assertEqual(v["code"], sc.decision)
        # a synthetic run says so in the banner title itself and in its first reason
        title = D.VERDICT_TITLE[sc.decision]
        self.assertEqual(v["title"], ("연습용 판정(합성 데이터) · " + title[0],
                                      "Practice verdict (synthetic data) · " + title[1]))
        self.assertEqual(v["reasons"][0], ("이 판정은 합성(가상) 데이터로 계산한 연습용이며 실제 시장 결과가 아닙니다.",
                                           "This verdict is computed on synthetic data: a toy, not a market result."))
        self.assertTrue(1 <= len(v["reasons"]) - 1 <= 3, "1-3 decisive reasons after the synthetic qualifier")
        by_key = {c.key: c for c in v["checks"]}
        self.assertEqual(by_key["dsr"].status, "pass" if sc.dsr >= V.GATE["dsr_min"] else "fail")
        self.assertEqual(by_key["interval"].status, "pass" if sc.ci90[0] > 0 else "fail")
        self.assertEqual(by_key["trades"].value, f"{sc.n_trades:,}")
        self.assertEqual(by_key["mdd"].status, "info")

    def test_withheld_run_shows_no_verdict_and_keeps_the_recorded_sentence(self):
        r = fixture(cost=1.0)
        v = D.run_verdict(r)
        self.assertEqual((v["code"], v["decision"]), ("NO VERDICT", "WITHHELD"))
        self.assertEqual(v["reasons"][0][0], "이 실행은 합성(가상) 데이터로 계산한 연습용이며 실제 시장 결과가 아닙니다.")
        self.assertTrue(v["title"][0].startswith("연습용 실행(합성 데이터) · 판정 없음"))
        self.assertEqual(v["reasons"][1][1], r["withheld"])
        self.assertRegex(v["reasons"][1][0], HANGUL)
        self.assertNotIn(r["score"].decision, " ".join(D.pick(x, "en") for x in v["reasons"]))

    def test_sections_are_presentation_only(self):
        r = fixture("vol_target")
        before = (flow.narrative(r), json.dumps(flow.payload(r), default=str, sort_keys=True))
        ko = flow.narrative_sections(r, "ko")
        en = flow.narrative_sections(r, "en")
        self.assertEqual([h for h, _ in ko], ["결론", "데이터와 설정", "검증 결과", "위험과 참고"])
        self.assertEqual([h for h, _ in en], ["Conclusion", "Data and setup", "Validation results", "Risks and notes"])
        self.assertEqual(before, (flow.narrative(r), json.dumps(flow.payload(r), default=str, sort_keys=True)))
        risks_en = en[3][1]
        for line in exposure_lines(r["exposure"]):
            self.assertIn(line, risks_en)
        self.assertEqual(len(D.exposure_lines_ko(r["exposure"])), len(exposure_lines(r["exposure"])))
        self.assertTrue(all(HANGUL.search(x) for _, items in ko for x in items if not x.startswith(("SPY", "QQQ"))))

    def test_lab_sections_omit_the_criteria_and_do_not_restate_the_banner(self):
        r = fixture()
        v = D.run_verdict(r)
        for language, heads in (("ko", ["결론", "데이터와 설정", "위험과 참고"]),
                                ("en", ["Conclusion", "Data and setup", "Risks and notes"])):
            with self.subTest(language=language):
                lab = flow.narrative_sections(r, language, include_results=False)
                self.assertEqual([h for h, _ in lab], heads)
                conclusion = lab[0][1]
                self.assertTrue(conclusion)
                banner = [D.pick(v["title"], language)] + [D.pick(x, language) for x in v["reasons"]]
                if v["next"]:
                    banner.append(D.pick(v["next"], language))
                for line in conclusion:
                    for said in banner:
                        self.assertNotIn(said, line, "the conclusion adds meaning, it does not repeat the banner")
                self.assertIn(v["code"], " ".join(conclusion))
                full = flow.narrative_sections(r, language)
                self.assertEqual(len(full), 4, "other callers keep the validation-results section")

    def test_setup_lines_name_parameters_in_words(self):
        self.assertEqual(D.param_text("rule", "tsmom"), ("시계열 모멘텀(MOP 부호)", "time-series momentum (MOP sign)"))
        self.assertEqual(D.param_text("lookback", 126), ("126거래일", "126 sessions"))
        self.assertEqual(D.param_text("target", 0.1), ("10%", "10%"))
        self.assertEqual(D.param_text("top", 1 / 3), ("1/3", "1/3"))
        self.assertEqual(D.param_text("long_only", False), ("매수·매도", "long and short"))
        for family in ("trend_switch", "vol_target"):
            r = fixture(family)
            data = dict(flow.narrative_sections(r, "ko"))["데이터와 설정"]
            setup = next(x for x in data if x.startswith("마지막 학습 구간의 최적 설정"))
            for raw in ("tsmom", "sma", "True", "False", "0.333"):
                self.assertNotIn(raw, setup.split(": ", 1)[1])
            walk = next(x for x in data if x.startswith("워크포워드"))
            self.assertRegex(walk, r"학습 \d+거래일 · 검증 \d+거래일 · 간격 \d+거래일")

    def test_pass_banner_states_the_haircut_and_the_family_ledger(self):
        from dataclasses import replace
        r = fixture()
        passed = dict(r, score=replace(r["score"], decision="PASS", reason="every gate criterion met",
                                       revise_target=None), sources=["YFINANCE"] * 3, ledger_n=1240)
        v = D.run_verdict(passed)
        self.assertEqual(v["title"], D.VERDICT_TITLE["PASS"], "no practice qualifier on market data")
        ko = [x[0] for x in v["reasons"]]
        self.assertTrue(any("할인 적용 샤프" in x and "참고값" in x for x in ko))
        self.assertIn(f"보정 샤프는 이번 실행의 설정 {len(r['grid'])}개만 셉니다. 이 계열에서 지금까지 시험한 설정은 "
                      "1,240개입니다.", ko)
        self.assertEqual(len(D.run_verdict(dict(passed, ledger_n=len(r["grid"])))["reasons"]), 2)
        haircut = next(c for c in v["checks"] if c.key == "haircut")
        self.assertEqual(haircut.label, (f"할인 적용 샤프 (참고값, 표본 외 × {V.GATE['haircut']})",
                                         f"Haircut Sharpe (reference, OOS × {V.GATE['haircut']})"))
        self.assertIn("McLean–Pontiff 2016", haircut.help[0])
        self.assertIn("예측치가 아닙니다", haircut.help[0])
        self.assertEqual(D.VERDICT_TITLE["INSUFFICIENT_DATA"][0], "데이터 부족: 데이터가 부족해 결론을 낼 수 없습니다")

    def test_funding_reason_matches_its_card(self):
        card = next(json.loads(p.read_text(encoding="utf-8")) for p in CARD_FILES if p.stem == "M_C4_funding")
        (reason, _) = D.reason_text(card["decision_reason"], card)
        self.assertIn("부트스트랩 p < 0.05", reason[0])
        self.assertLess(card["tests"]["bootstrap_p"], 0.05, "the sentence claims p < 0.05")
        self.assertLess(card["stats"]["top_decile_fwd30"], card["stats"]["bottom_decile_fwd30"])


class PageTests(unittest.TestCase):
    def build(self, r=None, locale=None):
        page = Mock()
        page.run_thread.side_effect = lambda work: work()
        page.run_task.side_effect = AssertionError("no async work while building or running")
        if locale:
            page.qg_locale = LocaleContext(locale)
        captured = {}

        def panel(page, **kw):
            captured.update(kw)
            return ft.Text("analysis panel fixture")
        with patch.object(page_module, "analysis_panel", side_effect=panel), \
             patch.object(page_module, "run_family", return_value=r or fixture()):
            root = page_module.build_strategy_lab_page(page)
            if r is not False:
                next(c for c in walk(root) if isinstance(c, ft.Button) and c.content == "Run").on_click(None)
        return root, captured

    def test_source_selector_is_hidden_and_the_run_asks_for_best(self):
        root, _ = self.build(r=False)
        source = next(c for c in walk(root) if isinstance(c, ft.Dropdown) and c.label == "Source")
        self.assertFalse(source.visible)
        self.assertEqual(source.value, "best")
        self.assertTrue({"best", "auto", "synthetic"} <= {o.key for o in source.options})
        with patch.object(page_module, "_run_family", return_value=fixture()) as run:
            page_module.run_family("trend_switch", ["SPY"])
        self.assertEqual(run.call_args.kwargs["source"], "best")

    def test_korean_page_reads_without_raw_keys_and_keeps_verdict_codes(self):
        root, captured = self.build(locale="ko_KR")
        translate_controls(root, LocaleContext("ko_KR"))
        shown = texts(root)
        joined = "\n".join(shown)
        for code in ("PASS", "REVISE", "REJECT"):
            self.assertIn(code, joined)
        for raw in ("kupiec95_p", "cc_p", "bootstrap_p", "theo_gap_pts", "distribution", "every gate criterion met"):
            self.assertNotIn(raw, joined)
        for caption in ("전략 실험실", "검증 결과 요약", "카드별 결과", "직접 검증해 보기", "전략 종류", "종목 (쉼표로 구분)"):
            self.assertIn(caption, joined + "\n" + "\n".join(str(c.label) for c in walk(root)
                                                             if isinstance(c, (ft.TextField, ft.Dropdown))))
        self.assertIn(D.VERDICT_TITLE[fixture()["score"].decision][0], joined)
        picker = next(c for c in walk(root) if isinstance(c, ft.Dropdown) and c.label == "검증 카드 선택")
        self.assertIn("BTC 무기한선물 펀딩비 신호 — 통과 · PASS", [o.text for o in picker.options])
        self.assertIn("M_C4_funding", picker.value)
        # the full disclosures stay available (expandables), and the analysis gets organised sections
        self.assertTrue(any(EXPOSURE_HELP in t or "변동성 목표와 가상자산 추세 전략은 자산마다" in t for t in shown))
        for line in fixture()["score"].lines:
            self.assertIn(line, joined)
        self.assertEqual(captured["kind"], "strategy_gate")
        self.assertEqual(captured["narrative"], flow.narrative(fixture()))
        self.assertEqual(captured["sections"](LocaleContext("ko_KR"))[0][0], "결론")
        translate_controls(root, LocaleContext("en_US"))
        joined_en = "\n".join(texts(root))
        self.assertIn(D.VERDICT_TITLE[fixture()["score"].decision][1], joined_en)
        self.assertNotRegex(joined_en, r"검증 결과 요약|카드별 결과|직접 검증해 보기")

    def test_run_result_reads_once_with_four_equal_tiles(self):
        with patch.object(page_module.xc, "equity_chart", wraps=page_module.xc.equity_chart) as chart:
            root, captured = self.build(locale="ko_KR")
        translate_controls(root, LocaleContext("ko_KR"))
        shown = texts(root)
        joined = "\n".join(shown)
        # the synthetic notice comes before the banner, and the banner title carries the qualifier
        notice_at = next(i for i, t in enumerate(shown) if t.startswith("합성(가상) 데이터가 포함되어 있습니다. 이 판정은"))
        title_at = next(i for i, t in enumerate(shown) if t.startswith("연습용 판정(합성 데이터) · "))
        self.assertLess(notice_at, title_at)
        # four headline tiles of one fixed height; every criterion stays in the checklist
        tiles = [c for c in walk(root) if isinstance(c, ft.Container) and c.height == page_module._TILE_HEIGHT]
        self.assertEqual(len(tiles), 4)
        labels = [texts(t)[0] for t in tiles]
        self.assertEqual(labels, ["표본 외 샤프 지수", "보정 샤프(DSR)", "벤치마크 대비 샤프 차이", "최대 낙폭"])
        self.assertTrue(all(t.tooltip for t in tiles), "each tile explains itself")
        for c in D.run_verdict(fixture())["checks"]:
            self.assertIn(c.label[0], joined)
        self.assertEqual([h for h, _ in captured["sections"](LocaleContext("ko_KR"))],
                         ["결론", "데이터와 설정", "위험과 참고"])
        self.assertEqual(chart.call_args.kwargs["title_ko"], "추세 전환 (Faber 이동평균 / MOP 부호): 표본 외(OOS) 누적 성과")
        # the offer policy is a visible line, and the agreed vocabulary is used
        self.assertTrue(any(t.startswith("통과 · PASS는 기본으로 제공하고") for t in shown))
        for word in ("암호화폐", "모델 카드", "· 코인 ", "수익 신뢰구간", "판단 보류", "섞여 있습니다", "아래 판정"):
            self.assertNotIn(word, joined)
        self.assertIn("가상자산 BTC-USD, KRW-BTC", joined)

    def test_scorecard_korean_wraps_between_words_only(self):
        root, _ = self.build(r=False, locale="ko_KR")
        translate_controls(root, LocaleContext("ko_KR"))
        joined = [t for t in texts(root) if page_module.WORD_JOINER in t]
        cards = [flow._study_card(json.loads(p.read_text(encoding="utf-8"))) for p in CARD_FILES]
        reasons = {D.reason_text(c["decision_reason"], c)[0][0] for c in cards}
        names = {D.card_text(c).name[0] for c in cards}
        plain = {t.replace(page_module.WORD_JOINER, "") for t in joined}
        self.assertEqual(reasons | names, plain, "only the scorecard's names and reasons, characters unchanged")
        for t in joined:
            self.assertIsNone(re.search(r"[가-힣][^\s⁠]|[^\s⁠][가-힣]", t), t)

    def test_summary_tiles_count_every_verdict(self):
        root, _ = self.build(r=False)
        shown = texts(root)
        counts = {}
        for p in CARD_FILES:
            d = json.loads(p.read_text(encoding="utf-8")).get("decision")
            counts[d] = counts.get(d, 0) + 1
        for code, n in counts.items():
            self.assertIn(str(n), shown)
            self.assertIn(code, shown)
        self.assertTrue(any(t.startswith("v2 macro model cards (CARD-O / CARD-P) are under Macro → Model cards")
                            for t in shown))


class AnalysisPanelTests(unittest.TestCase):
    def test_narrative_becomes_bullets_without_losing_text(self):
        narrative = "First sentence with 0.72 inside. Second one (p 0.10). Third: done."
        page = Mock()
        with patch.object(panel_module.insights, "ai_ready", return_value=False):
            panel = panel_module.analysis_panel(page, kind="portfolio", narrative=narrative, payload_fn=dict)
        block = panel.content.controls[1]
        self.assertEqual(block.value, narrative)
        self.assertEqual(panel_module.split_sentences(narrative),
                         ["First sentence with 0.72 inside.", "Second one (p 0.10).", "Third: done."])
        shown = texts(block)
        for s in panel_module.split_sentences(narrative):
            self.assertIn(s, shown)
        self.assertIn(narrative, shown, "the whole paragraph stays available, selectable as one piece")
        single = panel_module.analysis_panel(page, kind="portfolio", narrative="One line.", payload_fn=dict)
        self.assertEqual(single.content.controls[1].controls[0].value, "One line.")

    def test_sections_follow_the_language_and_chrome_is_translated(self):
        calls = []

        def sections(ctx):
            calls.append(ctx.language)
            return [("결론" if ctx.language == "ko" else "Conclusion", ["a", "b"])]
        page = Mock()
        page.qg_locale = LocaleContext("en_US")
        with patch.object(panel_module.insights, "ai_ready", return_value=False):
            panel = panel_module.analysis_panel(page, kind="strategy_gate", narrative="x. Y.", payload_fn=dict,
                                                sections=sections)
        translate_controls(panel, LocaleContext("ko_KR"))
        shown = texts(panel)
        for caption in ("분석 요약", "결론", "로컬 해설", "영문 원문 보기"):
            self.assertIn(caption, shown)
        labels = [c.label for c in walk(panel) if isinstance(c, ft.TextField)]
        self.assertEqual(labels, ["AI 분석가에게 물어볼 질문 (선택)"])
        self.assertIn("심층 분석", [c.content for c in walk(panel) if isinstance(c, ft.Button)])
        translate_controls(panel, LocaleContext("en_US"))
        self.assertIn("Conclusion", texts(panel))
        self.assertIn("Deep analysis", [c.content for c in walk(panel) if isinstance(c, ft.Button)])
        self.assertEqual(calls, ["en", "ko", "en"])


if __name__ == "__main__":
    unittest.main()
