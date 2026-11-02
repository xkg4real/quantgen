"""Offline protocol/normalization tests; never reads a local KIS key or cache."""
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch

import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from core.market.models import ChartRequest, Instrument
    from data.kis_workspace import MarketDataService, supported_intervals, _MAX_PAGES
    from data.krx.kis_client import KISError, check_quotation_path

KST = ZoneInfo('Asia/Seoul')
NOW = datetime(2026, 11, 2, 15, 0, tzinfo=KST)


class Client:
    ready = True
    def __init__(self, handler):
        self.handler, self.calls = handler, []
    def _get(self, path, tr_id, params):
        check_quotation_path(path)
        self.calls.append((path, tr_id, params.copy()))
        return self.handler(path, tr_id, params)


def domestic_row(day, close='100', time=None, volume='10'):
    row = {'stck_bsop_date': day, 'stck_oprc': '99', 'stck_hgpr': '102', 'stck_lwpr': '98',
           'stck_clpr': close, 'stck_prpr': close, 'acml_vol': volume, 'cntg_vol': volume}
    if time is not None:
        row['stck_cntg_hour'] = time
    return row


def no_quote(path):
    return path.endswith('/inquire-price') or path.endswith('/price')


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        p = patch('requests.sessions.Session.request', side_effect=AssertionError('No live network'))
        p.start(); self.addCleanup(p.stop)

    def service(self, handler, **kwargs):
        return MarketDataService(Client(handler), now=lambda: NOW, **kwargs)

    def test_daily_pagination_dedup_and_strict_ohlc(self):
        def handler(path, tr, params):
            if no_quote(path):
                return {'output': {'stck_prpr':'100', 'prdy_vrss':'2', 'prdy_vrss_sign':'5', 'prdy_ctrt':'2'}}
            if params['FID_INPUT_DATE_2'] == '20261102':
                bad = domestic_row('20261029'); bad['stck_oprc'] = ''
                nan = domestic_row('20261028', 'NaN')
                return {'output2': [domestic_row('20261102'), domestic_row('20261030'), bad, nan]}
            return {'output2': [domestic_row('20261030', '101'), domestic_row('20261028')]}
        s = self.service(handler)
        out = s.load(ChartRequest(limit=20))
        self.assertEqual([c.timestamp for c in out.candles], ['2026-10-28', '2026-10-30', '2026-11-02'])
        self.assertEqual(out.candles[1].close, 100)  # older overlapping page cannot overwrite newest
        self.assertEqual(out.quote.change, -2)
        self.assertEqual(out.quote.change_pct, -2)
        self.assertEqual(s.client.calls[1][2]['FID_INPUT_DATE_2'], '20261029')
        self.assertEqual(s.client.calls[0][2]['FID_ORG_ADJ_PRC'], '1')
        self.assertIn('Partial history: 3/20', out.note)
        self.assertEqual(out.quote.market_time, '')  # retrieval time is not exchange trade time

    def test_domestic_minutes_aggregate_volume_without_filling_session_gap(self):
        calls = [0]
        def handler(path, tr, params):
            if no_quote(path): return {'output': {}}
            calls[0] += 1
            self.assertEqual(tr, 'FHKST03010230')
            self.assertEqual(params['FID_FAKE_TICK_INCU_YN'], '')
            if calls[0] == 1:
                self.assertEqual(params['FID_INPUT_HOUR_1'], '150000')
                return {'output2': [domestic_row('20261102', time='090200', volume='3'),
                                    domestic_row('20261102', time='090100', volume='2'),
                                    domestic_row('20261102', time='090000', volume='1'),
                                    domestic_row('20261102', time='180000', volume='999')]}
            return {'output2': [domestic_row('20261030', time='152900', volume='4')]}
        s = self.service(handler)
        out = s.load(ChartRequest(interval='5m', limit=20))
        self.assertEqual(len(out.candles), 2)
        self.assertEqual(out.candles[0].timestamp, '2026-10-30T15:25:00+09:00')
        self.assertEqual(out.candles[1].timestamp, '2026-11-02T09:00:00+09:00')
        self.assertEqual(out.candles[1].volume, 6)
        self.assertEqual(out.candles[0].volume, 4)
        self.assertEqual(s.client.calls[1][2]['FID_INPUT_HOUR_1'], '085900')
        self.assertIsNone(out.quote)
        self.assertIn('Current quote unavailable', out.note)

    def test_forming_domestic_minute_does_not_repeat_previous_volume(self):
        def handler(path,tr,p):
            if no_quote(path):return {'output':{}}
            return {'output2':[domestic_row('20261102',time='150000',volume='999'),
                               domestic_row('20261102',time='145900',volume='999')]}
        out=self.service(handler).load(ChartRequest(interval='1m',limit=20))
        self.assertEqual(out.candles[0].volume,999)
        self.assertIsNone(out.candles[1].volume)
        self.assertIn('forming minute volume',out.note)

    def test_overseas_minutes_page_on_local_clock_with_dst(self):
        dates = [('20261102','093000'),('20261030','093000')]
        def handler(path, tr, params):
            if no_quote(path): return {'output': {'last':'101', 'base':'100', 'rate':'1', 'tvol':'123'}}
            self.assertEqual(params['NMIN'],'1')
            idx = 0 if params['KEYB'] == '' else 1
            d,h=dates[idx]
            return {'output1': {'next':'1'}, 'output2': [{'xymd':d,'xhms':h,'open':'100','high':'102',
                     'low':'99','last':'101','evol':'7'}]}
        s = self.service(handler)
        # 09:30 NY Nov2 is 23:30 Korea, so set retrieval later.
        s._now = lambda: datetime(2026,11,3,1,tzinfo=KST)
        out = s.load(ChartRequest(Instrument('overseas_stock','AAPL','NAS'),'5m',20))
        self.assertEqual(out.candles[0].timestamp,'2026-10-30T09:30:00-04:00')
        self.assertEqual(out.candles[1].timestamp,'2026-11-02T09:30:00-05:00')
        self.assertEqual(out.candles[1].volume,7)
        self.assertEqual(s.client.calls[1][2]['KEYB'],'20261102092900')
        self.assertEqual(s.client.calls[1][2]['NEXT'],'1')
        self.assertEqual(out.quote.currency,'USD')
        self.assertIsNone(out.quote.open)  # simple price endpoint does not provide OHLC
        self.assertIn('0-minute delay',out.note)

    def test_overseas_hour_uses_common_civil_clock_not_vendor_session_anchor(self):
        def handler(path,tr,p):
            if no_quote(path):return {'output':{}}
            self.assertEqual(p['NMIN'],'1')
            rows=[]
            for clock,op,hi,lo,close,vol in [('093000','100','102','99','101','2'),
                                         ('095900','101','104','100','103','3'),
                                         ('100000','103','105','102','104','4')]:
                rows.append({'xymd':'20261102','xhms':clock,'open':op,'high':hi,'low':lo,'last':close,'evol':vol})
            return {'output2':rows}
        s=self.service(handler)
        s._now=lambda:datetime(2026,11,3,1,tzinfo=KST)
        out=s.load(ChartRequest(Instrument('overseas_stock','AAPL','NAS'),'60m',20))
        self.assertEqual(out.candles[0].timestamp,'2026-11-02T09:00:00-05:00')
        self.assertEqual((out.candles[0].open,out.candles[0].high,out.candles[0].low,out.candles[0].close,out.candles[0].volume),
                         (100,104,99,103,5))
        self.assertEqual(out.candles[1].timestamp,'2026-11-02T10:00:00-05:00')
        self.assertEqual(out.candles[1].volume,4)
        self.assertIn('first/latest bars can be partial',out.note)

    def test_weekly_and_monthly_use_period_start(self):
        def handler(path,tr,params):
            return {'output2':[domestic_row('20261030')]} if not no_quote(path) else {'output':{}}
        s=self.service(handler)
        self.assertEqual(s.load(ChartRequest(interval='1w',limit=20)).candles[0].timestamp,'2026-10-26')
        self.assertEqual(s.load(ChartRequest(interval='1M',limit=20)).candles[0].timestamp,'2026-10-01')

    def test_derivative_market_and_overnight_rollover(self):
        def handler(path,tr,params):
            if no_quote(path): return {'output1':{}}
            self.assertEqual(params['FID_COND_MRKT_DIV_CODE'],'CM')
            self.assertEqual(params['FID_HOUR_CLS_CODE'],'60')
            return {'output2':[{'stck_bsop_date':'20261030','stck_cntg_hour':'253000',
                      'futs_oprc':'300','futs_hgpr':'302','futs_lwpr':'299','futs_prpr':'301','cntg_vol':'2'}]}
        out=self.service(handler).load(ChartRequest(Instrument('domestic_future','A01612','CM'),'5m',20))
        self.assertEqual(out.candles[0].timestamp,'2026-10-31T01:30:00+09:00')
        self.assertEqual(out.candles[0].volume,2)
        s=self.service(lambda *a:self.fail('ambiguous market must fail before HTTP'))
        with self.assertRaises(KISError): s.load(ChartRequest(Instrument('domestic_future','A65612'),'1d',20))

    def test_domestic_derivative_quote_uses_contract_units(self):
        for market,code in [('F','A01612'),('O','B01612300'),('CF','A65612'),('JF','A11112')]:
            s=self.service(lambda *a:{'output1':{'futs_prpr':'301.5','futs_prdy_vrss':'1','futs_prdy_ctrt':'0.3'}})
            quote=s.quote(Instrument('domestic_future',code,market))
            self.assertEqual(quote.currency,'quote units')
            self.assertIn('contract quote units',quote.note)
            self.assertNotEqual(quote.currency,'KRW')

    def test_bond_minute_rejected_and_daily_retains_per_face_prices(self):
        ins=Instrument('bond','KR2033022D33')
        s=self.service(lambda *a:self.fail('unsupported interval must fail before HTTP'))
        with self.assertRaises(KISError):s.load(ChartRequest(ins,'1m',20))
        self.assertEqual(supported_intervals(ins),('1d',))
        def handler(path,tr,params):
            if no_quote(path):return {'output':{'bond_prpr':'9999','bond_oprc':'9990'}}
            return {'output':[{'stck_bsop_date':'20261030','bond_oprc':'9990','bond_hgpr':'10010',
                       'bond_lwpr':'9980','bond_prpr':'9999','acml_vol':'0'}]}
        out=self.service(handler).load(ChartRequest(ins,'1d',20))
        self.assertEqual(out.candles[0].close,9999)
        self.assertEqual(out.candles[0].volume,0)
        self.assertIn('10,000 face',out.note)

    def test_foreign_futures_exact_master_cp949_scaling_and_cursor(self):
        raw=bytearray(b' '*223)
        raw[:32]=b'GCU26'.ljust(32)
        raw[82:132]='골드 선물'.encode('cp949').ljust(50)
        raw[132:142]=b'CME'.ljust(10)
        raw[160:165]=b'-1'.rjust(5)
        master=bytes(raw).decode('cp949')
        calls=[0]
        def handler(path,tr,params):
            if no_quote(path):return {'output1':{'last_price':'19225','prev_diff_price':'10','prev_diff_rate':'2','prev_diff_flag':'5','crc_cd':'USD'}}
            calls[0]+=1
            self.assertEqual(params['EXCH_CD'],'CME')
            if calls[0]==1:
                self.assertEqual(params['QRY_TP'],'Q')
                return {'output1':{'index_key':'opaque-cursor'},'output2':[{'data_date':'20261030',
                       'open_price':'19220','high_price':'19230','low_price':'19200','last_price':'19225','vol':'10'}]}
            self.assertEqual(params['INDEX_KEY'],'opaque-cursor')
            self.assertEqual(params['QRY_TP'],'P')
            return {'output1':{},'output2':[]}
        s=self.service(handler,master_loader=lambda name:[master])
        out=s.load(ChartRequest(Instrument('overseas_future','GCU26','CME'),'1d',20))
        self.assertEqual(out.candles[0].close,1922.5)
        self.assertEqual(out.quote.price,1922.5)
        self.assertEqual(out.quote.change,-1)
        self.assertEqual(out.quote.change_pct,-2)
        self.assertEqual(out.quote.currency,'USD')
        self.assertEqual(out.candles[0].timestamp,'2026-10-30')
        self.assertNotIn('1m',supported_intervals(out.request.instrument))
        s=self.service(lambda *a:self.fail('no master cannot request unscaled prices'),master_loader=lambda name:[])
        with self.assertRaises(KISError):s.load(out.request)

    def test_paging_bound_and_empty_invalid_data_never_fabricated(self):
        s=self.service(lambda path,tr,p:{'output2':[domestic_row('20261030',close='inf')]})
        with self.assertRaises(KISError):s.load(ChartRequest(limit=20))
        self.assertEqual(len(s.client.calls),1)
        s=self.service(lambda path,tr,p:{'output2':[domestic_row('20261030')]})
        out=s.load(ChartRequest(limit=500))
        self.assertEqual(len(out.candles),1)
        self.assertLessEqual(len(s.client.calls),_MAX_PAGES+1)

    def test_exact_paging_cap_and_last_cursor_are_bounded(self):
        count = [0]
        last = [None]
        def handler(path, tr, p):
            if no_quote(path): return {'output':{}}
            count[0] += 1
            cursor = datetime.strptime(p['FID_INPUT_DATE_1'] + p['FID_INPUT_HOUR_1'], '%Y%m%d%H%M%S').replace(tzinfo=KST)
            if last[0] is not None:
                self.assertEqual(cursor, last[0] - timedelta(minutes=1))
            last[0] = cursor
            return {'output2':[domestic_row(cursor.strftime('%Y%m%d'),time=cursor.strftime('%H%M%S'))]}
        out=self.service(handler).load(ChartRequest(interval='60m',limit=500))
        self.assertEqual(count[0],_MAX_PAGES)
        self.assertEqual(last[0],NOW - timedelta(minutes=_MAX_PAGES-1))
        self.assertIn('Partial history',out.note)
        self.assertTrue(all(c.volume is None or c.volume <= _MAX_PAGES*10 for c in out.candles))

    def test_new_quotation_paths_do_not_allow_account_or_orders(self):
        additions = (
            '/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice',
            '/uapi/domestic-futureoption/v1/quotations/inquire-time-fuopchartprice',
            '/uapi/overseas-price/v1/quotations/inquire-time-itemchartprice',
            '/uapi/overseas-futureoption/v1/quotations/weekly-ccnl',
            '/uapi/overseas-futureoption/v1/quotations/monthly-ccnl',
            '/uapi/overseas-futureoption/v1/quotations/inquire-price',
        )
        for path in additions:
            self.assertEqual(check_quotation_path(path),path)
        for path in ('/uapi/domestic-stock/v1/trading/order-cash', '/uapi/domestic-stock/v1/trading/inquire-balance'):
            with self.assertRaises(KISError): check_quotation_path(path)


if __name__=='__main__':unittest.main()
