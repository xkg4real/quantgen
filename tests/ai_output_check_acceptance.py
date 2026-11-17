"""Advisory AI number check (§10 NEW-M6-12, NEW-M6-19: limitations a and d).

Pure tests: no network, no API, no files. The check compares the numbers cited in
AI commentary with the JSON payload that was sent; it never changes the text, an
error code, a payload or a verdict.
"""
from copy import deepcopy
import json
import unittest

from core.research.ai_output_check import (AI_LABEL, COARSE_SIGNIFICANT_DIGITS, MAX_LISTED, NumberCheck,
                                           _FORMATTED, check_line, number_check)

# Shaped like the payloads that are sent: numeric leaves, a formatted-number cell,
# a digit-only code, free text with numbers, a date, and a non-finite marker.
PAYLOAD = json.loads(json.dumps({
    "as_of": "2026-11-03", "sharpe": 0.42, "ann_vol": 0.153, "chg_1w": -0.0008, "y10": 4.12,
    "spread_bp": -80.25, "cell": "2.345%", "btc_usd": 67012.34, "usdkrw": 1350.52, "median": 105.2,
    "half_life_days": 7.736, "vol_window": 63, "code": "122630",
    "sleeve_price_basis": "Simulated series (GBM, μ=3%, σ=27%) — no market data provider was used.",
    "garch": {"nu": "+inf: normal innovations (the fitted Student-t degrees of freedom are at the normal "
                    "limit, eta = 0)"},
}, ensure_ascii=False))
WEEKLY = "Explain the risk.\n\nWrite a research note over the trailing 252-session window."


def check(text, question=""):
    return number_check(text, PAYLOAD, question)


