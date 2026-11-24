"""DIDM-5: Stage 1 measurement tools. Metrics against hand-worked numbers, the isotonic map, the gold-set
sampling rule, and the registered verdict rule on SYNTHETIC labels and judgements.

No gold set exists yet: nothing here is a Stage 1 result. No network, no model, no real article."""
from __future__ import annotations

import ast
import io
import json
import random
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from core.didm.calibration import isotonic as iso
from core.didm.eval import metrics as m
from core.didm.eval import sampling, stage1
from core.didm.llm import cutoffs
from core.didm.llm import schema as s
from core.didm.llm.judgement import ScoreRequest, validate_judgement
from tools.didm import stage1_report

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc


class Metrics(unittest.TestCase):
    def test_kappa_by_hand(self):
        a = ["x"] * 20 + ["x"] * 5 + ["y"] * 10 + ["y"] * 15          # 2x2 table: 20, 5, 10, 15
        b = ["x"] * 20 + ["y"] * 5 + ["x"] * 10 + ["y"] * 15
        self.assertAlmostEqual(m.cohen_kappa(a, b), 0.4)               # po 0.7, pe 0.5
        self.assertAlmostEqual(m.cohen_kappa(a, a), 1.0)
        self.assertAlmostEqual(m.cohen_kappa(["x", "y"] * 10, ["y", "x"] * 10), -1.0)
        with self.assertRaises(m.MetricError):
            m.cohen_kappa(["x"] * 5, ["x"] * 5)                        # undefined, not "perfect"
        with self.assertRaises(m.MetricError):
            m.cohen_kappa(["x"], ["x", "y"])
        with self.assertRaises(m.MetricError):
            m.cohen_kappa([], [])

    def test_macro_f1_by_hand(self):
        gold = ["a", "a", "a", "b", "b", "c"]
        pred = ["a", "a", "b", "b", "c", "c"]
        scores = {c.label: c for c in m.per_class(gold, pred, ["a", "b", "c", "d"])}
        self.assertAlmostEqual(scores["a"].f1, 0.8)                    # P 1, R 2/3
        self.assertAlmostEqual(scores["b"].f1, 0.5)                    # P 1/2, R 1/2
        self.assertAlmostEqual(scores["c"].f1, 2 / 3)                  # P 1/2, R 1
        self.assertEqual((scores["d"].support, scores["d"].f1), (0, 0.0))
        self.assertAlmostEqual(m.macro_f1(gold, pred, ["a", "b", "c", "d"]), (0.8 + 0.5 + 2 / 3) / 3)   # d left out
        self.assertAlmostEqual(m.macro_f1(["a", "b"], ["d", "d"], ["a", "b", "d"]), 0.0)
        self.assertAlmostEqual(m.accuracy(gold, pred), 4 / 6)
        with self.assertRaises(m.MetricError):
            m.macro_f1(gold, pred, ["a", "b"])                         # label outside the list

    def test_linking(self):
        gold = {("a1", "E1"), ("a2", "E2"), ("a3", "E3"), ("a4", "E4"), ("a5", "E5")}
        pred = {("a1", "E1"), ("a2", "E2"), ("a3", "E3"), ("a4", "E9")}
        score = m.linking_scores(gold, pred)
        self.assertEqual((score.precision, score.recall), (0.75, 0.6))
        with self.assertRaises(m.MetricError):
            m.linking_scores(gold, set())
        with self.assertRaises(m.MetricError):
            m.linking_scores(set(), pred)

    def test_brier_and_skill_by_hand(self):
        labels = ["u", "d"]
        probs = [{"u": 0.8, "d": 0.2}, {"u": 0.6, "d": 0.4}]
        outcomes = ["u", "d"]
        self.assertAlmostEqual(m.brier(probs, outcomes, labels), (0.08 + 0.72) / 2)
        self.assertAlmostEqual(m.brier_skill(probs, outcomes, labels, {"u": 0.5, "d": 0.5}), 1 - 0.4 / 0.5)
        self.assertAlmostEqual(m.brier_skill([{"u": 1.0, "d": 0.0}, {"u": 0.0, "d": 1.0}], outcomes, labels,
                                             {"u": 0.5, "d": 0.5}), 1.0)
        self.assertLess(m.brier_skill([{"u": 0.0, "d": 1.0}, {"u": 1.0, "d": 0.0}], outcomes, labels,
                                      {"u": 0.5, "d": 0.5}), 0.0)
        self.assertEqual(m.base_rates(["u", "u", "d", "u"], labels), {"u": 0.75, "d": 0.25})
        for bad in ([{"u": 0.8, "d": 0.3}, probs[1]], [{"u": 0.8}, probs[1]], [{"u": True, "d": 0.0}, probs[1]]):
            with self.assertRaises(m.MetricError):
                m.brier(bad, outcomes, labels)

    def test_ece_by_hand(self):
        conf = [0.95] * 10 + [0.55] * 10
        correct = [True] * 8 + [False] * 2 + [True] * 5 + [False] * 5
        self.assertAlmostEqual(m.ece(conf, correct), 0.5 * abs(0.8 - 0.95) + 0.5 * abs(0.5 - 0.55))
        self.assertAlmostEqual(m.ece([1.0] * 4, [True] * 4), 0.0)       # confidence 1.0 falls in the last bin
        self.assertAlmostEqual(m.ece([1.0] * 4, [False] * 4), 1.0)
        # bins of unequal size are weighted by their share (18 and 2 items)
        uneven_conf = [0.95] * 18 + [0.55] * 2
        uneven_ok = [True] * 9 + [False] * 9 + [True, False]
        self.assertAlmostEqual(m.ece(uneven_conf, uneven_ok), 0.9 * abs(0.5 - 0.95) + 0.1 * abs(0.5 - 0.55))   # 0.41
        bins = m.reliability(conf, correct)
        self.assertEqual([b.count for b in bins], [0, 0, 0, 0, 0, 10, 0, 0, 0, 10])
        with self.assertRaises(m.MetricError):
            m.ece([1.2], [True])

    def test_top_label_and_bootstrap(self):
        labels = ["a", "b", "c"]
        picks, confs = m.top_label([{"a": 0.4, "b": 0.4, "c": 0.2}, {"a": 0.1, "b": 0.2, "c": 0.7}], labels)
        self.assertEqual((picks, confs), (["a", "c"], [0.4, 0.7]))       # first label wins a tie
        rng = random.Random(3)
        gold = [rng.choice("ab") for _ in range(300)]
        good = [g if rng.random() < 0.9 else "b" for g in gold]
        poor = [g if rng.random() < 0.6 else "a" for g in gold]
        one = m.paired_bootstrap(gold, good, poor, m.accuracy, seed=11, resamples=300)
        two = m.paired_bootstrap(gold, good, poor, m.accuracy, seed=11, resamples=300)
        self.assertEqual(one, two)
        self.assertGreater(one.lower, 0.0)
        self.assertLessEqual(one.lower, one.difference)
        self.assertLessEqual(one.difference, one.upper)
        same = m.paired_bootstrap(gold, good, good, m.accuracy, seed=11, resamples=300)
        self.assertEqual((same.lower, same.upper), (0.0, 0.0))


