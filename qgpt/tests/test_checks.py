"""QuantGPT checks: the abstain rule on numbers, citations, look-ahead, and parity with the host check."""
import importlib.util
import json
import sys
import unittest

from _path import HOST

from quantgpt.checks import numbers as N
from quantgpt.checks.citations import check_citations
from quantgpt.checks.leakage import check_leakage, find_dates
from quantgpt.checks.schema import SchemaError

PAYLOAD = {"as_of": "2026-11-03", "sharpe": 0.42, "bench_sharpe": 0.74, "ann_vol": 0.153, "bench_vol": 0.121,
           "max_drawdown": -0.188, "bench_mdd": -0.254, "n_trades": 37, "n_sessions": 1884, "price": 1350.52,
           "prev_price": 1312.4, "weights": {"AAA": 0.6, "BBB": 0.4}, "y10": 4.12, "y2": 3.47}

# Fixed cases: one sentence, one number that is calculated from payload values and is not itself in the payload.
DERIVED = (
    ("difference", "샤프 비율은 벤치마크보다 0.32 낮습니다."),
    ("difference", "The Sharpe ratio is 0.32 below the benchmark."),
    ("difference", "변동성은 벤치마크보다 3.2%p 높습니다."),
    ("difference", "낙폭은 벤치마크보다 6.6%p 작습니다."),
    ("difference", "The 10-year yield is 65bp above the 2-year yield."),
    ("difference", "가격은 전일보다 38.12 올랐습니다."),
    ("ratio", "변동성은 벤치마크의 1.26배입니다."),
    ("ratio", "The Sharpe ratio is 57% of the benchmark's."),
    ("ratio", "낙폭은 벤치마크의 74% 수준입니다."),
    ("ratio", "AAA의 비중은 BBB의 1.5배입니다."),
    ("percent_change", "가격은 전일보다 2.9% 올랐습니다."),
    ("percent_change", "The price rose 2.90% from the previous close."),
    ("sum", "두 종목의 비중 합은 100%입니다."),
    ("sum", "두 금리의 합은 7.59%입니다."),
    ("average", "두 금리의 평균은 3.795%입니다."),
    ("average", "The average of the two volatilities is 13.7%."),
    ("rescale", "거래는 연 4.9회꼴입니다."),
    ("rescale", "표본은 약 7.5년입니다."),
    ("rescale", "일간 변동성으로는 0.96%입니다."),
    ("complement", "AAA를 뺀 나머지 비중은 40%입니다."),
)
# Sentences whose numbers are all in the payload (rounded or rescaled): never withheld.
GROUNDED = (
    "샤프 비율은 0.42이고 벤치마크는 0.74입니다.", "변동성은 15.3%입니다.", "최대 낙폭은 18.8%입니다.",
    "The 10-year yield is 4.12% and the 2-year yield is 3.47%.", "거래 횟수는 37회입니다.",
    "가격은 1,350.52입니다.", "AAA 비중은 60%, BBB 비중은 40%입니다.", "표본 크기는 1,884입니다.",
)
INVENTED = ("샤프 비율은 1.37입니다.", "The hit rate is 63.5%.", "변동성은 22.4%입니다.", "기대 수익률은 9.9%입니다.")


