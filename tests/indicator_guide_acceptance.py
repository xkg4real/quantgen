"""Bounded educational calculations, provenance, localization and report contracts."""
import csv
from dataclasses import replace
from datetime import date,timedelta
from html import unescape
from io import BytesIO
import hashlib
import json
from pathlib import Path
import re
from string import Formatter
import unittest
from unittest.mock import patch
from zipfile import ZipFile

import dotenv
import numpy as np
with patch.object(dotenv,'load_dotenv',return_value=False):
    from core.education.indicators import (INDICATORS,ChartSeries,historical_case,indicator_values,
                                           counterexamples,selection)
    from core.education.chart import chart_svg,learning_bundle,reading_text
    from core.quant.signals import sma,ema,rsi,macd
from core.i18n import LocaleContext,locale_choices,numeric_presentation
from core.ui_messages import MESSAGES
from core.research.display_rights import display_rights,FIELDS,OUTCOMES
from core.research.markets import SPECS
from core.theme import LIGHT,DARK


class IndicatorGuideTests(unittest.TestCase):
    def setUp(self):
        deny=patch('requests.sessions.Session.request',side_effect=AssertionError('Network forbidden'))
        deny.start();self.addCleanup(deny.stop)

    def test_historical_sample_is_pinned_attributed_and_correctly_oriented(self):
        _,series,meta=historical_case()
        folder=Path(__file__).resolve().parents[1]/'core/education/samples'
        raw=(folder/'usdeur_daily.csv').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),meta['data_sha256'])
        rows=list(csv.DictReader(raw.decode().splitlines()))
        self.assertEqual(len(rows),1247)
        self.assertEqual((rows[0]['date'],float(rows[0]['reference_rate'])),('2018-01-02',.8299))
        # Board H.10 2018-01-08 reports 1.2050 USD/EUR for Jan 2; mirror is reciprocal, 4dp.
        self.assertAlmostEqual(float(rows[0]['reference_rate']),1/1.2050,delta=.00005)
        self.assertEqual(meta['symbol'],'USD/EUR');self.assertEqual(meta['unit'],'EUR per USD')
        self.assertFalse(meta['synthetic']);self.assertFalse(series.ohlc);self.assertFalse(series.volume)
        self.assertIn('round',meta['transformation']);self.assertIn('federalreserve.gov',meta['rights_url'])

    def test_all_indicators_share_one_sample_and_preserve_existing_formulas(self):
        keys=tuple(i.key for i in INDICATORS)
        name,series,_=historical_case(keys)
        self.assertEqual(name,'2020')
        values=indicator_values(series);px=np.asarray(series.closes)
        self.assertTrue(all(len(v)==len(series.dates) for v in values.values()))
        np.testing.assert_equal(values['SMA20'],sma(px,20));np.testing.assert_equal(values['SMA50'],sma(px,50))
        np.testing.assert_equal(values['EMA12'],ema(px,12));np.testing.assert_equal(values['EMA26'],ema(px,26))
        for index in (14,50,len(px)-1):self.assertAlmostEqual(values['RSI14'][index],rsi(px[:index+1]),places=12)
        line,signal=macd(px)
        self.assertEqual(values['MACD'][-1],line);self.assertEqual(values['Signal'][-1],signal)
        self.assertAlmostEqual(values['Upper'][-1],float(px[-20:].mean()+2*px[-20:].std(ddof=0)))
        self.assertTrue(np.isnan(values['RSI14'][:14]).all())
        self.assertTrue(np.isnan(values['SMA50'][:49]).all())

    def test_indicator_values_do_not_use_future_prices(self):
        _,series,_=historical_case(('rsi','macd'))
        prefix=replace(series,dates=series.dates[:100],closes=series.closes[:100])
        whole,short=indicator_values(series),indicator_values(prefix)
        for name in short:np.testing.assert_equal(short[name],whole[name][:100])

    def test_cursor_reading_uses_selected_observations_and_cached_values_are_read_only(self):
        _,series,_=historical_case(('sma','rsi'))
        ctx=LocaleContext('en_US');values=indicator_values(series)
        self.assertIn('not enough observations',reading_text(series,('sma','rsi'),0,ctx))
        last=len(series.dates)-1
        comparison='above' if values['SMA20'][last]>values['SMA50'][last] else 'below'
        self.assertIn('SMA20 is '+comparison+' SMA50',reading_text(series,('sma',),last,ctx))
        self.assertNotIn('RSI',reading_text(series,('sma',),last,ctx))
        self.assertIs(values,indicator_values(series))
        with self.assertRaises(ValueError):values['SMA20'][last]=0

    def test_selection_and_counterexamples_have_explicit_common_dates_and_hindsight(self):
        self.assertEqual(selection(('macd','sma','sma')),('sma','macd'))
        with self.assertRaises(ValueError):selection(('unknown',))
        for key in (i.key for i in INDICATORS):
            _,series,_=historical_case((key,))
            events=counterexamples(series,(key,))
            self.assertTrue(events,key)
            for event in events:
                index=event['index']
                self.assertEqual(event['date'],series.dates[index])
                self.assertEqual(event['horizon_observations'],5)
                self.assertEqual(event['change'],series.closes[index+5]/series.closes[index]-1)
                self.assertLess(event['interpretation_direction']*event['change'],0)

    def test_svg_panels_and_candles_require_actual_aligned_observations(self):
        _,series,_=historical_case(('sma','rsi','macd','bb'))
        for width in (350,960):
            for palette in (LIGHT,DARK):
                svg=chart_svg(series,('sma','rsi','macd','bb'),width=width,colors=palette)
                self.assertNotIn('nan',svg.lower());self.assertNotIn('inf,',svg.lower())
                self.assertNotIn('<script',svg);self.assertNotIn('http://',svg.replace('http://www.w3.org/2000/svg',''))
                for key in ('sma','rsi','macd','bb'):
                    self.assertIn(next(s.color for s in INDICATORS if s.key==key),svg)
        with self.assertRaises(ValueError):chart_svg(series,chart_type='candles')
        px=(100.,101.,99.)
        bars=tuple((v-.1,v+.5,v-.5,v) for v in px)
        supplied=ChartSeries('FIXTURE',('2020-01-01','2020-01-02','2020-01-03'),px,'SYNTHETIC',ohlc=bars,volume=(5,6,7))
        self.assertIn('stroke=',chart_svg(supplied,chart_type='candles'))
        with self.assertRaises(ValueError):replace(supplied,ohlc=bars[:-1]).validate()

    def test_localized_bundle_is_integrity_checked_and_not_a_research_verdict(self):
        name,series,meta=historical_case(('rsi','macd'))
        for locale,heading in (('ko_KR','무엇을 나타내나요?'),('en_US','What does it measure?')):
            with ZipFile(BytesIO(learning_bundle(series,('rsi','macd'),meta,case_name=name,locale=LocaleContext(locale)))) as archive:
                record=json.loads(archive.read('education.json'));html=archive.read('report.html').decode()
                manifest=json.loads(archive.read('MANIFEST.json'))
                self.assertIn(heading,html);self.assertEqual(record['verdict'],'NOT_RUN');self.assertTrue(record['education_only'])
                self.assertEqual(record['selected_indicators'],['rsi','macd'])
                for path,evidence in manifest['files'].items():
                    self.assertEqual(hashlib.sha256(archive.read(path)).hexdigest(),evidence['sha256'])


