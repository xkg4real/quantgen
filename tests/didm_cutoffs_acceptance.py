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
        self.assertFalse(c.eligibility(m, published_at=date(2024, 3, 30), received_at=date(2024, 3, 30)).eligible)
        self.assertTrue(c.eligibility(m, published_at=date(2024, 3, 31), received_at=date(2024, 3, 31)).eligible)
        self.assertTrue(c.eligibility(m, published_at=date(2026, 1, 1), received_at=date(2026, 1, 1)).eligible)
        self.assertFalse(c.eligibility(m, published_at=date(2023, 6, 1), received_at=date(2023, 6, 1)).eligible)

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
        self.assertFalse(c.eligibility(m, published_at=datetime(2024, 3, 31, 8, 0, tzinfo=kst), received_at=datetime(2024, 3, 31, 8, 0, tzinfo=kst)).eligible)
        self.assertTrue(c.eligibility(m, published_at=datetime(2024, 3, 31, 9, 0, tzinfo=kst), received_at=datetime(2024, 3, 31, 9, 0, tzinfo=kst)).eligible)
        with self.assertRaises(c.CutoffError):
            c.eligibility(m, published_at=datetime(2024, 4, 1, 0, 0), received_at=datetime(2024, 4, 1, 0, 0))
        with self.assertRaises(c.CutoffError):
            c.eligibility(m, published_at="2024-04-01", received_at="2024-04-01")

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
            self.assertFalse(c.eligibility(m, published_at=day, received_at=day).eligible)

    def test_missing_snapshot_source_or_check_date(self):
        for missing in ("snapshot_id", "source_url", "checked_on"):
            with self.subTest(missing=missing):
                m = card(**{missing: None})
                self.assertFalse(m.verified)
                self.assertFalse(c.eligibility(m, published_at=date(2099, 1, 1), received_at=date(2099, 1, 1)).eligible)

    def test_model_outside_the_registry(self):
        self.assertFalse(c.REGISTRY.eligibility("some-new-model", published_at=date(2099, 1, 1), received_at=date(2099, 1, 1)).eligible)
        self.assertFalse(c.eligibility(None, published_at=date(2099, 1, 1), received_at=date(2099, 1, 1)).eligible)


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
                self.assertFalse(c.eligibility(m, published_at=date(2099, 1, 1), received_at=date(2099, 1, 1)).eligible)

    def test_unverified_base_makes_the_in_house_model_unverified(self):
        base = card(key="base", source_url=None)     # has a date but no source
        m = c.in_house_card("own-1", base=base, finetune_through=date(2025, 1, 31), snapshot_id="s",
                            source_url=URL, checked_on=date(2026, 11, 24))
        self.assertFalse(m.verified)

    def test_base_must_follow_the_cutoff_rule(self):
        with self.assertRaises(c.CutoffError):
            c.in_house_card("own-1", base=card(rule=c.Rule.BASELINE), finetune_through=date(2025, 1, 31),
                            snapshot_id="s", source_url=URL, checked_on=date(2026, 11, 24))


