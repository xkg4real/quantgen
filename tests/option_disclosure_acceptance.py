"""§10 options rework (M4-N4, M4-N7, M4-N9): say what three option-board numbers are.

* M4-N4 box: priced only from four two-sided legs, shown with its sensitivity and its range at
  the quoted bids and asks, and never called a funding rate.
* M4-N7 hedge: under the GBM engine (sigma_true = sigma_h) the expected mean P&L is 0 by
  construction, so its sign is not coloured or reported as earnings.
* M4-N9 MFIV: the strip's strike range is stated; the omitted wings bias it downward.

Offline synthetic boards only; no provider, AI or network call.
"""
from copy import deepcopy
from dataclasses import replace
import json
import math
import os
import re
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.ficc import equity_deriv as ED
    from core.ficc.common import BP
    from core.research import derivatives_workflow as wf
    from core.research import option_disclosure as OD
    from core.research.market_analysis import DerivativesRequest, MarketOutput
    from quantgen_desktop.market_narrative_language import derivatives_korean, market_variants
    from ui import derivatives_page
import flet as ft
from tests.portfolio_scope_acceptance import controls

NUMBER = re.compile(r'[-+]?\d[\d,]*(?:\.\d+)?%?')


def numbers(text):
    return sorted(NUMBER.findall(text))


def snap(**kw):
    with patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden')):
        return wf.snapshot(source='synthetic', n_paths=kw.pop('n_paths', 400), **kw)


def output(data):
    return MarketOutput(DerivativesRequest(source='synthetic', n_paths=400), data, wf.narrative(data), 'NOT_APPLICABLE')


class BoxTests(unittest.TestCase):
    def test_two_sided_box_is_unchanged_and_carries_its_band_and_sensitivity(self):
        quotes, T, F = wf.synthetic_board(), 20 / 365, 1126.0
        box, check = OD.box_check(quotes, T, F, live=True)
        k1 = max(q.strike for q in quotes if q.strike <= F); k2 = min(q.strike for q in quotes if q.strike > F)
        self.assertEqual(box, ED.box_rate(quotes, T, k1=k1, k2=k2))  # the shown rate is the same number as before
        a, b = {q.strike: q for q in quotes}[k1], {q.strike: q for q in quotes}[k2]
        bought = a.call_ask - b.call_bid + b.put_ask - a.put_bid
        self.assertEqual((check['status'], check['k1'], check['k2'], check['width_pts']), ('COMPUTED', k1, k2, 2.5))
        self.assertAlmostEqual(check['rate_bought_at_quotes'], -math.log(bought / 2.5) / T)
        self.assertAlmostEqual(check['bp_per_0_01pt'], 0.01 / (box['box'] * T) / BP)
        self.assertGreater(check['bp_per_0_01pt'], 500)  # a 2.5-point box: 0.01 point moves the rate by over 5 pp
        self.assertLess(check['rate_bought_at_quotes'], box['rate']); self.assertGreater(check['rate_sold_at_quotes'], box['rate'])

    def test_missing_legs_closed_market_and_no_bracket_are_not_priced(self):
        quotes, T, F = wf.synthetic_board(), 20 / 365, 1126.0
        k1 = max(q.strike for q in quotes if q.strike <= F)
        one_sided = [replace(q, put_bid=None) if q.strike == k1 else q for q in quotes]  # a last print or one-sided quote
        box, check = OD.box_check(one_sided, T, F, live=True)
        self.assertIsNone(box)
        self.assertEqual((check['status'], check['reason'], check['legs_without_two_sided_quote']),
                         ('NOT_RUN', 'legs_not_two_sided', [f'put {k1:g}']))
        self.assertEqual(OD.box_check(quotes, T, F, live=False)[1]['reason'], 'market_closed')
        self.assertEqual(OD.box_check([q for q in quotes if q.strike <= F], T, F, live=True)[1]['reason'],
                         'no_bracketing_strikes')

    def test_texts_never_call_it_a_funding_rate_and_keep_numbers_in_both_languages(self):
        s = snap()
        en, ko = OD.box_text(s), OD.box_korean(s)
        self.assertNotIn('funding rate of', en); self.assertIn('not a funding-rate estimate', en)
        self.assertIn('호가 품질 점검', ko); self.assertEqual(numbers(en), numbers(ko))
        cases = [dict(box=None),                                                             # box withheld, check kept
                 dict(box=None, box_check={'status': 'NOT_RUN', 'reason': 'legs_not_two_sided',
                                           'legs_without_two_sided_quote': ['call 1125', 'put 1125']}),
                 dict(box_check=None)]                                                       # older fixture
        for change in cases:
            d = {**deepcopy(s), **change}
            with self.subTest(change=list(change)):
                self.assertEqual(numbers(OD.box_text(d)), numbers(OD.box_korean(d)))
        self.assertIn('2 of its 4 legs', OD.box_text({**s, **cases[1]}))
        self.assertEqual(OD.box_korean({**s, 'box': None}), '중간값으로 가격을 산출할 수 있는 ATM 박스가 없습니다.')