class LocaleAndRightsTests(unittest.TestCase):
    def test_catalogue_keys_placeholders_and_explicit_fallback(self):
        self.assertEqual(set(MESSAGES['ko']),set(MESSAGES['en']))
        for key in MESSAGES['en']:
            fields=lambda text:{name for _,name,_,_ in Formatter().parse(text) if name}
            self.assertEqual(fields(MESSAGES['ko'][key]),fields(MESSAGES['en'][key]),key)
        self.assertGreater(len(locale_choices()),700)
        fallback=LocaleContext('ar_EG')
        self.assertTrue(fallback.is_fallback);self.assertEqual(fallback.language,'en')
        self.assertIn('English',fallback.t('language_fallback'))
        self.assertNotEqual(fallback.date('2020-12-31'),LocaleContext('en_US').date('2020-12-31'))

    def test_display_numbers_and_templates_preserve_identity_and_parameters(self):
        ctx=LocaleContext('fr_FR')
        self.assertEqual(numeric_presentation('1,234.50',ctx),ctx.number(1234.5,2))
        self.assertEqual(numeric_presentation('005930',ctx),'005930')
        self.assertEqual(LocaleContext('en_US').text('FAILED · ProviderError · 입력/데이터를 확인하세요.'),
                         'FAILED · ProviderError · Check inputs/data.')
        self.assertEqual(LocaleContext('ko_KR').text('Yield %'),'수익률 %')
        self.assertEqual(LocaleContext('en_US').money(1234.5,'USD'),'$1,234.50')

    def test_rights_inventory_covers_all_registered_and_home_items_without_grants(self):
        record=display_rights()
        root=Path(__file__).resolve().parents[1]
        inventory=json.loads((root/'docs/product/DATA_READINESS_2026-10-29.json').read_text())
        self.assertEqual({row['series_id'] for row in record['registered_series']},{row['series_id'] for row in inventory['series']})
        self.assertEqual({row['series_id'] for row in record['home']},{row[1] for row in SPECS})
        self.assertEqual(len(record['registered_series']),73)
        self.assertFalse(record['publication_authorization']);self.assertFalse(record['legal_opinion'])
        for policy in record['policies'].values():
            self.assertIn(policy['outcome'],OUTCOMES)
            for field in FIELDS:
                self.assertTrue(policy[field]['ko']);self.assertTrue(policy[field]['en'])
            self.assertTrue(policy['evidence'])
        home={row['series_id']:row for row in record['home']}
        self.assertEqual(home['^GSPC']['outcome'],'rights_replace')
        self.assertEqual(home['VIXCLS']['outcome'],'rights_conditional')


if __name__=='__main__':unittest.main()