class Isotonic(unittest.TestCase):
    def test_fit_is_monotone_and_pools_violators(self):
        raw = [0.1] * 10 + [0.2] * 10 + [0.3] * 10 + [0.9] * 10
        hit = [False] * 10 + [True] * 6 + [False] * 4 + [True] * 2 + [False] * 8 + [True] * 10
        f = iso.fit_isotonic(raw, hit)
        self.assertEqual(f.values, tuple(sorted(f.values)))
        self.assertAlmostEqual(f(0.1), 0.0)
        self.assertAlmostEqual(f(0.2), 0.4)          # 0.2 (rate 0.6) and 0.3 (rate 0.2) pooled to 0.4
        self.assertAlmostEqual(f(0.3), 0.4)
        self.assertAlmostEqual(f(0.25), 0.4)
        self.assertAlmostEqual(f(0.95), 1.0)
        self.assertAlmostEqual(f(0.0), 0.0)          # below the first threshold: the first value
        with self.assertRaises(iso.CalibrationError):
            iso.fit_isotonic([0.5] * 5, [True] * 5)  # too few items
        with self.assertRaises(iso.CalibrationError):
            f(1.5)

    def test_overconfident_scorer_is_pulled_back(self):
        rng = random.Random(5)
        labels = ("+1", "-1", "0")
        rows, outcomes = [], []
        for _ in range(900):
            truth = rng.choice(labels)
            pick = truth if rng.random() < 0.6 else rng.choice([k for k in labels if k != truth])
            rows.append({k: (0.98 if k == pick else 0.01) for k in labels})      # says 98%, right 60% of the time
            outcomes.append(truth)
        fit, test = list(range(600)), list(range(600, 900))
        before = m.top_label_ece([rows[i] for i in test], [outcomes[i] for i in test], labels)
        cal = iso.fit_map("direction", labels, [rows[i] for i in fit], [outcomes[i] for i in fit])
        after = m.top_label_ece([cal.apply(rows[i]) for i in test], [outcomes[i] for i in test], labels)
        self.assertGreater(before, 0.30)
        self.assertLess(after, 0.06)
        out = cal.apply_direction((0.98, 0.01, 0.01))
        self.assertAlmostEqual(sum(out), 1.0)
        self.assertLess(out[0], 0.75)

    def test_map_version_follows_the_map(self):
        labels = ("+1", "-1", "0")
        rows = [{"+1": 0.6, "-1": 0.3, "0": 0.1}] * 40
        one = iso.fit_map("direction", labels, rows, ["+1"] * 24 + ["-1"] * 12 + ["0"] * 4)
        same = iso.fit_map("direction", labels, rows, ["+1"] * 24 + ["-1"] * 12 + ["0"] * 4)
        other = iso.fit_map("direction", labels, rows, ["+1"] * 20 + ["-1"] * 16 + ["0"] * 4)
        self.assertEqual(one.version, same.version)
        self.assertNotEqual(one.version, other.version)
        self.assertRegex(one.version, r"^iso-direction-[0-9a-f]{16}$")
        self.assertNotEqual(one.version, "uncalibrated")
        with self.assertRaises(iso.CalibrationError):
            one.apply({"+1": 0.5, "-1": 0.5})
        with self.assertRaises(iso.CalibrationError):
            iso.fit_map("event_type", ("a", "b"), [{"a": 0.5, "b": 0.5}] * 40, ["c"] * 40)

    def test_time_split_never_looks_ahead(self):
        times = [datetime(2026, 10, 1, tzinfo=UTC) + timedelta(hours=i) for i in range(10)]
        shuffled = [times[i] for i in (3, 9, 0, 7, 1, 8, 2, 6, 4, 5)]
        fit, test = iso.time_split(shuffled)
        self.assertEqual((len(fit), len(test)), (7, 3))
        self.assertLess(max(shuffled[i] for i in fit), min(shuffled[i] for i in test))
        same_time = [times[0]] * 3 + [times[1]] * 4 + [times[2]] * 3
        fit, test = iso.time_split(same_time)
        self.assertLess(max(same_time[i] for i in fit), min(same_time[i] for i in test))
        with self.assertRaises(iso.CalibrationError):
            iso.time_split([times[0]] * 10)


