"""DIDM-1: V0 score schema accepts well-formed records and rejects bad ones. No network."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.didm.llm import schema as s

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "didm"


def good() -> dict:
    return json.loads((FIXTURES / "score_record_v0.json").read_text(encoding="utf-8"))


class ScoreRecordAccepts(unittest.TestCase):
    def test_fixture_passes(self):
        rec = s.validate_record(good())
        self.assertEqual(rec.event_type, s.EventType.MONETARY_POLICY)
        self.assertEqual(rec.ess_like_0_100, 20.0)
        self.assertEqual(rec.received_at.isoformat(), "2026-11-05T19:15:00+00:00")

    def test_round_trip(self):
        rec = s.validate_record(good())
        self.assertEqual(s.validate_record(rec.as_dict()), rec)

    def test_schema_version_optional_on_input(self):
        raw = good()
        raw.pop("schema_version")
        self.assertEqual(s.validate_record(raw).schema_version, s.SCHEMA_VERSION)

    def test_target_none(self):
        raw = good()
        raw.update(target_kind="none", entity_id=None, event_type="none")
        self.assertIsNone(s.validate_record(raw).entity_id)


class ScoreRecordRejects(unittest.TestCase):
    def assertRejects(self, raw, fragment):
        with self.assertRaises(s.SchemaError) as cm:
            s.validate_record(raw)
        self.assertIn(fragment, str(cm.exception))

    def test_score_out_of_range(self):
        for field, value in (("relevance_0_100", 100.5), ("relevance_0_100", -1),
                             ("novelty_24h_0_100", 101), ("p_credibility", 1.2)):
            raw = good()
            raw[field] = value
            self.assertRejects(raw, field)

    def test_missing_received_at(self):
        raw = good()
        raw.pop("received_at")
        self.assertRejects(raw, "received_at")

    def test_null_received_at(self):
        raw = good()
        raw["received_at"] = None
        self.assertRejects(raw, "received_at")

    def test_naive_timestamp(self):
        raw = good()
        raw["received_at"] = "2026-11-05T19:15:00"
        self.assertRejects(raw, "timezone")

    def test_unknown_event_type(self):
        raw = good()
        raw["event_type"] = "weather"
        self.assertRejects(raw, "event_type")

    def test_unknown_confirmation(self):
        raw = good()
        raw["market_confirmation"] = "MAYBE"
        self.assertRejects(raw, "market_confirmation")

    def test_unknown_field(self):
        raw = good()
        raw["ravenpack_ess"] = 50
        self.assertRejects(raw, "unknown fields")

    def test_ess_must_match_direction(self):
        raw = good()
        raw["ess_like_0_100"] = 55.0
        self.assertRejects(raw, "ess_like_0_100")

    def test_entropy_must_match(self):
        raw = good()
        raw["uncertainty_entropy"] = 0.1
        self.assertRejects(raw, "uncertainty_entropy")

    def test_direction_must_sum_to_one(self):
        raw = good()
        raw["direction_probs"] = [0.5, 0.5, 0.5]
        self.assertRejects(raw, "sum to 1")

    def test_bad_prompt_hash(self):
        raw = good()
        raw["prompt_sha256"] = "ABC"
        self.assertRejects(raw, "prompt_sha256")

    def test_bool_is_not_a_number(self):
        raw = good()
        raw["relevance_0_100"] = True
        self.assertRejects(raw, "relevance_0_100")

    def test_entity_required_for_firm(self):
        raw = good()
        raw.update(target_kind="firm", entity_id=None)
        self.assertRejects(raw, "entity_id")


class Helpers(unittest.TestCase):
    def test_ess_like(self):
        self.assertEqual(s.ess_like(0.5, 0.5), 50.0)
        self.assertEqual(s.ess_like(1.0, 0.0), 100.0)
        self.assertEqual(s.ess_like(0.0, 1.0), 0.0)
        with self.assertRaises(s.SchemaError):
            s.ess_like(0.7, 0.7)

    def test_novelty(self):
        self.assertEqual(s.novelty_24h(1, 0.5), 100.0)
        self.assertEqual(s.novelty_24h(3, 0.5), 25.0)
        with self.assertRaises(s.SchemaError):
            s.novelty_24h(0, 0.5)
        with self.assertRaises(s.SchemaError):
            s.novelty_24h(1, 1.0)

    def test_enum_size_v0(self):
        # DIDM 5.1: K <= 12 typed events in V0, plus "none".
        self.assertEqual(len([e for e in s.EventType if e is not s.EventType.NONE]), 12)


class GoldLabelFormat(unittest.TestCase):
    def test_stage1_example_passes(self):
        raw = json.loads((FIXTURES / "gold_label_v0.json").read_text(encoding="utf-8"))
        label = s.validate_gold(raw)
        self.assertTrue(label.is_new_event)
        self.assertEqual(label.direction, s.Direction.NEGATIVE)

    def test_gold_rejects_unknown_type(self):
        raw = json.loads((FIXTURES / "gold_label_v0.json").read_text(encoding="utf-8"))
        raw["event_type"] = "sports"
        with self.assertRaises(s.SchemaError):
            s.validate_gold(raw)

    def test_gold_rejects_missing_received_at(self):
        raw = json.loads((FIXTURES / "gold_label_v0.json").read_text(encoding="utf-8"))
        raw.pop("received_at")
        with self.assertRaises(s.SchemaError):
            s.validate_gold(raw)


if __name__ == "__main__":
    unittest.main()
