"""M4-N3 product scenarios: synthetic mathematics, injected histories, no study IO."""
from dataclasses import replace
from functools import lru_cache
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch


def _no_private_io(event, args):
    if event == 'socket.connect':
        raise AssertionError('No providers in LETF scenario tests')
    if event == 'open' and isinstance(args[0], (str, bytes)):
        p = Path(args[0].decode() if isinstance(args[0], bytes) else args[0])
        if p.name == '.env' or set(p.parts) & {'cache', 'paper_live', 'grokteam', 'cards', '_backup'}:
            raise AssertionError('Protected input is outside the test scope')


sys.addaudithook(_no_private_io)
import numpy as np
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.ficc.common import FICCError
    from core.ficc.equity_deriv import letf_drag, letf_drag_scenario
    from core.ficc.letf_assumptions import resolve_letf_assumptions
    from core.research import etf_workflow as wf
    from core.research.market_analysis import ETFRequest, execute_etf
    from ui import etf_page
import flet as ft


@lru_cache
def product(code='122630', benchmark='zero_rate_reference', q=None):
    kw = {} if benchmark == 'zero_rate_reference' else {
        'letf_benchmark': benchmark, 'letf_funding_rate': .0321,
        'letf_annual_fee': .0064, 'letf_dividend_yield': q}
    return wf.analyze(code, days=60, source='synthetic', card_loader=lambda p: (), **kw)


def controls(root):
    yield root
    for child in getattr(root, 'controls', None) or []:
        yield from controls(child)
    content = getattr(root, 'content', None)
    if isinstance(content, ft.Control):
        yield from controls(content)


