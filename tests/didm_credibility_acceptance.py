"""DIDM-9: credibility state and Version 0 shock construction. Synthetic reports and records only: no real
article, no market data, no model, no network, no clock."""
from __future__ import annotations

import ast
import math
import random
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.didm.credibility import shock
from core.didm.credibility import state as st
from core.didm.llm import schema as s

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc
T0 = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)
W = st.PLACEHOLDER                      # LLR 2.0 / 1.0 / 0.3, even prior odds


def rep(i, minutes, tier, stance=1, origin=None, official=False, event="ev-1"):
    return st.Report(f"a{i}", event, T0 + timedelta(minutes=minutes), tier, origin or f"cl-{i}", stance, official)


def logistic(x):
    return 1 / (1 + math.exp(-x))


class State(unittest.TestCase):
    def test_log_odds_accumulate_by_hand(self):
        steps = st.path([rep(1, 0, 3), rep(2, 10, 2), rep(3, 20, 1)], "ev-1", W)
        self.assertEqual([round(x.pi_after, 6) for x in steps],
                         [round(logistic(0.3), 6), round(logistic(1.3), 6), round(logistic(3.3), 6)])
        self.assertAlmostEqual(steps[0].pi_before, 0.5)
        self.assertEqual([x.pi_before for x in steps[1:]], [x.pi_after for x in steps[:-1]])
        self.assertTrue(all(x.resolved is None for x in steps))

    def test_a_contradicting_report_lowers_belief(self):
        steps = st.path([rep(1, 0, 2), rep(2, 10, 2, stance=-1), rep(3, 20, 1, stance=-1)], "ev-1", W)
        self.assertAlmostEqual(steps[1].pi_after, 0.5)                    # +1.0 then -1.0
        self.assertAlmostEqual(steps[2].pi_after, logistic(-2.0))

    def test_copies_of_one_origin_count_once(self):
        """The 2025-04 pattern: one social post re-posted many times is still one source."""
        cascade = [rep(i, i, 3, origin="cl-same") for i in range(1, 41)]
        steps = st.path(cascade, "ev-1", W)
        self.assertAlmostEqual(steps[-1].pi_after, logistic(0.3))          # forty copies = one report
        self.assertEqual([x.counted for x in steps[:3]], [1.0, 0.0, 0.0])
        independent = [rep(i, i, 3) for i in range(1, 41)]                  # forty separate origins
        self.assertAlmostEqual(st.path(independent, "ev-1", W)[-1].pi_after, st.PI_CEILING)
        half = st.Weights(W.llr_by_tier, W.prior_logit, copy_weight=0.5)
        self.assertAlmostEqual(st.path(cascade[:3], "ev-1", half)[-1].pi_after, logistic(0.3 + 0.15 + 0.15))

    def test_unresolved_belief_is_never_certain(self):
        many = [rep(i, i, 1) for i in range(1, 11)]
        self.assertEqual(st.path(many, "ev-1", W)[-1].pi_after, 0.99)
        against = [rep(i, i, 1, stance=-1) for i in range(1, 11)]
        self.assertEqual(st.path(against, "ev-1", W)[-1].pi_after, 0.01)
        self.assertEqual((st.PI_FLOOR, st.PI_CEILING), (0.01, 0.99))

    def test_official_statement_resolves_and_nothing_moves_it_afterwards(self):
        steps = st.path([rep(1, 0, 3), rep(2, 10, 1, official=True), rep(3, 20, 3, stance=-1)], "ev-1", W)
        self.assertEqual([x.pi_after for x in steps[1:]], [1.0, 1.0])
        self.assertEqual([x.resolved for x in steps], [None, "confirmed", "confirmed"])
        self.assertEqual(steps[2].counted, 0.0)
        denied = st.path([rep(1, 0, 3), rep(2, 5, 2), rep(3, 10, 1, stance=-1, official=True)], "ev-1", W)
        self.assertEqual((denied[-1].pi_after, denied[-1].resolved), (0.0, "debunked"))

    def test_the_two_readings_are_weights_fields_and_change_the_numbers(self):
        self.assertEqual((W.copy_weight, W.official_resolves), (0.0, True))
        cascade = [rep(i, i, 3, origin="cl-same") for i in range(1, 41)]
        partial = st.Weights(W.llr_by_tier, W.prior_logit, copy_weight=0.5)
        self.assertAlmostEqual(st.path(cascade, "ev-1", W)[-1].pi_after, 0.5744, places=4)
        self.assertEqual(st.path(cascade, "ev-1", partial)[-1].pi_after, 0.99)        # 0.3 + 39 * 0.15 = 6.15
        official = [rep(1, 0, 3), rep(2, 10, 1, official=True)]
        soft = st.Weights(W.llr_by_tier, W.prior_logit, official_resolves=False)
        self.assertEqual(st.path(official, "ev-1", W)[-1].pi_after, 1.0)
        self.assertAlmostEqual(st.path(official, "ev-1", soft)[-1].pi_after, 0.9089, places=4)   # logistic(2.3)
        self.assertIsNone(st.path(official, "ev-1", soft)[-1].resolved)
        self.assertNotEqual(W.version, soft.version)
        self.assertNotEqual(W.version, partial.version)

    def test_point_in_time(self):
        reports = [rep(1, 0, 3), rep(2, 10, 2), rep(3, 20, 1, official=True)]
        self.assertIsNone(st.pi_at(reports, "ev-1", T0 - timedelta(minutes=1), W))
        self.assertAlmostEqual(st.pi_at(reports, "ev-1", T0, W), logistic(0.3))            # at the receipt time
        self.assertAlmostEqual(st.pi_at(reports, "ev-1", T0 + timedelta(minutes=15), W), logistic(1.3))
        self.assertEqual(st.pi_at(reports, "ev-1", T0 + timedelta(minutes=20), W), 1.0)
        # later reports and the order of the list never change an earlier answer
        self.assertEqual(st.pi_at(list(reversed(reports)), "ev-1", T0 + timedelta(minutes=15), W),
                         st.pi_at(reports[:2], "ev-1", T0 + timedelta(minutes=15), W))
        self.assertIsNone(st.pi_at(reports, "another-event", T0 + timedelta(hours=1), W))
        with self.assertRaises(st.CredibilityError):
            st.pi_at(reports, "ev-1", datetime(2026, 11, 2, 9, 0), W)

    def test_events_do_not_mix(self):
        reports = [rep(1, 0, 1, event="ev-1"), rep(2, 5, 1, stance=-1, event="ev-2")]
        self.assertGreater(st.path(reports, "ev-1", W)[-1].pi_after, 0.8)
        self.assertLess(st.path(reports, "ev-2", W)[-1].pi_after, 0.2)

    def test_impulses_and_the_debunk_reversal(self):
        steps = st.path([rep(1, 0, 2), rep(2, 10, 2), rep(3, 20, 1, stance=-1, official=True)], "ev-1", W)
        moves = [m for _, m in st.impulses(steps, impact_if_true=-0.10)]            # a -10% event if true
        p1, p2 = logistic(1.0), logistic(2.0)
        self.assertAlmostEqual(moves[0], p1 * -0.10)
        self.assertAlmostEqual(moves[1], (p2 - p1) * -0.10)
        self.assertAlmostEqual(moves[2], -p2 * -0.10)                               # -pi_before * D
        self.assertAlmostEqual(sum(moves), 0.0)                                     # everything priced is reversed
        confirmed = st.path([rep(1, 0, 2), rep(2, 10, 1, official=True)], "ev-1", W)
        self.assertAlmostEqual(sum(m for _, m in st.impulses(confirmed, 0.05)), 0.05)   # total impact D
        with self.assertRaises(st.CredibilityError):
            st.impulses(steps, float("nan"))

    def test_bad_reports(self):
        for kwargs in (dict(source_tier=4), dict(stance=0), dict(stance=True), dict(official="yes"),
                       dict(received_at=datetime(2026, 11, 2, 9, 0))):
            base = dict(article_id="a", event_id="e", received_at=T0, source_tier=1, origin_cluster_id="c", stance=1)
            with self.subTest(kwargs=kwargs), self.assertRaises(st.CredibilityError):
                st.Report(**dict(base, **kwargs))
        with self.assertRaises(st.CredibilityError):
            st.path([rep(1, 0, 1), rep(1, 5, 1)], "ev-1", W)
        with self.assertRaises(st.CredibilityError):
            st.Weights((1.0, 1.0), 0.0)
        with self.assertRaises(st.CredibilityError):
            st.Weights((1.0, 1.0, 1.0), 0.0, copy_weight=1.5)


