"""Authored display prose switches language without changing analysis evidence."""
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
import json
import unittest
from unittest.mock import patch

# These fixtures inject synthetic data and suppress dotenv before engine imports.
from tests.desktop_acceptance import signals_fixture, structuring_fixture
from tests.ar1_decay_acceptance import etf_fixture, crypto_fixture
from tests.letf_disclosure_acceptance import fixture as letf_fixture
from tests.quote_coverage_acceptance import output as derivatives_fixture
from tests.desktop_fx_language_acceptance import numbers
from core.research.signals_analysis import SignalsRequest
from core.research.structuring_analysis import StructuringRequest
from core.research.letf_disclosure import letf_text, letf_unavailable_text
from quantgen_desktop.market_narrative_language import (
    market_variants, etf_korean, crypto_korean, derivatives_korean,
    letf_korean, letf_unavailable_korean,
)
from quantgen_desktop.model_narrative_language import signals_variants, structured_variants, strategy_variants
from quantgen_desktop.translations import translate
from quantgen_desktop.localization import UiLabel
from quantgen_desktop.app import ResearchWindow
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QEvent


def structure_cases():
    return [StructuringRequest(source='synthetic', tool='ppn'),
            StructuringRequest(source='synthetic', tool='ppn', underlying='EQ', spot=100, vol=.25,
                               maturity='5y', protection=.9, futures_dv01=65),
            StructuringRequest(source='synthetic', tool='rc', maturity='1y'),
            StructuringRequest(source='synthetic', tool='dcd', maturity='3m', spot=1350, strike=1300,
                               vol=.09, r_for=.045, margin=.25),
            StructuringRequest(source='synthetic', tool='dcd', maturity='3m', spot=1350, strike=1300,
                               vol=.09, r_for=.045, margin=90),
            StructuringRequest(source='synthetic', tool='steep', maturity='5y'),
            StructuringRequest(source='synthetic', tool='steep', maturity='5y', cap=.03)]


class AuthoredProseLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ('requests.sessions.Session.request', 'core.quant.validate.load_cards',
                       'core.quant.gate_ledger.family_ledger'):
            p = patch(target, side_effect=AssertionError('live I/O forbidden'))
            p.start(); self.addCleanup(p.stop)

    def test_market_narratives_preserve_every_number_and_verdict(self):
        for kind, out in [('etf', etf_fixture()), ('etf', letf_fixture()),
                          ('crypto', crypto_fixture()), ('derivatives', derivatives_fixture()),
                          ('derivatives', derivatives_fixture(True))]:
            with self.subTest(kind=kind, request=out.request):
                variants = market_variants(out, kind)
                self.assertEqual(variants['en'], out.narrative)
                self.assertEqual(numbers(variants['en']), numbers(variants['ko']))
                self.assertRegex(variants['ko'], '[가-힣]')
                self.assertIsNone(market_variants(replace(out, narrative='External source 원문 12.34'), kind))
        c = crypto_fixture()
        for converged, at_bound, funding in ((False, ['nu', 'alpha'], None), (True, [], c.data['funding'])):
            d = deepcopy(c.data); d['garch'].update(converged=converged, at_bound=at_bound);d['funding'] = funding
            d['verdicts']['D_C2_garch_btc'] = 'REJECT'; d['ethbtc']['verdict'] = 'SUPPLIED 판정'
            from core.research.crypto_workflow import narrative
            ko = crypto_korean(d)
            self.assertEqual(numbers(narrative(d)), numbers(ko))
            self.assertIn('REJECT', ko); self.assertIn('SUPPLIED 판정', ko)
            if not converged: self.assertIn('수렴하지 않았습니다', ko)

    def test_derivatives_missing_models_box_and_failed_gate_are_not_pass(self):
        from core.research.derivatives_workflow import narrative
        d = deepcopy(derivatives_fixture().data)
        d['reconcile']['ok'] = False; d['box'] = None
        d['mfiv'] = {'error': 'External reason 원문 91.23'}
        d['svi'] = replace(d['svi'], min_g=-1)
        ko = derivatives_korean(d)
        self.assertEqual(numbers(narrative(d)), numbers(ko))
        for text in ('게이트 밖', '버터플라이 차익거래 구간', '91.23', '산출할 수 있는 ATM 박스가 없습니다'):
            self.assertIn(text, ko)

    def test_letf_scope_and_unavailable_errors_preserve_not_run(self):
        lt = letf_fixture().data['letf']
        ko = letf_korean(lt)
        self.assertEqual(numbers(letf_text(lt)), numbers(ko))
        for warning in ('실현 드래그', '검증하지 않습니다', '실현 선물 벤치마크가 아닙니다', '권고로 사용하지 마세요'):
            self.assertIn(warning, ko)
        for error in ('Required index history or exact code mapping unavailable; no substitute index used.',
                      'Index model calculation failed.', 'Provider 원문 12.34'):
            unavailable = {'underlying_index': 'KOSDAQ150', 'error': error}
            ko = letf_unavailable_korean(unavailable)
            self.assertIn('NOT_RUN', ko); self.assertIn('KOSDAQ150', ko)
            self.assertEqual(numbers(letf_unavailable_text(unavailable)), numbers(ko))
            if error.startswith('Provider'): self.assertIn(error, ko)
        d = deepcopy(etf_fixture().data); d['letf'] = unavailable
        from core.research.etf_workflow import narrative
        self.assertEqual(numbers(narrative(d)), numbers(etf_korean(d)))

    def test_signals_all_tools_and_backtest_branches_keep_signs_and_raw_reasons(self):
        from core.quant.insights import narrate_signals, narrate_backtest
        for tool in ('ma_cross', 'momentum', 'rsi_revert'):
            out = signals_fixture(SignalsRequest(tool=tool, source='synthetic'))
            for beat, drawdown, win_rate in ((True, -.1, .6), (False, -.01, None), (False, -.99, .25)):
                b = replace(out.backtest, total_return=out.backtest.bench_return + (.1 if beat else -.1),
                            max_drawdown=drawdown, win_rate=win_rate)
                narrative = narrate_signals(out.report) + ' ' + narrate_backtest(b)
                variants = signals_variants(replace(out, backtest=b, narrative=narrative))
                self.assertEqual(numbers(narrative), numbers(variants['ko']))
                self.assertIn('과거에 대한 설명', variants['ko'])
            self.assertIsNone(signals_variants(replace(out, narrative='User 원문')))
        self.assertEqual(translate('Provider 원문 Price is 12% above its 50-day average.', 'ko'),
                         'Provider 원문 Price is 12% above its 50-day average.')

    def test_structuring_all_products_and_warnings_keep_number_tokens(self):
        for request in structure_cases():
            with self.subTest(request=request):
                out = structuring_fixture(request); variants = structured_variants(out)
                self.assertEqual(numbers(variants['en']), numbers(variants['ko']))
                self.assertIsNone(structured_variants(replace(out, narrative='Provider 원문')))
                if request.tool == 'steep':
                    self.assertIn('볼록성 조정 없이', variants['ko'])
                    self.assertIn('과대평가', variants['ko'])
                    detail = out.report.legs[1].detail
                    self.assertEqual(numbers(detail), numbers(translate(detail, 'ko')))
                    self.assertNotIn('spread', translate(detail, 'ko'))
                    self.assertIn('스프레드', translate(detail, 'ko'))
                elif request.tool in ('ppn', 'rc'):
                    self.assertIn('발행자 신용 스프레드를 반영하지 않습니다', variants['ko'])

    def test_signals_stance_labels_roundtrip_without_changing_canonical_enum(self):
        from core.quant.insights import narrate_signals, narrate_backtest
        # Include a catalog collision as an unknown stance: it must stay raw.
        labels = {'strong bullish': '강한 상승 우위', 'bullish': '상승 우위',
                  'neutral': '중립', 'bearish': '하락 우위',
                  'strong bearish': '강한 하락 우위', 'Gold': 'Gold'}
        original = signals_fixture(SignalsRequest(source='synthetic'))
        window = ResearchWindow(auto_refresh=False, language='en')
        try:
            pane = window.signals
            for stance, korean in labels.items():
                signal = replace(original.report, stance=stance)
                narrative = narrate_signals(signal) + ' ' + narrate_backtest(original.backtest)
                out = replace(original, report=signal, narrative=narrative)
                pane.show_result(out); pane.bind_output('Stance fixture', out)
                report = deepcopy(pane.report); sections = deepcopy(pane.sections)
                values = deepcopy(pane.values())
                summary = next(x for x in pane.findChildren(UiLabel) if x.source_text == narrative)
                with patch.object(window.jobs, 'start', side_effect=AssertionError('must not recompute')):
                    for language in ('ko', 'en', 'ko'):
                        window.set_language(language)
                        expected = korean if language == 'ko' else stance
                        self.assertEqual(pane.tables['Composite'].item(0, 1).text(), expected)
                        self.assertIn(expected, summary.text())
                        self.assertEqual(out.report.stance, stance)
                        self.assertEqual(out.report.composite, original.report.composite)
                        self.assertEqual(pane.report, report); self.assertEqual(pane.sections, sections)
                        self.assertEqual(pane.values(), values)
                        self.assertEqual(numbers(summary.text()), numbers(narrative))
                self.assertIn(narrative, [s['text'] for s in pane.sections if s['type'] == 'text'])
                pane.clear_result()
        finally:
            window.signals.clear_result(); window.deleteLater()
            self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_strategy_withheld_reason_and_recorded_score_evidence_stay_raw(self):
        from tests.strategy_exposure_acceptance import fixture
        from core.research.strategy_analysis import StrategyRequest, StrategyOutput
        from core.research.strategy_workflow import narrative, payload
        from quantgen_desktop.strategy_view import CODE_ROLE
        for cost in (50, 1):
            data = fixture(cost=cost)
            variants = strategy_variants(data)
            self.assertEqual(numbers(variants['en']), numbers(variants['ko']))
            self.assertIn(payload(data)['reason'], variants['ko'])
            for line in data['score'].lines: self.assertIn(line, variants['ko'])
            self.assertIn('노출을 일치시킨 비교가 아닙니다', variants['ko'])
            if data.get('withheld'): self.assertIn('판정 보류', variants['ko'])
        w = ResearchWindow(auto_refresh=False, language='ko')
        try:
            data = fixture(cost=1); out = StrategyOutput(StrategyRequest(cost_bps=1), data)
            w.strategy.show_result(out); w.strategy.bind_output('Synthetic strategy', out)
            original = deepcopy(w.strategy.report)
            summary = next(x for x in w.strategy.findChildren(UiLabel) if x.source_text == narrative(data))
            for language in ('en', 'ko', 'en'):
                w.set_language(language)
                self.assertEqual(summary.text(), strategy_variants(data)[language])
                self.assertEqual(w.strategy.report, original)
            w.strategy.clear_result()
            # Historical cards must remain intact in either UI language.
            card = {'card_id': 'CUSTOM_ID', 'kind': 'strategy', 'decision': 'REJECT',
                    'hypothesis': 'Historical 원문', 'decision_reason': 'Previous reason 3.21',
                    'lines': ['Historical evidence 12.34', 'Provider: ORIGINAL'], 'citations': ['Source A']}
            out = StrategyOutput(StrategyRequest(tool='cards'), {'cards': [card]})
            w.strategy.show_result(out)
            for language in ('ko', 'en'):
                w.set_language(language)
                text = '\n'.join(x.text() for x in w.strategy.findChildren(UiLabel))
                self.assertIn('Historical 원문', text); self.assertIn('Historical evidence 12.34', text)
                self.assertIn('Provider: ORIGINAL', text)
                # The verdict code stays visible and raw; a Korean window shows its meaning beside it
                # ('기각 · REJECT', owner issue 09).
                verdict = w.strategy.tables['Study scorecard'].item(0, 2)
                self.assertEqual(verdict.text(), {'ko': '기각 · REJECT', 'en': 'REJECT'}[language])
                self.assertEqual(verdict.data(CODE_ROLE), 'REJECT')
        finally:
            w.strategy.clear_result();w.deleteLater();self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_provider_notes_matching_ui_vocabulary_are_not_translated(self):
        raw = 'Provider: RAW_ORIGINAL'
        self.assertNotEqual(translate(raw, 'ko'), raw)  # An actual catalog collision.
        w = ResearchWindow(auto_refresh=False, language='ko')
        try:
            signal = signals_fixture(SignalsRequest(source='synthetic'))
            signal = replace(signal, history=replace(signal.history, note=raw))
            structured = structuring_fixture(structure_cases()[0])
            structured = replace(structured, panel=SimpleNamespace(source='SYNTHETIC', note=raw),
                                 curve=SimpleNamespace(date='2026-01-02', method='bootstrap', note=raw))
            deriv = derivatives_fixture(); data = deepcopy(deriv.data); data['quotes_note'] = raw
            deriv = replace(deriv, data=data)
            for pane, out in ((w.signals, signal), (w.structuring, structured), (w.derivatives, deriv)):
                pane.show_result(out)
                for language in ('en', 'ko'):
                    w.set_language(language)
                    self.assertIn(raw, '\n'.join(x.text() for x in pane.findChildren(UiLabel)))
                pane.clear_result()
            from core.research.market_analysis import KRXRequest, KRXOutput
            w.krx.show_result(KRXOutput(KRXRequest(), SimpleNamespace(source='MOCK', ok=False, reason=raw)))
            w.set_language('ko')
            self.assertIn(raw, [x.text() for x in w.krx.findChildren(UiLabel)])
        finally:
            for pane in (w.signals, w.structuring, w.derivatives, w.krx): pane.clear_result()
            w.deleteLater();self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_window_switch_preserves_inputs_models_tables_reports_and_does_not_recompute(self):
        w = ResearchWindow(auto_refresh=False, language='ko')
        try:
            cases = [(w.etf, letf_fixture()), (w.crypto, crypto_fixture()),
                     (w.derivatives, derivatives_fixture(True)),
                     (w.signals, signals_fixture(SignalsRequest(source='synthetic'))),
                     (w.structuring, structuring_fixture(structure_cases()[0])),
                     (w.structuring, structuring_fixture(structure_cases()[-1]))]
            for pane, out in cases:
                pane.show_result(out); pane.bind_output('Language fixture', out)
                report = deepcopy(pane.report); values = deepcopy(pane.values())
                sections = json.dumps(pane.sections, sort_keys=True, default=lambda v: v.item())
                source, tool = pane.source.currentData(), pane.tool.currentData()
                summary = next(x for x in pane.findChildren(UiLabel) if x.source_text == out.narrative)
                self.assertTrue(summary.localized_text)
                self.assertIn(out.narrative, [s['text'] for s in pane.sections if s['type'] == 'text'])
                with patch.object(w.jobs, 'start', side_effect=AssertionError('must not recompute')):
                    for language in ('en', 'ko', 'en', 'ko'):
                        w.set_language(language)
                        self.assertEqual(summary.text(), summary.localized_text[language])
                        self.assertEqual(pane.report, report)
                        self.assertEqual(json.dumps(pane.sections, sort_keys=True, default=lambda v: v.item()), sections)
                        self.assertEqual(pane.values(), values)
                        self.assertEqual((pane.source.currentData(), pane.tool.currentData()), (source, tool))
                        if pane is w.signals:
                            table = pane.tables['Signal components']
                            for i, component in enumerate(out.report.components):
                                self.assertEqual(table.item(i, 4).text(), translate(component.reason, language))
                                self.assertEqual(table.item(i, 3).text(), component.value)
                        if pane is w.structuring:
                            self.assertEqual(pane.tables['Metrics'].item(0, 1).text(),
                                             translate(out.report.product, language))
                            note = next(x for x in pane.findChildren(UiLabel) if x.source_text.startswith('Hedge 부호:'))
                            self.assertTrue(note.text().startswith('Hedge sign:' if language == 'en' else 'Hedge 부호:'))
                            greeks = pane.tables['Greeks']
                            self.assertEqual(greeks.horizontalHeaderItem(0).text(), 'Risk' if language == 'en' else '위험')
                            self.assertEqual(greeks.item(0, 0).text(), 'Delta · per +1% spot' if language == 'en' else '델타 · 현물 +1%당')
                            table = pane.tables['Hedge sheet']
                            for i, hedge in enumerate(out.report.hedge):
                                self.assertEqual(table.item(i, 0).text(), translate(hedge.instrument, language))
                pane.clear_result();self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        finally:
            for pane in (w.etf, w.crypto, w.derivatives, w.signals, w.structuring): pane.clear_result()
            w.deleteLater();self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)


if __name__ == '__main__': unittest.main()
