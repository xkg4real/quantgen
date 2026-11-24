"""DIDM-3: the look-ahead rule of PREREG_V0 section 5 as code, and the cutoff table. No network."""
from __future__ import annotations

import ast
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from core.didm.llm import cutoffs as c

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "didm" / "MODEL_CUTOFFS.md"
URL = "https://example.org/model-card"


def card(**kw) -> c.ModelCard:
    base = dict(key="m", family="f", rule=c.Rule.CUTOFF, snapshot_id="snap-1", cutoff=date(2023, 12, 31),
                source_url=URL, checked_on=date(2026, 11, 24))
    base.update(kw)
    return c.ModelCard(**base)


class MarginRule(unittest.TestCase):
    def test_cutoff_2023_12_31_is_eligible_from_2024_03_31(self):
        m = card()
        self.assertEqual(m.eligible_from, date(2024, 3, 31))
        self.assertFalse(c.eligibility(m, date(2024, 3, 30)).eligible)
        self.assertTrue(c.eligibility(m, date(2024, 3, 31)).eligible)
        self.assertTrue(c.eligibility(m, date(2026, 1, 1)).eligible)
        self.assertFalse(c.eligibility(m, date(2023, 6, 1)).eligible)

    def test_margin_is_three_calendar_months_with_month_end_clamp(self):
        self.assertEqual(c.MARGIN_MONTHS, 3)
        self.assertEqual(c.add_months(date(2023, 11, 30), 3), date(2024, 2, 29))
        self.assertEqual(c.add_months(date(2022, 11, 30), 3), date(2023, 2, 28))
        self.assertEqual(c.add_months(date(2024, 10, 15), 3), date(2025, 1, 15))
        self.assertEqual(c.add_months(date(2024, 12, 31), 0), date(2024, 12, 31))

    def test_received_at_uses_the_utc_day_and_needs_a_timezone(self):
        m = card()
        kst = timezone(timedelta(hours=9))
        # 2024-03-31 08:00 KST is still 2024-03-30 in UTC: not yet eligible.
        self.assertFalse(c.eligibility(m, datetime(2024, 3, 31, 8, 0, tzinfo=kst)).eligible)
        self.assertTrue(c.eligibility(m, datetime(2024, 3, 31, 9, 0, tzinfo=kst)).eligible)
        with self.assertRaises(c.CutoffError):
            c.eligibility(m, datetime(2024, 4, 1, 0, 0))
        with self.assertRaises(c.CutoffError):
            c.eligibility(m, "2024-04-01")

    def test_month_only_cutoff_counts_to_the_last_day(self):
        self.assertEqual(c.cutoff_from_text("2026-06"), date(2026, 6, 30))
        self.assertEqual(c.cutoff_from_text("2024-02"), date(2024, 2, 29))
        self.assertEqual(c.cutoff_from_text("2023-12-31"), date(2023, 12, 31))
        for bad in ("2026", "2026-13", "June 2026", "2026-02-30", "", None):
            with self.subTest(bad=bad), self.assertRaises(c.CutoffError):
                c.cutoff_from_text(bad)


class UnknownMeansNotEligible(unittest.TestCase):
    def test_unknown_cutoff(self):
        m = card(cutoff=None)
        self.assertFalse(m.verified)
        self.assertIsNone(m.eligible_from)
        for day in (date(2000, 1, 1), date(2026, 11, 24), date(2099, 1, 1)):
            self.assertFalse(c.eligibility(m, day).eligible)

    def test_missing_snapshot_source_or_check_date(self):
        for missing in ("snapshot_id", "source_url", "checked_on"):
            with self.subTest(missing=missing):
                m = card(**{missing: None})
                self.assertFalse(m.verified)
                self.assertFalse(c.eligibility(m, date(2099, 1, 1)).eligible)

    def test_model_outside_the_registry(self):
        self.assertFalse(c.REGISTRY.eligibility("some-new-model", date(2099, 1, 1)).eligible)
        self.assertFalse(c.eligibility(None, date(2099, 1, 1)).eligible)


class InHouseModel(unittest.TestCase):
    def make(self, base_cutoff, finetune_through):
        base = card(key="base", cutoff=base_cutoff)
        return c.in_house_card("own-1", base=base, finetune_through=finetune_through, snapshot_id="own-1@abc",
                               source_url=URL, checked_on=date(2026, 11, 24))

    def test_cutoff_is_the_later_of_base_and_finetune_data(self):
        later_finetune = self.make(date(2024, 6, 30), date(2025, 9, 30))
        self.assertEqual(later_finetune.effective_cutoff, date(2025, 9, 30))
        self.assertEqual(later_finetune.eligible_from, date(2025, 12, 30))
        later_base = self.make(date(2025, 3, 31), date(2024, 1, 31))
        self.assertEqual(later_base.effective_cutoff, date(2025, 3, 31))
        self.assertEqual(later_base.eligible_from, date(2025, 6, 30))

    def test_either_part_unknown_means_not_eligible(self):
        for base_cutoff, finetune in ((None, date(2025, 1, 31)), (date(2024, 6, 30), None)):
            with self.subTest(base=base_cutoff, finetune=finetune):
                m = self.make(base_cutoff, finetune)
                self.assertFalse(m.verified)
                self.assertFalse(c.eligibility(m, date(2099, 1, 1)).eligible)

    def test_unverified_base_makes_the_in_house_model_unverified(self):
        base = card(key="base", source_url=None)     # has a date but no source
        m = c.in_house_card("own-1", base=base, finetune_through=date(2025, 1, 31), snapshot_id="s",
                            source_url=URL, checked_on=date(2026, 11, 24))
        self.assertFalse(m.verified)

    def test_base_must_follow_the_cutoff_rule(self):
        with self.assertRaises(c.CutoffError):
            c.in_house_card("own-1", base=card(rule=c.Rule.BASELINE), finetune_through=date(2025, 1, 31),
                            snapshot_id="s", source_url=URL, checked_on=date(2026, 11, 24))


