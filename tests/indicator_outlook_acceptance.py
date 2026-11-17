"""The conclusion part (결론부) of every chart-study explanation (owner 2026-11-17), offline.

Owner, verbatim: "모든 기술지표 해석에, '결론부'가 필요합니다 ... 기술지표가 이렇게 있을때 상승흐름이 예상되고, 이렇게 있을때
하강흐름이 예상된다. 이부분을 표현해주는게 중요합니다" and "보통 bb기준 하단에 있을때 추후에 상승이 찾아올 확률이 높다고
해석하는게 전문가의 해석 아닌가요? ... 여러 논문들 참고해서 검토합니다".

Covered: every study has two upward and two downward conditions, a regime line, an evidence grade with its reason, in
Korean 해요체 and English, without promises or orders; the Bollinger reading follows Bollinger's own rules (a re-entry
with a flat middle line reads as a rebound; walking the lower band with a falling middle line reads as the fall
continuing) rather than "lower band = rise"; `now()` reads constructed price paths correctly; the guide card shows the
conclusion first and the guide page's reading ends with it.
"""
import math
import os
import re
import unittest
from datetime import date, timedelta
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from core.education import indicators as E
from core.education import outlook as O
from core.market.models import Candle

HANGUL = re.compile("[가-힣]")
PROMISES = re.compile(r"(?<!횡)보장|확실|반드시|매수하세요|매도하세요|사세요|파세요|확률이 높|무조건|100%")


def bars_from(closes, volume=1e6):
    day, days = date(2025, 1, 2), []
    while len(days) < len(closes):
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    candles = []
    for d, c in zip(days, closes):
        candles.append(Candle(d.isoformat(), c, c * 1.004, c * 0.996, c, volume))
    return E.bars_from_candles(tuple(candles), "1d")


class OutlookContentTests(unittest.TestCase):
    def test_every_study_has_a_two_sided_conclusion_in_both_languages(self):
        self.assertEqual(set(O.OUTLOOK), {s.key for s in E.STUDIES})
        for key in O.OUTLOOK:
            with self.subTest(key=key):
                ko, en = O.outlook(key, "ko"), O.outlook(key, "en")
                self.assertEqual((len(ko.up), len(ko.down), len(en.up), len(en.down)), (2, 2, 2, 2))
                self.assertIn(ko.grade, O.GRADES)
                for text in (ko.concept, *ko.up, *ko.down, ko.regime, ko.grade_reason):
                    self.assertTrue(HANGUL.search(text), text)
                    self.assertTrue(text.endswith(("요", "요)")), text)          # 해요체
                    self.assertNotIn("봉", text)                                  # owner R-D9-2
                    self.assertIsNone(PROMISES.search(text), text)
                    self.assertLessEqual(len(text), 60, text)
                for text in (en.concept, *en.up, *en.down, en.regime, en.grade_reason):
                    self.assertFalse(HANGUL.search(text), text)

    def test_bollinger_follows_bollingers_rules_not_lower_band_means_rise(self):
        bb = O.outlook("bb", "ko")
        joined_up, joined_down = " ".join(bb.up), " ".join(bb.down)
        self.assertIn("중심선이 평평할 때", joined_up)           # range condition for the rebound reading
        self.assertIn("다시 밴드 안으로", joined_up)              # a re-entry, not a touch
        self.assertIn("사이 고점을 넘으면", joined_up)            # W-bottom confirmation
        self.assertIn("하단 밖에 머물", joined_down)              # walking the lower band
        self.assertIn("중심선이 내려가", joined_down)
        self.assertIn("추세장에선 하단을 타고 더 내려가요", bb.regime)
        self.assertEqual(bb.grade, "weak")
        self.assertIn("Bollinger (2001)", bb.sources)
        self.assertNotIn("확률", joined_up)

    def test_text_block_lists_both_sides_now_regime_and_evidence(self):
        block = O.text_block("rsi", "ko", O.Now("up", "상승 흐름 쪽", "30 아래에 있다가 다시 위로 올라왔어요"))
        for part in ("상승 흐름 쪽으로 읽는 경우", "하락 흐름 쪽으로 읽는 경우", "지금은 상승 흐름 쪽", "근거 엇갈림", "근거 자료"):
            self.assertIn(part, block)


