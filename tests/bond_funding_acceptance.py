"""BS-21: financing must repay the present value at the horizon discount factor."""
import math
import unittest

from core.ficc import bonds, curves


class FundingTests(unittest.TestCase):
    def test_money_market_quote_is_the_financing_rate(self):
        for rate in (0.052, 0.0, -0.01):
            with self.subTest(rate=rate):
                curve = curves.bootstrap_par_curve([0.25, 1, 2], [rate] * 3)
                bond = bonds.Bond(coupon=0.05, maturity=2.0)
                result = bonds.carry_roll(bond, curve, 98.0, horizon=0.25)
                self.assertAlmostEqual(result.carry, 1.25 - 98.0 * rate * 0.25, places=11)

    def test_zero_coupon_financing_repayments_match_redemption(self):
        for rate in (0.06, 0.0, -0.02):
            for maturity in (0.1, 0.25, 1.0):
                with self.subTest(rate=rate, maturity=maturity):
                    curve = curves.flat_curve(rate)
                    bond = bonds.Bond(coupon=0.0, maturity=maturity)
                    price = 100.0 * math.exp(-rate * maturity)
                    result = bonds.carry_roll(bond, curve, price, horizon=maturity + 0.1)
                    self.assertAlmostEqual(result.total, 0.0, places=11)
                    self.assertAlmostEqual(price - result.carry, 100.0, places=11)


if __name__ == "__main__":
    unittest.main()
