"""Native Strategy Lab, owner UI review 2026-11-10 (issues 01, 04/12, 06, 07, 09, 10, 11, 14).

What the owner sees: a run leads with a plain verdict (good or bad, why, what next), four headline tiles
and a readable checklist; study cards show by name with a verdict summary; there is no data-source
selector and the request asks for the automatic source; one language per window, switched without a
rerun; the export is exactly what it was. Synthetic inputs only: no network, no ledger, no Yahoo.
"""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from datetime import date, timedelta
from functools import lru_cache
import json
from pathlib import Path
import re
import unittest
from unittest.mock import Mock, patch

import dotenv
import numpy as np

with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.quant.history import History
    from core.research import strategy_display as D
    from core.research import strategy_workflow as flow
    from core.research.strategy_analysis import StrategyOutput, StrategyRequest, execute_strategy
    from core.research.strategy_exposure import exposure_lines
    from core.theme import DARK, LIGHT
    from quantgen_desktop.app import ResearchWindow
    from quantgen_desktop.model_narrative_language import strategy_variants
    from quantgen_desktop.strategy_view import CODE_ROLE, MetricTile, ToneScope, VerdictBanner
    from quantgen_desktop.tools import fmt
from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import QAbstractButton, QApplication, QComboBox, QLabel, QMessageBox, QTableWidget
from tests.qt_fixture_cleanup import delete_owned_widget

ROOT = Path(__file__).resolve().parents[1]
CARD_FILES = sorted((ROOT / 'docs' / 'asset_expansion' / 'cards').glob('*.json'))
HANGUL = re.compile(r'[가-힣]')
RAW_FIELD = re.compile(r'\b(?:kupiec\d+_p|cc_p|bootstrap_p|theo_gap_pts|sr_oos|return_p_bonferroni)\b')


@lru_cache
def run_fixture(family='trend_switch', cost=None):
    symbols = ('SPY', 'QQQ', 'TLT')
    rng = np.random.default_rng(1107)
    prices = 100 * np.exp(np.vstack([np.zeros(3), np.cumsum(rng.normal(.0004, .01, (1499, 3)), axis=0)]))
    dates = tuple((date(2020, 1, 1) + timedelta(days=i)).isoformat() for i in range(len(prices)))

    def loader(symbol, **kw):
        return History(symbol, 'SYNTHETIC', dates, tuple(prices[:, symbols.index(symbol)]), note='synthetic fixture')
    chosen = symbols[:2] if family == 'pairs' else symbols         # a pair is y then x
    return flow.run_family(family, list(chosen), history_loader=loader, source='synthetic', cost_bps=cost,
                           bootstrap_B=40)


def legacy_run_sections(d):
    """The export sections the pane wrote before the display rewrite (base commit 66470f4), verbatim."""
    sc, wf = d['score'], d['wf']
    safe = flow.payload(d)
    out = [f"{d['label']} · {', '.join(d['symbols'])}\n"
           f"sources={', '.join(d['sources'])} · {len(d['panel'])} shared sessions · {d['cost_bps']:g} bp/side"]
    if 'SYNTHETIC' in d['sources']:
        out.append('SYNTHETIC · 아래 점수는 합성 시연입니다. 공식 연구카드 판정이 아닙니다.')
    out += exposure_lines(d.get('exposure'))
    out.append(f"Decision: {safe['decision']} · {safe['reason']}")
    out.append(f"Grid/DSR trials {len(d['grid'])}/{sc.n_trials} · cumulative ledger configurations {d['ledger_n']}\n"
               f"Walk-forward: {wf.note} · last in-sample winner: {d['chosen']}")
    if d.get('convention'):
        out.append(d['convention'])
    sections = [{'type': 'text', 'text': t} for t in out]
    sections.append({'type': 'table', 'name': 'Validation statistics', 'headers': ['Metric', 'Value'], 'rows': [
        ('OOS Sharpe', fmt(sc.sr_oos)), ('90% interval', str(sc.ci90)), ('Deflated Sharpe', fmt(sc.dsr)),
        ('PBO', fmt(sc.pbo)), ('OOS / IS', fmt(sc.oos_is)), ('2× cost Sharpe', fmt(sc.sr_stress)),
        ('Positive years', fmt(sc.years_positive, 'pct')), ('Plateau', fmt(sc.plateau, 'pct')),
        ('Plateau edge', str(sc.edge)), ('Trades', sc.n_trades), ('Max drawdown', fmt(sc.max_drawdown, 'pct')),
        ('Benchmark Sharpe', fmt(sc.bench_sr)), ('Benchmark difference', fmt(sc.bench_diff)),
        ('Benchmark p', fmt(sc.bench_p)), ('Haircut Sharpe', fmt(sc.haircut_sr))]})
    series = [('Strategy', list(d['equity']))]
    if d['bench_equity'] is not None:
        series.append(('Benchmark', list(d['bench_equity'])))
    sections.append({'type': 'line', 'name': 'Walk-forward equity', 'x': list(range(len(d['equity']))),
                     'series': series, 'x_label': 'OOS observations', 'y_label': 'Equity'})
    sections.append({'type': 'text', 'text': ' · '.join(d['notes'])})
    sections.append({'type': 'text', 'text': flow.narrative(d)})
    return sections