class Baselines(unittest.TestCase):
    def test_pinned_baseline_is_usable_at_any_date(self):
        m = card(rule=c.Rule.BASELINE, cutoff=None)
        self.assertTrue(m.verified)
        self.assertTrue(c.eligibility(m, date(2015, 1, 2)).eligible)

    def test_unpinned_baseline_is_not(self):
        m = card(rule=c.Rule.BASELINE, cutoff=None, snapshot_id=None)
        self.assertFalse(c.eligibility(m, date(2015, 1, 2)).eligible)


RULE_NAMES = {"마감일": c.Rule.CUTOFF, "기준선": c.Rule.BASELINE}


def table_rows() -> list[dict]:
    lines = [ln for ln in DOC.read_text(encoding="utf-8").splitlines() if ln.startswith("|")]
    header = [cell.strip() for cell in lines[0].strip("|").split("|")]
    return [dict(zip(header, [cell.strip() for cell in ln.strip("|").split("|")])) for ln in lines[2:]]


class TableMatchesRegistry(unittest.TestCase):
    def test_same_rows_in_the_same_order(self):
        rows = table_rows()
        self.assertEqual([r["키 (`model_version`)"] for r in rows], [m.key for m in c.REGISTRY])

    def test_every_row_is_complete_or_says_not_verified(self):
        def text(value):
            return "—" if value is None else (value.isoformat() if isinstance(value, date) else value)
        for row, m in zip(table_rows(), c.REGISTRY):
            with self.subTest(m.key):
                self.assertEqual(row["계열"], m.family)
                self.assertIs(RULE_NAMES[row["규칙"]], m.rule)
                self.assertEqual(row["스냅샷 ID"], text(m.snapshot_id))
                self.assertEqual(row["마감일"], text(m.effective_cutoff))
                self.assertEqual(row["자격 시작"], text(m.eligible_from))
                self.assertEqual(row["출처 URL"], text(m.source_url))
                self.assertEqual(row["확인일"], text(m.checked_on))
                if m.verified:
                    self.assertEqual(row["상태"], "검증됨")
                    self.assertTrue(m.source_url.startswith("https://"))
                    self.assertNotIn("—", (row["스냅샷 ID"], row["출처 URL"], row["확인일"]))
                else:
                    self.assertEqual(row["상태"], c.NOT_VERIFIED)
                    # nothing half-filled: an unverified row carries no date that could be mistaken for a cutoff
                    self.assertEqual((row["마감일"], row["자격 시작"]), ("—", "—"))

    def test_required_families_are_listed(self):
        families = {m.family for m in c.REGISTRY}
        for wanted in ("Loughran-McDonald 사전", "FinBERT", "ChronoGPT 빈티지", "Qwen3 후보", "Claude (API)", "자체 LLM"):
            self.assertIn(wanted, families)
        self.assertIsNotNone(c.REGISTRY.get("ProsusAI/finbert"))

    def test_registry_examples(self):
        self.assertFalse(c.REGISTRY.eligibility("ProsusAI/finbert", date(2020, 1, 2)).eligible)   # not pinned yet
        self.assertFalse(c.REGISTRY.eligibility("quantgpt-in-house", date(2099, 1, 1)).eligible)
        claude = c.REGISTRY.get("claude-fable-5-2")
        self.assertEqual((claude.cutoff, claude.eligible_from), (date(2026, 6, 30), date(2026, 9, 30)))
        self.assertFalse(c.REGISTRY.eligibility("claude-fable-5-2", date(2024, 12, 31)).eligible)
        self.assertTrue(c.REGISTRY.eligibility("claude-fable-5-2", date(2026, 9, 30)).eligible)

    def test_duplicate_keys_are_refused(self):
        with self.assertRaises(c.CutoffError):
            c.REGISTRY.with_card(card(key="claude-fable-5-2"))
        self.assertEqual(len(c.REGISTRY.with_card(card(key="new-model"))), len(c.REGISTRY) + 1)


class Boundaries(unittest.TestCase):
    def test_no_network_or_clock(self):
        tree = ast.parse((ROOT / "core" / "didm" / "llm" / "cutoffs.py").read_text(encoding="utf-8"))
        source = ast.unparse(tree)
        for banned in ("import requests", "import urllib", "import time", "import socket", ".now(", ".today(", "data.didm"):
            self.assertNotIn(banned, source)


if __name__ == "__main__":
    unittest.main()