class BackfilledArticles(unittest.TestCase):
    """PREREG_V0 5.1: an old article fetched today has received_at = today. The model may have been
    trained on it, so the earlier of the two days decides."""

    def test_old_article_received_today_is_not_eligible(self):
        claude = c.REGISTRY.get("claude-fable-5-2")                  # cutoff 2026-06-30, eligible from 2026-09-30
        published = datetime(2020, 3, 2, 13, 0, tzinfo=timezone.utc)
        received = datetime(2026, 11, 24, 3, 0, tzinfo=timezone.utc)
        result = c.eligibility(claude, published_at=published, received_at=received)
        self.assertFalse(result.eligible)
        self.assertIn("published or received before", result.reason)
        self.assertFalse(c.REGISTRY.eligibility("claude-fable-5-2", published_at=published,
                                                received_at=received).eligible)

    def test_the_earlier_day_decides_in_both_orders(self):
        m = card()                                                   # eligible from 2024-03-31
        early, late = date(2024, 3, 30), date(2024, 4, 2)
        self.assertFalse(c.eligibility(m, published_at=early, received_at=late).eligible)
        self.assertFalse(c.eligibility(m, published_at=late, received_at=early).eligible)   # vendor clock ahead
        self.assertTrue(c.eligibility(m, published_at=date(2024, 3, 31), received_at=late).eligible)
        self.assertEqual(c.article_day(early, late), early)
        self.assertEqual(c.article_day(late, early), early)

    def test_sentinel_timestamps_fail_closed_with_a_cutoff_error(self):
        m = card()
        ok = datetime(2026, 11, 24, tzinfo=timezone.utc)
        low = datetime(1, 1, 1, 0, 0, tzinfo=timezone(timedelta(hours=9)))             # no UTC day exists
        high = datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone(timedelta(hours=-5)))
        for bad in (low, high):
            with self.subTest(bad=bad.isoformat()), self.assertRaises(c.CutoffError):
                c.eligibility(m, published_at=bad, received_at=ok)
        zero_utc = datetime(1, 1, 1, tzinfo=timezone.utc)
        self.assertFalse(c.eligibility(m, published_at=zero_utc, received_at=ok).eligible)

    def test_a_plain_date_is_taken_as_the_utc_day(self):
        claude = c.REGISTRY.get("claude-fable-5-2")                                    # eligible from 2026-09-30
        kst = timezone(timedelta(hours=9))
        moment = datetime(2026, 9, 30, 0, 30, tzinfo=kst)                              # 2026-09-29 15:30 UTC
        later = date(2026, 11, 24)
        self.assertFalse(c.eligibility(claude, published_at=moment, received_at=later).eligible)
        self.assertTrue(c.eligibility(claude, published_at=moment.date(), received_at=later).eligible)   # caller's
        # local date, not the UTC day: the documented reason to pass the record's datetimes
        self.assertFalse(c.eligibility(claude, published_at=moment.astimezone(timezone.utc).date(),
                                       received_at=later).eligible)

    def test_both_timestamps_are_required_by_keyword(self):
        m = card()
        with self.assertRaises(TypeError):
            c.eligibility(m, date(2024, 4, 2))
        with self.assertRaises(TypeError):
            c.eligibility(m, received_at=date(2024, 4, 2))
        with self.assertRaises(TypeError):
            c.REGISTRY.eligibility("claude-fable-5-2", date(2026, 10, 1))
        with self.assertRaises(c.CutoffError):
            c.eligibility(m, published_at=datetime(2024, 4, 1, 0, 0), received_at=date(2024, 4, 2))
        with self.assertRaises(c.CutoffError):
            c.eligibility(m, published_at=None, received_at=date(2024, 4, 2))


