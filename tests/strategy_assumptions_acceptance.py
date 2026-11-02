"""N6/N9/N10 and bounded interpretation notices using synthetic data only."""
from copy import deepcopy
from inspect import signature
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import warnings

import numpy as np
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.quant import strategies as S, validate as V
    from core.research import strategy_workflow as flow
    from ui import strategy_lab_page as page_module
from core.research.strategy_assumptions import assumption_summary, assumption_lines, historical_card_lines
from tests.strategy_exposure_acceptance import fixture
from tests.portfolio_scope_acceptance import controls
import flet as ft


class AdfCompatibilityTests(unittest.TestCase):
    def test_installed_adf_pvalues_identical_without_return_type_warning(self):
        from statsmodels.tsa.stattools import adfuller
        rng = np.random.default_rng(61010)
        for count in (30, 80, 252):
            for x in (rng.normal(size=count), np.cumsum(rng.normal(size=count))):
                kwargs = {'autolag': 'AIC'}
                if 'result_object' in signature(adfuller).parameters:
                    kwargs['result_object'] = False
                expected = float(adfuller(x, **kwargs)[1])
                with warnings.catch_warnings(record=True) as captured:
                    warnings.simplefilter('always')
                    actual = S.adf_pvalue(x)
                self.assertEqual(actual, expected)
                self.assertFalse([w for w in captured if issubclass(w.category, FutureWarning)])

    def test_legacy_tuple_contract_receives_no_new_keyword(self):
        calls = []
        def old_adf(x, maxlag=None, regression='c', autolag='AIC', store=False, regresults=False):
            calls.append((x.copy(), regression, autolag))
            return (-2.0, .12345, 1, len(x), {})
        x = np.arange(30.)
        with patch('statsmodels.tsa.stattools.adfuller', old_adf):
            self.assertEqual(S.adf_pvalue(x), .12345)
        np.testing.assert_array_equal(calls[0][0], x)
        self.assertEqual(calls[0][1:], ('c', 'AIC'))

    def test_new_result_contract_opts_in_and_reads_named_pvalue(self):
        calls = []
        def new_adf(x, maxlag=None, regression='c', autolag='AIC', store=False,
                    regresults=False, *, result_object=None):
            calls.append((regression, autolag, result_object))
            return SimpleNamespace(pvalue=.0625)
        with patch('statsmodels.tsa.stattools.adfuller', new_adf):
            self.assertEqual(S.adf_pvalue(np.arange(30.)), .0625)
        self.assertEqual(calls, [('c', 'AIC', True)])

    def test_failures_remain_missing_not_a_pass(self):
        with patch('statsmodels.tsa.stattools.adfuller', side_effect=ValueError('invalid data')):
            self.assertTrue(math.isnan(S.adf_pvalue(np.ones(30))))
        self.assertTrue(math.isnan(S.adf_pvalue(np.ones(30))))