def study_cards():
    return [flow._study_card(json.loads(p.read_text(encoding='utf-8'))) for p in CARD_FILES]


def shown(root):
    """Every text a reader can see under `root` (closed folds excluded), in display order."""
    window = root.window()
    out = []
    for widget in root.findChildren(QLabel):
        if widget.isVisibleTo(window) and widget.text():
            out.append(widget.text())
    for widget in root.findChildren(QAbstractButton):
        if widget.isVisibleTo(window) and widget.text():
            out.append(widget.text())
    for table in root.findChildren(QTableWidget):
        if table.isVisibleTo(window):
            out += [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]
            out += [table.item(r, c).text() for r in range(table.rowCount()) for c in range(table.columnCount())]
    for combo in root.findChildren(QComboBox):
        if combo.isVisibleTo(window):
            out += [combo.itemText(i) for i in range(combo.count())]
    return out


class OwnerStrategyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ('requests.sessions.Session.request', 'core.quant.gate_ledger.family_ledger',
                       'core.quant.validate.load_cards', 'core.ficc.data._yf_fetch'):
            p = patch(target, side_effect=AssertionError('live I/O forbidden'))
            p.start()
            self.addCleanup(p.stop)
        self.window = ResearchWindow(auto_refresh=False, language='ko')
        self.pane = self.window.strategy

    def tearDown(self):
        self.pane.clear_result()
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
            self.window.close()
        delete_owned_widget(self.window)
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def settle(self):
        for _ in range(4):
            self.app.processEvents()

    def show_run(self, d, request=None):
        out = StrategyOutput(request or StrategyRequest(), d)
        self.pane.show_result(out)
        self.pane.bind_output('Strategy Lab', out)
        self.settle()
        return out

    def test_source_selector_is_hidden_and_the_run_asks_for_the_automatic_source(self):
        pane = self.pane
        self.assertTrue(pane.source.isHidden())
        self.assertTrue(pane.source_label.isHidden())
        self.assertEqual(pane.source.currentData(), 'best')
        self.assertTrue({'best', 'auto', 'synthetic'} <= {pane.source.itemData(i) for i in range(pane.source.count())})
        pane.fields['run']['symbols'].setText('SPY, QQQ')
        request = pane.make_request()
        request.validate()
        self.assertEqual(request.source, 'best')
        runner = Mock(return_value=run_fixture())
        execute_strategy(request, runner=runner)
        self.assertEqual(runner.call_args.kwargs['source'], 'best')
        # run_family hands the automatic source to load_history unchanged
        with patch.object(flow, 'load_history', side_effect=RuntimeError('stop after the first fetch')) as load:
            with self.assertRaises(RuntimeError):
                flow.run_family('trend_switch', ['SPY'], source='best')
        self.assertEqual(load.call_args.kwargs['source'], 'best')
        # the window says neither "출처를 선택" nor "auto" anywhere in the form
        form = '\n'.join(shown(pane.input_box))
        self.assertNotIn('데이터 출처', form)
        self.assertNotIn('auto', form)
        self.assertNotIn('출처를 선택', pane.status.text())

    def test_run_leads_with_a_plain_verdict_and_readable_checks_in_korean(self):
        d = run_fixture()
        self.show_run(d)
        verdict = D.run_verdict(d)
        banner = self.pane.findChild(VerdictBanner)
        self.assertIsNotNone(banner)
        view = self.pane.findChild(ToneScope)
        self.assertIs(view.column.itemAt(0).widget(), banner, 'the verdict comes first')
        self.assertEqual(banner.title.text(), verdict['title'][0])
        self.assertTrue(banner.title.text().startswith('연습용 판정(합성 데이터) · '))
        self.assertIn(d['score'].decision, banner.pill.text(), 'the verdict code stays visible')
        self.assertTrue(HANGUL.search(banner.pill.text()))
        tiles = self.pane.findChildren(MetricTile)
        self.assertEqual([t.findChildren(QLabel)[0].text() for t in tiles],
                         ['표본 외 샤프 지수', '보정 샤프(DSR)', '벤치마크 대비 샤프 차이', '최대 낙폭'])
        self.assertTrue(all(t.toolTip() for t in tiles), 'each tile explains itself')
        checks = self.pane.tables['Result per criterion']
        self.assertEqual([checks.horizontalHeaderItem(c).text() for c in range(5)],
                         ['검증 항목', '결과', '기준', '판정', '뜻'])
        self.assertEqual(checks.rowCount(), len(verdict['checks']))
        cells = [checks.item(r, c).text() for r in range(checks.rowCount()) for c in range(5)]
        self.assertIn('~', cells[1], 'the interval reads "-0.10 ~ 1.77"')
        self.assertEqual({checks.item(r, 3).data(CODE_ROLE) for r in range(checks.rowCount())} - {'pass', 'fail', 'info', 'na'}, set())
        text = '\n'.join(shown(self.pane))
        for raw in (str(d['score'].ci90), 'True', 'False', 'Validation statistics', 'Walk-forward equity',
                    'Symbols · pairs는', 'Decision:', 'Grid/DSR'):
            self.assertNotIn(raw, text)
        self.assertEqual(self.pane.narrative_view.headings('ko'), ['결론', '데이터와 설정', '위험과 참고'])
        self.assertTrue(all(HANGUL.search(line) for line in self.pane.narrative_view.lines('ko')))

    def test_english_window_is_english_and_switching_never_reruns_or_changes_the_report(self):
        d = run_fixture()
        self.show_run(d)
        report = deepcopy(self.pane.report)
        with patch.object(self.window.jobs, 'start', side_effect=AssertionError('no rerun')):
            self.window.set_language('en')
            self.settle()
            banner = self.pane.findChild(VerdictBanner)
            self.assertEqual(banner.title.text(), D.run_verdict(d)['title'][1])
            visible = [t for t in shown(self.pane) if HANGUL.search(t)]
            self.assertEqual(visible, [], 'no Korean in the English window')
            self.assertEqual(self.pane.narrative_view.headings(), ['Conclusion', 'Data and setup', 'Risks and notes'])
            self.window.set_language('ko')
            self.settle()
            self.assertEqual(banner.title.text(), D.run_verdict(d)['title'][0])
        self.assertEqual(self.pane.report, report)

    def test_export_sections_are_exactly_the_previous_ones(self):
        for d in (run_fixture(), run_fixture(cost=1), run_fixture('vol_target'), run_fixture('pairs')):
            with self.subTest(family=d['family'], withheld=bool(d.get('withheld'))):
                self.show_run(d)
                self.assertEqual(self.pane.sections, legacy_run_sections(d))
                self.assertIn('Walk-forward equity', self.pane.charts)
                self.assertEqual(self.pane.report['verdict'], 'NOT_RUN')

    def test_withheld_run_shows_no_verdict(self):
        d = run_fixture(cost=1)
        self.show_run(d)
        banner = self.pane.findChild(VerdictBanner)
        self.assertIn('NO VERDICT', banner.pill.text())
        self.assertIn('판정 없음', banner.title.text())
        self.assertIn('WITHHELD', str(self.pane.sections))
        # the folded full paragraph keeps the reviewed Korean variant of the recorded narrative
        self.assertIn(strategy_variants(d)['ko'], [w.text() for w in self.pane.findChildren(QLabel)])

    def test_cards_read_by_name_with_a_verdict_summary_in_both_languages(self):
        cards = study_cards()
        self.assertTrue(cards, 'the study cards are part of the repository')
        self.pane.tool.setCurrentIndex(self.pane.tool.findData('cards'))
        out = StrategyOutput(StrategyRequest(tool='cards'), {'cards': cards})
        self.pane.show_result(out)
        self.pane.bind_output('Strategy Lab', out)
        self.settle()
        table = self.pane.tables['Study scorecard']
        self.assertEqual(table.rowCount(), len(cards))
        ids = {c['card_id'] for c in cards}
        names = [table.item(r, 0).text() for r in range(table.rowCount())]
        self.assertFalse(ids & set(names), 'no raw card id as a name')
        self.assertTrue(all(table.item(r, 0).toolTip().startswith(cards[r]['card_id']) for r in range(len(cards))))
        self.assertTrue(all(HANGUL.search(n) for n in names))
        for r, c in enumerate(cards):
            self.assertIn(c['decision'], table.item(r, 2).text(), 'the verdict code stays visible')
            self.assertEqual(table.item(r, 2).data(CODE_ROLE), c['decision'])
        text = '\n'.join(shown(self.pane))
        self.assertIsNone(RAW_FIELD.search(text), RAW_FIELD.search(text))
        self.assertNotIn('Sources:', text)
        funding = next(i for i, c in enumerate(cards) if c['card_id'] == 'M_C4_funding')
        picker = next(c for c in self.pane.findChildren(QComboBox) if c.count() == len(cards))
        self.assertEqual(picker.itemText(funding), 'BTC 무기한선물 펀딩비 신호 — 통과 · PASS')
        table.cellClicked.emit(funding, 0)
        self.settle()
        self.assertEqual(picker.currentData(), 'M_C4_funding')
        detail = [w.text() for w in self.pane.findChild(ToneScope).detail.findChildren(QLabel)]
        self.assertIn('BTC 무기한선물 펀딩비 신호', detail)
        self.assertIn('M_C4_funding · 모형', detail, 'the id is a secondary line of the detail')
        report = deepcopy(self.pane.report)
        with patch.object(self.window.jobs, 'start', side_effect=AssertionError('no rerun')):
            self.window.set_language('en')
            self.settle()
            self.assertEqual(picker.itemText(funding), 'BTC perpetual funding signal — PASS')
            self.assertEqual(table.item(funding, 0).text(), 'BTC perpetual funding signal')
            self.assertEqual([t for t in shown(self.pane) if HANGUL.search(t)], [])
        self.assertEqual(self.pane.report, report)
        self.assertEqual(self.pane.sections[0]['rows'][0][0], cards[0]['card_id'], 'the export keeps raw ids')

    def test_verdict_colours_follow_the_theme(self):
        self.show_run(run_fixture())
        checks = self.pane.tables['Result per criterion']
        failed = next(r for r in range(checks.rowCount()) if checks.item(r, 3).data(CODE_ROLE) == 'fail')
        self.assertEqual(checks.item(failed, 3).foreground().color().name().lower(), LIGHT.error.lower())
        self.window.change_theme(1)
        for _ in range(8):
            self.app.processEvents()
        self.assertEqual(checks.item(failed, 3).foreground().color().name().lower(), DARK.error.lower())
        self.assertIn(DARK.error, self.pane.findChild(ToneScope).styleSheet())
        self.window.change_theme(0)
        self.settle()


if __name__ == '__main__':
    unittest.main()