class OutlookNowTests(unittest.TestCase):
    def values(self, key, bars):
        return E.compute_study(key, bars)

    def test_walking_down_the_lower_band_reads_as_the_fall_continuing(self):
        closes = [100.0 + 0.3 * math.sin(k) for k in range(40)] + [100 * 0.99 ** k for k in range(1, 11)]
        closes.append(closes[-1] * 0.94)             # a falling middle line and a close below the lower band
        bars = bars_from(closes)
        now = O.now("bb", self.values("bb", bars), bars)
        self.assertEqual(now.side, "down", now.reason)
        self.assertIn("하단 밖", now.reason)

    def test_a_re_entry_with_a_flat_middle_line_reads_as_a_rebound(self):
        wave = [100 + 1.5 * math.sin(k / 2.0) for k in range(56)]
        closes = wave + [94.0, 99.4]                 # a dip below the lower band, then back inside
        bars = bars_from(closes)
        values = self.values("bb", bars)
        now = O.now("bb", values, bars)
        self.assertEqual(now.side, "up", now.reason)
        self.assertIn("안으로 돌아왔", now.reason)

    def test_rsi_back_above_30_reads_as_a_rebound_and_staying_low_is_not_called(self):
        falling = [100 * (0.98 ** k) for k in range(30)]
        bars = bars_from(falling)
        low = O.now("rsi", self.values("rsi", bars), bars)
        self.assertEqual(low.side, "neutral")          # oversold alone is not a rebound
        recovered = falling + [falling[-1] * 1.04 ** j for j in range(1, 5)]
        bars = bars_from(recovered)
        values = self.values("rsi", bars)
        self.assertGreater(values["RSI14"][-1], 30)
        self.assertEqual(O.now("rsi", values, bars).side, "up")

    def test_every_study_answers_or_declines_without_raising(self):
        bars = bars_from([100 + 5 * math.sin(k / 7) + k * 0.05 for k in range(260)])
        for key in O.OUTLOOK:
            with self.subTest(key=key):
                try:
                    values = E.compute_study(key, bars)
                except Exception:
                    continue
                for index in (-1, -40, 10):
                    for language in ("ko", "en"):
                        now = O.now(key, values, bars, index, language)
                        if now is not None:
                            self.assertIn(now.side, O.SIDES)
                            self.assertNotRegex(now.reason, r"(?<![\w.])-(?=\d)")   # typographic minus only


class GuideScreensTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_the_guide_card_leads_with_the_conclusion(self):
        from quantgen_desktop.indicator_picker import IndicatorPicker
        bars = bars_from([100 + 4 * math.sin(k / 6) for k in range(200)])
        picker = IndicatorPicker()
        picker.resize(360, 900)
        picker.show()
        picker.set_context(bars, asset="domestic_stock", interval="1d")
        picker._emit(("bb",))
        row = picker.rows()["bb"]
        row.open_guide(True)
        self.app.processEvents()
        card = row.guide
        block = card.conclusion
        self.assertTrue(block.isVisibleTo(card))
        self.assertEqual(block.title.text(), "결론")
        up_frame, up_head, up_items = block.sides["up"]
        down_frame, down_head, down_items = block.sides["down"]
        self.assertEqual(up_head.text(), "▲ 상승 흐름 쪽으로 읽는 경우")
        self.assertEqual(down_head.text(), "▼ 하락 흐름 쪽으로 읽는 경우")
        self.assertEqual([w.text() for w in up_items], ["· " + t for t in O.outlook("bb").up])
        self.assertTrue(block.now_pill.text() in {v[0] for v in O.SIDES.values()})
        self.assertTrue(block.grade.text().startswith("근거 약함"))
        from core.education.study_guide import short_guide
        self.assertEqual(card.one_liner.text(), short_guide("bb", "ko").one_liner)   # the concept: one short line
        self.assertFalse(card.cues.isVisibleTo(card))
        self.assertEqual(card.caution.text(), O.outlook("bb").regime)
        layout = card.layout()
        self.assertLess(layout.indexOf(block), layout.indexOf(card.one_liner))  # conclusion before the concept
        self.assertTrue(any("근거 자료" in t for t in card.long_texts))
        picker.deleteLater()

    def test_the_guide_page_reading_ends_with_now(self):
        from core.education import catalog as C
        from core.i18n import LocaleContext
        _name, series, _meta = C.historical_case(("bb", "rsi"), "auto")
        text = C.reading_text(series, ("bb", "rsi"), len(series.closes) * 2 // 3, LocaleContext("ko_KR"))
        self.assertEqual(text.count("지금은 "), 2)
        english = C.reading_text(series, ("bb",), len(series.closes) // 2, LocaleContext("en_US"))
        self.assertIn("Now: ", english)


if __name__ == "__main__":
    unittest.main()