class LETFAssumptionsTests(unittest.TestCase):
    def scenario(self, beta, **kw):
        args = {'funding_rate': .0321, 'annual_fee': .0064, 'benchmark': 'total_return'}
        args.update(kw)
        return letf_drag_scenario(beta, np.full(63, .20**2 / 252), **args)

    def test_independent_63_session_carry_and_sign_oracles(self):
        for beta, funding_bp, variance_bp, total_bp in ((2., -80.25, -100., -196.25),
                                                       (-1., 160.5, -100., 44.5),
                                                       (-2., 240.75, -300., -75.25)):
            with self.subTest(beta=beta):
                out = self.scenario(beta)
                self.assertAlmostEqual(out['funding_term'] * 10000, funding_bp, places=11)
                self.assertAlmostEqual(out['variance_term'] * 10000, variance_bp, places=11)
                self.assertAlmostEqual(out['fee_term'] * 10000, -16., places=11)
                self.assertEqual(out['dividend_term'], 0.)
                self.assertAlmostEqual(out['drag_bp'], total_bp, places=10)

    def test_price_comparison_has_signed_dividend_term_total_return_cancels_it(self):
        for beta, dividend_bp in ((2., 61.5), (-1., -30.75), (-2., -61.5)):
            tr = self.scenario(beta)
            price = self.scenario(beta, benchmark='price_return', dividend_yield=.0123)
            self.assertAlmostEqual(price['dividend_term'] * 10000, dividend_bp, places=11)
            self.assertAlmostEqual(price['drag_bp'] - tr['drag_bp'], dividend_bp, places=10)

    def test_deterministic_self_financing_wealth_against_both_benchmarks(self):
        # With zero volatility: asset price growth7%, yield2%, funding3%, fee1%.
        # Fund wealth solves the cash/asset self-financing ODE exactly; compare
        # its terminal wealth to independently compounded price and TR assets.
        years, mu, q, rate, fee = .25, .07, .02, .03, .01
        for beta in (2., -1., -2.):
            fund = math.exp((beta * (mu + q) + (1-beta) * rate - fee) * years)
            for benchmark, asset in (('price_return', math.exp(mu * years)),
                                      ('total_return', math.exp((mu + q) * years))):
                out = letf_drag_scenario(beta, np.zeros(63), funding_rate=rate, annual_fee=fee,
                                        benchmark=benchmark, dividend_yield=q if benchmark == 'price_return' else None)
                self.assertAlmostEqual(out['drag'], math.log(fund) - beta * math.log(asset), places=14)

    def test_period_scaling_and_negative_funding_are_explicit(self):
        for n in (21, 63, 252):
            out = letf_drag_scenario(2., np.zeros(n), funding_rate=-.02, annual_fee=0., benchmark='total_return')
            self.assertAlmostEqual(out['funding_term'], .02*n/252)
            self.assertEqual(out['year_fraction'], n/252)
            self.assertGreater(out['drag'], 0)

    def test_reference_rejects_silently_ignored_inputs(self):
        ref = resolve_letf_assumptions()
        self.assertEqual(ref['mode'], 'ZERO_RATE_REFERENCE')
        self.assertEqual(ref['funding_source'], 'REFERENCE_ZERO_NOT_MARKET_DATA')
        for kw in ({'funding_rate': 0.}, {'annual_fee': .0064}, {'dividend_yield': 0.}):
            with self.assertRaises(ValueError): resolve_letf_assumptions(**kw)

    def test_missing_rates_fee_or_price_yield_refuse(self):
        for kw in ({'benchmark': 'total_return'}, {'benchmark': 'total_return', 'funding_rate': .03},
                   {'benchmark': 'price_return', 'funding_rate': .03, 'annual_fee': .0064}):
            with self.assertRaises(ValueError): resolve_letf_assumptions(**kw)

    def test_total_return_refuses_double_counted_dividends_even_zero(self):
        for q in (0., .02):
            with self.assertRaises(ValueError):
                self.scenario(2., dividend_yield=q)

    def test_nonfinite_bool_negative_cost_and_unknown_basis_refuse(self):
        for field, value in (('funding_rate', float('nan')), ('funding_rate', True),
                             ('annual_fee', float('inf')), ('annual_fee', -.01),
                             ('benchmark', 'guess_from_fund_name')):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.scenario(2., **{field: value})
        with self.assertRaises(ValueError):
            self.scenario(2., benchmark='price_return', dividend_yield=-.01)

    def test_invalid_variance_path_is_not_a_valid_scenario(self):
        for v in ([], [[.01]], [float('nan')], [float('inf')], [-.01]):
            with self.assertRaises(FICCError):
                letf_drag_scenario(2., v, funding_rate=.03, annual_fee=.0064, benchmark='total_return')
        for beta in (True, float('nan'), float('inf')):
            with self.assertRaises(FICCError): self.scenario(beta)

    def test_request_validates_before_injected_execution(self):
        fn = Mock(side_effect=AssertionError('must not execute'))
        with self.assertRaises(ValueError):
            execute_etf(ETFRequest(letf_benchmark='price_return'), analyze_fn=fn)
        fn.assert_not_called()
        loader = Mock(side_effect=AssertionError('must not load prices'))
        with self.assertRaises(ValueError):
            wf.analyze('122630', letf_benchmark='total_return', history_loader=loader, card_loader=lambda p: ())
        loader.assert_not_called()

    def test_native_request_forwards_explicit_contract_and_preserves_study_status(self):
        request = ETFRequest(source='synthetic', code='122630', days=60, letf_benchmark='price_return',
                             letf_funding_rate=.0321, letf_annual_fee=.0064, letf_dividend_yield=.0123)
        out = execute_etf(request)
        assumptions = out.data['letf']['assumptions']
        self.assertEqual(assumptions['benchmark'], 'price_return')
        self.assertEqual(assumptions['funding_rate'], .0321)
        self.assertEqual(out.study_status, 'NOT_LOADED')
        self.assertEqual(out.data['letf']['verdict'], 'not run')

    def test_all_funds_reference_keeps_legacy_results_and_fixed_fee_provenance(self):
        for code in wf.LETF:
            lt = product(code)['letf']
            self.assertEqual(lt['calculation_status'], 'COMPUTED')
            self.assertEqual(lt['assumptions']['mode'], 'ZERO_RATE_REFERENCE')
            self.assertIn('NOT_VERIFIED', lt['assumptions']['fee_source'])
            expected = letf_drag(lt['beta'], np.full(63, lt['last_quarter_vol']**2/252), fee=lt['fee'])
            self.assertAlmostEqual(lt['last_quarter_drag_bp'], expected['drag_bp'], places=10)
            self.assertEqual(lt['last_quarter_drag_bp'], lt['last_quarter_reference_drag_bp'])
            for row in lt['rows']:
                self.assertEqual(row['drag_bp'], row['reference_drag_bp'])
                self.assertEqual(row['funding_bp'], 0)
                self.assertEqual(row['dividend_bp'], 0)

    def test_product_carry_changes_only_named_scenario_and_reports_components(self):
        for code, carry in (('122630', -80.25), ('114800', 160.5), ('252670', 240.75)):
            ref = product(code)['letf']
            lt = product(code, 'total_return')['letf']
            self.assertEqual(lt['last_quarter_reference_drag_bp'], ref['last_quarter_drag_bp'])
            self.assertAlmostEqual(lt['last_quarter_drag_bp'] - ref['last_quarter_drag_bp'], carry, places=10)
            row = next(r for r in lt['rows'] if r['sessions'] == 63)
            self.assertAlmostEqual(row['funding_bp'], carry)
            self.assertAlmostEqual(row['fee_bp'], -16.)
            self.assertAlmostEqual(row['drag_bp'], sum(row[k] for k in ('variance_bp','funding_bp','fee_bp','dividend_bp')))

    def test_user_fee_override_changes_scenario_without_rewriting_legacy_reference(self):
        ref = product('122630')['letf']
        out = execute_etf(ETFRequest(source='synthetic', code='122630', days=60, letf_benchmark='total_return',
                                    letf_funding_rate=0., letf_annual_fee=.01))
        lt = out.data['letf']
        self.assertEqual(lt['fee'], .01)
        self.assertEqual(lt['last_quarter_reference_drag_bp'], ref['last_quarter_drag_bp'])
        self.assertAlmostEqual(lt['last_quarter_drag_bp'] - ref['last_quarter_drag_bp'], -9., places=10)
        self.assertIn('fee=1.00%', out.narrative)

    def test_export_narrative_keeps_assumptions_and_unvalidated_study_boundary(self):
        data = product('122630', 'price_return', .0123)
        payload = wf.payload(data)
        encoded = json.dumps(payload)
        self.assertIn('USER_ASSUMPTION_NOT_MARKET_DATA', encoded)
        self.assertEqual(payload['letf']['interpretation']['rate_assumption'], .0321)
        self.assertEqual(payload['letf']['interpretation']['current_proxy_validation'], 'NOT_RUN')
        text = wf.narrative(data)
        self.assertIn('funding rate=3.21%', text)
        self.assertIn('dividend yield=1.23%', text)
        self.assertIn('price-return comparison', text)
        self.assertIn('ZERO_RATE_REFERENCE', text)
        self.assertNotIn('Current assumptions: rate=0', text)
        self.assertIn('does not validate this fund', text)

    def test_flet_fields_route_percent_inputs_and_component_tooltips(self):
        data = product('122630', 'price_return', .0123)
        page = Mock(); page.run_thread.side_effect = lambda work: work()
        with patch.object(etf_page, 'analyze', return_value=data) as analyze, \
             patch.object(etf_page, 'analysis_panel', return_value=ft.Text('injected AI')):
            root = etf_page.build_etf_page(page)
            fields = {c.label: c for c in controls(root) if isinstance(c, (ft.TextField, ft.Dropdown))}
            fields['LETF comparison'].value = 'price_return'
            fields['LETF comparison'].on_select(None)
            for label, value in (('ETF code', '122630'), ('Annual funding rate (%)', '3.21'),
                                 ('Annual fee (%)', '.64'), ('Annual dividend yield (%)', '1.23')):
                fields[label].value = value
            next(c for c in controls(root) if isinstance(c, ft.Button) and c.content == 'Analyze').on_click(None)
            kw = analyze.call_args.kwargs
            self.assertAlmostEqual(kw['letf_funding_rate'], .0321)
            self.assertAlmostEqual(kw['letf_annual_fee'], .0064)
            self.assertAlmostEqual(kw['letf_dividend_yield'], .0123)
            tooltips = '\n'.join(str(getattr(c, 'tooltip', '') or '') for c in controls(root))
            self.assertIn('funding -80.25 bp', tooltips)
            self.assertIn('dividend +61.50 bp', tooltips)

    def test_flet_missing_explicit_inputs_do_not_call_analysis(self):
        page = Mock(); page.run_thread.side_effect = lambda work: work()
        with patch.object(etf_page, 'analyze') as analyze:
            root = etf_page.build_etf_page(page)
            dropdown = next(c for c in controls(root) if isinstance(c, ft.Dropdown) and c.label == 'LETF comparison')
            dropdown.value = 'price_return'; dropdown.on_select(None)
            next(c for c in controls(root) if isinstance(c, ft.Button) and c.content == 'Analyze').on_click(None)
            analyze.assert_not_called()
            text = '\n'.join(str(c.value) for c in controls(root) if isinstance(c, ft.Text))
            self.assertIn('Enter explicit funding', text)


if __name__ == '__main__':
    unittest.main()
