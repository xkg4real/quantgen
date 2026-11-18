"""Owner decision P2: novelty = model P(new | features), tested at cutoff 0.75 on a time-ordered hold-out.

Simulated data only (Stage 0), no network, fixed seed.
"""
from __future__ import annotations

import random
import unittest
from datetime import datetime, timedelta, timezone

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


if __name__ == "__main__":
    unittest.main()
