"""QSS v0: the 34 stored cards validate and round-trip byte for byte."""
import copy
import json
import math
import unittest

from _path import CARDS

from quantgpt.checks.schema import SchemaError
from quantgpt.contracts import qss

DRAFT = dict(card_id="S_X1_demo", kind="strategy", hypothesis="A 126-session trend switch lowers drawdown.",
             rules={"family": "trend_switch", "grid": [{"rule": "sma", "lookback": 126}]},
             market={"symbols": ["AAA", "BBB"], "venue": "synthetic"},
             data={"source": "synthetic", "start": "2015-01-01", "end": "2020-12-31"},
             costs={"cost_bps": 3.0}, protocol={"w_is": 756, "w_oos": 126}, n_planned=1, seed=11)

CARD = {
    "card_id": "S_X1_demo", "kind": "strategy", "hypothesis": "A synthetic rule.", "rules": {"family": "demo"},
    "universe": {"symbols": ["AAA"]}, "data": {"start": "2015-01-01", "end": "2020-12-31", "sessions": 1500},
    "costs": {"cost_bps": 3.0}, "protocol": {"w_is": 756},
    "trials": {"N_planned": 2, "N_total": 3, "ledger": ["run 2: one more lookback"]}, "seed": 11,
    "stats": {"sr_oos": 0.4, "bench_sr": math.nan, "hi": math.inf, "lo": -math.inf},
    "tests": {"dsr": 0.5, "pbo": 0.3}, "decision": "REJECT", "decision_reason": "deflated Sharpe below 0.95",
    "revise_target": None, "lines": ["Deflated Sharpe 0.50 after 3 trials: fails."],
    "decay_haircut": {"factor": 0.6, "source": "synthetic"}, "created": "2026-09-27", "author": "test",
    "results_file": "results.csv", "results_md5": "0" * 32, "citations": ["none"],
}


@unittest.skipUnless(CARDS.is_dir(), "stored research cards are not present")
class StoredCardTests(unittest.TestCase):
    def setUp(self):
        self.files = sorted(CARDS.glob("*.json"))

    def test_all_34_cards_validate_and_round_trip_byte_for_byte(self):
        self.assertEqual(len(self.files), 34)
        kinds = {}
        for path in self.files:
            with self.subTest(card=path.name):
                raw = path.read_text(encoding="utf-8")
                doc = qss.card_to_qss(json.loads(raw))
                qss.validate_qss(doc, "recorded")
                strict = json.loads(qss.qss_text(doc))          # strict JSON survives a reparse
                self.assertEqual(qss.card_text(qss.qss_to_card(strict)), raw)
                self.assertEqual(doc["card_id"], path.stem)
                kinds[doc["kind"]] = kinds.get(doc["kind"], 0) + 1
        self.assertEqual(kinds, {"strategy": 17, "distribution": 9, "model": 8})

    def test_strict_text_has_no_nan_token_but_the_cards_do(self):
        raw_nan = sum(p.read_text(encoding="utf-8").count("NaN") for p in self.files)
        self.assertGreater(raw_nan, 0)
        for path in self.files:
            text = qss.qss_text(qss.card_to_qss(json.loads(path.read_text(encoding="utf-8"))))
            json.loads(text, parse_constant=lambda token: self.fail(f"{path.name}: {token}"))


class QssRuleTests(unittest.TestCase):
    def test_valid_documents(self):
        draft = qss.draft_from(**DRAFT)
        self.assertEqual(draft["stage"], "draft")
        recorded = qss.card_to_qss(copy.deepcopy(CARD))
        self.assertEqual(recorded["evidence"]["stats"]["bench_sr"], {"$nonfinite": "NaN"})
        self.assertEqual(recorded["evidence"]["stats"]["hi"], {"$nonfinite": "+Infinity"})
        self.assertEqual(qss.card_text(qss.qss_to_card(recorded)), qss.card_text(CARD))
        for kind in qss.KINDS:
            qss.draft_from(**{**DRAFT, "kind": kind})
        qss.draft_from(**{**DRAFT, "costs": None, "protocol": None})
        passing = copy.deepcopy(CARD); passing["decision"] = "PASS"
        self.assertEqual(qss.card_to_qss(passing)["decision"]["verdict"], "PASS")

    def test_a_draft_cannot_carry_evidence_or_a_decision(self):
        draft = qss.draft_from(**DRAFT)
        recorded = qss.card_to_qss(copy.deepcopy(CARD))
        for name in ("evidence", "decision", "decay_haircut", "provenance"):
            with self.subTest(name=name), self.assertRaises(SchemaError):
                qss.validate_qss({**draft, name: recorded[name]})
        with self.assertRaises(SchemaError):
            qss.validate_qss({**draft, "trials": recorded["trials"]})

    def test_rejections(self):
        draft = qss.draft_from(**DRAFT)
        recorded = qss.card_to_qss(copy.deepcopy(CARD))
        bad = [
            {**draft, "qss_version": "qss-v1"},
            {**draft, "kind": "signal"},
            {**draft, "hypothesis": "  "},
            {**draft, "card_id": "1 bad id"},
            {**draft, "trials": {"n_planned": 0}},
            {**draft, "rules": {"x": float("nan")}},
            {**draft, "stage": "final"},
            {**draft, "order": {"side": "buy"}},
            {k: v for k, v in draft.items() if k != "market"},
            {**recorded, "decision": {**recorded["decision"], "verdict": "BUY"}},
            {**recorded, "trials": {**recorded["trials"], "n_total": 1}},
            {**recorded, "evidence": {**recorded["evidence"], "results_md5": "xyz"}},
            {**recorded, "provenance": {**recorded["provenance"], "created": "yesterday"}},
            {**recorded, "decay_haircut": {"factor": 1.5, "source": "s"}},
        ]
        for i, doc in enumerate(bad):
            with self.subTest(i=i), self.assertRaises(SchemaError):
                qss.validate_qss(doc)
        with self.assertRaises(SchemaError):
            qss.validate_qss(draft, "recorded")

    def test_a_pass_strategy_card_must_show_dsr_and_pbo(self):
        card = copy.deepcopy(CARD); card["decision"] = "PASS"; card["tests"] = {"dsr": 0.97}
        with self.assertRaises(SchemaError):
            qss.card_to_qss(card)

    def test_card_layout_is_enforced(self):
        reordered = dict(reversed(list(CARD.items())))
        extra = {**CARD, "order": "buy"}
        reserved = copy.deepcopy(CARD); reserved["stats"]["x"] = {"$nonfinite": "NaN", "y": 1}
        for card in (reordered, extra, reserved, {k: v for k, v in CARD.items() if k != "seed"}):
            with self.assertRaises(SchemaError):
                qss.card_to_qss(card)
        doc = qss.card_to_qss(copy.deepcopy(CARD)); doc["evidence"]["stats"]["hi"] = {"$nonfinite": "big"}
        with self.assertRaises(SchemaError):
            qss.qss_to_card(doc)


if __name__ == "__main__":
    unittest.main()
