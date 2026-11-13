"""The educational catalogue shares real study calculations and missing-data rules."""
from datetime import date,timedelta
from dataclasses import replace
import json
from io import BytesIO
from zipfile import ZipFile
import unittest
import numpy as np
from core.education import catalog as C,indicators as I
from core.i18n import LocaleContext
from core.market.models import Candle,ChartRequest,MarketSnapshot
from core.market.presentation import chart_svg


class IndicatorCatalogTests(unittest.TestCase):
    def snapshot(self):
        return MarketSnapshot(ChartRequest(),tuple(Candle((date(2026,1,1)+timedelta(days=n)).isoformat(),
            100+n,103+n,99+n,102+n,1000+n) for n in range(100)),source='fixture')

    def test_all_market_studies_selectable_but_close_only_sample_never_fakes_ohlcv(self):
        self.assertEqual(set(C.BY_KEY),{s.key for s in I.STUDIES})
        _,series,_=C.historical_case()
        values=C.values_for(series,C.ORDER)
        for key in ('atr','psar','stoch','obv','vwap','investor_flow','short_ratio'):
            self.assertNotIn(key,values)
            self.assertTrue(C.missing_reason(series,key,'en'))
        self.assertIn('Required data is absent',C.chart_svg(series,('atr',),locale=LocaleContext('en_US')))

    def test_observed_market_chart_is_the_same_renderer_and_uses_true_high_low(self):
        snapshot=self.snapshot();series=C.from_snapshot(snapshot)
        self.assertEqual(series.ohlc[0],(100,103,99,102))
        atr=C.values_for(series,('atr',))['atr']
        expected=I.compute_study('atr',I.Bars(series.dates,*zip(*series.ohlc),series.volume,'1d'))
        for key in atr:np.testing.assert_allclose(atr[key],expected[key],equal_nan=True)
        self.assertEqual(C.chart_svg(series,('sma','atr'),width=960,locale=LocaleContext('en_US')),
                         chart_svg(snapshot,indicators=('sma','atr'),width=960,visible=None,language='en'))
        changed=C.from_snapshot(replace(snapshot,candles=tuple(replace(c,volume=None) for c in snapshot.candles)))
        self.assertTrue(C.missing_reason(changed,'obv','en'))

    def test_export_keeps_full_selected_explanations_and_explicit_education_scope(self):
        case,series,meta=C.historical_case(('atr','rsi'))
        for locale in ('ko_KR','en_US'):
            ctx=LocaleContext(locale)
            with ZipFile(BytesIO(C.learning_bundle(series,('atr','rsi'),meta,case_name=case,locale=ctx))) as archive:
                record=json.loads(archive.read('education.json'))
                self.assertEqual(record['selected_indicators'],['rsi','atr'])
                self.assertEqual(record['verdict'],'NOT_RUN')
                self.assertIn(C.missing_reason(series,'atr',ctx.language),archive.read('report.html').decode())

    def test_ticks_with_equal_exchange_times_remain_distinct_observations(self):
        stamp='2026-11-13T09:00:00+09:00'
        snapshot=MarketSnapshot(ChartRequest(interval='1tick'),(
            Candle(stamp,100,100,100,100,10,sequence=1,trade_count=1),
            Candle(stamp,101,101,101,101,20,sequence=2,trade_count=1)))
        series=C.from_snapshot(snapshot)
        self.assertEqual(series.dates,(stamp,stamp));self.assertEqual(series.closes,(100,101))
        self.assertIn('<svg',C.chart_svg(series,('rsi',)))


if __name__=='__main__':unittest.main()