class HedgeTests(unittest.TestCase):
    def test_scope_follows_the_arguments_the_simulation_received(self):
        self.assertEqual(OD.hedge_scope('gbm', .2)['expected_mean_status'], 'ZERO_BY_CONSTRUCTION')
        for kw in ({'sigma_true': .25}, {'drift_daily': .0001}, {'cost_bps': 2.0}):
            self.assertEqual(OD.hedge_scope('gbm', .2, **kw)['expected_mean_status'], 'MODEL_RESULT', kw)
        self.assertEqual(OD.hedge_scope('garch_t', .2)['expected_mean_status'], 'MODEL_RESULT')

    def test_gbm_mean_is_labelled_noise_and_garch_is_a_model_result(self):
        gbm, garch = snap(engine='gbm'), snap(engine='garch_t')
        self.assertTrue(OD.same_vol(gbm)); self.assertFalse(OD.same_vol(garch))
        for s, expected in ((gbm, True), (garch, False)):
            en, ko = wf.narrative(s), derivatives_korean(s)
            self.assertEqual('0 bp by construction' in en, expected); self.assertEqual('정의상 0 bp' in ko, expected)
            self.assertNotIn('earns', en)
            self.assertEqual(numbers(en), numbers(ko))
            hedge = wf.payload(s)['hedge']
            self.assertEqual(hedge['expected_mean_status'], 'ZERO_BY_CONSTRUCTION' if expected else 'MODEL_RESULT')
            self.assertEqual(hedge['expected_mean_pnl_bp'], 0.0 if expected else None)
            self.assertEqual(hedge['mean_pnl_bp'], s['hedge'].mean_pnl_bp)  # the simulated number itself is unchanged

    def test_no_claim_without_the_recorded_scope(self):
        s = deepcopy(snap())
        s['hedge'] = ED.hedge_pnl_simulation(spot=1126.0, strike=1125.0, horizon_days=14, sigma_hedge=.17,
                                             sigma_true=.17 * 1.25, rate=.032, n_paths=400, seed=7)
        del s['hedge_scope']   # a fixture or loader that did not record how the simulation ran
        self.assertFalse(OD.same_vol(s))
        self.assertNotIn('by construction', wf.narrative(s)); self.assertNotIn('정의상', derivatives_korean(s))
        self.assertNotIn('expected_mean_status', wf.payload(s)['hedge'])


class MfivTests(unittest.TestCase):
    def test_strip_range_is_stated_in_both_languages_and_payload(self):
        s = snap()
        strip = OD.mfiv_strip(s)
        mv = s['mfiv']
        self.assertEqual((strip['status'], strip['k_min'], strip['k_max']), ('COMPUTED', mv['k_min'], mv['k_max']))
        self.assertAlmostEqual(strip['lower_moneyness'], mv['k_min'] / s['F'] - 1)
        sd = s['atm'].iv * math.sqrt(s['T'])
        self.assertAlmostEqual(strip['upper_atm_vol_sd'], math.log(mv['k_max'] / s['F']) / sd)
        en, ko = wf.narrative(s), derivatives_korean(s)
        self.assertIn('biases the model-free vol downward', en); self.assertIn('낮게 편향', ko)
        self.assertEqual(numbers(en), numbers(ko))
        body = wf.payload(s)
        self.assertEqual(body['mfiv'], mv['vol'])  # existing key unchanged
        json.dumps({k: body[k] for k in ('mfiv_strip', 'box_check', 'hedge')}, allow_nan=False)

    def test_not_computed_strip_states_nothing(self):
        s = {**deepcopy(snap()), 'mfiv': {'vol': float('nan'), 'n_strikes': 0, 'error': 'too few strikes'}}
        self.assertEqual(OD.mfiv_strip(s)['status'], 'NOT_RUN'); self.assertEqual(OD.mfiv_text(OD.mfiv_strip(s)), '')
        self.assertIn('Model-free variance not computed', wf.narrative(s))
        json.dumps(OD.mfiv_strip(s), allow_nan=False)


