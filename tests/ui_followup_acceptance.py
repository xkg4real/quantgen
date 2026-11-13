"""Owner D11-D15: US session boundaries, bounded ranks, frozen exports and score lifecycle; offline."""
from dataclasses import replace
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

from core.market.models import Instrument, ChartRequest, MarketSnapshot
from core.research.qscore import compute_q_score
from tests.qscore_acceptance import snapshot, fixture, NOW
from core.market import rankings as R
from core.market.qscore_rankings import ScoreCache, CANDIDATES


class ScoreV2Tests(unittest.TestCase):
    def test_domestic_v01_numerical_results_are_preserved(self):
        for trend, expected in ((.001, 71.57), (-.001, 50.34), (.0001, 63.59)):
            result = compute_q_score(fixture(trend=trend), now=NOW)
            self.assertEqual(result['score'], expected)
            self.assertEqual(result['methodology'], 'Q-SCORE v0.2')

    def test_us_uses_new_york_session_not_korean_next_day(self):
        base = snapshot()
        us = replace(base, request=replace(base.request, instrument=Instrument('overseas_stock', 'AAPL', 'NAS')))
        # Nov 2, 19:30 New York is Nov 3 in Korea. Only one Nov 2 provisional daily observation is added.
        now = datetime(2026, 11, 3, 0, 30, tzinfo=timezone.utc)
        result = compute_q_score(us, latest_price=base.candles[-1].close, as_of=now, now=now)
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['history_end'], '2026-11-02')
        self.assertEqual(result['session_timezone'], 'America/New_York')
        self.assertEqual(result['source'], 'KIS REST')
        self.assertEqual(compute_q_score(replace(us, request=replace(us.request, adjusted=False)), now=now)['reason'],
                         'adjusted_history_required')
        other = replace(us, request=replace(us.request, instrument=Instrument('overseas_stock', '700', 'HKS')))
        self.assertEqual(compute_q_score(other, now=now)['reason'], 'unsupported_instrument')

    def test_cache_bounds_calls_and_cancels_between_instruments(self):
        calls = []
        def load(request):
            calls.append(request)
            return replace(snapshot(), request=request)
        records = [R.QuoteRecord(m, 100, 1, 1, 10, i + 1, None, 'KIS', 'kis', NOW.isoformat())
                   for i, m in enumerate(R.DOMESTIC)]
        cache = ScoreCache(load)
        results = cache.run(records, now=NOW)
        self.assertEqual(len(calls), min(len(records), CANDIDATES))
        self.assertTrue(all(r.adjusted and r.interval == '1d' for r in calls))
        self.assertTrue(all(v['status'] == 'ready' for v in results.values()))
        cache.run(records, now=NOW + timedelta(seconds=400))
        self.assertEqual(len(calls), CANDIDATES)
        stopped = ScoreCache(load)
        count = len(calls)
        stopped.run(records, cancelled=lambda: len(calls) > count, now=NOW)
        self.assertEqual(len(calls), count + 1)

    def test_ranking_retains_missing_and_zero_with_missing_last(self):
        records = [R.QuoteRecord(m, 100, 1, 1, 10, 10, None, 'KIS', 'kis', NOW.isoformat(), q_score=score)
                   for m, score in zip(R.DOMESTIC, (None, 0, 80, 50))]
        rows = R.rank(records, 'qscore', missing='last')
        self.assertEqual([r.value for r in rows], [80, 50, 0, None])
        self.assertEqual(rows[-1].rank, 0)
        self.assertEqual(len(R.rank([replace(r, q_score=None) for r in records], 'qscore', missing='last')), 4)
        from core.market.screen import category_note
        with patch('core.market.qscore_rankings.ENABLED', False):
            self.assertTrue(category_note('kr', 'qscore'))
        self.assertFalse(category_note('us', 'qscore'))
        self.assertTrue(category_note('etf_us', 'qscore'))


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests import desktop_stock_detail_acceptance as detail
        cls.case = detail.StockDetailTests('test_arrows_pan_through_end_and_ctrl_wheel_zooms')
        cls.case.setUp()
        cls.addClassCleanup(cls.case.doCleanups)
        cls.case.open()
        cls.case.wait(lambda: not cls.case.view.score.jobs.busy)
        from quantgen_desktop.stock_report import capture
        cls.report, cls.image = capture(cls.case.view, include_all=True)

    def test_formats_share_score_readings_and_embedded_chart(self):
        from quantgen_desktop.stock_report import write_report
        from core.market.stock_report import report_dict
        with tempfile.TemporaryDirectory() as folder:
            for ext in ('pdf', 'png', 'json', 'csv'):
                path = Path(folder) / ('report.' + ext)
                write_report(path, self.report, self.image)
                self.assertGreater(path.stat().st_size, 500)
            data = json.loads((Path(folder) / 'report.json').read_text(encoding='utf-8'))
            self.assertEqual(data, report_dict(self.report))
            self.assertIn('Q-SCORE', (Path(folder) / 'report.csv').read_text(encoding='utf-8-sig'))
            self.assertTrue((Path(folder) / 'report.pdf').read_bytes().startswith(b'%PDF'))
            import shutil, subprocess
            if shutil.which('pdftotext'):
                copied = subprocess.check_output(['pdftotext', '-enc', 'UTF-8', str(Path(folder) / 'report.pdf'), '-']).decode('utf-8')
                self.assertIn('005930', copied)
                self.assertIn('-0.34%', copied)
                self.assertIn('삼성전자', copied)
            self.assertEqual(data['provenance']['network'], 'none')
            self.assertEqual(data['q_score']['methodology'], 'Q-SCORE v0.2')

    def test_cancel_writes_nothing_and_capture_is_frozen(self):
        from quantgen_desktop.stock_report import export_dialog
        from core.market.stock_report import report_json
        original = report_json(self.report)
        with patch('quantgen_desktop.stock_report.capture', return_value=(self.report, self.image)), \
                patch('quantgen_desktop.stock_report.QFileDialog.getSaveFileName', return_value=('', '')), \
                patch('quantgen_desktop.stock_report.write_report') as writer:
            self.assertFalse(export_dialog(self.case.view))
            writer.assert_not_called()
        self.case.view.side.card.price.setText('CHANGED')
        self.assertEqual(report_json(self.report), original)

    def test_format_choice_changes_suffix_but_does_not_overwrite_unconfirmed_file(self):
        from quantgen_desktop.stock_report import export_dialog, text
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'report.json'
            target.write_text('keep')
            with patch('quantgen_desktop.stock_report.capture', return_value=(self.report, self.image)), \
                    patch('quantgen_desktop.stock_report.QFileDialog.getSaveFileName',
                          return_value=(str(Path(folder) / 'report.pdf'), text('ko', 'filter_json'))), \
                    patch('quantgen_desktop.stock_report.QMessageBox.question', return_value=0), \
                    patch('quantgen_desktop.stock_report.write_report') as writer:
                self.assertFalse(export_dialog(self.case.view))
                writer.assert_not_called()
                self.assertEqual(target.read_text(), 'keep')

    def test_qscore_criterion_displays_sorted_scores_and_retains_unknown_rows(self):
        board = self.case.window.markets_view.rankings
        board.clock = lambda: NOW
        entries = []
        for member, points in zip(R.DOMESTIC[:3], (50, None, 80)):
            record = R.QuoteRecord(member, 100, 1, 1, 10, 10, None, 'KIS', 'kis', NOW.isoformat())
            entries.append(record)
            if points is not None:
                key = (member.instrument.asset, member.exchange, member.code)
                result = {'status': 'ready', 'score': points, 'stars': 1 + int(points // 20), 'as_of': '2026-10-30'}
                board.scores.cache.entries[key] = NOW.astimezone(__import__('zoneinfo').ZoneInfo('Asia/Seoul')).date(), NOW, result
                board.scores.results[key] = result
        board.batches['kr'] = R.Batch('kr', tuple(entries), 'kis', NOW.isoformat())
        board.set_category('qscore')
        self.assertEqual([r.value for r in board.ranked], [80, 50, None])
        self.assertIn('80', board.rows[0].figures['qscore'].text())
        self.assertEqual(board.rows[2].figures['qscore'].text(), '—')
        self.assertTrue(board.rows[2].figures['qscore'].toolTip())
        self.assertIn('20', board.footnote.text())

    def test_score_controller_accepts_us_and_drops_wrong_stock_history(self):
        from quantgen_desktop.stock_qscore import StockScore
        score = StockScore(now=lambda: NOW)
        apple = Instrument('overseas_stock', 'AAPL', 'NAS')
        score.open(apple)
        self.assertEqual(score.state, 'waiting')
        self.assertFalse(score.set_history(snapshot()))
        us = replace(snapshot(), request=replace(snapshot().request, instrument=apple))
        self.assertTrue(score.set_history(us))
        self.case.wait(lambda: not score.jobs.busy)
        self.assertEqual(score.result['status'], 'ready')
        score.stop()


if __name__ == '__main__':
    unittest.main()
