"""Risk display contracts using synthetic metadata only; no model or provider runs."""
from copy import deepcopy
from types import SimpleNamespace
import unittest

from quantgen_desktop.metric_help import financial_help, mc_metadata, risk_help, risk_pair, stock_risk_help


class RiskExplanationTests(unittest.TestCase):
    def test_live_mc_uses_effective_horizon_and_unrounded_confidence(self):
        requested = {'parameters': {'horizon_days': 5, 'var_level': .95}}
        actual = SimpleNamespace(horizon_days=42, var_level=.975)
        label, hover = risk_pair('var', 'mc_terminal_loss', **mc_metadata(requested, actual))
        for language in range(2):
            self.assertIn('97.5%', label[language])
            self.assertIn('42', hover[language])
            self.assertNotIn('95%', label[language])
        self.assertIn('terminal / initial', hover[0])
        self.assertIn('not maximum loss', hover[0])

    def test_old_saved_run_does_not_acquire_a_95_percent_confidence(self):
        saved = {'parameters': {'horizon_days': 126}, 'metrics': {'var_pct': .12, 'cvar_pct': .18}}
        untouched = deepcopy(saved)
        metadata = mc_metadata(saved)
        for kind in ('var', 'cvar'):
            value = risk_help(kind, 'mc_terminal_loss', 'en', **metadata)
            self.assertIn('confidence not recorded', value.hover)
            self.assertNotIn('95%', value.label + value.hover)
            self.assertIn('126 trading sessions', value.hover)
        self.assertEqual(saved, untouched)

    def test_hedge_explains_signed_lower_pnl_tail_without_positive_loss_clamp(self):
        value = risk_help('cvar', 'hedge_signed_bp', 'en', confidence=.95, horizon_days=21, unit='bp')
        self.assertIn('worst 5%', value.label)
        self.assertIn('Negative is a loss', value.hover)
        self.assertIn('positive may be a gain', value.hover)
        self.assertIn('at least one path', value.hover)
        self.assertNotIn('negative risk estimates display as zero', value.hover)
        self.assertIn('1 bp = 0.01%', value.hover)
        with self.assertRaises(ValueError):
            risk_help('var', 'hedge_signed_bp', 'en', confidence=.95)

    def test_rates_money_loss_has_year_horizon_and_no_invented_currency(self):
        value = risk_help('cvar', 'rates_pv_loss', 'en', confidence=.95, horizon_years=.25)
        self.assertIn('0.25 years', value.hover)
        self.assertIn("today's PV", value.hover)
        self.assertIn('not %, not bp', value.hover)
        self.assertIn('currency unspecified', value.hover)
        self.assertNotIn('trading sessions', value.hover)
        self.assertNotIn('USD', value.hover)

    def test_loss_tail_and_signed_tail_have_distinct_korean_meanings(self):
        positive_loss = risk_help('cvar', 'mc_terminal_loss', 'ko', confidence=.99, horizon_days=63)
        signed = risk_help('cvar', 'hedge_signed_bp', 'ko', confidence=.95, horizon_days=63)
        self.assertIn('큰 손실 평균', positive_loss.label)
        self.assertIn('나쁜 5% 때 평균손익', signed.label)
        self.assertIn('음수는 손실', signed.hover)
        self.assertIn('양수는 이익', signed.hover)

    def test_invalid_confidence_stays_unknown_instead_of_using_a_default(self):
        for level in (None, True, 0, 1, float('nan'), float('inf'), '0.95'):
            with self.subTest(level=level):
                value = risk_help('var', 'mc_terminal_loss', 'en', confidence=level)
                self.assertIn('confidence not recorded', value.hover)
                self.assertNotIn('95%', value.label)

    def test_stock_history_retains_its_daily_log_loss_context(self):
        value = stock_risk_help('var', 'en', confidence=.975, horizon_days=1, unit='%', basis='historical_log_loss')
        self.assertIn('97.5%', value.label)
        self.assertIn('1-day', value.hover)
        self.assertIn('historical daily log loss', value.hover)
        self.assertIn('not the maximum loss', value.hover)

    def test_financial_zero_denominators_are_not_only_low_multiple_warnings(self):
        for metric in ('per', 'pbr', 'roe', 'psr'):
            with self.subTest(metric=metric):
                self.assertIn('undefined', financial_help(metric, 'en').hover)
                self.assertIn('0이면 정의할 수 없', financial_help(metric, 'ko').hover)


if __name__ == '__main__':
    unittest.main()