class ValidInputsUnchanged(unittest.TestCase):
    def test_every_existing_payload_value_is_kept(self):
        """Only keys are added; the GBM hedge sentence only swaps 'earns ... on average' for 'has a simulated mean P&L of'."""
        s = snap(engine='gbm')
        body = wf.payload(s)
        self.assertEqual(body['box_rate'], s['box']['rate'])
        self.assertEqual(set(body['hedge']) - {'expected_mean_status', 'expected_mean_pnl_bp', 'scope'},
                         {'engine', 'sigma_hedge', 'mean_pnl_bp', 'se_bp', 'cvar95_bp', 'breakeven_vol',
                          'identity_slope', 'identity_r2'})


class FletPage(unittest.TestCase):
    def test_tiles_tooltips_and_ai_payload(self):
        s = snap(engine='gbm'); page = Mock(); page.run_thread.side_effect = lambda f: f(); seen = {}
        original = derivatives_page.stat

        def stat(title, value, **kw):
            seen[title] = (value, kw.get('token', 'text'), kw.get('tooltip', ''))
            return original(title, value, **kw)

        def ai(page, **kw):
            seen['payload'] = kw['payload_fn'](); return ft.Text('injected AI')
        with patch.object(derivatives_page, 'snapshot', return_value=s), \
             patch.object(derivatives_page, 'stat', side_effect=stat), \
             patch.object(derivatives_page, 'analysis_panel', side_effect=ai):
            root = derivatives_page.build_derivatives_page(page)
            next(c for c in controls(root) if isinstance(c, ft.Button) and c.on_click).on_click(None)
        value, token, tip = seen['Hedge P&L (mean)']
        self.assertEqual(value, f"{s['hedge'].mean_pnl_bp:+.0f} bp"); self.assertEqual(token, 'text')
        self.assertIn('Monte Carlo noise', tip)
        self.assertIn('by construction', seen['Break-even realised vol'][2])
        self.assertIn('not a funding-rate estimate', seen['Box rate (quote check)'][2])
        self.assertIn('of F', seen['MFIV strike range'][0]); self.assertIn('biases the model-free vol', seen['MFIV'][2])
        self.assertEqual(seen['payload']['hedge']['expected_mean_status'], 'ZERO_BY_CONSTRUCTION')
        self.assertEqual(seen['payload']['box_check']['status'], 'COMPUTED')
        text = '\n'.join(str(c.value) for c in controls(root) if isinstance(c, ft.Text))
        self.assertIn('0 bp by construction', text)


class NativePane(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_rows_sections_and_disclosure(self):
        from PyQt6.QtWidgets import QLabel
        from quantgen_desktop.app import ResearchWindow
        from core.research.tool_export import report_bytes
        w = ResearchWindow(auto_refresh=False); p = w.derivatives
        try:
            out = output(snap(engine='gbm'))
            p.show_result(out); p.bind_output('Option disclosure fixture', out)
            table = p.tables['Futures & volatility']
            rows = {table.item(i, 0).text(): table.item(i, 1).text() for i in range(table.rowCount())}
            self.assertIn('/', rows['Model-free IV strike range · % of forward'])
            self.assertIn('/', rows['Box rate at quotes · bought / sold'])
            self.assertNotIn('Box funding', rows)
            obj = json.loads(report_bytes(p.report))
            types = {sec['type'] for sec in obj['sections']}
            self.assertTrue({'hedge_scope', 'box_check', 'mfiv_strip'} <= types)
            self.assertTrue(any('0 bp by construction' in x.text() for x in p.findChildren(QLabel)))
            self.assertEqual(market_variants(out, 'derivatives')['en'], out.narrative)
        finally:
            p.clear_result(); w.close(); w.deleteLater(); self.app.processEvents()


if __name__ == '__main__':
    unittest.main()