def candidates(n=6000, seed=1):
    rng = random.Random(seed)
    start = datetime(2026, 10, 1, tzinfo=UTC)
    return [sampling.Candidate(f"art-{i:05d}", "EN" if rng.random() < 0.85 else "KR", rng.choice([1, 2, 2, 3]),
                               start + timedelta(hours=rng.randrange(24 * 90))) for i in range(n)]


class GoldSetSampling(unittest.TestCase):
    def test_same_seed_same_sample_and_size_rules(self):
        pool = candidates()
        one, two, other = sampling.draw(pool, 1200, 7), sampling.draw(pool, 1200, 7), sampling.draw(pool, 1200, 8)
        self.assertEqual(one, two)
        self.assertNotEqual(one, other)
        self.assertEqual(len({c.article_id for c in one}), 1200)
        self.assertEqual(sampling.draw(list(reversed(pool)), 1200, 7), one)       # input order does not matter
        for n in (999, 1501):
            with self.assertRaises(sampling.SamplingError):
                sampling.draw(pool, n, 7)

    def test_both_markets_and_every_stratum_are_represented(self):
        pool = candidates()
        sample = sampling.draw(pool, 1000, 7)
        kr = sum(c.market == "KR" for c in sample)
        self.assertGreaterEqual(kr, 300)                                           # 15% of candidates, 30% floor
        strata = {c.stratum for c in pool}
        counts = {k: sum(c.stratum == k for c in sample) for k in strata}
        self.assertTrue(all(v >= min(sampling.MIN_PER_STRATUM, sum(c.stratum == k for c in pool))
                            for k, v in counts.items()))

    def test_bad_candidates_are_refused(self):
        pool = candidates()
        with self.assertRaises(sampling.SamplingError):
            sampling.draw([c for c in pool if c.market == "EN"], 1000, 7)
        with self.assertRaises(sampling.SamplingError):
            sampling.draw(pool + [pool[0]], 1000, 7)
        with self.assertRaises(sampling.SamplingError):
            sampling.draw(pool[:500], 1000, 7)
        with self.assertRaises(sampling.SamplingError):
            sampling.Candidate("a", "US", 1, datetime(2026, 10, 1, tzinfo=UTC))
        with self.assertRaises(sampling.SamplingError):
            sampling.Candidate("a", "EN", 1, datetime(2026, 10, 1))

    def test_candidate_carries_no_text_score_or_price(self):
        self.assertEqual(set(sampling.Candidate.__dataclass_fields__), {"article_id", "market", "source_tier", "received_at"})


