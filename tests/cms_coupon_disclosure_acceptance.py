"""CMS first-period annualized coupon meaning, with synthetic curves only."""
from copy import deepcopy
from dataclasses import asdict, replace
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch


def _no_private_io(event, args):
    if event == 'socket.connect':
        raise AssertionError('No provider calls in coupon disclosure tests')
    if event == 'open' and isinstance(args[0], (str, bytes)):
        path = Path(args[0].decode() if isinstance(args[0], bytes) else args[0])
        if path.name == '.env' or set(path.parts) & {'cache', 'paper_live', 'grokteam', 'cards', '_backup'}:
            raise AssertionError('Protected input is outside coupon disclosure tests')


sys.addaudithook(_no_private_io)
from tests.desktop_acceptance import QApplication, ResearchWindow
from tests.desktop_fx_language_acceptance import numbers
from core.ficc.curves import YieldCurve
from core.ficc import structured, insights
from core.ficc.common import tenor_label
from core.research.structuring_analysis import StructuringRequest, StructuringOutput
from core.research.structured_disclosure import cms_coupon_context
from quantgen_desktop.model_narrative_language import structured_korean, structured_variants
from quantgen_desktop.commentary import commentary_payload
from quantgen_desktop.localization import UiLabel
from quantgen_desktop.tools import fmt
from ui import structuring_page
from PyQt6.QtCore import QEvent
import flet as ft


LABEL = 'First-period expected coupon · p.a.'
KO_LABEL = '첫 기간 예상 쿠폰 · 연율'


def curve(shape='nonflat'):
    zeros = {'nonflat': (.03, .031, .032, .034, .035, .036, .037),
             'flat': (.035,) * 7,
             'inverted': (.05, .049, .047, .043, .04, .038, .037)}[shape]
    return YieldCurve('2026-01-02', 'SYNTHETIC', (.5, 1, 2, 5, 10, 20, 30), zeros)


@lru_cache
def output(shape='nonflat', frequency=1, floor=0., cap=None, tool='steep'):
    c = curve(shape)
    q = StructuringRequest(tool=tool, source='synthetic', maturity='5y' if tool=='steep' else '1y',
                           frequency=frequency, floor=floor, cap=cap)
    if tool == 'steep':
        r = structured.steepener_note(c, maturity=5, freq=frequency, floor=floor, cap=cap)
    elif tool == 'rc':
        r = structured.reverse_convertible(c, spot=1.1, vol=.1, r_for_or_div=.02, maturity=1)
    elif tool == 'dcd':
        r = structured.dual_currency_deposit(c, spot=1350, vol=.09, r_for=.045, maturity=1,
                                           strike=1300, base_ccy='USD', quote_ccy='KRW')
    else:
        r = structured.principal_protected_note(c, spot=1.1, vol=.08, r_for_or_div=.02, maturity=1)
    panel = SimpleNamespace(source='SYNTHETIC', note='Injected curve; no market source')
    return StructuringOutput(q, panel, c, r, insights.narrate_structured(r))


def walk(control):
    yield control
    for child in getattr(control, 'controls', None) or []:
        yield from walk(child)
    content = getattr(control, 'content', None)
    if isinstance(content, ft.Control):
        yield from walk(content)


class CouponDisclosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ('requests.sessions.Session.request', 'core.quant.validate.load_cards',
                       'core.quant.gate_ledger.family_ledger'):
            p = patch(target, side_effect=AssertionError('live I/O forbidden'))
            p.start(); self.addCleanup(p.stop)

    def test_first_period_matches_independent_cashflow_par_rates_and_is_annualized(self):
        # Independent annual-pay swap equation from discount factors. The CMS
        # projection fixes the first spread at time zero regardless of coupon frequency.
        for shape in ('nonflat', 'flat', 'inverted'):
            c = curve(shape)
            par = lambda years: (1-c.df(years)) / sum(c.df(i) for i in range(1, years+1))
            for floor, cap in ((0., None), (.005, None), (0., .006), (.005, .005)):
                expected = max(4*(par(10)-par(2)), floor)
                if cap is not None: expected = min(expected, cap)
                for frequency in (1, 2):
                    with self.subTest(shape=shape, floor=floor, cap=cap, frequency=frequency):
                        out = output(shape, frequency, floor, cap)
                        self.assertAlmostEqual(out.report.coupon, expected, places=14)
                        context = cms_coupon_context(out.report)
                        self.assertEqual(context['value'], out.report.coupon)
                        self.assertEqual(context['unit'], 'ANNUAL_DECIMAL_RATE')
                        self.assertEqual(context['quantity'], 'FIRST_PERIOD_EXPECTED_ANNUALIZED_COUPON')
                        self.assertEqual(context['scope'], 'FIRST_PERIOD_ONLY')
                        self.assertEqual(context['payment_guarantee'], 'NOT_ESTABLISHED_BY_MODEL')

    def test_nonflat_schedule_differs_and_zero_coupon_keeps_first_period_notice(self):
        out = output()
        coupons = structured._cms_coupons(out.curve, 5, 1, 4, 0, None)
        self.assertNotAlmostEqual(coupons[0][3], coupons[-1][3], places=6)
        detail = next(leg.detail for leg in out.report.legs if leg.name.startswith('CMS'))
        for _, end, spread, coupon in coupons:
            self.assertIn(f'{tenor_label(end)}: {coupon:.2%}', detail)
        zero = output('inverted').report
        self.assertEqual(zero.coupon, 0.)
        self.assertIsNotNone(cms_coupon_context(zero))
        self.assertIn('first-period expected coupon is 0.00% annualized', insights.narrate_structured(zero))

    def test_cms_narrative_in_both_languages_preserves_numbers_and_restricts_meaning(self):
        for out in (output(), output('flat'), output('inverted'), output(frequency=2, cap=.006),
                    output(floor=.005, cap=.005)):
            en, ko = out.narrative, structured_korean(out.report)
            self.assertEqual(numbers(en), numbers(ko))
            self.assertIn('first-period expected coupon', en)
            self.assertIn('first-period figure alone does not establish a fixed coupon for all periods or guarantee payment', en)
            self.assertIn('첫 기간 예상 쿠폰은 연율', ko)
            self.assertIn('기간별 선도 곡선 일정', ko)
            self.assertNotIn('The coupon is ', en)
            self.assertNotIn('연간 쿠폰은 ', ko)
            self.assertIn('NO convexity adjustment', en)

    def test_flet_label_and_ai_payload_keep_coupon_and_existing_schedule(self):
        for out in (output(), output('inverted'), output(frequency=2, floor=.005)):
            before = asdict(out.report)
            captured = {}
            def ai(page, **kw):
                captured.update(payload=kw['payload_fn'](), narrative=kw['narrative'])
                return ft.Text('Injected commentary')
            with patch.object(structuring_page, 'analysis_panel', side_effect=ai), \
                 patch.object(structuring_page.fcharts, 'payoff_chart', return_value=ft.Text('Injected chart')):
                blocks = structuring_page._render(Mock(), 'steep', out.report, out.panel, out.curve)
            text = '\n'.join(str(c.value) for b in blocks for c in walk(b) if isinstance(c, ft.Text))
            self.assertIn(LABEL, text)
            self.assertNotIn('Coupon (p.a.)', text)
            self.assertEqual(captured['payload']['coupon'], out.report.coupon)
            self.assertEqual(captured['payload']['coupon_interpretation'], cms_coupon_context(out.report))
            self.assertEqual(captured['payload']['legs'][1]['detail'], out.report.legs[1].detail)
            self.assertEqual(captured['narrative'], out.narrative)
            self.assertEqual(asdict(out.report), before)

    def test_native_labels_export_and_ai_keep_original_numbers_on_language_change(self):
        window = ResearchWindow(auto_refresh=False, language='en')
        pane = window.structuring
        try:
            for out in (output(), output('inverted'), output(frequency=2, cap=.006)):
                before = asdict(out.report)
                pane.show_result(out); pane.bind_output('structuring', out)
                report = deepcopy(pane.report)
                context = next(s for s in report['sections'] if s['type']=='coupon_interpretation')
                self.assertEqual(context, {'type': 'coupon_interpretation', **cms_coupon_context(out.report)})
                self.assertEqual(report['verdict'], 'NOT_RUN')
                payload = commentary_payload(report)
                self.assertIn(context, payload['sections'])
                for language in ('ko', 'en'):
                    window.set_language(language)
                    table = pane.tables['Metrics']
                    cells = {table.item(i, 0).text():table.item(i, 1).text() for i in range(table.rowCount())}
                    self.assertEqual(cells[KO_LABEL if language=='ko' else LABEL], fmt(out.report.coupon, 'pct'))
                    self.assertEqual(pane.report, report)
                    narrative = next(x for x in pane.findChildren(UiLabel) if x.source_text==out.narrative)
                    self.assertEqual(narrative.text(), structured_korean(out.report) if language=='ko' else out.narrative)
                self.assertEqual(asdict(out.report), before)
                pane.clear_result(); self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        finally:
            window.deleteLater(); self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_non_cms_rc_dcd_ppn_keep_existing_semantics_and_payload_shape(self):
        for tool in ('rc', 'dcd', 'ppn'):
            out = output(tool=tool); before = asdict(out.report); captured = {}
            self.assertIsNone(cms_coupon_context(out.report))
            self.assertNotIn('first-period', out.narrative)
            self.assertNotIn('첫 기간', structured_korean(out.report))
            if out.report.coupon is not None:
                self.assertIn(f'The coupon is {out.report.coupon:.2%} a year.', out.narrative)
            def ai(page, **kw):
                captured.update(kw['payload_fn']())
                return ft.Text('Injected commentary')
            with patch.object(structuring_page, 'analysis_panel', side_effect=ai), \
                 patch.object(structuring_page.fcharts, 'payoff_chart', return_value=ft.Text('Injected chart')):
                blocks = structuring_page._render(Mock(), tool, out.report, out.panel, out.curve)
            text = '\n'.join(str(c.value) for b in blocks for c in walk(b) if isinstance(c, ft.Text))
            self.assertNotIn(LABEL, text)
            self.assertNotIn('coupon_interpretation', captured)
            if tool=='dcd': self.assertIn('Enhanced yield (simple)', text)
            elif tool=='rc': self.assertIn('Coupon (p.a.)', text)
            self.assertEqual(asdict(out.report), before)

    def test_historical_or_external_narrative_is_not_rewritten(self):
        out = output(); original = f'The coupon is {out.report.coupon:.2%} a year. Historical report.'
        historical = replace(out, narrative=original)
        self.assertIsNone(structured_variants(historical))
        self.assertEqual(historical.narrative, original)
        self.assertIsNone(cms_coupon_context(replace(out.report, coupon=None)))


if __name__ == '__main__': unittest.main()
