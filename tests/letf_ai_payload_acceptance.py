"""Real Flet LETF scenario to optional AI; synthetic histories and a stub sender."""
import json
import unittest
from unittest.mock import Mock, patch

import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.quant import insights
    from core.quant.history import synthetic_history
    from core.research.ai_payload import private_field
    from ui import etf_page
import flet as ft


def controls(root):
    yield root
    for child in getattr(root, 'controls', None) or []:
        yield from controls(child)
    content = getattr(root, 'content', None)
    if isinstance(content, ft.Control):
        yield from controls(content)


class LETFAiPayloadTests(unittest.TestCase):
    def test_real_flet_scenario_reaches_ai_only_after_explicit_click(self):
        runner = Mock(return_value=insights.Analysis('Synthetic commentary', 'fixture-model'))
        page = Mock()
        page.run_thread.side_effect = lambda worker: worker()

        def history(symbol, *, source, days):
            self.assertEqual(source, 'synthetic')
            return synthetic_history(symbol, days=days)

        with patch('socket.socket.connect', side_effect=AssertionError('No live network')), \
             patch('requests.sessions.Session.request', side_effect=AssertionError('No providers')), \
             patch.object(etf_page, 'load_history', side_effect=history), \
             patch.object(etf_page, 'load_cards', return_value=()), \
             patch('core.quant.gate_ledger.family_ledger', side_effect=AssertionError('No ledger')), \
             patch.object(insights, 'ai_ready', return_value=True), \
             patch.object(insights, 'deep_analysis', runner):
            root = etf_page.build_etf_page(page)
            fields = {c.label: c for c in controls(root)
                      if isinstance(c, (ft.TextField, ft.Dropdown))}
            fields['Source'].value = 'synthetic'
            fields['ETF code'].value = '122630'
            fields['Sessions'].value = '60'
            fields['LETF comparison'].value = 'price_return'
            fields['LETF comparison'].on_select(None)
            for name, value in [('Annual funding rate (%)', '3.21'),
                                ('Annual fee (%)', '.64'),
                                ('Annual dividend yield (%)', '1.23')]:
                fields[name].value = value
            next(c for c in controls(root) if isinstance(c, ft.Button)
                 and c.content == 'Analyze').on_click(None)
            runner.assert_not_called()
            texts_before = [c.value for c in controls(root) if isinstance(c, ft.Text)]
            self.assertTrue(any('User scenario:' in str(s) for s in texts_before))
            self.assertTrue(any('price-return comparison' in str(s) for s in texts_before))
            button = next(c for c in controls(root) if isinstance(c, ft.Button)
                          and c.content == 'Deep analysis')
            self.assertFalse(button.disabled)
            button.on_click(None)

        runner.assert_called_once()
        kind, payload = runner.call_args.args
        self.assertEqual(kind, 'etf_structure')
        self.assertEqual(runner.call_args.kwargs['question'], '')
        self.assertEqual(payload['data_source'], 'SYNTHETIC')
        lt = payload['letf']
        assumptions = lt['assumptions']
        self.assertEqual(assumptions['benchmark'], 'price_return')
        self.assertAlmostEqual(assumptions['funding_rate'], .0321)
        self.assertAlmostEqual(assumptions['annual_fee'], .0064)
        self.assertAlmostEqual(assumptions['dividend_yield'], .0123)
        self.assertEqual(assumptions['funding_source'], 'USER_ASSUMPTION_NOT_MARKET_DATA')
        self.assertEqual(lt['index_status'], 'SYNTHETIC')
        self.assertEqual(lt['interpretation']['current_proxy_validation'], 'NOT_RUN')
        self.assertEqual(lt['verdict'], 'not run')
        row = next(r for r in lt['rows'] if r['sessions'] == 63)
        self.assertAlmostEqual(row['funding_bp'], -80.25)
        self.assertAlmostEqual(row['fee_bp'], -16.)
        self.assertAlmostEqual(row['dividend_bp'], 61.5)
        self.assertAlmostEqual(row['drag_bp'], sum(row[k] for k in
                              ('variance_bp', 'funding_bp', 'fee_bp', 'dividend_bp')))
        self.assertIn('reference_drag_bp', row)
        # These new scenario numbers must be finite. Existing GARCH nu may use
        # infinity as the normal-innovation limit, outside this input contract.
        json.dumps({'assumptions': assumptions, 'rows': lt['rows']}, allow_nan=False)

        def no_private_fields(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    self.assertFalse(private_field(key), key)
                    no_private_fields(child)
            elif isinstance(value, (list, tuple)):
                for child in value:
                    no_private_fields(child)

        no_private_fields(payload)
        # AI completion adds commentary; it does not replace the computed local explanation.
        texts_after = [c.value for c in controls(root) if isinstance(c, ft.Text)]
        for text in texts_before:
            self.assertIn(text, texts_after)
        self.assertIn('Synthetic commentary', texts_after)


if __name__ == '__main__':
    unittest.main()