TYPES = [e.value for e in s.EventType]
DIRS = ["+1", "-1", "0"]
LLM = "toy-llm-1"
REGISTRY = cutoffs.REGISTRY.with_card(cutoffs.ModelCard(
    key=LLM, family="toy", rule=cutoffs.Rule.CUTOFF, snapshot_id="toy@1", cutoff=date(2026, 6, 30),
    source_url="https://example.org/toy-model-card", checked_on=date(2026, 11, 24)))
for _key in (stage1.LM_KEY, stage1.FINBERT_KEY):          # the baselines must be pinned for these tests
    if not cutoffs.REGISTRY.get(_key).verified:
        REGISTRY = cutoffs.Registry(tuple(
            cutoffs.ModelCard(key=c.key, family=c.family, rule=c.rule, snapshot_id="toy-pin",
                              source_url="https://example.org/baseline", checked_on=date(2026, 11, 24))
            if c.key == _key else c for c in REGISTRY))


def world(n=1000, seed=4, a_err=0.08, b_err=0.08, type_acc=0.90, dir_acc=0.85, lm_acc=0.50, fin_acc=0.62,
          conf=None, start=datetime(2026, 10, 5, tzinfo=UTC), link_miss=0.1, link_wrong=0.02):
    """Synthetic annotators, gold and scorer runs. Every value is drawn from the seeded generator."""
    rng = random.Random(seed)

    def noisy(value, options, err):
        return value if rng.random() >= err else rng.choice([o for o in options if o != value])

    def label(i, who, etype, direction, when):
        return s.validate_gold({
            "article_id": f"art-{i:05d}", "annotator_id": who, "market": "KR" if i % 3 == 0 else "EN",
            "source_tier": 1 + i % 3, "target_kind": "firm", "entity_id": f"E:{i % 97:03d}", "is_subject": True,
            "event_type": etype, "direction": direction, "is_new_event": i % 4 != 0, "claim_status": "reported",
            "published_at": (when - timedelta(minutes=20)).isoformat(), "received_at": when.isoformat()})

    def judgement(gold, acc_type, acc_dir, p_type, p_dir):
        etype = noisy(gold.event_type.value, TYPES, 1 - acc_type)
        direction = noisy(gold.direction.value, DIRS, 1 - acc_dir)
        rest = (1 - p_type) / 14
        raw = {"judgement_version": "didm-judgement-v0", "article_id": gold.article_id, "target_kind": "firm",
               "entity_id": gold.entity_id, "p_subject": 0.9, "event_type": etype,
               "event_type_probs": {t: (p_type if t == etype else rest) for t in TYPES},
               "direction_probs": [p_dir if d == direction else (1 - p_dir) / 2 for d in DIRS],
               "claim_status": "reported"}
        request = ScoreRequest(gold.article_id, "en", "Synthetic", None, gold.target_kind, gold.entity_id, "Synthetic Co")
        return validate_judgement(raw, request)

    gold, ann_a, ann_b = [], [], []
    for i in range(n):
        when = start + timedelta(minutes=37 * i)
        etype, direction = rng.choice(TYPES), rng.choice(DIRS)
        gold.append(label(i, "adjudicator", etype, direction, when))
        ann_a.append(label(i, "ann-a", noisy(etype, TYPES, a_err), noisy(direction, DIRS, a_err), when))
        ann_b.append(label(i, "ann-b", noisy(etype, TYPES, b_err), noisy(direction, DIRS, b_err), when))
    p_type, p_dir = conf or (type_acc, dir_acc)
    key = lambda g: (g.article_id, g.entity_id)
    llm = stage1.ScorerRun(LLM, {key(g): judgement(g, type_acc, dir_acc, p_type, p_dir) for g in gold})
    base = {stage1.LM_KEY: stage1.ScorerRun(stage1.LM_KEY, {key(g): judgement(g, 0.07, lm_acc, 0.5, 0.6) for g in gold}),
            stage1.FINBERT_KEY: stage1.ScorerRun(stage1.FINBERT_KEY,
                                                 {key(g): judgement(g, 0.07, fin_acc, 0.5, 0.7) for g in gold})}
    links = set()
    for g in gold:
        if rng.random() >= link_miss:
            links.add(key(g))
        if rng.random() < link_wrong:
            links.add((g.article_id, "E:wrong"))
    return dict(annotator_a=ann_a, annotator_b=ann_b, gold=gold, llm=llm, baselines=base, predicted_links=links)


