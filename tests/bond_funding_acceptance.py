"""BS-21 owner-approved discount-factor funding; deterministic cashflow oracles."""
import math
import unittest
from unittest.mock import patch
import numpy as np
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.ficc.bonds import Bond, carry_roll, price_from_curve
    from core.ficc.curves import flat_curve


class SimpleFundingCurve:
    def __init__(self, rate): self.rate = rate
    def df(self, time): return 1.0 / (1.0 + self.rate * np.asarray(time))
    def zero(self, time): raise AssertionError('Funding must use the discount contract')


class BondFundingTests(unittest.TestCase):
    def test_simple_repo_repayment_matches_contract_interest(self):
        # A simple rate quote defines repayment P*(1+r*t), independent of a
        # continuous-zero quote or the implementation's discount conversion.
        bond=Bond(coupon=.04,maturity=3)
        for r in (-.01,0,.05,.20):
            for h in (.01,.25,1):
                with self.subTest(rate=r,horizon=h):
                    result=carry_roll(bond,SimpleFundingCurve(r),97,horizon=h)
                    interest=bond.coupon*bond.face*h-result.carry
                    self.assertAlmostEqual(interest,97*r*h,places=11)

    def test_continuous_curve_uses_exact_accumulation_not_linear_approximation(self):
        bond=Bond(coupon=.03,maturity=5);r=.20;h=1
        result=carry_roll(bond,flat_curve(r),98,horizon=h)
        interest=bond.coupon*bond.face*h-result.carry
        self.assertAlmostEqual(interest,98*math.expm1(r*h),places=11)
        self.assertGreater(abs(interest-98*r*h),1)

    def test_horizon_stops_funding_at_maturity(self):
        bond=Bond(coupon=.04,maturity=.10);curve=SimpleFundingCurve(.05)
        result=carry_roll(bond,curve,99,horizon=.25)
        self.assertAlmostEqual(result.carry,.04*100*.10-99*.05*.10,places=11)
        self.assertAlmostEqual(result.rolldown,1)
        self.assertAlmostEqual(result.total,result.carry+result.rolldown)

    def test_discount_repayment_identity_and_face_scaling(self):
        curve=flat_curve(.045)
        first=Bond(coupon=.05,maturity=7,face=100)
        second=Bond(coupon=.05,maturity=7,face=1000)
        a=carry_roll(first,curve,98,horizon=.25);b=carry_roll(second,curve,980,horizon=.25)
        self.assertAlmostEqual(b.carry,10*a.carry,places=10)
        # Discount the repayment reconstructed from the public carry output.
        repayment=98+first.coupon*first.face*.25-a.carry
        self.assertAlmostEqual(repayment*float(curve.df(.25)),98,places=11)

    def test_invalid_funding_discount_is_rejected(self):
        bond = Bond(coupon=.04, maturity=3)
        for discount in (0, -1, math.nan, math.inf):
            with self.subTest(discount=discount):
                curve = SimpleFundingCurve(.05)
                with patch.object(curve, 'df', return_value=discount):
                    with self.assertRaisesRegex(ValueError, 'finite and positive'):
                        carry_roll(bond, curve, 97, horizon=.25)

    def test_existing_holding_period_pnl(self):
        from tests.ficc_acceptance import test_bond_carry_roll_is_a_holding_period_pnl
        test_bond_carry_roll_is_a_holding_period_pnl()


if __name__=='__main__':unittest.main()
