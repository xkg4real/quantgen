"""M4-N6: descriptive CIP differences across local/native/Flet/AI/export paths."""
from collections import Counter
from copy import deepcopy
from io import BytesIO
import json
import math
import re
import unittest
from unittest.mock import Mock, patch
from zipfile import ZipFile

import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.ficc import fx, insights
    from core.ficc.common import BP
    from core.ficc.data import Series
    from core.quant import insights as ai_insights
    from core.research.fx_analysis import FXRequest, execute_fx
    from core.research.tool_export import report_bytes
    from quantgen_desktop.app import ResearchWindow
    from quantgen_desktop.commentary import commentary_payload
    from quantgen_desktop.fx_narrative import fx_korean
    from quantgen_desktop.localization import UiLabel
    from ui import fx_page
import flet as ft
from PyQt6.QtWidgets import QApplication


BASIS_BP = (None, 0, -4.9, 4.9, -5, 5, -12, 12)


def spot():
    return Series('EURUSD', 'EURUSD', 'SYNTHETIC', ('2026-01-01',), (1.1,), 'injected')


def fixture(basis_bp):
    market = None if basis_bp is None else 1.1 * math.exp((.03 - .02 + basis_bp * BP) * .5)
    request = FXRequest(tool='forward', source='synthetic', domestic_rate=.03,
                        foreign_rate=.02, tenor='6m', market_forward=market)
    return execute_fx(request, spot_loader=lambda *a, **k: spot(),
                      rate_loader=Mock(side_effect=AssertionError('no provider')))


def controls(root):
    yield root
    for child in getattr(root, 'controls', None) or []:
        yield from controls(child)
    content = getattr(root, 'content', None)
    if isinstance(content, ft.Control):
        yield from controls(content)


def numbers(text):
    return Counter(re.findall(r'[+-]?\d+(?:[.,]\d+)*(?:e[+-]?\d+)?', text))


class FXBasisDisclosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ('requests.sessions.Session.request', 'socket.socket.connect'):
            guard = patch(target, side_effect=AssertionError('network forbidden'))
            guard.start(); self.addCleanup(guard.stop)

    def test_all_sizes_keep_descriptive_wording_and_signed_number(self):
        base = insights.narrate_fx_forward('EURUSD', 1.1, 1.105, 50, -.01)
        self.assertIsNone(insights.fx_basis_note(None))
        for bp in BASIS_BP:
            with self.subTest(bp=bp):
                basis = None if bp is None else bp * BP
                text = insights.narrate_fx_forward('EURUSD', 1.1, 1.105, 50, -.01, basis)
                if basis is None:
                    self.assertEqual(text, base)
                    continue
                self.assertEqual(numbers(text), numbers(base + ' ' + f'{bp:+.1f}bp'))
                self.assertIn('signed annualized CIP discrepancy', text)
                self.assertIn('under the input rates', text)
                self.assertIn('timestamps, maturities and rate/quote conventions', text)
                self.assertIn('have not been verified as aligned', text)
                self.assertIn('does not establish a funding premium or statistical significance', text)
                self.assertNotIn('within noise', text)
                self.assertNotIn('a real funding premium', text)

    def test_analytic_forward_carry_curve_and_signed_basis_values_unchanged(self):
        for bp in BASIS_BP:
            with self.subTest(bp=bp):
                out = fixture(bp); data = out.data
                expected_forward = 1.1 * math.exp(.01 * .5)
                self.assertEqual(data['forward'], fx.forward(1.1, .03, .02, .5))
                self.assertAlmostEqual(data['forward'], expected_forward, places=14)
                self.assertEqual(data['points'], fx.forward_points(1.1, data['forward']))
                self.assertEqual(data['carry'], .02 - .03)
                for tenor, value in data['curve']:
                    self.assertEqual(value, fx.forward(1.1, .03, .02, tenor))
                if bp is None:
                    self.assertIsNone(data['basis'])
                else:
                    self.assertAlmostEqual(data['basis'], bp * BP, places=14)
                    self.assertAlmostEqual(data['basis'], math.log(out.request.market_forward / data['forward']) / .5, places=14)
                before = deepcopy(data)
                korean = fx_korean(out)
                self.assertEqual(numbers(out.narrative), numbers(korean))
                self.assertEqual(data, before)
                self.assertNotIn('잡음 범위 안', korean)
                self.assertNotIn('실제 자금조달 프리미엄을 나타냅니다', korean)
                if bp is not None:
                    self.assertIn('부호 있는 연환산 CIP 차이', korean)
                    self.assertIn('호가 시점, 만기 및 금리·호가 규약', korean)
                    self.assertIn('통계적 유의성을 판단할 수 없습니다', korean)

    def test_native_language_ai_preview_and_json_zip_keep_values_and_limits(self):
        w = ResearchWindow(auto_refresh=False, language='ko',
                           paper_factory=Mock(side_effect=AssertionError('no store')))
        self.addCleanup(w.deleteLater)
        for bp in BASIS_BP:
            with self.subTest(bp=bp):
                out = fixture(bp)
                w.fx.show_result(out)
                with patch('core.research.provenance.code_evidence', return_value={'commit': 'fixture'}), \
                     patch('core.research.provenance.runtime_evidence', return_value={'python': 'fixture'}):
                    w.fx.bind_output('fx', out)
                before = deepcopy(w.fx.report)
                widget = next(x for x in w.fx.findChildren(UiLabel) if x.source_text == out.narrative)
                for language in ('en', 'ko'):
                    w.set_language(language)
                    self.assertEqual(widget.text(), out.narrative if language == 'en' else fx_korean(out))
                    self.assertEqual(w.fx.report, before)
                canonical = json.loads(report_bytes(before))
                self.assertEqual(canonical['verdict'], 'NOT_RUN')
                self.assertEqual(canonical['parameters']['market_forward'], out.request.market_forward)
                self.assertTrue(any(s.get('text') == out.narrative for s in canonical['sections']))
                metric = next(s for s in canonical['sections'] if s.get('name') == 'Metrics')
                self.assertEqual(dict(metric['rows'])['Implied basis'],
                                 '—' if bp is None else f"{out.data['basis'] * 10000:+.2f} bp")
                payload = commentary_payload(before)
                self.assertEqual(payload['official_verdict'], 'NOT_RUN')
                self.assertTrue(any(s.get('text') == out.narrative for s in payload['sections']))
                with ZipFile(BytesIO(report_bytes(before, bundle=True))) as archive:
                    self.assertEqual(json.loads(archive.read('analysis.json')), canonical)
                    self.assertIn(out.narrative, archive.read('report.html').decode())

    def test_flet_display_and_real_ai_boundary_keep_disclosure_and_neutral_tone(self):
        for bp in BASIS_BP:
            with self.subTest(bp=bp):
                out = fixture(bp)
                page = Mock(); page.run_thread.side_effect = lambda work: work()
                calls = []
                def deep(kind, payload, **kw):
                    calls.append((kind, payload))
                    return ai_insights.Analysis('synthetic AI result', 'fixture')
                with patch.object(fx_page, 'load_fx_spot', return_value=spot()), \
                     patch.object(fx_page, 'load_short_rate', side_effect=AssertionError('no provider')), \
                     patch.object(fx_page.fcharts, 'fx_spot_chart', return_value=ft.Text('chart fixture')), \
                     patch.object(ai_insights, 'ai_ready', return_value=True), \
                     patch.object(ai_insights, 'deep_analysis', side_effect=deep), \
                     patch.object(fx_page, 'stat', wraps=fx_page.stat) as stat:
                    root = fx_page.build_fx_page(page)
                    fields = {c.label: c for c in controls(root) if isinstance(c, (ft.TextField, ft.Dropdown))}
                    for name, value in {'Data source': 'synthetic', 'Quote-ccy rate %': '3',
                                        'Base-ccy rate %': '2', 'Tenor': '6m',
                                        'Market forward (optional)': '' if bp is None else repr(out.request.market_forward)}.items():
                        fields[name].value = value
                    next(c for c in controls(root) if isinstance(c, ft.Button)).on_click(None)
                    text = '\n'.join(str(c.value) for c in controls(root) if isinstance(c, ft.Text))
                    self.assertIn(out.narrative, text)
                    next(c for c in controls(root) if isinstance(c, ft.Button) and c.content == 'Deep analysis').on_click(None)
                    basis_calls = [c for c in stat.call_args_list if c.args[0] == 'Implied basis']
                self.assertEqual(len(calls), 1)
                kind, payload = calls[0]
                self.assertEqual(kind, 'fx_forward')
                self.assertEqual(payload['market_forward'], out.request.market_forward)
                self.assertEqual(payload['implied_basis'], out.data['basis'])
                self.assertEqual(payload['forward'], out.data['forward'])
                self.assertEqual(payload['carry_pa_long_base'], out.data['carry'])
                self.assertEqual(payload['implied_basis_note'], insights.fx_basis_note(out.data['basis']))
                if bp is None:
                    self.assertFalse(basis_calls)
                else:
                    self.assertEqual(len(basis_calls), 1)
                    self.assertEqual(basis_calls[0].kwargs['token'], 'text')
                    self.assertIn('not been verified as aligned', basis_calls[0].kwargs['tooltip'])
                json.dumps(payload, allow_nan=False)


if __name__ == '__main__':
    unittest.main()