def run(**kw):
    return stage1.evaluate(**world(**kw), registry=REGISTRY, bootstrap_resamples=120)


class Stage1Verdict(unittest.TestCase):
    def test_thresholds_are_the_registered_ones(self):
        self.assertEqual((stage1.KAPPA_GO, stage1.KAPPA_NO_GO, stage1.MACRO_F1_MIN), (0.6, 0.4, 0.75))
        self.assertEqual((stage1.LINK_PRECISION_MIN, stage1.LINK_RECALL_MIN), (0.95, 0.80))
        self.assertEqual((stage1.ECE_MAX, stage1.BRIER_SKILL_MIN), (0.05, 0.0))
        self.assertEqual((sampling.TARGET_MIN, sampling.TARGET_MAX), (1000, 1500))
        prereg = (ROOT / "docs" / "didm" / "PREREG_V0.md").read_text(encoding="utf-8")
        self.assertIn("사람 κ ≥ 0.6, 사건 유형 macro-F1 ≥ 0.75, 연결 정밀도 ≥ 0.95·재현율 ≥ 0.80, "
                      "보정 뒤 ECE ≤ 0.05, Brier skill > 0, LLM > LM 사전·FinBERT", prereg)
        self.assertIn("사람 κ < 0.4 또는 LLM ≤ FinBERT", prereg)

    def test_a_good_synthetic_world_is_go(self):
        report = run()
        self.assertEqual(report.verdict, "GO", stage1.render(report))
        self.assertEqual(report.line, "STAGE1: GO")
        self.assertEqual(len(report.criteria), 10)
        self.assertTrue(all(c.passed for c in report.criteria))
        self.assertEqual((report.info["n_calibration_fit"], report.info["n_calibration_test"]), (700, 300))
        self.assertRegex(report.info["calibration_version_direction"], r"^iso-direction-")
        self.assertIn("STAGE1: GO", stage1.render(report))

    def test_same_inputs_same_report(self):
        self.assertEqual(run(), run())

    def test_low_human_agreement(self):
        mid = run(a_err=0.25, b_err=0.25)                    # kappa about 0.5
        kappa = mid.criteria[0].value
        self.assertTrue(0.4 <= kappa < 0.6, kappa)
        self.assertEqual(mid.verdict, "REVISE")
        self.assertTrue(any("lower the number of event types" in n for n in mid.notes))
        low = run(a_err=0.45, b_err=0.45)
        self.assertLess(low.criteria[0].value, 0.4)
        self.assertEqual(low.verdict, "NO-GO")

    def test_llm_not_above_finbert_is_no_go(self):
        report = run(dir_acc=0.55, fin_acc=0.70)
        self.assertEqual(report.verdict, "NO-GO")
        self.assertTrue(any("FinBERT" in n for n in report.notes))

    def test_single_missed_conditions_are_revise(self):
        for change, name in ((dict(type_acc=0.70), "event-type macro-F1"),
                             (dict(link_miss=0.30), "linking recall"),
                             (dict(link_wrong=0.20), "linking precision")):
            with self.subTest(name):
                report = run(**change)
                self.assertEqual(report.verdict, "REVISE", stage1.render(report))
                self.assertIn(f"not met: {name}", report.notes)

    def test_missing_judgements_count_as_wrong_answers(self):
        w = world()
        kept = dict(list(w["llm"].judgements.items())[::2])                 # half the items have no judgement
        w["llm"] = stage1.ScorerRun(LLM, kept)
        report = stage1.evaluate(**w, registry=REGISTRY, bootstrap_resamples=120)
        f1 = {c.name: c for c in report.criteria}["event-type macro-F1"]
        self.assertLess(f1.value, 0.65)
        self.assertFalse(f1.passed)
        self.assertAlmostEqual(report.info["llm_coverage"], 0.5)

    def test_articles_inside_the_training_window_make_the_run_invalid(self):
        report = run(start=datetime(2026, 9, 1, tzinfo=UTC))                # before 2026-09-30
        self.assertEqual(report.verdict, "INVALID")
        self.assertTrue(any("training-cutoff rule" in n for n in report.notes))
        w = world()
        w["llm"] = stage1.ScorerRun("unlisted-model", w["llm"].judgements)
        self.assertEqual(stage1.evaluate(**w, registry=REGISTRY, bootstrap_resamples=120).verdict, "INVALID")

    def test_an_old_article_fetched_recently_makes_the_run_invalid(self):
        """Backfill: published inside the model's training window, received after it."""
        from dataclasses import replace
        w = world()
        old_day = datetime(2020, 3, 2, 13, 0, tzinfo=UTC)
        for name in ("gold", "annotator_a", "annotator_b"):
            w[name] = [replace(w[name][0], published_at=old_day)] + w[name][1:]
        report = stage1.evaluate(**w, registry=REGISTRY, bootstrap_resamples=120)
        self.assertEqual(report.verdict, "INVALID")
        self.assertTrue(any("llm" in n and "1 gold items fail" in n for n in report.notes), report.notes)

    def test_readings_live_in_one_config_and_change_the_verdict_as_documented(self):
        default = stage1.Stage1Config()
        self.assertEqual((default.kappa_fields, default.calibration_fields, default.beat_rule, default.missing_judgement),
                         (("event_type",), ("direction", "event_type"), "point", "wrong"))
        # (1) kappa also on direction: annotators who agree on type but not on direction now fail kappa
        w = world()
        rng = random.Random(9)
        from dataclasses import replace
        flip = {"+1": "-1", "-1": "0", "0": "+1"}
        w["annotator_b"] = [replace(x, direction=s.Direction(flip[x.direction.value])) if rng.random() < 0.45 else x
                            for x in w["annotator_b"]]
        kw = dict(registry=REGISTRY, bootstrap_resamples=120)
        self.assertEqual(stage1.evaluate(**w, **kw).verdict, "GO")
        both = stage1.evaluate(**w, **kw, config=stage1.Stage1Config(kappa_fields=("event_type", "direction")))
        self.assertIn(both.verdict, ("REVISE", "NO-GO"))
        self.assertEqual(len([c for c in both.criteria if c.name.startswith("human kappa")]), 2)
        # (2) calibration gated on direction only: two criteria fewer
        one = stage1.evaluate(**world(), **kw, config=stage1.Stage1Config(calibration_fields=("direction",)))
        self.assertEqual(len(one.criteria), 8)
        self.assertNotIn("calibration_version_event_type", one.info)
        # (3) a small edge over FinBERT passes the point rule and fails the bootstrap rule
        close = world(dir_acc=0.65, fin_acc=0.64, seed=4)      # edge +0.025: GO by the point rule
        point = stage1.evaluate(**close, **kw)
        strict = stage1.evaluate(**close, **kw, config=stage1.Stage1Config(beat_rule="bootstrap95"))
        gap = {c.name: c for c in point.criteria}[f"LLM direction macro-F1 minus {stage1.FINBERT_KEY}"]
        self.assertTrue(gap.passed and gap.value < 0.05, gap)
        lower = [c for c in strict.criteria if stage1.FINBERT_KEY in c.name][0]
        self.assertFalse(lower.passed)
        self.assertLess(lower.value, 0.0)
        self.assertEqual(strict.verdict, "REVISE")                    # not No-Go: the point estimate is still above
        self.assertIn("bootstrap95_vs_" + stage1.FINBERT_KEY, strict.info)
        # (4) missing judgements skipped instead of counted wrong
        half = world()
        half["llm"] = stage1.ScorerRun(LLM, dict(list(half["llm"].judgements.items())[::2]))
        wrong = stage1.evaluate(**half, **kw)
        skip = stage1.evaluate(**half, **kw, config=stage1.Stage1Config(missing_judgement="skip"))
        f1 = lambda r: {c.name: c for c in r.criteria}["event-type macro-F1"].value
        self.assertLess(f1(wrong), 0.65)
        self.assertGreater(f1(skip), 0.85)
        for bad in (dict(kappa_fields=()), dict(kappa_fields=("mood",)), dict(beat_rule="vibes"),
                    dict(missing_judgement="ignore"), dict(calibration_fields=("p_subject",)),
                    dict(min_calibration_items=5)):
            with self.subTest(bad=bad), self.assertRaises(stage1.Stage1Error):
                stage1.Stage1Config(**bad)

    def test_wrong_size_gold_set_is_invalid(self):
        report = run(n=400)
        self.assertEqual(report.verdict, "INVALID")
        self.assertTrue(any("1000-1500" in n for n in report.notes))

    def test_mismatched_inputs_are_refused(self):
        w = world(n=1000)
        with self.assertRaises(stage1.Stage1Error):
            stage1.evaluate(**dict(w, annotator_b=w["annotator_b"][:-1]), registry=REGISTRY)
        with self.assertRaises(stage1.Stage1Error):
            stage1.evaluate(**dict(w, baselines={stage1.LM_KEY: w["baselines"][stage1.LM_KEY]}), registry=REGISTRY)
        with self.assertRaises(stage1.Stage1Error):
            stage1.evaluate(**dict(w, gold=w["gold"] + [w["gold"][0]]), registry=REGISTRY)


