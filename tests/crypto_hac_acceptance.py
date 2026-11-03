"""Independent HAC sandwich oracles on synthetic prices, no provider or store."""
from datetime import date, timedelta
import math
import unittest
from unittest.mock import patch

import dotenv
import numpy as np
with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.crypto.analytics import kimchi_premium


class KimchiHacTests(unittest.TestCase):
    def test_slope_and_t_match_independent_multivariate_sandwich(self):
        for size in (180, 540):
            for horizon in (1, 7, 14):
                with self.subTest(size=size, horizon=horizon):
                    rng = np.random.default_rng(size + horizon)
                    keys = [(date(2024, 1, 1) + timedelta(days=i)).isoformat() for i in range(size)]
                    btc = 100 * np.exp(np.cumsum(rng.normal(0, .01, size)))
                    premium = rng.normal(.02, .004, size)
                    got = kimchi_premium(dict(zip(keys, btc * 1300 * (1 + premium))),
                        dict(zip(keys, btc)), dict(zip(keys, np.full(size, 1300.))), horizon=horizon)
                    returns = np.log(btc[horizon:] / btc[:-horizon])
                    z = got.z_1y[:-horizon]
                    mask = np.isfinite(z)
                    X = np.column_stack((np.ones(mask.sum()), z[mask]))
                    y = returns[mask]
                    beta = np.linalg.lstsq(X, y, rcond=None)[0]
                    scores = X * (y - X @ beta)[:, None]
                    meat = scores.T @ scores
                    for lag in range(1, horizon):
                        cross = scores[lag:].T @ scores[:-lag]
                        meat += (1 - lag / horizon) * (cross + cross.T)
                    bread = np.linalg.inv(X.T @ X)
                    t = beta[1] / math.sqrt((bread @ meat @ bread)[1, 1])
                    self.assertAlmostEqual(got.pred_slope, beta[1], places=12)
                    self.assertAlmostEqual(got.pred_t, t, places=10)
                    self.assertAlmostEqual(got.last_pct, premium[-1] * 100, places=10)

    def test_insufficient_sample_does_not_invent_significance(self):
        keys = [(date(2024, 1, 1) + timedelta(days=i)).isoformat() for i in range(80)]
        btc = 100 * np.exp(np.linspace(0, .1, len(keys)))
        got = kimchi_premium(dict(zip(keys, btc * 1300 * 1.02)), dict(zip(keys, btc)),
                            dict(zip(keys, np.full(len(keys), 1300.))))
        self.assertTrue(math.isnan(got.pred_t))


if __name__ == "__main__":
    unittest.main()
