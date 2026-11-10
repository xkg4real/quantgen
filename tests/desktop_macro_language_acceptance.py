"""Display-only macro localization preserves source, units, warnings and run state."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from dataclasses import replace
from itertools import product
import unittest
from unittest.mock import patch
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.ficc import insights
    from core.ficc.macro import (MacroRow, MacroSheet, Regime, INDICATORS,
        CURVE_REGIMES, RISK_REGIMES, DOLLAR_REGIMES, TREND_REGIMES)
    from core.research.macro_analysis import MacroRequest, execute_macro
    from quantgen_desktop.app import ResearchWindow
    from quantgen_desktop.localization import UiLabel
    from quantgen_desktop.macro_narrative_language import PAIRS, macro_korean, sheet_note_korean, summary_korean, indicator_caption
    from quantgen_desktop import translations
    from tests.desktop_fx_language_acceptance import numbers
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QCloseEvent


def fixture(*, synthetic=True, sign=1, missing=False, short=False):
    rows=[]
    for index, ind in enumerate(INDICATORS):
        last = .03 + index * .001 if ind.unit=='pct' else (.001 + index*.0001 if ind.unit=='bp' else 100.+index)
        day = sign * (.0001 if ind.unit in ('pct','bp') else .3)
        rows.append(MacroRow(ind.id, ind.label, ind.group, ind.unit, last,
            '2026-11-02', None if missing else day, None if missing else day*3,
            None if missing else day*4, None if missing else day*7,
            sign*(index*.17), index/18, 'SYNTHETIC' if synthetic else 'FIXTURE'))
    ids=tuple(x.id for x in rows) if synthetic else ()
    summary=('[descriptive read — not a regime model (P19)] Curve bull steepener '
        '(10y -14bp, 2s10s +12bp over 20 sessions); risk-off (VIX/HY z +0.91); '
        'dollar weak (-2.1% 1m); breakevens falling, real yields rising (1m -10bp / +15bp).')
    note=('18/18 indicators are SYNTHETIC: '+', '.join(ids)+'.') if synthetic else ''
    if short:note+=(' ' if note else '')+'Shortest series has 35 obs; z/percentile use fewer than 252.'
    return MacroSheet('2026-11-02',tuple(rows),Regime('bull steepener','risk-off','weak','falling','rising',summary),
        {'SYNTHETIC' if synthetic else 'FIXTURE':len(rows)}, ids, note)


def output(tool='sheet', **kwargs):
    sheet=fixture(**kwargs)
    return execute_macro(MacroRequest(tool=tool,source='synthetic'),sheet_loader=lambda **_:sheet)


class MacroLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ('requests.sessions.Session.request', 'core.ficc.macro.macro_sheet'):
            blocker=patch(target, side_effect=AssertionError('provider/loader forbidden'))
            blocker.start();self.addCleanup(blocker.stop)

    def test_each_narrative_preserves_all_numbers_units_source_and_warning(self):
        for tool,synthetic,sign,missing in product(('sheet','daily','weekly'),(True,False),(1,-1),(True,False)):
            with self.subTest(tool=tool,synthetic=synthetic,sign=sign,missing=missing):
                out=output(tool,synthetic=synthetic,sign=sign,missing=missing)
                before=deepcopy(out)
                korean=macro_korean(out)
                self.assertIsNotNone(korean)
                self.assertEqual(numbers(out.narrative),numbers(korean))
                for unit in ('bp','%','n/a'):
                    self.assertEqual(out.narrative.count(unit),korean.count(unit))
                self.assertEqual('SYNTHETIC' in out.narrative,'SYNTHETIC' in korean)
                self.assertIn('국면 모형',korean)
                if synthetic and tool!='daily':self.assertIn('시장',korean)
                if tool=='weekly':self.assertIn('투자 권고를 하지 않습니다',korean)
                self.assertEqual(before,out)

    def test_all_supported_summary_categories_keep_numeric_tokens(self):
        for curve,risk,dollar,trend in product(CURVE_REGIMES,RISK_REGIMES,DOLLAR_REGIMES,TREND_REGIMES):
            text=fixture().regime.summary.replace('bull steepener',curve).replace('risk-off',risk).replace('dollar weak','dollar '+dollar).replace('breakevens falling','breakevens '+trend)
            korean=summary_korean(text)
            self.assertNotEqual(text,korean)
            self.assertEqual(numbers(text),numbers(korean))
            self.assertEqual(text.count('bp'),korean.count('bp'))
            self.assertEqual(text.count('%'),korean.count('%'))

    def test_known_words_in_wrong_summary_roles_are_not_reinterpreted(self):
        text=fixture().regime.summary
        for wrong in (text.replace('Curve bull steepener','Curve neutral'),
                      text.replace('; risk-off','; strong'),
                      text.replace('dollar weak','dollar rising'),
                      text.replace('breakevens falling','breakevens risk-on')):
            self.assertEqual(wrong,summary_korean(wrong))

    def test_sheet_notes_preserve_all_ids_numbers_and_unknown_prose(self):
        for synthetic,short in product((True,False),(True,False)):
            s=fixture(synthetic=synthetic,short=short)
            korean=sheet_note_korean(s.note)
            self.assertEqual(numbers(s.note),numbers(korean))
            for ident in s.synthetic_ids:self.assertIn(ident,korean)
            if synthetic:self.assertIn('SYNTHETIC',korean)
        for text in ('Provider narrative 15bp unchanged', 'Unknown: '+fixture().note, 'note: '+fixture().regime.summary):
            self.assertEqual(text,sheet_note_korean(text));self.assertEqual(text,summary_korean(text))

    def test_unknown_or_historical_narratives_and_optional_extensions_remain_raw(self):
        out=output('weekly')
        for narrative in ('Provider text: Buy 12 at 2.5%', out.narrative+' Historical observation.', out.narrative.replace('Weekly','Historic',1)):
            self.assertIsNone(macro_korean(replace(out,narrative=narrative)))
        self.assertIsNone(macro_korean(replace(out,request=replace(out.request,tool='unknown'))))
        altered=replace(out.sheet,regime=replace(out.sheet.regime,summary='Provider says 15bp; do not translate.'))
        out=execute_macro(out.request,sheet_loader=lambda **_:altered)
        self.assertIn(altered.regime.summary,macro_korean(out))

    def test_missing_rows_and_empty_sheet_preserve_na_and_numbers(self):
        base=fixture(synthetic=False)
        for rows in ((),tuple(x for x in base.rows if x.id not in ('DGS10','T10Y2Y','DTWEXBGS'))):
            sheet=replace(base,rows=rows)
            for tool in ('sheet','daily','weekly'):
                out=execute_macro(MacroRequest(tool=tool,source='synthetic'),sheet_loader=lambda **_:sheet)
                korean=macro_korean(out)
                self.assertEqual(numbers(out.narrative),numbers(korean))
                self.assertEqual(out.narrative.count('n/a'),korean.count('n/a'))

    def test_language_switch_translates_captions_but_preserves_jobs_report_and_cells(self):
        # Exercise the shipped registration, with no injected catalogue entries.
        with self.subTest(catalogue='production'):
            window=ResearchWindow(auto_refresh=False,language='ko')
            self.addCleanup(window.deleteLater)
            pane=window.macro
            out=output('weekly',short=True)
            pane.show_result(out);pane.bind_output('macro',out);self.app.processEvents()
            report=deepcopy(pane.report);sections=deepcopy(pane.sections)
            narrative=next(w for w in pane.findChildren(UiLabel) if w.source_text==out.narrative)
            as_of=next(w for w in pane.findChildren(UiLabel) if w.source_text.startswith('As of '))
            numeric_table=pane.tables['Macro indicators']
            cells=[[numeric_table.item(r,c).text() for c in range(2,numeric_table.columnCount())] for r in range(numeric_table.rowCount())]
            before_request=pane.make_request();chart_rows=deepcopy(pane.charts['1y z-scores · descriptive only'].rows)
            with patch.object(window.jobs,'start',side_effect=AssertionError('job started')) as start:
                for language in ('ko','en','ko','en'):
                    window.set_language(language);self.app.processEvents()
                    self.assertEqual(narrative.text(),macro_korean(out) if language=='ko' else out.narrative)
                    self.assertTrue(as_of.text().startswith('기준일 ' if language=='ko' else 'As of '))
                    self.assertEqual(numbers(as_of.text()),numbers(as_of.source_text))
                    self.assertEqual(pane.tables['Descriptive read'].item(0,0).text(),PAIRS[out.sheet.regime.curve] if language=='ko' else out.sheet.regime.curve)
                    self.assertEqual(numeric_table.item(0,0).text(),PAIRS['rates'] if language=='ko' else 'rates')
                    self.assertEqual(numeric_table.item(4,1).text(), '10년 실질금리 (TIPS)' if language == 'ko' else '10y real (TIPS)')
                    self.assertEqual(numeric_table.item(17,1).text(), '금' if language == 'ko' else 'Gold')
                    chart = pane.charts['1y z-scores · descriptive only']
                    self.assertEqual(chart.display_label(17), '금 · SYNTHETIC' if language == 'ko' else 'Gold · SYNTHETIC')
                    self.assertEqual(cells,[[numeric_table.item(r,c).text() for c in range(2,numeric_table.columnCount())] for r in range(numeric_table.rowCount())])
                    self.assertEqual(chart_rows,pane.charts['1y z-scores · descriptive only'].rows)
                    self.assertEqual(report,pane.report);self.assertEqual(sections,pane.sections)
                    self.assertEqual(before_request,pane.make_request())
                start.assert_not_called()
            self.assertTrue(any(s.get('text')==out.narrative for s in pane.report['sections']))

    def test_indicator_captions_require_matching_registered_id_even_when_names_collide(self):
        sheet = fixture(synthetic=False)
        unknown = replace(sheet.rows[-1], id='PROVIDER_GOLD', source='PROVIDER', z_1y=100.)
        rows = (replace(sheet.rows[0], label='Provider Treasury'), *sheet.rows[1:], unknown)
        sheet = replace(sheet, rows=rows)
        out = execute_macro(MacroRequest(source='synthetic'), sheet_loader=lambda **_: sheet)
        self.assertEqual(indicator_caption(unknown), 'Gold')
        self.assertEqual(indicator_caption(rows[0]), 'Provider Treasury')
        self.assertIn('Gold:', macro_korean(out))
        window = ResearchWindow(auto_refresh=False, language='ko')
        self.addCleanup(window.deleteLater)
        pane = window.macro;pane.show_result(out);pane.bind_output('macro fixture', out)
        report = deepcopy(pane.report); chart = pane.charts['1y z-scores · descriptive only']
        for language in ('ko', 'en', 'ko'):
            window.set_language(language)
            table = pane.tables['Macro indicators']
            self.assertEqual(table.item(0, 1).text(), 'Provider Treasury')
            self.assertEqual(table.item(18, 1).text(), 'Gold')
            self.assertEqual(table.item(18, 9).text(), 'PROVIDER')
            self.assertEqual(chart.display_label(18), 'Gold')
            self.assertEqual(chart.display_label(17), '금' if language == 'ko' else 'Gold')
            self.assertEqual(pane.report, report)
        pane.clear_result()

    def test_signals_bar_names_switch_without_changing_scores_or_unknown_names(self):
        from tests.desktop_acceptance import signals_fixture
        from core.research.signals_analysis import SignalsRequest
        from quantgen_desktop.charts import SignedBars
        out = signals_fixture(SignalsRequest(source='synthetic'))
        window = ResearchWindow(auto_refresh=False, language='ko')
        self.addCleanup(window.deleteLater)
        pane = window.signals;pane.show_result(out);pane.bind_output('signals fixture',out)
        chart = pane.charts['Component scores · -100…100']; original = deepcopy(chart.rows)
        report = deepcopy(pane.report); request = pane.make_request()
        # A provider/user caption identical to a catalog word is raw unless its
        # originating pane explicitly tags that individual row as authored.
        unknown = SignedBars([('Gold', 2.5), ('Provider Treasury', -1.25)], parent=window)
        with patch.object(window.jobs, 'start', side_effect=AssertionError('recompute forbidden')):
            for language in ('ko', 'en', 'ko'):
                window.set_language(language)
                self.assertEqual(chart.display_label(0), '가격과 50일 이동평균' if language == 'ko' else 'Price vs 50-day SMA')
                self.assertEqual(chart.rows, original)
                self.assertEqual(pane.report, report);self.assertEqual(pane.make_request(), request)
                self.assertEqual([unknown.display_label(i) for i in range(2)], ['Gold', 'Provider Treasury'])
        pane.clear_result()

    def test_failed_paper_stop_close_status_uses_selected_language(self):
        window = ResearchWindow(auto_refresh=False, language='en')
        self.addCleanup(window.deleteLater)
        with patch.object(window.paper_session, 'stop', return_value=False):
            for language in ('en', 'ko', 'en'):
                window.set_language(language)
                event = QCloseEvent();window.closeEvent(event)
                self.assertFalse(event.isAccepted())
                expected = ('Wait for the paper engine\'s current lookup, then close again.' if language == 'en' else
                            '모의 엔진의 진행 중인 조회가 끝나면 다시 종료해 주세요.')
                self.assertEqual(window.statusBar().currentMessage(), expected)


if __name__=='__main__':unittest.main()
