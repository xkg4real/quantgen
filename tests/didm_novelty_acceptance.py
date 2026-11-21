"""Owner decision P2: novelty = model P(new | features), tested at cutoff 0.75 on a time-ordered hold-out.

Simulated data only (Stage 0), no network, fixed seed.
"""
from __future__ import annotations

import random
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np

from core.didm import novelty as nv
from core.didm.llm.schema import EventType

T0 = datetime(2026, 1, 5, tzinfo=timezone.utc)
TYPES = [e for e in EventType if e is not EventType.NONE]


def simulate(n_clusters=400, seed=7):
    """Each cluster = one real event: a first report, then 0-5 follow-ups within hours."""
    rng = random.Random(seed)
    arts, labels, cluster = [], [], {}
    for c in range(n_clusters):
        start = T0 + timedelta(minutes=rng.randrange(0, 60 * 24 * 90))
        ent, et = f"E{rng.randrange(60)}", rng.choice(TYPES)
        for k in range(1 + rng.choice([0, 0, 1, 2, 3, 5])):
            a = nv.Article(f"c{c}-{k}", start + timedelta(minutes=k * rng.randrange(5, 240) + k),
                           ent, et, f"src{rng.randrange(8)}", rng.choice([1, 2, 2, 3]))
            arts.append(a); labels.append(1 if k == 0 else 0); cluster[a.article_id] = c
    def sim(a, b):
        same = cluster[a.article_id] == cluster[b.article_id]
        return min(1.0, max(0.0, (0.9 if same else 0.15) + rng.gauss(0, 0.05)))
    return arts, labels, sim