class Baselines(unittest.TestCase):
    def test_pinned_named_baseline_is_usable_at_any_date(self):
        for key in sorted(c.BASELINE_KEYS):
            m = card(key=key, rule=c.Rule.BASELINE, cutoff=None)
            self.assertTrue(m.verified, key)
            self.assertTrue(c.eligibility(m, published_at=date(2015, 1, 2), received_at=date(2015, 1, 2)).eligible)
        self.assertEqual(c.BASELINE_KEYS, {"loughran-mcdonald", "ProsusAI/finbert"})

    def test_unpinned_baseline_is_not(self):
        m = card(key="ProsusAI/finbert", rule=c.Rule.BASELINE, cutoff=None, snapshot_id=None)
        self.assertFalse(c.eligibility(m, published_at=date(2015, 1, 2), received_at=date(2015, 1, 2)).eligible)

    def test_labelling_another_model_a_baseline_does_not_exempt_it(self):
        m = card(key="any-llm-2030", rule=c.Rule.BASELINE, cutoff=None)
        self.assertFalse(m.verified)
        self.assertFalse(c.eligibility(m, published_at=date(2015, 1, 2), received_at=date(2015, 1, 2)).eligible)
        self.assertFalse(c.REGISTRY.with_card(m).eligibility(
            "any-llm-2030", published_at=date(2015, 1, 2), received_at=date(2015, 1, 2)).eligible)

    def test_a_baseline_key_may_carry_its_snapshot(self):
        """Two snapshots of one baseline, each with its own verified row; other look-alike keys are not baselines."""
        day = date(2015, 1, 2)
        registry = c.Registry((
            card(key="loughran-mcdonald@1993-2023", rule=c.Rule.BASELINE, cutoff=None, snapshot_id="LM 1993-2023"),
            card(key="loughran-mcdonald@1993-2025", rule=c.Rule.BASELINE, cutoff=None, snapshot_id="LM 1993-2025"),
            card(key="ProsusAI/finbert@0bc2ac1", rule=c.Rule.BASELINE, cutoff=None),
        ))
        for key in ("loughran-mcdonald@1993-2023", "loughran-mcdonald@1993-2025", "ProsusAI/finbert@0bc2ac1"):
            self.assertTrue(registry.eligibility(key, published_at=day, received_at=day).eligible, key)
        for key in ("loughran-mcdonald-2024", "prosusai/finbert", "ProsusAI/finbert@", "ProsusAI/finbert-tone",
                    "x@loughran-mcdonald", "other/ProsusAI/finbert@abc"):
            self.assertFalse(c.is_baseline_key(key), key)
            self.assertFalse(card(key=key, rule=c.Rule.BASELINE, cutoff=None).verified, key)
        self.assertFalse(c.is_baseline_key(None))
        with self.assertRaises(c.CutoffError):
            registry.with_card(card(key="loughran-mcdonald@1993-2025", rule=c.Rule.BASELINE, cutoff=None))

    def test_pinned_baseline_rows_of_the_shipped_table_are_verified(self):
        for key in sorted(c.BASELINE_KEYS):
            row = c.REGISTRY.get(key)
            self.assertTrue(row.verified, key)
            self.assertIsNone(row.cutoff)                      # the cutoff column of a baseline row stays empty

    def test_a_baseline_card_cannot_carry_a_cutoff(self):
        for field in ("base_cutoff", "finetune_through"):
            with self.subTest(field=field), self.assertRaises(c.CutoffError):
                card(key="ProsusAI/finbert", rule=c.Rule.BASELINE, cutoff=None, **{field: date(2020, 1, 1)})
        with self.assertRaises(c.CutoffError):
            card(key="ProsusAI/finbert", rule=c.Rule.BASELINE, cutoff=date(2030, 1, 1))
        with self.assertRaises(c.CutoffError):
            card(key="ProsusAI/finbert", rule=c.Rule.BASELINE, cutoff=None, in_house=True)


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
        def on(key, day):
            return c.REGISTRY.eligibility(key, published_at=day, received_at=day).eligible
        self.assertTrue(on("ProsusAI/finbert", date(2020, 1, 2)))            # pinned, named baseline
        self.assertTrue(on("loughran-mcdonald", date(2015, 1, 2)))
        self.assertFalse(on("qwen3-candidates", date(2099, 1, 1)))           # no public cutoff
        chrono = [m for m in c.REGISTRY if m.family == "ChronoGPT 빈티지"]
        self.assertEqual(len(chrono), 26)
        self.assertEqual({len(m.snapshot_id) for m in chrono}, {40})
        first = c.REGISTRY.get("manelalab/chrono-gpt-v1-19991231")
        self.assertEqual((first.cutoff, first.eligible_from), (date(1999, 12, 31), date(2000, 3, 31)))
        # the 2014 vintage may score 2015-03-31 onwards, not January 2015
        self.assertFalse(on("manelalab/chrono-gpt-v1-20141231", date(2015, 1, 15)))
        self.assertTrue(on("manelalab/chrono-gpt-v1-20141231", date(2015, 3, 31)))
        # a 2014 article fetched in 2026 is still a 2014 article for the 2014 vintage
        self.assertFalse(c.REGISTRY.eligibility("manelalab/chrono-gpt-v1-20141231", published_at=date(2014, 6, 2),
                                                received_at=date(2026, 11, 24)).eligible)
        self.assertFalse(on("quantgpt-in-house", date(2099, 1, 1)))
        claude = c.REGISTRY.get("claude-fable-5-2")
        self.assertEqual((claude.cutoff, claude.eligible_from), (date(2026, 6, 30), date(2026, 9, 30)))
        self.assertFalse(c.REGISTRY.eligibility("claude-fable-5-2", published_at=date(2024, 12, 31), received_at=date(2024, 12, 31)).eligible)
        self.assertTrue(c.REGISTRY.eligibility("claude-fable-5-2", published_at=date(2026, 9, 30), received_at=date(2026, 9, 30)).eligible)

    def test_duplicate_keys_are_refused(self):
        with self.assertRaises(c.CutoffError):
            c.REGISTRY.with_card(card(key="claude-fable-5-2"))
        self.assertEqual(len(c.REGISTRY.with_card(card(key="new-model"))), len(c.REGISTRY) + 1)


class Boundaries(unittest.TestCase):
    """Import and clock rules for cutoffs.py are checked with the other DIDM-2/3 modules in
    tests/didm_contract_acceptance.py (one AST check for all of them)."""

    def test_cutoffs_is_in_the_shared_boundary_check(self):
        from tests import didm_contract_acceptance as contract
        self.assertIn("core/didm/llm/cutoffs.py", contract.Boundaries.FILES)
        source = (ROOT / "core" / "didm" / "llm" / "cutoffs.py").read_text(encoding="utf-8")
        check = contract.Boundaries()
        self.assertEqual(check.problems(source), [])                # run here too, so this module stands alone
        self.assertNotEqual(check.problems(source + "\nimport socket\n"), [])
        self.assertNotEqual(check.problems(source + "\nSTAMP = datetime.now(timezone.utc)\n"), [])
        self.assertEqual(ast.parse((ROOT / "core" / "didm" / "llm" / "cutoffs.py").read_text(encoding="utf-8")).body[0]
                         .value.value[:6], "DIDM-3")


if __name__ == "__main__":
    unittest.main()