class ReportTool(unittest.TestCase):
    def test_folder_inside_the_repository_is_refused(self):
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(stage1_report.main(["--dir", str(ROOT / "tests")]), 2)
        self.assertIn("outside the repository", err.getvalue())

    def test_reads_files_and_prints_the_verdict_line(self):
        w = world()

        def gold_row(g):
            return {"article_id": g.article_id, "annotator_id": g.annotator_id, "market": g.market,
                    "source_tier": g.source_tier, "target_kind": g.target_kind.value, "entity_id": g.entity_id,
                    "is_subject": g.is_subject, "event_type": g.event_type.value, "direction": g.direction.value,
                    "is_new_event": g.is_new_event, "claim_status": g.claim_status,
                    "published_at": g.published_at.isoformat(), "received_at": g.received_at.isoformat()}

        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name in ("annotator_a", "annotator_b", "gold"):
                (folder / f"{name}.jsonl").write_text("\n".join(json.dumps(gold_row(g)) for g in w[name]), encoding="utf-8")
            files = {"llm": w["llm"], **w["baselines"]}
            for i, (name, scorer) in enumerate(files.items()):
                rows = [json.dumps(j.as_dict()) for j in scorer.judgements.values()]
                if name == "llm":
                    rows[0] = json.dumps(dict(json.loads(rows[0]), rationale="x"))     # one rejected line
                (folder / f"s{i}.jsonl").write_text("\n".join(rows), encoding="utf-8")
            spec = {"llm": {"model_version": stage1.LM_KEY, "file": "s0.jsonl"},
                    "baselines": {name: {"model_version": name, "file": f"s{i}.jsonl"}
                                  for i, name in enumerate(files) if name != "llm"}}
            (folder / "scorers.json").write_text(json.dumps(spec), encoding="utf-8")
            (folder / "links.jsonl").write_text(
                "\n".join(json.dumps({"article_id": a, "entity_id": e}) for a, e in sorted(w["predicted_links"])),
                encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(stage1_report.main(["--dir", str(folder), "--bootstrap-seed", "1"]), 0)
        text = out.getvalue()
        self.assertRegex(text, r"STAGE1: (GO|REVISE|NO-GO|INVALID)\n")
        self.assertIn("rejected judgements in s0.jsonl: 1", text)
        self.assertIn("| event-type macro-F1 |", text)


class Boundaries(unittest.TestCase):
    FILES = ("core/didm/eval/metrics.py", "core/didm/eval/sampling.py", "core/didm/eval/stage1.py",
             "core/didm/calibration/isotonic.py", "tools/didm/stage1_report.py")
    BANNED = ("data", "requests", "urllib", "http", "socket", "time", "numpy", "pandas", "scipy", "sklearn",
              "jsonschema", "pydantic", "anthropic", "openai", "transformers", "torch", "subprocess")

    def test_standard_library_only_no_network_no_clock(self):
        for rel in self.FILES:
            tree = ast.parse((ROOT / rel).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                for name in names:
                    self.assertNotIn(name.split(".")[0], self.BANNED, f"{rel} imports {name}")
                if isinstance(node, ast.Call):
                    func = node.func
                    called = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                    self.assertNotIn(called, ("now", "today", "utcnow"), rel)

    def test_metrics_module_depends_on_nothing_in_the_project(self):
        tree = ast.parse((ROOT / "core/didm/eval/metrics.py").read_text(encoding="utf-8"))
        modules = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertFalse([name for name in modules if name.split(".")[0] in ("core", "data", "tools")])


if __name__ == "__main__":
    unittest.main()