class NoveltyModel(unittest.TestCase):
    def test_features_point_in_time(self):
        arts, _, sim = simulate(60)
        sim_fixed = lambda a, b: 0.9 if a.article_id.split("-")[0] == b.article_id.split("-")[0] else 0.1
        early = [a for a in arts if a.received_at < T0 + timedelta(days=30)]
        X_early = nv.build_features(early, sim_fixed)
        X_all = nv.build_features(arts, sim_fixed)
        idx = {a.article_id: i for i, a in enumerate(arts)}
        for j, a in enumerate(early):
            np.testing.assert_array_equal(X_early[j], X_all[idx[a.article_id]])

    def test_features_are_invariant_to_timezone_representation(self):
        # Sunday UTC is already Monday in Korea: both time and weekend must agree.
        received = datetime(2026, 1, 4, 23, tzinfo=timezone.utc)
        korean_time = received.astimezone(timezone(timedelta(hours=9)))
        utc_article = nv.Article("same", received, "E", TYPES[0], "s", 2)
        kr_article = nv.Article("same", korean_time, "E", TYPES[0], "s", 2)
        utc_features = nv.build_features([utc_article], lambda *_: 0.0)
        kr_features = nv.build_features([kr_article], lambda *_: 0.0)
        np.testing.assert_array_equal(utc_features, kr_features)
        self.assertEqual(utc_features[0, nv.FEATURES.index("weekend")], 1.0)

    def test_elapsed_hours_use_real_time_across_dst_changes(self):
        ny = ZoneInfo("America/New_York")
        cases = ((datetime(2026, 3, 8, 0, 30, tzinfo=ny),
                  datetime(2026, 3, 8, 3, 30, tzinfo=ny), 2),
                 (datetime(2026, 11, 1, 0, 30, tzinfo=ny),
                  datetime(2026, 11, 1, 2, 30, tzinfo=ny), 3))
        for before, after, hours in cases:
            with self.subTest(before=before, after=after):
                arts = [nv.Article(str(i), t, "E", TYPES[0], "s", 2)
                        for i, t in enumerate((before, after))]
                X = nv.build_features(arts, lambda *_: 0.9)
                utc_arts = [replace(a, received_at=a.received_at.astimezone(timezone.utc)) for a in arts]
                np.testing.assert_array_equal(X, nv.build_features(utc_arts, lambda *_: 0.9))
                self.assertAlmostEqual(X[1, nv.FEATURES.index("hours_since_sim_log")], np.log1p(hours))

    def test_dst_fold_orders_by_instant_and_preserves_callback_objects(self):
        ny = ZoneInfo("America/New_York")
        early = nv.Article("early", datetime(2026, 11, 1, 1, 45, tzinfo=ny, fold=0),
                           "E", TYPES[0], "s", 2)
        late = nv.Article("late", datetime(2026, 11, 1, 1, 15, tzinfo=ny, fold=1),
                          "E", TYPES[0], "s", 2)
        calls = []
        def similarity(a, b):
            self.assertIs(a, late)
            self.assertIs(b, early)
            calls.append((a, b))
            return 0.9
        X = nv.build_features([late, early], similarity)
        self.assertEqual(len(calls), 1)
        self.assertAlmostEqual(X[0, nv.FEATURES.index("hours_since_sim_log")], np.log1p(0.5))
        self.assertEqual(X[1, nv.FEATURES.index("n_sim_24h_log")], 0.0)

    def test_time_windows_use_elapsed_hours_at_dst_boundaries(self):
        ny = ZoneInfo("America/New_York")
        cases = ((datetime(2026, 10, 31, 12, tzinfo=ny),
                  datetime(2026, 11, 1, 12, tzinfo=ny), 0, 1),  # 25h, outside 24h
                 (datetime(2026, 10, 31, 12, tzinfo=ny),
                  datetime(2026, 11, 1, 11, tzinfo=ny), 1, 1),  # exactly 24h
                 (datetime(2026, 3, 7, 12, tzinfo=ny),
                  datetime(2026, 3, 8, 12, tzinfo=ny), 1, 1),  # 23h, inside 24h
                 (datetime(2026, 10, 25, 12, tzinfo=ny),
                  datetime(2026, 11, 1, 12, tzinfo=ny), 0, 0),  # 169h, outside 7d
                 (datetime(2026, 3, 1, 12, tzinfo=ny),
                  datetime(2026, 3, 8, 12, tzinfo=ny), 0, 1))   # 167h, inside 7d
        for before, after, count24, count7 in cases:
            with self.subTest(before=before, after=after):
                arts = [nv.Article(str(i), t, "E", TYPES[0], "s", 2)
                        for i, t in enumerate((before, after))]
                X = nv.build_features(arts, lambda *_: 0.9)
                for feature in ("n_sim_24h_log", "entity_type_count_24h_log"):
                    self.assertAlmostEqual(X[1, nv.FEATURES.index(feature)], np.log1p(count24))
                self.assertAlmostEqual(X[1, nv.FEATURES.index("entity_count_7d_log")], np.log1p(count7))

    def test_similarity_excludes_different_entity_with_same_event_type(self):
        arts = [nv.Article("first", T0, "E1", TYPES[0], "s", 2),
                nv.Article("second", T0 + timedelta(hours=1), "E2", TYPES[0], "s", 2)]
        X = nv.build_features(arts, lambda *_: 1.0)
        self.assertEqual(X[1, nv.FEATURES.index("max_sim_24h")], 0.0)
        self.assertEqual(X[1, nv.FEATURES.index("n_sim_24h_log")], 0.0)

    def test_similarity_excludes_same_entity_with_different_event_type(self):
        arts = [nv.Article("first", T0, "E", TYPES[0], "s", 2),
                nv.Article("second", T0 + timedelta(hours=1), "E", TYPES[1], "s", 2)]
        X = nv.build_features(arts, lambda *_: 1.0)
        self.assertEqual(X[1, nv.FEATURES.index("max_sim_24h")], 0.0)
        self.assertEqual(X[1, nv.FEATURES.index("n_sim_24h_log")], 0.0)
        self.assertAlmostEqual(X[1, nv.FEATURES.index("entity_count_7d_log")], np.log(2))

    def test_similarity_includes_known_matching_entity_and_event_type(self):
        arts = [nv.Article("first", T0, "E", TYPES[0], "s", 2),
                nv.Article("second", T0 + timedelta(hours=1), "E", TYPES[0], "s", 2)]
        X = nv.build_features(arts, lambda *_: 1.0)
        self.assertEqual(X[1, nv.FEATURES.index("max_sim_24h")], 1.0)
        self.assertAlmostEqual(X[1, nv.FEATURES.index("n_sim_24h_log")], np.log(2))
        self.assertAlmostEqual(X[1, nv.FEATURES.index("entity_type_count_24h_log")], np.log(2))

    def test_unknown_entities_are_not_treated_as_one_shared_entity(self):
        arts = [nv.Article("first", T0, None, TYPES[0], "s", 2),
                nv.Article("second", T0 + timedelta(hours=1), None, TYPES[0], "s", 2)]
        X = nv.build_features(arts, lambda *_: 1.0)
        for feature in ("max_sim_24h", "n_sim_24h_log", "entity_type_count_24h_log", "entity_count_7d_log"):
            self.assertEqual(X[1, nv.FEATURES.index(feature)], 0.0)

    def test_pipeline_passes_on_informative_simulation(self):
        arts, y, sim = simulate()
        rep = nv.fit_and_test(arts, y, sim)
        self.assertEqual(rep.cutoff, 0.75)
        self.assertGreaterEqual(rep.accuracy, 0.90)
        self.assertTrue(rep.passes)
        self.assertTrue(rep.beats_majority)
        self.assertLess(rep.coefficients["max_sim_24h"], 0)  # similar earlier story -> less novel

    def test_fails_when_labels_are_noise(self):
        arts, _, sim = simulate()
        rng = random.Random(1)
        noise = [rng.randrange(2) for _ in arts]
        rep = nv.fit_and_test(arts, noise, sim)
        self.assertFalse(rep.passes)

    def test_time_split_is_ordered(self):
        arts, _, _ = simulate(50)
        train, test = nv.time_split([a.received_at for a in arts])
        self.assertLessEqual(max(arts[i].received_at for i in train), min(arts[i].received_at for i in test))

    def test_rejects_naive_times_and_bad_labels(self):
        a = nv.Article("x", datetime(2026, 1, 1), "E", TYPES[0], "s", 1)
        with self.assertRaises(nv.NoveltyError):
            nv.build_features([a], lambda *_: 0.0)
        with self.assertRaises(nv.NoveltyError):
            nv.fit_logistic(np.ones((3, 2)), np.array([0, 2, 1]))

    def test_evaluate_counts(self):
        m = nv.evaluate(np.array([1, 1, 0, 0]), np.array([0.9, 0.5, 0.8, 0.1]))
        self.assertEqual(m["accuracy"], 0.5)
        self.assertEqual(m["precision"], 0.5)
        self.assertEqual(m["recall"], 0.5)