class AbstainRuleTests(unittest.TestCase):
    def test_grounded_text_is_shown_in_both_modes(self):
        for text in GROUNDED:
            for mode in ("tool", "owner"):
                with self.subTest(text=text, mode=mode):
                    decision = N.decide(text, PAYLOAD, mode=mode)
                    self.assertFalse(decision.abstain)
                    self.assertTrue(decision.numbers)
                    self.assertTrue(all(n["found_in_payload"] for n in decision.numbers))

    def test_an_invented_number_is_withheld_in_tool_mode_and_recorded_in_owner_mode(self):
        for text in INVENTED:
            with self.subTest(text=text):
                tool, owner = N.decide(text, PAYLOAD, mode="tool"), N.decide(text, PAYLOAD, mode="owner")
                self.assertTrue(tool.abstain)
                self.assertFalse(owner.abstain)
                self.assertEqual(tool.not_found, owner.not_found)
                self.assertEqual(len(tool.not_found), 1)

    def test_a_number_from_the_request_text_is_not_an_invented_number(self):
        decision = N.decide("PER 10 이하라는 조건은 표본에 없습니다.", PAYLOAD, "PER 10 이하면 저평가인가요?")
        self.assertFalse(decision.abstain)
        self.assertEqual(decision.numbers, ({"text": "10", "found_in_payload": True},))
        self.assertTrue(N.decide("PER 12 이하입니다.", PAYLOAD, "PER 10 이하면?").abstain)

    def test_text_without_numbers_and_unknown_modes(self):
        self.assertEqual(N.decide("숫자가 없는 문장입니다.", PAYLOAD), N.NumberDecision(False, (), ()))
        with self.assertRaises(ValueError):
            N.decide("x", PAYLOAD, mode="admin")

    def test_entries_fit_the_envelope_and_follow_text_order(self):
        entries = N.cited_entries("샤프 0.42, 적중률 63.5%, 변동성 15.3%.", PAYLOAD)
        self.assertEqual([e["text"] for e in entries], ["0.42", "63.5%", "15.3%"])
        self.assertEqual([e["found_in_payload"] for e in entries], [True, False, True])

    def test_text_of_collects_every_string_in_a_body(self):
        body = {"summary": "a 0.42", "points": ["b 9.99", {"t": "c"}], "n": 5}
        self.assertEqual(N.text_of(body), "a 0.42\nb 9.99\nc")
        self.assertTrue(N.decide(N.text_of(body), PAYLOAD).abstain)

    def test_measured_abstention_on_calculated_numbers(self):
        """Fixed measurement: how often a correct, calculated number is withheld under the rule."""
        withheld = [(kind, text) for kind, text in DERIVED if N.decide(text, PAYLOAD).abstain]
        by_kind = {}
        for kind, _ in DERIVED:
            by_kind.setdefault(kind, [0, 0])[1] += 1
        for kind, _ in withheld:
            by_kind[kind][0] += 1
        self.assertEqual(len(DERIVED), 20)
        self.assertEqual(len(withheld), MEASURED["withheld"], by_kind)
        self.assertEqual({k: tuple(v) for k, v in by_kind.items()}, MEASURED["by_kind"])


# The measurement the test above pins down (withheld, total) per kind of calculation.
# Two of the twenty are shown only by coincidence: "74%" equals another payload value (0.74, the benchmark
# Sharpe ratio), and the complement "40%" is itself a payload weight.
MEASURED = {"withheld": 18, "by_kind": {"difference": (6, 6), "ratio": (3, 4), "percent_change": (2, 2),
                                         "sum": (2, 2), "average": (2, 2), "rescale": (3, 3),
                                         "complement": (0, 1)}}


class CitationTests(unittest.TestCase):
    EVIDENCE = {"card:S_E1_trend_krx": "2026-09-27", "doc:sharpe": "2025-01-10", "doc:late": "2026-12-01"}

    def test_accepted(self):
        cites = [{"source_id": "card:S_E1_trend_krx", "as_of": "2026-09-27"},
                 {"source_id": "doc:sharpe", "as_of": "2025-01-10"}]
        check = check_citations(cites, self.EVIDENCE, as_of="2026-11-24", required=True)
        self.assertTrue(check.ok)
        self.assertIsNone(check.reason_code)
        self.assertTrue(check_citations([], self.EVIDENCE).ok)
        self.assertTrue(check_citations(cites[:1], self.EVIDENCE, as_of="2026-09-27").ok)   # same day is not late

    def test_rejected(self):
        cases = [
            ([{"source_id": "doc:made_up", "as_of": "2026-01-01"}], "citation_unknown"),
            ([{"source_id": "doc:sharpe", "as_of": "2026-01-10"}], "citation_unknown"),      # wrong date
            ([{"source_id": "doc:late", "as_of": "2026-12-01"}], "after_as_of"),
            ([], "no_evidence"),
        ]
        for cites, reason in cases:
            with self.subTest(reason=reason, cites=cites):
                check = check_citations(cites, self.EVIDENCE, as_of="2026-11-24", required=True)
                self.assertFalse(check.ok)
                self.assertEqual(check.reason_code, reason)
        with self.assertRaises(SchemaError):
            check_citations([{"source_id": "doc:sharpe", "as_of": "someday"}], self.EVIDENCE)