class NumberCheckTests(unittest.TestCase):
    def test_invented_numbers_are_not_found_in_english_and_korean(self):
        self.assertEqual(check("The Sharpe ratio of 9.99 and a hit rate of 47.5%.").not_found, ("9.99", "47.5%"))
        self.assertEqual(check("샤프 비율이 9.99일 때 위험조정 성과는 높습니다.").not_found, ("9.99",))
        self.assertEqual(check("변동성이 7.77만큼 높습니다.").not_found, ("7.77",))

    def test_rounding_percent_and_bp_scaling_are_found(self):
        for text in ("Volatility of 15.3%.", "A 8bp fall.", "The spread is -80.3bp.", "The cell reads 2.35%.",
                     "비트코인 가격은 67,012달러입니다.", "샤프 비율은 0.42이며", "변동성은 15.3%입니다.",
                     "중앙값은 105.2원", "8bp로 하락했습니다.", "두 값의 0.42차이는 작습니다.", "반감기는 7.7일입니다."):
            with self.subTest(text=text):
                c = check(text)
                self.assertEqual((c.checked, c.not_found, c.question_only), (1, (), ()))
                self.assertEqual(c.found + c.coarse_found, 1)

    def test_free_text_and_code_strings_are_references(self):
        self.assertEqual(check("The synthetic series assumes a 27% volatility.").not_found, ())
        self.assertEqual(check("시뮬레이션은 변동성 27%를 가정합니다.").not_found, ())
        c = check("Fund 122630 tracks the index.")
        self.assertEqual((c.found, c.not_found), (1, ()))
        # Marker strings and dates are never references.
        self.assertEqual(check("The value 11 is cited.").not_found, ("11",))

    def test_question_only_numbers_are_reported_apart_from_the_data(self):
        c = check("A Sharpe of 2.40 is not supported.", "Is a Sharpe of 2.40 plausible?")
        self.assertEqual((c.question_only, c.not_found, c.found), (("2.40",), (), 0))
        c = check("Against the trailing 252 sessions the level of 4.12% is elevated.", WEEKLY)
        self.assertEqual((c.question_only, c.not_found), (("252",), ()))
        self.assertEqual(check("Against the trailing 252 sessions.").not_found, ("252",))

    def test_dates_tenors_windows_ranges_and_identifiers_are_skipped(self):
        skipped = ("Litterman & Scheinkman (1991)", "2y/5y/10y", "the 5th percentile", "M6-19",
                   "a 10-year tenor", "a 1-week change", "3억 원", "52주 최고치",
                   "the 95% VaR", "1.2 billion contracts", "the S&P 500", "the KOSPI 200",
                   "the 15-20% band", "within 0.38-0.47")
        for text in skipped:
            with self.subTest(text=text):
                c = check(text)
                self.assertEqual(c.checked, 0)
                self.assertGreaterEqual(c.skipped, 1)
        for text in ("2026-11-03", "November 3, 2026", "As of October 2026", "Data as of 03/11/2026",
                     "2026.11.03 기준", "10월 들어", "2026년 11월 3일", "10:30 KST"):
            with self.subTest(text=text):
                self.assertEqual(check(text).checked, 0)

    def test_formatted_number_regex_escapes_the_hyphen(self):
        for text in ("A12", "Q3", "M6", "T10", "x1.5"):
            self.assertIsNone(_FORMATTED.match(text), text)
        for text in ("+3.20 bp", "−2.1%", "12.345%", "1,350.5", " 122630 "):
            self.assertIsNotNone(_FORMATTED.match(text), text)

    def test_day_month_year_dates_do_not_add_numeric_claims(self):
        for date in ("27 October 2026", "31 Oct. 2026", "3 November 2026", "3rd November 2026"):
            with self.subTest(date=date):
                c = number_check(f"As of {date}, the yield is 4.12%.", {"yield": 4.12})
                self.assertEqual((c.checked, c.not_found), (1, ()))

    def test_bp_values_quoted_in_percent_are_found_after_rounding(self):
        for value, quoted in ((-662.79, "-6.63%"), (-598.79, "5.99%"), (-84.54, "-0.85%")):
            with self.subTest(value=value, quoted=quoted):
                c = number_check(f"The spread is {quoted}.", {"spread_bp": value})
                self.assertEqual((c.checked, c.not_found, c.question_only), (1, (), ()))
        self.assertEqual(number_check("The spread is 6.70%.", {"spread_bp": -662.79}).not_found,
                         ("6.70%",))

    def test_range_spellings_skip_both_bounds_but_keep_other_numbers(self):
        for interval in ("15~20%", "15 ～ 20%", "from 15 to 20%", "15% to 20%",
                         "0.38~0.47", "from -2.5 to -1.5%", "15 - 20%", "15%–20%"):
            with self.subTest(interval=interval):
                c = number_check(f"Range {interval}; the yield is 4.12%.", {"yield": 4.12})
                self.assertEqual((c.checked, c.not_found), (1, ()))
                self.assertGreaterEqual(c.skipped, 2)
        # An ordinary list is two claims, not a range.
        self.assertEqual(number_check("Values 15 and 20.", {}).checked, 2)

    def test_additional_unit_spellings_use_the_same_conversions(self):
        for text, payload in (("Volatility is 15.3 pct.", {"vol": .153}),
                              ("Volatility is 15.3 PCT.", {"vol": .153}),
                              ("스프레드는 8 베이시스 포인트입니다.", {"spread": -.0008})):
            with self.subTest(text=text):
                c = number_check(text, payload)
                self.assertEqual((c.checked, c.not_found), (1, ()))

    def test_scientific_notation_is_skipped_as_a_whole(self):
        for value in ("3.04 × 10⁻⁸", "3.04×10⁻⁸", "3.04 × 10^-8", "3.04e-08"):
            with self.subTest(value=value):
                c = number_check(f"ADF p-value {value}; Sharpe 0.42.", {"sharpe": .42})
                self.assertEqual((c.checked, c.not_found), (1, ()))
                self.assertGreaterEqual(c.skipped, 1)

    def test_korean_skip_rules_allow_spaces_without_hiding_amounts(self):
        for phrase in ("20 거래일", "3 개월", "3 억 원", "52 주", "1.2 조 원"):
            with self.subTest(phrase=phrase):
                c = number_check(f"최근 {phrase} 기준.", {})
                self.assertEqual(c.checked, 0)
                self.assertGreaterEqual(c.skipped, 1)
        for phrase in ("10 달러", "10 주식", "10 차이"):
            with self.subTest(phrase=phrase):
                self.assertEqual(number_check(phrase, {}).not_found, ("10",))

    def test_number_check_describes_values_only_and_keeps_keys_excluded(self):
        c = number_check("At the 95% level.", {"cvar95_bp": -84.53})
        self.assertEqual(c.not_found, ("95%",))
        self.assertIn("not found in the values sent", check_line(c, "en"))
        self.assertIn("전송한 값에서 찾지 못한 숫자", check_line(c, "ko"))
        self.assertIn("전송한 데이터를 바탕으로 Claude가", AI_LABEL["ko"])

    def test_coarse_matches_are_counted_and_swapped_measures_still_match(self):
        c = check("Volatility is 0.42 and the Sharpe ratio is 15.3%.")
        self.assertEqual((c.checked, c.found, c.coarse_found, c.not_found), (2, 1, 1, ()))
        self.assertEqual(COARSE_SIGNIFICANT_DIGITS, 2)
        line = check_line(c, "en")
        self.assertIn("1 of the matches has two significant digits or fewer", line)
        plural = check_line(NumberCheck(2, (), (), 0, 2, 0), "en")
        self.assertIn("2 of the matches have two significant digits or fewer", plural)
        self.assertIn("the measure it refers to", line)
        self.assertIn("유효숫자가 두 자리 이하", check_line(c, "ko"))

    def test_lists_are_truncated_and_lines_are_bilingual(self):
        text = " ".join(f"{i}.{i}{i}7" for i in range(1, MAX_LISTED + 4))
        c = check(text)
        self.assertEqual(len(c.not_found), MAX_LISTED + 3)
        en, ko = check_line(c, "en"), check_line(c, "ko")
        self.assertIn("and 3 more", en); self.assertIn("외 3개", ko)
        self.assertIn(f"Number check ({MAX_LISTED + 3} checked)", en)
        self.assertIn(f"숫자 대조(확인한 숫자 {MAX_LISTED + 3}개)", ko)
        self.assertIn("may be derived", en); self.assertIn("계산해 낸 값", ko)
        self.assertEqual(check_line(None, "en"), "Number check: not run.")
        self.assertEqual(check_line(None, "ko"), "숫자 대조: 실행하지 않음.")
        none = check("No numbers are cited here.")
        self.assertEqual(none, NumberCheck(0, (), (), 0, 0, 0))
        self.assertEqual(check_line(none, "en"), "Number check: the commentary cites no numbers to compare.")
        self.assertEqual(check_line(none, "ko"), "숫자 대조: 해설에 대조할 숫자가 없습니다.")
        clean = check("Volatility of 15.3% and a median of 105.2.")
        self.assertIn("not found in the values sent: none.", check_line(clean, "en"))
        self.assertIn("찾지 못한 숫자: 없음.", check_line(clean, "ko"))
        q = check("A Sharpe of 2.40.", "Is 2.40 plausible?")
        self.assertIn("Only in the question text", check_line(q, "en"))
        self.assertIn("질문 문장", check_line(q, "ko"))

    def test_label_says_not_verified_in_both_languages(self):
        self.assertIn("not verified", AI_LABEL["en"]); self.assertIn("different text", AI_LABEL["en"])
        self.assertIn("검증 안 됨", AI_LABEL["ko"]); self.assertIn("다른 글", AI_LABEL["ko"])
        for language in ("en", "ko"):
            self.assertIn("verdict" if language == "en" else "판정", AI_LABEL[language])

    def test_inputs_are_not_mutated_and_counts_add_up(self):
        payload, text, question = deepcopy(PAYLOAD), "Sharpe 0.42, 9.99 and 2.40; 15.3% in 2026.", "2.40?"
        c = number_check(text, payload, question)
        self.assertEqual(payload, PAYLOAD)
        self.assertEqual(c.checked, c.found + c.coarse_found + len(c.not_found) + len(c.question_only))
        self.assertEqual((c.not_found, c.question_only), (("9.99",), ("2.40",)))


if __name__ == "__main__":
    unittest.main()
