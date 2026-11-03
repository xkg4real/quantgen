"""M4-N5 and M3-N07: independent synthetic inputs, no data stores/providers."""
from datetime import date, timedelta
import math
import unittest
from unittest.mock import patch
import numpy as np
import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from core.ficc import fx_styles as F, swaps
    from core.ficc.data import Series
    from core.ficc.curves import YieldCurve
    from core.ficc.common import FICCError
    from core.research.rates_analysis import RatesRequest, execute_rates


def monthly_fixture(n, rho, step=21):
    rng = np.random.default_rng(n + int((rho + 1) * 100))
    x = rng.normal(.001, .002, n)
    e = rng.normal(size=n) * (.004 + 2 * abs(x))
    for i in range(1, n):
        e[i] += rho * e[i-1]
    y = .0003 - .8 * x + e
    count = n * step + 1
    ds = tuple((date(2000, 1, 1) + timedelta(days=i)).isoformat() for i in range(count))
    px = np.exp(np.interp(np.arange(count), np.arange(n+1) * step, np.r_[0., y.cumsum()]))
    usd = np.full(count, .02)
    eur = usd + np.r_[np.repeat(x * 252 / step, step), x[-1] * 252 / step]
    def series(name, values):
        return Series(name, name, "SYNTHETIC", ds, tuple(values))
    return {"EURUSD": series("EURUSD", px)}, {"EUR": series("EUR", eur), "USD": series("USD", usd)}, x, y


class FiccBoundaryTests(unittest.TestCase):
    def test_fama_slope_t_matches_full_matrix_hac_sandwich(self):
        for n in (60, 140):
            for rho in (-.4, 0., .65):
                with self.subTest(n=n, rho=rho):
                    spots, rates, x, y = monthly_fixture(n, rho)
                    row = F.fama_regression(spots, rates)[0]
                    X = np.column_stack((np.ones(n), x))
                    beta = np.linalg.lstsq(X, y, rcond=None)[0]
                    score = X * (y - X @ beta)[:, None]
                    bread = np.linalg.inv(X.T @ X)
                    lagged = score[1:].T @ score[:-1]
                    meat = score.T @ score + .5 * (lagged + lagged.T)
                    covariance = bread @ meat @ bread
                    t = beta[1] / math.sqrt(covariance[1, 1])
                    self.assertAlmostEqual(row.slope, beta[1], places=11)
                    self.assertAlmostEqual(row.t_stat, t, places=10)
                    self.assertEqual(row.n_months, n)

    def test_fama_insufficient_or_constant_differential_stays_unreported(self):
        spots, rates, _, _ = monthly_fixture(10, .2)
        self.assertEqual(F.fama_regression(spots, rates), [])
        spots, rates, _, _ = monthly_fixture(20, .2)
        rates["EUR"] = rates["USD"]
        self.assertEqual(F.fama_regression(spots, rates), [])

    def test_no_unfixed_caplets_refuses_instead_of_zero_premium(self):
        curve = YieldCurve("2026-01-01", "SYNTHETIC", (.1, 1., 10.), (.04, .04, .04))
        for tenor in (.1, .25):
            for cap in (False, True):
                with self.subTest(tenor=tenor, cap=cap):
                    with self.assertRaisesRegex(FICCError, "no unfixed"):
                        swaps.price_cap_floor(curve, tenor, None, vol=.008, cap=cap)

    def test_forward_start_short_cap_still_prices_its_one_caplet(self):
        curve = YieldCurve("2026-01-01", "SYNTHETIC", (.1, 1., 10.), (.04, .04, .04))
        out = swaps.price_cap_floor(curve, .25, .04, start=.5, vol=.008)
        self.assertEqual(len(out.caplets), 1)
        fwd = (curve.df(.5) / curve.df(.75) - 1) / .25
        z = (fwd - .04) / (.008 * math.sqrt(.5))
        cdf = .5 * (1 + math.erf(z / math.sqrt(2)))
        density = math.exp(-z*z/2) / math.sqrt(2*math.pi)
        expected = 1e6 * .25 * curve.df(.75) * ((fwd - .04) * cdf + .008 * math.sqrt(.5) * density)
        self.assertAlmostEqual(out.premium, expected, places=8)

    def test_native_invalid_short_cap_refuses_before_provider_read(self):
        for kind in ("cap", "floor"):
            request = RatesRequest(tool="option", kind=kind, tenor="3m")
            with self.assertRaisesRegex(ValueError, "unfixed"):
                execute_rates(request, curve_loader=lambda **kw: self.fail("invalid cap fetched a curve"))


if __name__ == "__main__":
    unittest.main()
