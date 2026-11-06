"""Authored rates display text must retain numbers, branches and source reports."""
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from tests.desktop_acceptance import rates_fixture
from tests.desktop_fx_language_acceptance import numbers
from core.research.rates_analysis import RatesRequest
from core.research.tool_export import report_bytes
from core.ficc import insights
from quantgen_desktop.rates_narrative import rates_korean, curve_korean, simulation_korean, SHAPES, REGIMES
from quantgen_desktop.localization import UiLabel
from quantgen_desktop.app import ResearchWindow
from quantgen_desktop.tools import fmt
from PyQt6.QtWidgets import QApplication


class RatesLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        blocked = patch('requests.sessions.Session.request', side_effect=AssertionError('network forbidden'))
        blocked.start(); self.addCleanup(blocked.stop)

    def test_curve_fit_methods_pca_and_synthetic_disclosure(self):
        for method in ('bootstrap','nelson_siegel','svensson'):
            out = rates_fixture(RatesRequest(method=method,source='synthetic'))
            ko = rates_korean(out)
            self.assertEqual(numbers(out.narrative),numbers(ko))
            self.assertIn('SYNTHETIC',ko)
            self.assertIn('시장이 아닌 생성기',ko)
            self.assertIn('PCA 설명 분산',ko)
            self.assertIn(SHAPES[out.report.shape],ko)
            self.assertIn(REGIMES[out.report.regime],ko)

    def test_curve_without_pca_unknown_labels_and_missing_changes(self):
        out = rates_fixture(RatesRequest(source='synthetic'))
        r = replace(out.report,changes={},shape='future-shape',regime='future-regime')
        self.assertEqual(numbers(insights.narrate_curve(r)),numbers(curve_korean(r)))
        self.assertIn('future-shape',curve_korean(r)); self.assertIn('n/a',curve_korean(r))
        self.assertNotIn('PCA',curve_korean(r))
        pca = replace(out.pca,latest_scores=np.array([1.2]),labels=('unknown-component',))
        self.assertEqual(numbers(insights.narrate_curve(r,pca)),numbers(curve_korean(r,pca)))
        self.assertIn('unknown-component',curve_korean(r,pca))

    def test_swap_pay_receive_fixed_and_par_preserve_signs(self):
        for pay in (True,False):
            for fixed in (None,.08):
                out = rates_fixture(RatesRequest(tool='swap',source='synthetic',pay_fixed=pay,fixed_rate=fixed))
                ko = rates_korean(out)
                self.assertEqual(numbers(out.narrative),numbers(ko))
                self.assertIn('지급합니다' if pay else '수취합니다',ko)
                self.assertIn('곡선이 실현되면',ko)
                r = replace(out.report,krd={})
                self.assertEqual(numbers(insights.narrate_swap(r)),numbers(rates_korean(replace(out,report=r))))

    def test_option_kind_model_side_and_original_notes(self):
        for kind in ('swaption','cap','floor'):
            for model,vol in (('bachelier',.008),('black',.3)):
                for pay in (True,False):
                    out = rates_fixture(RatesRequest(tool='option',source='synthetic',kind=kind,
                        option_model=model,vol=vol,pay_fixed=pay,tenor='5y'))
                    ko = rates_korean(out)
                    self.assertEqual(numbers(out.narrative),numbers(ko))
                    self.assertIn('Bachelier' if model=='bachelier' else 'Black-76',ko)
                    if out.report.note: self.assertIn(out.report.note,ko)

    def test_unavailable_auxiliary_conversion_is_not_presented_as_success(self):
        out = rates_fixture(RatesRequest(tool='option',source='synthetic',strike=-.01))
        self.assertEqual(out.report.other_model_status,'UNAVAILABLE')
        ko = rates_korean(out)
        self.assertEqual(numbers(out.narrative),numbers(ko))
        self.assertNotIn('같은 프리미엄을 다른 모형으로 환산',ko)
        self.assertIn(out.report.note,ko)
        self.assertEqual(out.report.other_model_status,'UNAVAILABLE')

    def test_simulation_models_horizon_valuation_and_optional_evidence(self):
        for model,instrument in (('vasicek','none'),('cir','bond'),('hull_white','swap')):
            out = rates_fixture(RatesRequest(tool='sim',source='synthetic',model=model,instrument=instrument,
                                            horizon=.25,n_paths=100,threshold=.05))
            ko = rates_korean(out)
            self.assertEqual(numbers(out.narrative),numbers(ko))
            self.assertIn('초과할 확률',ko)
            self.assertEqual('기대 초과손실' in ko, instrument!='none')
            for note in (out.report.params.note,out.report.note):
                if note:self.assertIn(note,ko)
            r = replace(out.report,threshold=None,prob_above=None,model_curve_at_horizon=())
            self.assertEqual(numbers(insights.narrate_ratesim(r)),numbers(simulation_korean(r)))
            self.assertNotIn('초과할 확률',simulation_korean(r))
            self.assertNotIn('중앙 경로의 종료 시점 곡선',simulation_korean(r))

    def test_language_switch_restores_exact_sources_without_export_mutation(self):
        w = ResearchWindow(auto_refresh=False,language='ko');self.addCleanup(w.deleteLater)
        cases = [RatesRequest(source='synthetic'),RatesRequest(tool='swap',source='synthetic'),
                 RatesRequest(tool='option',source='synthetic'),
                 RatesRequest(tool='option',kind='floor',source='synthetic'),
                 RatesRequest(tool='sim',source='synthetic',horizon=.25,n_paths=100,threshold=.05)]
        with patch.object(w.jobs,'start',side_effect=AssertionError('language must not run jobs')):
            for q in cases:
                out = rates_fixture(q);w.rates.show_result(out);w.rates.bind_output('rates',out)
                before = deepcopy(w.rates.report)
                label = next(v for v in w.rates.findChildren(UiLabel) if v.source_text==out.narrative)
                for lang in ('ko','en','ko','en'):
                    w.set_language(lang)
                    self.assertEqual(label.text(),rates_korean(out) if lang=='ko' else out.narrative)
                    self.assertEqual(w.rates.report,before)
                self.assertTrue(any(s.get('text')==out.narrative for s in before['sections']))

    def test_unknown_tool_has_explicit_fallback(self):
        self.assertIsNone(rates_korean(SimpleNamespace(request=SimpleNamespace(tool='future'),report=None)))

    def assert_inline_roundtrip(self, window, output, variants):
        """Exercise actual result labels while canonical report/payload stay fixed."""
        pane = window.rates
        pane.show_result(output)
        pane.bind_output('rates', output)
        report = deepcopy(pane.report)
        exported = report_bytes(report)
        payload = deepcopy(window.commentary_sources())
        labels = {item.source_text: item for item in pane.findChildren(UiLabel)}
        for source, _en, _ko in variants:
            self.assertIn(source, labels)
            self.assertTrue(any(row.get('text') == source for row in report['sections']))
        with patch.object(window.jobs, 'start', side_effect=AssertionError('locale must not recompute')):
            for language in ('en', 'ko', 'en', 'ko'):
                window.set_language(language)
                for source, en, ko in variants:
                    item = labels[source]
                    self.assertEqual(item.source_text, source)
                    self.assertEqual(item.text(), ko if language == 'ko' else en)
                    self.assertEqual(numbers(source), numbers(item.text()))
                    self.assertNotEqual(item.property('display_role'), 'provenance')
                    self.assertTrue(item.property('reading_help_keep_visible'))
                self.assertEqual(pane.report, report)
                self.assertEqual(report_bytes(pane.report), exported)
                self.assertEqual(window.commentary_sources(), payload)

    def test_inline_source_summary_keeps_provider_notes_literal(self):
        w = ResearchWindow(auto_refresh=False, language='en'); self.addCleanup(w.deleteLater)
        base = rates_fixture(RatesRequest(source='synthetic'))
        # Catalog-looking lines inside source notes must not become UI translations.
        for source in ('SYNTHETIC', 'fixture-provider-unknown'):
            out = replace(base,
                          panel=replace(base.panel, source=source, note='Payer\nProvider note +1.250%'),
                          curve=replace(base.curve, note='Receive fixed\nCurve note -0.001%'))
            p, c = out.panel, out.curve
            original_prefix = '합성 곡선 · 현재 시장 데이터 아님\n' if source == 'SYNTHETIC' else ''
            notes = f'\n{p.note}\n{c.note}'
            original = original_prefix + f'{source} · {c.date} · {len(p)} observations · {c.method}' + notes
            en = ('Synthetic curve · not current market data\n' if source == 'SYNTHETIC' else '')
            en += f'{source} · {c.date} · {len(p)} observations · {c.method}' + notes
            ko = original_prefix + f'{source} · {c.date} · 관측 {len(p)}개 · {c.method}' + notes
            with self.subTest(source=source):
                self.assert_inline_roundtrip(w, out, [(original, en, ko)])

    def test_inline_swap_and_option_terms_preserve_units_sides_and_notes(self):
        w = ResearchWindow(auto_refresh=False, language='en'); self.addCleanup(w.deleteLater)
        for pay in (True, False):
            q = RatesRequest(tool='swap', source='synthetic', pay_fixed=pay, notional=1234567.4)
            out = rates_fixture(q)
            out = replace(out, report=replace(out.report, note='Payer\nSwap source note -1.25 bp'))
            r = out.report
            source = f'{q.notional:,.0f} notional · {r.swap.freq} payments/year · single curve · ACT/365F\n{r.note}'
            ko = f'명목금액 {q.notional:,.0f} · 연 {r.swap.freq}회 지급 · 단일 곡선 · ACT/365F\n{r.note}'
            with self.subTest(tool='swap', pay=pay):
                self.assert_inline_roundtrip(w, out, [(source, source, ko)])
        for kind in ('swaption', 'cap', 'floor'):
            for model, vol in (('bachelier', .008125), ('black', .3125)):
                for pay in (True, False):
                    q = RatesRequest(tool='option', source='synthetic', kind=kind, pay_fixed=pay,
                                     option_model=model, vol=vol, notional=1234567.4)
                    out = rates_fixture(q)
                    out = replace(out, report=replace(out.report, note='Receiver\nOption source +2.50%'))
                    value = fmt(vol, 'bp' if model == 'bachelier' else 'pct')
                    suffix = ' normal' if model == 'bachelier' else ' Black'
                    source = f'{model} · {value}{suffix} · {q.notional:,.0f} notional\n{out.report.note}'
                    ko = f'{model} · {value}' + (' 정규' if model == 'bachelier' else ' Black')
                    ko += f' · 명목금액 {q.notional:,.0f}\n{out.report.note}'
                    variants = [(source, source, ko)]
                    if kind == 'swaption':
                        direction = f'{q.expiry} × {q.tenor} · ' + ('Payer' if pay else 'Receiver')
                        ko_direction = f'{q.expiry} × {q.tenor} · ' + ('고정금리 지급형' if pay else '고정금리 수취형')
                        variants.append((direction, direction, ko_direction))
                    with self.subTest(kind=kind, model=model, pay=pay):
                        self.assert_inline_roundtrip(w, out, variants)

    def test_inline_simulation_seed_paths_and_model_notes_remain_literal(self):
        w = ResearchWindow(auto_refresh=False, language='en'); self.addCleanup(w.deleteLater)
        for model, source in (('vasicek', 'SYNTHETIC'), ('cir', 'fixture-short-rate-unknown'),
                              ('hull_white', 'SYNTHETIC')):
            out = rates_fixture(RatesRequest(tool='sim', source='synthetic', model=model,
                                            horizon=.25, n_paths=1000))
            out = replace(out, series=replace(out.series, source=source, note='Payer\nSeries note 3.00%'),
                          report=replace(out.report, note='Receiver\nSimulation note -0.25 bp',
                                         params=replace(out.report.params, note='Receive fixed\nParameter note 0.5')))
            s, r = out.series, out.report
            prefix = '합성 단기금리 · ' if source == 'SYNTHETIC' else ''
            evidence = f'{s.id} · {s.source} · {s.first_date} → {s.last_date}\n{s.note}\n{r.params.note}\n{r.note}\n'
            original = prefix + evidence + f'Seed 7 · {r.n_paths} paths'
            en = ('Synthetic short rate · ' if source == 'SYNTHETIC' else '') + evidence + f'Seed 7 · {r.n_paths} paths'
            ko = prefix + evidence + f'시드 7 · 경로 {r.n_paths}개'
            with self.subTest(model=model, source=source):
                self.assert_inline_roundtrip(w, out, [(original, en, ko)])


if __name__ == '__main__':unittest.main()