class NoveltyInputValidation(unittest.TestCase):
    def test_rejects_invalid_labels_only_in_holdout(self):
        # These previously produced accuracy 1.0 / passes=True for fractional y.
        arts = [nv.Article(str(i), T0 + timedelta(hours=i), "E", TYPES[0], "s", 2)
                for i in range(10)]
        for bad in (0.9, 2, float("nan"), float("inf")):
            with self.subTest(label=bad), self.assertRaises(nv.NoveltyError):
                nv.fit_and_test(arts, [0] * 7 + [bad] * 3, lambda *_: 0.0)

    def test_evaluate_rejects_fractional_and_nonbinary_labels(self):
        for labels in ([0, 0.9], [0, 2], [0, float("nan")],
                       [0, float("inf")], ["0", "1"]):
            with self.subTest(labels=labels), self.assertRaises(nv.NoveltyError):
                nv.evaluate(labels, [0.1, 0.9])

    def test_evaluate_rejects_broadcasting_shapes_and_length_mismatch(self):
        # A (2, 1) probability vector used to broadcast and report accuracy 2.0.
        cases = [([1, 1], [[1], [1]]), ([[1], [1]], [1, 1]),
                 ([0, 1], [0.1]), ([0], [0.1, 0.9]),
                 (1, [1]), ([1], 1), ([], [])]
        for labels, probabilities in cases:
            with self.subTest(y=labels, p=probabilities), self.assertRaises(nv.NoveltyError):
                nv.evaluate(labels, probabilities)

    def test_evaluate_rejects_nonprobabilities(self):
        for probabilities in ([-0.1, 0.9], [0.1, 1.1], [0.1, float("nan")],
                              [0.1, float("inf")], ["0.1", "0.9"], [0.1, 0.9j]):
            with self.subTest(p=probabilities), self.assertRaises(nv.NoveltyError):
                nv.evaluate([0, 1], probabilities)

    def test_evaluate_rejects_invalid_cutoff(self):
        for cutoff in (-0.1, 1.1, float("nan"), float("inf"), True, [0.75], "0.75"):
            with self.subTest(cutoff=cutoff), self.assertRaises(nv.NoveltyError):
                nv.evaluate([0, 1], [0.1, 0.9], cutoff)

    def test_probability_boundaries_and_binary_booleans_are_valid(self):
        result = nv.evaluate([False, False, True, True], [0.0, 0.74, 0.75, 1.0])
        self.assertEqual(result["accuracy"], 1.0)
        self.assertEqual(result["balanced_accuracy"], 1.0)
        self.assertEqual(nv.evaluate([1], [0.0], cutoff=0.0)["accuracy"], 1.0)
        self.assertEqual(nv.evaluate([1], [1.0], cutoff=1.0)["accuracy"], 1.0)

    def test_fit_rejects_bad_feature_shapes_or_values(self):
        for X, y in ((np.ones((2, 2)), [0, 1, 0]),
                     (np.ones((2, 2)), [[0], [1]]),
                     (np.ones(2), [0, 1]),
                     (np.array([[1, float("nan")], [1, 0]]), [0, 1])):
            with self.subTest(X=X, y=y), self.assertRaises(nv.NoveltyError):
                nv.fit_logistic(X, y)

    def test_time_split_rejects_invalid_fraction(self):
        received = [T0 + timedelta(hours=i) for i in range(10)]
        for fraction in (0.0, 1.0, -0.1, 1.1, float("nan"), float("inf"), True, [0.3]):
            with self.subTest(fraction=fraction), self.assertRaises(nv.NoveltyError):
                nv.time_split(received, fraction)

    def test_time_split_rejects_same_receipt_batch_at_boundary(self):
        received = [T0 + timedelta(hours=i) for i in range(10)]
        received[7] = received[6].astimezone(timezone(timedelta(hours=9)))
        for times in (received, [T0] * 10):
            with self.subTest(times=times), self.assertRaisesRegex(nv.NoveltyError, "distinct received_at"):
                nv.time_split(times)

    def test_time_split_keeps_registered_boundary_when_times_are_distinct(self):
        received = [T0 + timedelta(hours=i) for i in range(10)]
        train, test = nv.time_split(received)
        np.testing.assert_array_equal(train, np.arange(7))
        np.testing.assert_array_equal(test, np.arange(7, 10))

    def test_time_split_orders_distinct_dst_folds_by_instant(self):
        ny = ZoneInfo("America/New_York")
        before = [datetime(2026, 11, 1, i, tzinfo=timezone.utc) for i in range(6)]
        early = datetime(2026, 11, 1, 1, 30, tzinfo=ny, fold=0)
        late = datetime(2026, 11, 1, 1, 30, tzinfo=ny, fold=1)
        after = [datetime(2026, 11, 1, i, tzinfo=timezone.utc) for i in (7, 8)]
        train, test = nv.time_split(before + [late, early] + after)
        self.assertEqual(train[-1], 7)
        self.assertEqual(test[0], 6)

    def test_time_split_rejects_same_fold_instant_in_different_zones(self):
        ny = ZoneInfo("America/New_York")
        before = [datetime(2026, 11, 1, i, tzinfo=timezone.utc) for i in range(6)]
        late = datetime(2026, 11, 1, 1, 30, tzinfo=ny, fold=1)
        after = [datetime(2026, 11, 1, i, tzinfo=timezone.utc) for i in (7, 8)]
        with self.assertRaisesRegex(nv.NoveltyError, "distinct received_at"):
            nv.time_split(before + [late, late.astimezone(timezone.utc)] + after)


if __name__ == "__main__":
    unittest.main()