class LeakageTests(unittest.TestCase):
    AS_OF = "2026-11-24"
    EVENTS = [{"name": "12월 금리 결정", "aliases": ["December rate decision"], "date": "2026-12-10"},
              {"name": "3분기 실적 발표", "date": "2026-10-30"}]

    def test_dates_up_to_as_of_pass(self):
        for text in ("2026-11-24 기준입니다.", "2026년 11월 3일 발표", "2026.11.03 기준", "As of November 3, 2026",
                     "3 November 2026", "October 2026", "2026년 3분기", "Q3 2026", "2025년에는", "in 2024",
                     "2026-11", "2026년 11월", "샤프 비율은 0.42이고 표본은 2026 세션입니다.", "3분기 실적 발표 이후"):
            with self.subTest(text=text):
                self.assertTrue(check_leakage(text, self.AS_OF, self.EVENTS).ok)

    def test_later_dates_are_reported_as_written(self):
        cases = {"2026-11-25에 발표됩니다.": "2026-11-25", "2026년 12월 10일 회의": "2026년 12월 10일",
                 "2026.12.01 기준": "2026.12.01", "on December 10, 2026": "December 10, 2026",
                 "10 December 2026": "10 December 2026", "in January 2027": "January 2027",
                 "2027년 1분기": "2027년 1분기", "Q1 2027": "Q1 2027", "2027 Q2": "2027 Q2",
                 "2027년에는": "2027년", "by 2028": "by 2028", "2026-12": "2026-12", "2026년 12월": "2026년 12월"}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(check_leakage(text, self.AS_OF).late_dates, (expected,))

    def test_listed_events_after_as_of_are_reported(self):
        check = check_leakage("12월 금리 결정에서 동결했습니다.", self.AS_OF, self.EVENTS)
        self.assertEqual((check.late_dates, check.late_events), ((), ("12월 금리 결정",)))
        check = check_leakage("After the december RATE decision the curve steepened.", self.AS_OF, self.EVENTS)
        self.assertEqual(check.late_events, ("12월 금리 결정",))
        self.assertTrue(check_leakage("12월 금리 결정에서 동결했습니다.", "2026-12-10", self.EVENTS).ok)

    def test_one_expression_is_reported_once_and_impossible_dates_are_ignored(self):
        self.assertEqual([e for _, e, _ in find_dates("2027년 1월 5일")], ["2027년 1월 5일"])
        self.assertEqual(find_dates("2026-13-45"), [])
        both = check_leakage("2026-11-01 기준이며 2027-02-01에 다시 봅니다.", self.AS_OF)
        self.assertEqual(both.late_dates, ("2027-02-01",))
        with self.assertRaises(SchemaError):
            check_leakage("x", "soon")


@unittest.skipUnless((HOST / "core" / "research" / "ai_output_check.py").is_file(), "host check not present")
class HostParityTests(unittest.TestCase):
    def test_the_restated_check_gives_the_host_result(self):
        spec = importlib.util.spec_from_file_location("_host_ai_output_check",
                                                      HOST / "core/research/ai_output_check.py")
        host = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = host
        try:
            spec.loader.exec_module(host)
            texts = [t for _, t in DERIVED] + list(GROUNDED) + list(INVENTED) + [
                "Range 15~20%; the yield is 4.12%.", "ADF p-value 3.04e-08; Sharpe 0.42.", "최근 20 거래일 기준.",
                "As of 27 October 2026, the yield is 4.12%.", "the 95% VaR", "S&P 500", ""]
            for text in texts:
                for question in ("", "Is 2.40 plausible over 252 sessions?"):
                    with self.subTest(text=text, question=question):
                        mine = N.number_check(text, PAYLOAD, question)
                        theirs = host.number_check(text, PAYLOAD, question)
                        self.assertEqual(tuple(vars(mine).values()), tuple(vars(theirs).values()))
                        for language in ("en", "ko"):
                            self.assertEqual(N.check_line(mine, language), host.check_line(theirs, language))
        finally:
            sys.modules.pop(spec.name, None)


if __name__ == "__main__":
    unittest.main()
