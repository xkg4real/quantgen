"""Observed signals never use future observations or manufacture outcome statistics."""
import math
import unittest
from dataclasses import replace

from core.education.indicators import Bars, compute_study
from core.education.signal_context import signal_note, alignment_note


def bars(prices=(98, 102, 101)):
    return Bars(tuple(f"2026-11-{i+1:02d}" for i in range(len(prices))), prices,
                tuple(p + 1 for p in prices), tuple(p - 1 for p in prices), prices)


class SignalContextTests(unittest.TestCase):
    def test_rsi_exit_and_persistent_zone_are_different(self):
        b = bars()
        exit_note = signal_note("rsi", b, 1, values={"RSI14": (28, 34, 20)})
        self.assertIn("과매도 구간을 벗어났어요", exit_note)
        self.assertIn("확정된 것은 아니에요", exit_note)
        low = signal_note("rsi", b, 1, values={"RSI14": (28, 24, 20)})
        self.assertNotIn("벗어났", low)
        self.assertIn("이어질 수도", low)
        self.assertEqual(signal_note("rsi", b, 1, values={"RSI14": (45, 50, 20)}), "")

    def test_macd_and_price_crossings_describe_both_directions(self):
        b = bars()
        self.assertIn("위로 통과", signal_note("macd", b, 1, values={"HISTOGRAM": (-1, 2, 4)}))
        self.assertIn("아래로 통과", signal_note("macd", b, 1, values={"HISTOGRAM": (1, -2, 4)}))
        self.assertIn("이동평균선", signal_note("sma", b, 1, values={"SMA20": (100, 100, 100)}))
        self.assertEqual(signal_note("macd", b, 1, values={"HISTOGRAM": (1, 2, 4)}), "")

    def test_no_future_values_or_warmup_guess(self):
        b = bars()
        before = signal_note("rsi", b, 1, values={"RSI14": (28, 34, 50)})
        changed = signal_note("rsi", replace(b, close=(98, 102, 999)), 1,
                              values={"RSI14": (28, 34, 100)})
        self.assertEqual(before, changed)
        self.assertEqual(signal_note("macd", b, 1, values={"HISTOGRAM": (math.nan, 1, 2)}), "")
        self.assertEqual(signal_note("rsi", b, 1, values={"RSI14": (math.nan, math.nan, 34)}), "")
        self.assertEqual(signal_note("rsi", None), "")

    def test_bollinger_reentry_uses_the_real_engine_line_ids(self):
        b = bars((90, 101, 102))
        values = {"BB_LOWER": (95, 96, 97), "BB_UPPER": (110, 110, 110)}
        self.assertIn("하단 밴드 안", signal_note("bb", b, 1, values=values))
        actual = bars(tuple(100 + i % 5 for i in range(30)))
        self.assertIn("BB_LOWER", compute_study("bb", actual))

    def test_disagreement_is_not_a_majority_vote_or_score(self):
        values = {"sma": {"SMA20": (100, 100, 100)}, "rsi": {"RSI14": (60, 35, 40)}}
        note = alignment_note(("sma", "rsi"), bars(), 1, values=values)
        self.assertIn("엇갈려요", note)
        self.assertEqual(alignment_note(("sma",), bars(), 1, values=values), "")
        self.assertEqual(alignment_note(("sma", "rsi"), bars(), 1, values={"sma": values["sma"]}), "")
        for prohibited in ("매수 추천", "매도 추천", "수익 확률", "승률"):
            self.assertNotIn(prohibited, note)

    def test_english_explains_conditions_and_limits(self):
        note = signal_note("rsi", bars(), 1, language="en", values={"RSI14": (28, 34, 40)})
        self.assertIn("not confirmed", note)
        self.assertNotRegex(note, "[가-힣]")
        self.assertNotRegex(alignment_note(("sma", "rsi"), bars(), 1, language="en",
                                           values={"sma": {"SMA20": (100, 100, 100)},
                                                   "rsi": {"RSI14": (60, 35, 40)}}), "[가-힣]")


if __name__ == "__main__":
    unittest.main()
