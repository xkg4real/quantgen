"""Isolated real-model fixture, contract integrity, provider truthfulness and UI binding."""
import copy
from datetime import date, timedelta
import json
import math
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.quant.history import History
    from core.quant.montecarlo import run_monte_carlo
from core.research.runs import new_run, completed, failed, export_bytes, read_export, SessionResearch
from core.research.markets import load_markets


def result_fixture():
    dates = tuple((date(2026, 1, 1) + timedelta(days=i)).isoformat() for i in range(60))
    h = History('TEST', 'SYNTHETIC', dates, tuple(100 + i * .1 + math.sin(i) for i in range(60)), adjustment='split')
    mc = run_monte_carlo(h, model='gbm', seed=7, n_paths=200, horizon_days=5, drift='zero')
    run = new_run(dict(symbol='TEST', source_requested='synthetic', model='gbm', n_paths=200,
                       horizon_days=5, seed=7, drift='zero', target=None))
    return completed(run, h, mc, loaded_at='2026-10-29T09:00:00+00:00'), h, mc


class ResearchContractTests(unittest.TestCase):
    def test_real_model_roundtrip_preserves_evidence_not_investment_verdict(self):
        run, h, mc = result_fixture(); restored = read_export(export_bytes(run))
        self.assertEqual(restored, run); self.assertEqual(run['metrics']['p05'], mc.p05)
        self.assertTrue(run['data']['synthetic']); self.assertEqual(run['verdict'], 'NOT_RUN')
        self.assertEqual(run['cost']['status'], 'NOT_APPLIED')
        self.assertEqual(run['parameters']['seed'], 7)
        self.assertNotIn('closes', run['data']); self.assertIsNone(run['data']['provider_retrieved_at'])

    def test_fingerprint_tracks_input_values_and_adjustment(self):
        run, h, mc = result_fixture()
        from dataclasses import replace
        changed = completed(run, replace(h, adjustment='total'), mc, loaded_at=run['data']['loaded_at'])
        self.assertNotEqual(run['data']['fingerprint_sha256'], changed['data']['fingerprint_sha256'])

    def test_mutation_duplicate_order_payload_and_unknown_version_refused(self):
        run, _, _ = result_fixture(); raw = export_bytes(run); e = json.loads(raw)
        payload=json.loads(e['payload_json']); payload['metrics']['p50'] += 1; e['payload_json']=json.dumps(payload)
        with self.assertRaises(ValueError): read_export(json.dumps(e).encode())
        with self.assertRaises(ValueError): read_export(raw.replace(b'"order_capable":false', b'"order_capable":true'))
        with self.assertRaises(ValueError): read_export(raw.replace(b'"order_capable":false', b'"order_capable":false,"order_capable":false'))
        for change in ({'schema':'quantgen.research-run/2'}, {'verdict':'PASS'}, {'orders':[]}):
            r = copy.deepcopy(run); r.update(change)
            with self.assertRaises(ValueError): export_bytes(r)

    def test_failed_runs_are_counted_and_session_copies_are_isolated(self):
        a=SessionResearch(); b=SessionResearch(); r=new_run({'symbol':'TEST'})
        a.put(r); a.put(failed(r, 'HistoryError'))
        self.assertEqual(len(a.runs()), 1); self.assertEqual(b.runs(), [])
        rows=a.runs(); rows[0]['execution_status']='COMPLETED'
        self.assertEqual(a.runs()[0]['execution_status'], 'FAILED')

    def test_market_no_synthetic_fallback_staleness_units_and_partial_failure(self):
        def loader(symbol, source, days):
            if symbol == '^GSPC': raise RuntimeError('provider unavailable with private details')
            if symbol == 'BTC-USD': return SimpleNamespace(source='SYNTHETIC', dates=(), values=())
            return SimpleNamespace(source=source.upper(), dates=('2026-10-18','2026-10-19'), values=(4.,4.1))
        rows=load_markets(loader=loader, today=date(2026,10,29))
        self.assertEqual(rows[0]['status'], 'UNAVAILABLE'); self.assertIsNone(rows[0]['value'])
        self.assertEqual(rows[-1]['status'], 'UNAVAILABLE')
        self.assertEqual(rows[3]['status'], 'STALE'); self.assertAlmostEqual(rows[3]['change'],10.)
        self.assertAlmostEqual(rows[1]['change'],2.5)
        self.assertNotIn('private', json.dumps(rows))

    def test_future_nan_duplicate_dates_refused(self):
        for dates,values in [(('2026-10-28','2026-10-30'),(1,2)),
                             (('2026-10-28','2026-10-29'),(1,float('nan'))),
                             (('2026-10-29','2026-10-29'),(1,2))]:
            def loader(symbol, source, days): return SimpleNamespace(source=source.upper(),dates=dates,values=values)
            self.assertTrue(all(r['status']=='UNAVAILABLE' for r in load_markets(loader=loader,today=date(2026,10,29))))

    def test_home_consumes_computed_result_and_market_rows_without_network_on_build(self):
        from tests.research_home_acceptance import Page, walk
        import flet as ft
        from ui.research_home import build_home_page
        from core.research.runs import session_for
        page=Page(); run,_,_=result_fixture(); session_for(page).put(run)
        with patch('core.research.markets.load_markets',side_effect=AssertionError('network')):
            view=build_home_page(page,navigate=lambda _:None)
        texts=[c.value for c in walk(view) if isinstance(c,ft.Text)]
        self.assertIn(f"{run['metrics']['p05']:,.2f}", texts)
        self.assertIn('합성 입력으로 계산한 분포입니다.', texts)
        self.assertTrue(any('seed 7' in t for t in texts))

    def test_quant_lab_callback_records_actual_success_and_failure(self):
        import flet as ft
        from ui import quant_lab_page as lab
        from tests.research_home_acceptance import walk
        from core.research.runs import session_for
        run,h,mc=result_fixture()
        page=SimpleNamespace(run_thread=lambda fn:fn(),update=lambda:None)
        with patch.object(lab,'_lab_grade',return_value=None), patch.object(lab,'_grade_blocks',return_value=[]):
            view=lab.build_quant_lab_page(page)
            controls=list(walk(view))
            fields={c.label:c for c in controls if isinstance(c,ft.TextField)}
            dropdowns={c.label:c for c in controls if isinstance(c,ft.Dropdown)}
            dropdowns['Drift'].value='zero';dropdowns['Model'].value='gbm'
            fields['Paths'].value='200';fields['Horizon (sessions)'].value='5'
            fields['Symbol'].value='TEST'
            button=next(c for c in controls if isinstance(c,ft.Button))
            with patch.object(lab,'load_history',return_value=h): button.on_click(None)
            result=session_for(page).runs()[0]
            self.assertEqual(result['execution_status'],'COMPLETED')
            self.assertEqual(result['metrics']['p50'],mc.median_terminal)
            with patch.object(lab,'load_history',side_effect=lab.HistoryError('offline')): button.on_click(None)
            self.assertEqual(session_for(page).runs()[0]['execution_status'],'FAILED')
            self.assertEqual(len(session_for(page).runs()),2)

    def test_stable_computation_excludes_time_and_detects_code_data_changes(self):
        from core.research.provenance import code_evidence, runtime_evidence
        from core.research.runs import computation_fingerprint
        run,h,mc=result_fixture();run['code']=code_evidence();run['environment']=runtime_evidence()
        a=computation_fingerprint(run);b=copy.deepcopy(run)
        b['created_at']='2026-10-28T12:00:00+00:00'
        self.assertEqual(a,computation_fingerprint(b))
        b['code']['calculation_sha256']='0'*64
        self.assertNotEqual(a,computation_fingerprint(b))
        b=copy.deepcopy(run);b['data']['fingerprint_sha256']='f'*64
        self.assertNotEqual(a,computation_fingerprint(b))

    def test_report_bundle_hashes_match_files(self):
        from core.research.export import bundle_bytes
        from io import BytesIO
        from zipfile import ZipFile
        import hashlib
        r,_,_=result_fixture()
        with ZipFile(BytesIO(bundle_bytes(r))) as z:
            manifest=json.loads(z.read('MANIFEST.json'))
            self.assertEqual(set(z.namelist()),{'MANIFEST.json','research-run.json','report.html'})
            for name,info in manifest['files'].items():
                self.assertEqual(info['sha256'],hashlib.sha256(z.read(name)).hexdigest())
            self.assertEqual(read_export(z.read('research-run.json')),r)

    def test_refresh_exclusion(self):
        s=SessionResearch(); self.assertTrue(s.start_market_refresh()); self.assertFalse(s.start_market_refresh())
        s.finish_market_refresh([]); self.assertTrue(s.start_market_refresh())

    def test_desktop_save_writes_selected_file_and_cancel_does_not_write(self):
        import asyncio
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import AsyncMock
        from ui.research_home import ResearchHome
        page=SimpleNamespace(web=False,platform=SimpleNamespace(is_mobile=lambda:False),show_dialog=unittest.mock.Mock())
        view=ResearchHome(page,lambda _:None);r,_,_=result_fixture()
        with TemporaryDirectory() as directory:
            path=Path(directory)/'result.json'
            with patch('ui.research_home.ft.FilePicker') as picker:
                picker.return_value.save_file=AsyncMock(return_value=str(path))
                asyncio.run(view.download(r))
                self.assertEqual(read_export(path.read_bytes()),r)
                picker.return_value.save_file=AsyncMock(return_value=None)
                with patch('ui.research_home.save_desktop_export',side_effect=AssertionError('cancel wrote')):
                    asyncio.run(view.download(r))
            page.show_dialog.assert_not_called()

    def test_web_export_sends_bytes_without_server_file_write(self):
        import asyncio
        from unittest.mock import AsyncMock
        from ui.research_home import ResearchHome
        page=SimpleNamespace(web=True,show_dialog=unittest.mock.Mock())
        view=ResearchHome(page,lambda _:None);r,_,_=result_fixture()
        with patch('ui.research_home.ft.FilePicker') as picker, \
             patch('ui.research_home.save_desktop_export',side_effect=AssertionError('web wrote server path')):
            picker.return_value.save_file=AsyncMock(return_value='browser-selected.json')
            asyncio.run(view.download(r))
            self.assertEqual(read_export(picker.return_value.save_file.call_args.kwargs['src_bytes']),r)
        page.show_dialog.assert_not_called()


if __name__=='__main__': unittest.main()
