"""N11 descriptive statistics: synthetic prices only, no provider/store access."""
from copy import deepcopy
from dataclasses import replace
from datetime import date, timedelta
import json
import unittest
from unittest.mock import Mock, patch
import numpy as np
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.quant import backtest as B
    from core.quant.history import History
    from core.quant.insights import narrate_backtest
    from core.research.signals_analysis import SignalsRequest, execute_signals, trade_statistics


def history(values):
    return History('SYNTHETIC-N11', 'SYNTHETIC',
                   tuple((date(2026, 1, 1)+timedelta(days=i)).isoformat() for i in range(len(values))),
                   tuple(values), note='Injected synthetic statistics fixture')


def run(values, cost=10):
    return B.run_backtest(history(values), strategy='momentum', params={'lookback': 1}, cost_bps=cost)


class TradeStatisticsTests(unittest.TestCase):
    def setUp(self):
        for target in ('socket.socket.connect', 'requests.sessions.Session.request'):
            p=patch(target, side_effect=AssertionError('network forbidden'));p.start();self.addCleanup(p.stop)

    def test_final_only_entry_is_pending_and_never_charged(self):
        b=run([100.]*59+[101.])
        self.assertEqual((b.n_trades,b.completed_round_trips,b.pending_last_signal),(0,0,'entry'))
        self.assertIsNone(b.win_rate);self.assertEqual(b.exposure,0.)
        np.testing.assert_array_equal(b.equity,np.ones(60))
        self.assertIn('0 executed entry/exit sides',narrate_backtest(b))

    def test_final_exit_does_not_close_or_win_a_roundtrip(self):
        b=run([100.]*56+[101.,102.,103.,102.])
        self.assertEqual((b.n_trades,b.completed_round_trips,b.pending_last_signal),(1,0,'exit'))
        self.assertIsNone(b.win_rate)
        # One entry charge only. Last return belongs to the still-held position.
        expected=(102/101-.001)*(103/102)*(102/103)
        self.assertAlmostEqual(b.equity[-1],expected,places=14)

    def test_completed_roundtrip_has_two_sides_not_two_roundtrips(self):
        b=run([100.]*54+[101.,102.,103.,102.,101.,101.])
        self.assertEqual((b.n_trades,b.completed_round_trips,b.pending_last_signal),(2,1,'none'))
        self.assertEqual(b.win_rate,1.)
        expected=(102/101-.001)*(103/102)*(102/103)*(.999)
        self.assertAlmostEqual(b.equity[-1],expected,places=14)

    def test_no_trade_and_open_position_are_not_forcibly_liquidated(self):
        flat=run([100.]*60)
        self.assertEqual((flat.n_trades,flat.completed_round_trips,flat.pending_last_signal),(0,0,'none'))
        self.assertIsNone(flat.win_rate)
        opened=run([100.]*57+[101.,102.,103.])
        self.assertEqual((opened.n_trades,opened.completed_round_trips,opened.pending_last_signal),(1,0,'none'))
        self.assertIsNone(opened.win_rate)
        self.assertAlmostEqual(opened.equity[-1],(102/101-.001)*(103/102),places=14)

    def test_initial_position_and_pending_terminal_exit(self):
        # Exercise initial position semantics independently of any built-in signal.
        pos=np.r_[np.ones(5),np.zeros(55)]
        with patch.object(B,'_positions',return_value=pos):b=run(np.linspace(100,110,60))
        self.assertEqual((b.n_trades,b.completed_round_trips,b.win_rate),(2,1,1.))
        pos=np.r_[np.ones(59),0.]
        with patch.object(B,'_positions',return_value=pos):b=run(np.linspace(100,110,60))
        self.assertEqual((b.n_trades,b.completed_round_trips,b.pending_last_signal),(1,0,'exit'))
        self.assertIsNone(b.win_rate)

    def test_gross_win_is_explicit_even_when_costed_equity_loses(self):
        b=run([100.]*54+[100.01,100.02,100.03,100.02,100.01,100.01],cost=20)
        self.assertEqual(b.completed_round_trips,1);self.assertEqual(b.win_rate,1.)
        self.assertLess(b.total_return,0.)
        text=narrate_backtest(b)
        self.assertIn('Gross-price win rate',text);self.assertIn('before costs',text)
        meta=trade_statistics(b)
        self.assertEqual(meta['n_trades_basis'],'executed_entry_exit_sides')
        self.assertEqual(meta['win_rate_basis'],'gross_price_return_before_costs')
        self.assertFalse(meta['forced_terminal_liquidation'])
        legacy=B.BacktestResult('OLD','momentum',{},60,2,10)
        self.assertIsNone(legacy.completed_round_trips)
        self.assertEqual(trade_statistics(legacy)['n_trades_basis'],'legacy_unverified')


class TradePresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        for target in ('socket.socket.connect','requests.sessions.Session.request',
                       'core.quant.validate.load_cards','core.quant.gate_ledger.family_ledger'):
            p=patch(target,side_effect=AssertionError('live I/O forbidden'));p.start();self.addCleanup(p.stop)

    def test_native_languages_export_ai_and_numeric_state(self):
        from quantgen_desktop.app import ResearchWindow
        from quantgen_desktop.model_narrative_language import signals_variants
        from quantgen_desktop.commentary import commentary_payload
        from core.research.tool_export import report_bytes
        from tests.desktop_fx_language_acceptance import numbers
        q=SignalsRequest(tool='momentum',source='synthetic',fast=1)
        out=execute_signals(q,history_loader=lambda *a,**kw:history([100.]*59+[101.]))
        w=ResearchWindow(auto_refresh=False,language='en');self.addCleanup(w.deleteLater)
        pane=w.signals;pane.show_result(out);pane.bind_output('signals',out)
        before=deepcopy(pane.report);equity=out.backtest.equity.copy()
        english=signals_variants(out)['en'];korean=signals_variants(out)['ko']
        self.assertEqual(numbers(english),numbers(korean))
        self.assertIn('대기 상태',korean);self.assertIn('비용 차감 전',korean)
        for language,label,pending in [('ko','실행된 진입·청산 편도 횟수','진입 대기'),('en','Executed entry/exit sides','Entry pending')]:
            w.set_language(language)
            t=pane.tables['Backtest metrics']
            cells=[t.item(r,c).text() for r in range(t.rowCount()) for c in range(t.columnCount())]
            self.assertIn(label,cells);self.assertIn(pending,cells)
            self.assertEqual(pane.report,before);self.assertFalse(w.jobs.busy)
        np.testing.assert_array_equal(out.backtest.equity,equity)
        raw=json.loads(report_bytes(before));self.assertEqual(raw['verdict'],'NOT_RUN')
        ai=commentary_payload(before)
        for data in (raw,ai):
            text=json.dumps(data,ensure_ascii=False)
            self.assertIn('Executed entry/exit sides',text);self.assertIn('Completed round trips',text)
            self.assertIn('Entry pending',text);self.assertIn('Gross-price wins exclude costs',text)
            stats=next(s for s in data['sections'] if s['type']=='trade_statistics')
            self.assertEqual(stats['n_trades_basis'],'executed_entry_exit_sides')
            self.assertEqual(stats['completed_round_trips'],0)
            self.assertEqual(stats['pending_last_signal'],'entry')

    def test_legacy_and_unknown_versions_keep_unverified_display_basis(self):
        import flet as ft
        from core.quant.insights import narrate_signals
        from quantgen_desktop.app import ResearchWindow
        from quantgen_desktop.model_narrative_language import signals_variants
        from ui.signals_page import _trade_statistics_block
        from ui.localization import translate_controls
        from core.i18n import LocaleContext
        from tests.portfolio_scope_acceptance import controls
        from tests.desktop_fx_language_acceptance import numbers
        q=SignalsRequest(tool='momentum',source='synthetic',fast=1)
        out=execute_signals(q,history_loader=lambda *a,**kw:history([100.]*59+[101.]))
        w=ResearchWindow(auto_refresh=False,language='en');self.addCleanup(w.deleteLater)
        for version in ('legacy_unverified','future/99'):
            old=replace(out.backtest,n_trades=1,win_rate=.5,completed_round_trips=None,
                        pending_last_signal='NOT_RECORDED',statistics_version=version)
            narrative=narrate_signals(out.report)+' '+narrate_backtest(old)
            legacy=replace(out,backtest=old,narrative=narrative)
            self.assertIn('basis unverified',narrative)
            self.assertNotIn('1 executed entry/exit sides',narrative)
            variants=signals_variants(legacy)
            self.assertIn('미검증',variants['ko']);self.assertEqual(numbers(narrative),numbers(variants['ko']))
            w.signals.show_result(legacy);w.signals.bind_output('signals',legacy)
            saved=deepcopy(w.signals.report)
            block=_trade_statistics_block(old)
            for language,expected in [('ko','기록 거래 수 · 집계 기준 미검증'),('en','Recorded trade count · basis unverified')]:
                w.set_language(language)
                table=w.signals.tables['Backtest metrics']
                labels=[table.item(row,0).text() for row in range(table.rowCount())]
                self.assertIn(expected,labels)
                translate_controls(block,LocaleContext(language))
                self.assertIn(expected,[c.value for c in controls(block) if isinstance(c,ft.Text)])
                self.assertEqual(saved,w.signals.report)
            self.assertEqual(trade_statistics(old)['n_trades_basis'],'legacy_unverified')
            self.assertIsNone(trade_statistics(old)['completed_round_trips'])

    def test_flet_worker_localization_and_ai_payload(self):
        import flet as ft
        from ui import signals_page
        from ui.localization import translate_controls
        from core.i18n import LocaleContext
        from tests.portfolio_scope_acceptance import controls
        page=Mock();page.width=1200;page.qg_locale=LocaleContext('en_US');page.qg_theme='light'
        page.run_thread.side_effect=lambda fn:fn();seen={}
        def ai(_page,**kwargs):
            seen.update(kwargs);seen['payload']=kwargs['payload_fn']();return ft.Text('Injected AI, no request')
        with patch.object(signals_page,'load_history',return_value=history([100.]*59+[101.])),\
             patch.object(signals_page,'analysis_panel',side_effect=ai):
            root=signals_page.build_signals_page(page)
            all_controls=list(controls(root))
            strategy=next(c for c in all_controls if isinstance(c,ft.Dropdown) and c.label=='Backtest strategy')
            strategy.value='momentum'
            fast=next(c for c in all_controls if isinstance(c,ft.TextField) and c.label=='Fast/lookback')
            fast.value='1'
            next(c for c in all_controls if isinstance(c,ft.Button) and c.content=='Analyze').on_click(None)
        self.assertIn('payload',seen)
        payload=deepcopy(seen['payload'])
        self.assertEqual(payload['backtest']['n_trades'],0)
        self.assertEqual(payload['backtest']['completed_round_trips'],0)
        self.assertEqual(payload['backtest']['pending_last_signal'],'entry')
        self.assertEqual(payload['backtest']['win_rate_basis'],'gross_price_return_before_costs')
        for language,label,pending in [('ko_KR','실행된 진입·청산 편도 횟수','진입 대기'),('en_US','Executed entry/exit sides','Entry pending')]:
            translate_controls(root,LocaleContext(language))
            texts=[str(c.value) for c in controls(root) if isinstance(c,ft.Text)]
            self.assertIn(label,texts);self.assertIn(pending,texts)
            self.assertEqual(payload,seen['payload'])


if __name__=='__main__':unittest.main()