class LearnedWeights(unittest.TestCase):
    def world(self, n=600, seed=2):
        """Events are true with probability 0.5; each tier reports with its own accuracy."""
        rng = random.Random(seed)
        acc = {1: 0.90, 2: 0.75, 3: 0.55}
        reports, outcomes, k = [], {}, 0
        for e in range(n):
            truth = rng.random() < 0.5
            outcomes[f"ev-{e}"] = truth
            for _ in range(rng.randint(1, 5)):
                tier = rng.choice((1, 2, 3))
                says_true = truth if rng.random() < acc[tier] else not truth
                k += 1
                reports.append(st.Report(f"a{k}", f"ev-{e}", T0 + timedelta(minutes=k), tier, f"cl-{k}",
                                         1 if says_true else -1))
        return outcomes, reports, acc

    def test_weights_are_learned_and_ordered_by_tier(self):
        outcomes, reports, acc = self.world()
        w = st.fit_weights(outcomes, reports)
        self.assertEqual(w.fitted_on, 600)
        self.assertRegex(w.version, r"^cred-fitted-[0-9a-f]{12}$")
        self.assertRegex(st.PLACEHOLDER.version, r"^cred-placeholder-")
        for got, tier in zip(w.llr_by_tier, (1, 2, 3)):
            self.assertAlmostEqual(got, math.log(acc[tier] / (1 - acc[tier])), delta=0.45)   # the true log-odds
        self.assertGreater(w.llr_by_tier[0], w.llr_by_tier[1])
        self.assertGreater(w.llr_by_tier[1], w.llr_by_tier[2])
        self.assertAlmostEqual(w.prior_logit, 0.0, delta=0.3)
        self.assertEqual(st.fit_weights(outcomes, reports), w)                   # deterministic

    def test_reports_after_the_resolution_are_not_used_to_learn(self):
        row = st.design_row([rep(1, 0, 3), rep(2, 5, 1, official=True), rep(3, 9, 3), rep(4, 12, 2)], "ev-1")
        self.assertEqual(row, [1.0, 0.0, 0.0, 1.0])
        same_origin = st.design_row([rep(1, 0, 3, origin="o"), rep(2, 5, 3, origin="o"), rep(3, 9, 2, stance=-1)], "ev-1")
        self.assertEqual(same_origin, [1.0, 0.0, -1.0, 1.0])

    def test_too_few_or_one_sided_events_are_refused(self):
        outcomes, reports, _ = self.world(n=20)
        with self.assertRaises(st.CredibilityError):
            st.fit_weights(outcomes, reports)
        outcomes, reports, _ = self.world(n=60)
        with self.assertRaises(st.CredibilityError):
            st.fit_weights({k: True for k in outcomes}, reports)