class StrategyAssumptionTests(unittest.TestCase):
    def test_pair_weights_match_independent_beta_normalization_for_both_signs(self):
        rng = np.random.default_rng(6106)
        x = np.cumsum(rng.normal(0, .01, 83)) + 4
        for beta in (2., -1.):
            y = 2 + beta * x + .001 * np.cos(np.arange(83))
            y[80:] += .05
            price = np.column_stack([np.exp(y), np.exp(x)])
            weights, diagnostic = S.pairs(price, formation=80, trading=3, entry=.5, gross=1.7)
            estimated = float(np.cov(x[:80], y[:80], ddof=0)[0, 1] / np.var(x[:80]))
            expected = np.array([-1., estimated]) * 1.7 / (1 + abs(estimated))
            np.testing.assert_allclose(weights[80], expected, rtol=1e-12, atol=1e-12)
            self.assertAlmostEqual(abs(weights[80]).sum(), 1.7)
            self.assertAlmostEqual(weights[80].sum(), -1.7*(1-estimated)/(1+abs(estimated)))
            self.assertNotAlmostEqual(weights[80].sum(), 0.)
            self.assertEqual(np.sign(weights[80,0]) == np.sign(weights[80,1]), beta < 0)
            self.assertAlmostEqual(diagnostic.hedge_ratios[0], estimated)

    def test_full_oos_cutoff_changes_earlier_classification_without_changing_formulas(self):
        rng = np.random.default_rng(6109)
        b = np.r_[rng.normal(0, .002, 180), rng.normal(0, .03, 220)]
        pnl = rng.normal(.0002, .01, len(b))
        window = 20
        vols = np.array([np.std(b[max(0, i-window):i], ddof=1) if i>=5 else np.nan for i in range(len(b))])
        valid = np.isfinite(vols)
        high_full = vols > np.nanmedian(vols)
        high_prefix = vols[:180] > np.nanmedian(vols[:180])
        self.assertGreater(np.sum(high_prefix != high_full[:180]), 30)
        actual = V.regime_split(pnl, b, window=window)
        self.assertEqual(actual['high_vol'], V.sharpe(pnl[valid & high_full]))
        self.assertEqual(actual['low_vol'], V.sharpe(pnl[valid & ~high_full]))
        info = assumption_summary('trend_switch', cash_daily=.03/252, has_regime=True)
        self.assertEqual(info['regime_threshold_basis'], 'whole_oos_median_retrospective')
        self.assertIn('later observations can change earlier classifications', ' '.join(assumption_lines(info)))

    def test_metadata_distinguishes_cash_signal_and_sharpe_without_new_verdict(self):
        for family in ('trend_switch', 'tsmom', 'pairs', 'vol_target'):
            info = assumption_summary(family, cash_daily=.03/252, has_regime=family!='pairs')
            self.assertEqual(info['cash_rate_per_session'], .03/252)
            self.assertEqual(info['sharpe_basis'], 'net_returns_without_risk_free_subtraction')
            self.assertEqual(info['momentum_signal_cash_rate_per_session'],
                             0.0 if family in {'trend_switch', 'tsmom'} else None)
            self.assertEqual(bool(info['pairs_weighting']), family=='pairs')
            en, ko = assumption_lines(info), assumption_lines(info, 'ko')
            self.assertEqual(len(en), len(ko))
            self.assertIn('fixed 3% / 252', en[0])
            self.assertIn('고정 3% / 252', ko[0])
            self.assertNotIn('decision', info)
        self.assertEqual(assumption_lines(None), [])
        self.assertEqual(assumption_lines({'schema': 'historical-unknown'}), [])

    def test_historical_card_is_unchanged_and_unrelated_card_is_not_relabelled(self):
        pair = {'card_id':'S_E8_pair_example','decision':'REVISE',
                'stats':{'share_cointegrated': .8}, 'lines':['ADF rejects a unit root in 80% of windows'],
                'hypothesis':'dollar-neutral', 'decision_reason':'original reason', 'kind':'strategy'}
        before = deepcopy(pair)
        en = historical_card_lines(pair)
        self.assertIn('not an Engle–Granger cointegration p-value or pass rate', en[0])
        self.assertIn('generally have nonzero net exposure', en[1])
        self.assertEqual(len(historical_card_lines(pair, 'ko')), 2)
        self.assertEqual(pair, before)
        for card in ({'card_id':'S_E80_other'}, {'card_id':'D_OTHER', 'lines':pair['lines']}, {}):
            self.assertEqual(historical_card_lines(card), [])

    def test_flet_run_and_ai_basis_receive_identical_assumptions(self):
        r = fixture('vol_target', 1, cost=1)
        before = deepcopy(r['score'].__dict__)
        captured = {}; page = SimpleNamespace(update=lambda:None, run_thread=lambda work:work())
        def panel(page, **kw):
            captured.update(payload=kw['payload_fn'](), narrative=kw['narrative'])
            return ft.Text('injected AI panel')
        with patch.object(page_module, 'load_cards', return_value=[]), \
             patch.object(page_module, 'run_family', return_value=r), \
             patch.object(page_module, 'analysis_panel', side_effect=panel):
            root = page_module.build_strategy_lab_page(page)
            next(c for c in controls(root) if isinstance(c, ft.Button) and c.content=='Run').on_click(None)
        rendered = '\n'.join(str(c.value) for c in controls(root) if isinstance(c, ft.Text))
        for line in assumption_lines(r['assumptions']):
            self.assertIn(line, rendered)
            self.assertIn(line, captured['narrative'])
            self.assertIn(line, captured['payload']['assumption_notes'])
        self.assertEqual(captured['payload']['decision'], 'WITHHELD')
        self.assertNotIn('decision', captured['payload']['stats'])
        self.assertEqual(r['score'].__dict__, before)

    def test_flet_historical_pair_notes_keep_original_text_and_numbers(self):
        card = flow._study_card({'card_id':'S_E8_synthetic','decision':'REVISE','kind':'strategy',
            'hypothesis':'original dollar-neutral claim','decision_reason':'original reason',
            'stats':{'share_cointegrated':.8},'lines':['original ADF share 80%'],'citations':['source']})
        before = deepcopy(card)
        page = SimpleNamespace(update=lambda:None)
        with patch.object(page_module, 'load_cards', return_value=[card]):
            root = page_module.build_strategy_lab_page(page)
        rendered = '\n'.join(str(c.value) for c in controls(root) if isinstance(c, ft.Text))
        for line in historical_card_lines(card): self.assertIn(line, rendered)
        self.assertIn(card['hypothesis'], rendered)
        self.assertIn('original ADF share 80%', rendered)
        self.assertEqual(card, before)


if __name__=='__main__': unittest.main()