def record(i, minutes, entity="US:SYNM", etype="earnings", probs=(0.7, 0.1, 0.2), relevance=90.0, cred=0.8,
           cluster=None, kind="firm"):
    raw = {"record_id": f"r{i}", "source_id": "synthetic", "target_kind": kind,
           "entity_id": None if kind == "none" else entity,
           "published_at": (T0 + timedelta(minutes=minutes - 5)).isoformat(),
           "received_at": (T0 + timedelta(minutes=minutes)).isoformat(), "relevance_0_100": relevance,
           "ess_like_0_100": 50 + 50 * (probs[0] - probs[1]), "novelty_0_100": 90.0,
           "origin_cluster_id": cluster or f"cl-{i}", "event_type": etype, "direction_probs": list(probs),
           "uncertainty_entropy": s.entropy(list(probs)), "p_credibility": cred,
           "market_confirmation": "PENDING", "model_version": "toy", "prompt_sha256": "ab" * 32}
    return s.validate_record(raw)


PREV, NOW = T0, T0 + timedelta(hours=24)


def build(records, **kw):
    return shock.build(records, previous_decision=PREV, decision=NOW, **kw)


class Shocks(unittest.TestCase):
    def test_sum_of_credibility_times_expected_sign_by_hand(self):
        cells, dropped = build([record(1, 60, probs=(0.7, 0.1, 0.2), cred=0.8),
                                record(2, 120, probs=(0.2, 0.6, 0.2), cred=0.5)])
        cell = cells[("US:SYNM", s.EventType.EARNINGS)]
        self.assertAlmostEqual(cell.shock, 0.8 * 0.6 + 0.5 * -0.4)                 # 0.28
        self.assertAlmostEqual(cell.abs_shock, 0.28)
        expected_u = (0.8 * s.entropy([0.7, 0.1, 0.2]) + 0.5 * s.entropy([0.2, 0.6, 0.2])) / 1.3
        self.assertAlmostEqual(cell.uncertainty, expected_u)
        self.assertEqual((cell.n_records, cell.record_ids), (2, ("r1", "r2")))
        self.assertEqual(dropped, shock.Dropped())

    def test_cells_are_per_entity_and_event_type(self):
        cells, _ = build([record(1, 60), record(2, 70, entity="KR:900001"),
                          record(3, 80, etype="management", probs=(0.1, 0.8, 0.1))])
        self.assertEqual(set(cells), {("US:SYNM", s.EventType.EARNINGS), ("KR:900001", s.EventType.EARNINGS),
                                      ("US:SYNM", s.EventType.MANAGEMENT)})
        self.assertLess(cells[("US:SYNM", s.EventType.MANAGEMENT)].shock, 0)

    def test_only_articles_received_in_the_decision_window(self):
        """received_at <= decision time, no exception; and nothing from before the previous decision."""
        cells, dropped = build([record(1, 0), record(2, 1), record(3, 24 * 60), record(4, 24 * 60 + 1)])
        self.assertEqual(cells[("US:SYNM", s.EventType.EARNINGS)].record_ids, ("r2", "r3"))
        self.assertEqual(dropped.late_or_early, 2)
        with self.assertRaises(shock.ShockError):
            shock.build([], previous_decision=NOW, decision=PREV)
        with self.assertRaises(shock.ShockError):
            shock.build([], previous_decision=datetime(2026, 11, 2), decision=NOW)

    def test_relevance_floor_is_75(self):
        self.assertEqual(shock.RELEVANCE_MIN, 75.0)
        prereg = (ROOT / "docs" / "didm" / "PREREG_V0.md").read_text(encoding="utf-8")
        self.assertIn("P̂(대상이 기사의 주제) ≥ 0.75만 신호 (`relevance_0_100 ≥ 75`)", prereg)
        self.assertIn("같은 `origin_cluster_id`는 1건으로 셈", prereg)
        self.assertIn("`received_at ≤ 결정 시각`인 것만. 예외 없음", prereg)
        cells, dropped = build([record(1, 60, relevance=74.99), record(2, 70, relevance=75.0)])
        self.assertEqual(cells[("US:SYNM", s.EventType.EARNINGS)].record_ids, ("r2",))
        self.assertEqual(dropped.not_subject, 1)

    def test_none_type_and_no_target_are_never_signals(self):
        cells, dropped = build([record(1, 60, etype="none"), record(2, 70, kind="none", etype="earnings")])
        self.assertEqual(cells, {})
        self.assertEqual(dropped.no_type_or_target, 2)

    def test_a_reposted_story_counts_once_and_the_first_received_is_kept(self):
        cells, dropped = build([record(2, 120, cluster="cl-x", probs=(0.1, 0.8, 0.1)),
                                record(1, 60, cluster="cl-x", probs=(0.7, 0.1, 0.2)),
                                record(3, 180, cluster="cl-x", probs=(0.7, 0.1, 0.2))])
        cell = cells[("US:SYNM", s.EventType.EARNINGS)]
        self.assertEqual(cell.record_ids, ("r1",))
        self.assertAlmostEqual(cell.shock, 0.8 * 0.6)
        self.assertEqual(dropped.repeated_origin, 2)
        # the same origin about another firm is a separate record for that firm
        cells, dropped = build([record(1, 60, cluster="cl-x"), record(2, 70, cluster="cl-x", entity="KR:900001")])
        self.assertEqual((len(cells), dropped.repeated_origin), (2, 0))

    def test_credibility_as_known_at_the_decision_overrides_the_record(self):
        records = [record(1, 60, cred=0.8)]
        self.assertAlmostEqual(build(records)[0][("US:SYNM", s.EventType.EARNINGS)].shock, 0.48)
        updated = build(records, credibility={"r1": 0.0})[0][("US:SYNM", s.EventType.EARNINGS)]   # debunked since
        self.assertEqual((updated.shock, updated.uncertainty), (0.0, 0.0))
        with self.assertRaises(shock.ShockError):
            build(records, credibility={"r1": 1.4})
        with self.assertRaises(shock.ShockError):
            build([record(1, 60), record(1, 70)])

    def test_state_feeds_the_shock(self):
        """A social-media rumour re-posted forty times, then officially denied before the decision."""
        cascade = [st.Report(f"a{i}", "ev-1", T0 + timedelta(minutes=10 + i), 3, "cl-x", 1) for i in range(40)]
        denial = st.Report("a99", "ev-1", T0 + timedelta(hours=3), 1, "cl-official", -1, official=True)
        rumour = record(1, 10, cluster="cl-x", probs=(0.05, 0.9, 0.05), cred=0.5)
        before = st.pi_at(cascade + [denial], "ev-1", T0 + timedelta(hours=2), W)
        after = st.pi_at(cascade + [denial], "ev-1", NOW, W)
        self.assertAlmostEqual(before, logistic(0.3))                               # forty copies, one source
        self.assertEqual(after, 0.0)
        key = ("US:SYNM", s.EventType.EARNINGS)
        self.assertAlmostEqual(build([rumour], credibility={"r1": before})[0][key].shock, logistic(0.3) * -0.85)
        self.assertEqual(build([rumour], credibility={"r1": after})[0][key].shock, 0.0)


class Boundaries(unittest.TestCase):
    ALLOWED = {"core/didm/credibility/state.py": ("__future__", "hashlib", "json", "math", "dataclasses", "datetime",
                                                  "typing", "numpy", "core.didm"),
               "core/didm/credibility/shock.py": ("__future__", "dataclasses", "datetime", "typing",
                                                  "core.didm.llm.schema")}

    def test_no_data_source_network_or_clock(self):
        for rel, allowed in self.ALLOWED.items():
            for node in ast.walk(ast.parse((ROOT / rel).read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        self.assertIn(a.name, allowed, f"{rel} imports {a.name}")
                elif isinstance(node, ast.ImportFrom):
                    self.assertIn(node.module, allowed, f"{rel} imports {node.module}")
                elif isinstance(node, ast.Attribute):
                    self.assertNotIn(node.attr, ("now", "today", "utcnow", "import_module"), rel)
                elif isinstance(node, ast.Name):
                    self.assertNotIn(node.id, ("open", "__import__", "exec", "eval"), rel)


if __name__ == "__main__":
    unittest.main()
