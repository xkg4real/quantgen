"""Original-case-first guide contracts on fixed, offline display inputs.

The case is the primary chart. Teaching annotations must point to the original
renderer, not to another set of invented prices. Pure geometry checks inject
immutable, explicit line values; they do not run an indicator engine or loader.
"""
from contextlib import contextmanager
from dataclasses import replace
from datetime import date, timedelta
import importlib.util
import math
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from tests import guide_lessons_acceptance as lesson_contracts
from tests.guide_docking_acceptance import _helpers


def _fixed_history():
    dates=tuple((date(2020,1,1)+timedelta(days=i)).isoformat() for i in range(120))
    closes=tuple(10+i*.02+(i%9)*.04 for i in range(120))
    return SimpleNamespace(symbol='SYNTHETIC_DOCK_TEST',dates=dates,closes=closes,
                           source='FIXED_SYNTHETIC_UI_ONLY')


@unittest.skipUnless(importlib.util.find_spec('PyQt6'), 'native Qt runtime required')
class GuideCaseAnnotationContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lesson_contracts.GuideLessonContracts.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        lesson_contracts.GuideLessonContracts.tearDownClass.__func__(cls)

    @contextmanager
    def _guide(self):
        from PyQt6.QtCore import QCoreApplication,QEvent,Qt
        from PyQt6.QtWidgets import QApplication,QFrame,QVBoxLayout
        from core.i18n import LocaleContext
        from core.education import catalog,indicators as I
        from quantgen_desktop.localization import UiLabel
        from quantgen_desktop.stock_detail_style import text
        from quantgen_desktop.page_kit import Workspace
        root=Path(__file__).resolve().parents[1]
        app=QApplication.instance() or QApplication(['guide-case-contract','-platform','offscreen'])
        application=_helpers('quantgen_desktop.app',root/'quantgen_desktop/app.py',('label','panel'),
            {'UiLabel':UiLabel,'Qt':Qt,'QFrame':QFrame,'QVBoxLayout':QVBoxLayout})
        stock=_helpers('quantgen_desktop.stock_detail',root/'quantgen_desktop/stock_detail.py',
                       ('interval_words',),{'text':text})
        with patch.dict(sys.modules,{'quantgen_desktop.app':application,'quantgen_desktop.stock_detail':stock}), \
             patch.object(catalog,'historical_case',side_effect=AssertionError('real case forbidden')), \
             patch.object(I,'historical_case',side_effect=AssertionError('real case forbidden')):
            from quantgen_desktop.indicator_guide import IndicatorGuide
            guide=IndicatorGuide(locale=LocaleContext('ko_KR'),history=_fixed_history())
            try:
                guide.dock_into(Workspace(('Technical indicator guide','기술지표 가이드')))
                guide.resize(1000,800);guide.show()
                for _ in range(8):app.processEvents()
                yield guide,app
            finally:
                guide.close();guide.deleteLater()
                QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete.value)
                app.processEvents()

    def test_original_case_is_first_visible_and_keeps_context(self):
        from PyQt6.QtCore import QPoint
        with self._guide() as (guide,app):
            original=guide.chart
            before=(guide.series,guide.series.dates,guide.series.closes,dict(guide.meta),guide.cursor)
            self.assertTrue(guide.context_host.isVisible())
            self.assertTrue(original.isVisible())
            self.assertTrue(guide.case_title.isVisible())
            self.assertFalse(guide.lesson_toggle.isChecked())
            self.assertTrue(guide.lesson.isHidden())
            self.assertEqual(guide.workspace.canvas_scroll.verticalScrollBar().value(),0)
            y=original.mapTo(guide.workspace.canvas_scroll.viewport(),QPoint()).y()
            self.assertGreaterEqual(y,0)
            self.assertLess(y,guide.workspace.canvas_scroll.viewport().height())
            self.assertFalse(original.grab().isNull())
            self.assertTrue(original.annotations)
            text=' '.join(' '.join(a.text) for a in original.annotations)
            self.assertTrue(any(word in text for word in ('가격','날짜','커서')))
            self.assertTrue(any(a.index is not None and a.value==guide.series.closes[a.index]
                                for a in original.annotations))
            self.assertEqual((guide.series,guide.series.dates,guide.series.closes,dict(guide.meta),guide.cursor),before)

    def test_supplement_toggle_keeps_case_and_reading_state(self):
        from PyQt6.QtCore import QPoint
        from PyQt6.QtGui import QPalette
        from PyQt6.QtWidgets import QFrame,QVBoxLayout
        from core.i18n import LocaleContext
        from core.theme import DARK,LIGHT
        from quantgen_desktop.stock_detail_style import label,sheet
        with self._guide() as (guide,app):
            guide.choose('ema');guide.move_cursor(42)
            original=guide.chart
            before=(guide.keys,guide.focus,guide.series,dict(guide.meta),guide.cursor)
            for ctx in (LocaleContext('ko_KR'),LocaleContext('en_US')):
                for colors in (LIGHT,DARK):
                    guide.colors=colors;guide.set_theme(colors);guide.set_locale(ctx)
                    for width in (1000,1360):
                        guide.resize(width,800)
                        for opened in (True,False):
                            guide.lesson_toggle.setChecked(opened)
                            for _ in range(4):app.processEvents()
                            self.assertIs(guide.chart,original)
                            self.assertTrue(guide.context_host.isVisible())
                            self.assertTrue(original.isVisible())
                            self.assertEqual(guide.lesson.isVisible(),opened)
                            if opened:
                                self.assertLess(original.mapTo(guide,QPoint()).y(),
                                                guide.lesson.figure.mapTo(guide,QPoint()).y())
                                # Compare computed type/palette with the actual stock-detail helpers,
                                # rather than imposing another set of guide-only font constants.
                                reference=QFrame(guide);reference.setStyleSheet(sheet(colors,colors is DARK))
                                reference_body=QVBoxLayout(reference)
                                try:
                                    for actual,role in ((guide.lesson.title,'cardTitle'),
                                                        (guide.lesson.badge,'rowNote'),
                                                        (guide.lesson.caption,'body')):
                                        expected=label(role,wrap=True);reference_body.addWidget(expected)
                                        expected.setText(actual.text())
                                        reference.ensurePolished();expected.ensurePolished();actual.ensurePolished()
                                        self.assertEqual(actual.property('sd'),role)
                                        self.assertEqual(actual.styleSheet(),'')
                                        af,ef=actual.font(),expected.font()
                                        self.assertEqual((af.families(),af.pixelSize(),af.pointSizeF(),
                                                          af.weight(),af.letterSpacing()),
                                                         (ef.families(),ef.pixelSize(),ef.pointSizeF(),
                                                          ef.weight(),ef.letterSpacing()))
                                        self.assertEqual(actual.palette().color(QPalette.ColorRole.WindowText).rgba(),
                                                         expected.palette().color(QPalette.ColorRole.WindowText).rgba())
                                finally:reference.deleteLater()
                            self.assertFalse(original.grab().isNull())
                            self.assertTrue(original.annotations)
                            bounds=original.rect()
                            for box in original.annotation_boxes:
                                self.assertGreaterEqual(box.left(),bounds.left())
                                self.assertGreaterEqual(box.top(),bounds.top())
                                self.assertLessEqual(box.right(),bounds.right()+1)
                                self.assertLessEqual(box.bottom(),bounds.bottom()+1)
                            if ctx.language=='en':
                                self.assertFalse(re.search('[가-힣]',' '.join(' '.join(a.text) for a in original.annotations)))
                            self.assertEqual((guide.keys,guide.focus,guide.series,dict(guide.meta),guide.cursor),before)

    def _display_inputs(self):
        from core.education import catalog,indicators as I
        h=_fixed_history()
        ohlc=tuple((c-.02,c+.3,c-.3,c) for c in h.closes)
        volume=tuple(float(1000+i) for i in range(120))
        supply=I.Supply(tuple((d,float(i),float(-i),0.) for i,d in enumerate(h.dates)),
                        tuple((d,2.,20.) for d in h.dates))
        series=catalog.ObservedSeries(h.symbol,h.dates,h.closes,h.source,
            'price',ohlc,volume,'5m','domestic_stock',supply)
        values={}
        for spec in I.STUDIES:
            values[spec.key]={}
            for line_index,line in enumerate(spec.lines):
                if spec.bounds:
                    low,high=spec.bounds
                    seq=tuple(low+(high-low)*(.4+.1*math.sin(i/9+line_index)) for i in range(120))
                else:seq=tuple(c*(1+(line_index-1)*.004) for c in h.closes)
                values[spec.key][line.id]=tuple(math.nan if i<20 else v for i,v in enumerate(seq))
        return series,values

    def test_all_27_reference_anchors_match_original_svg_lines(self):
        from core.i18n import LocaleContext
        from core.theme import DARK,LIGHT
        from core.education import catalog,indicators as I
        from quantgen_desktop import guide_case_annotations as A
        series,values=self._display_inputs()
        def fixed_values(s,keys):
            self.assertIs(s,series)
            return {key:values[key] for key in keys}
        with patch.object(A,'values_for',side_effect=fixed_values), \
             patch.object(catalog,'values_for',side_effect=fixed_values):
            for spec in I.STUDIES:
                for language in ('ko','en'):
                    for width in (350,700):
                        for dark in (False,True):
                            with self.subTest(key=spec.key,language=language,width=width,dark=dark):
                                labels=A.case_annotations(series,(spec.key,),80,language,width=width,
                                                          legend_top=12,dark=dark)
                                bound=[a for a in labels if a.key==spec.key and a.value is not None]
                                self.assertTrue(bound)
                                svg=catalog.chart_svg(series,(spec.key,),locale=LocaleContext(language),
                                    colors=DARK if dark else LIGHT,width=width,legend=False)
                                nodes=list(ET.fromstring(svg).iter())
                                for a in bound:
                                    self.assertEqual(a.value,values[a.key][a.line_id][a.index])
                                    self.assertTrue(all(math.isfinite(v) for v in (a.value,a.x,a.y)))
                                    self.assertTrue(a.text)
                                    point=f'{a.x:.2f},{a.y:.2f}'
                                    path=any(n.tag.endswith('path') and n.attrib.get('stroke')==a.color and
                                             point in n.attrib.get('d','') for n in nodes)
                                    bar=any(n.tag.endswith('line') and n.attrib.get('stroke')==a.color and
                                            n.attrib.get('x2')==f'{a.x:.2f}' and
                                            n.attrib.get('y2')==f'{a.y:.2f}' for n in nodes)
                                    self.assertTrue(path or bar,('anchor is not on the original line',a))
                                    if language=='en':self.assertFalse(re.search('[가-힣]',' '.join(a.text)))

    def test_shifted_candle_anchors_use_actual_window_and_crop(self):
        from core.market.detail_svg import ChartLayout,PANEL_HEAD
        from quantgen_desktop import guide_case_annotations as A
        series,values=self._display_inputs()
        series=replace(series,snapshot=SimpleNamespace(candles=tuple(
            SimpleNamespace(open=o,high=h,low=l,close=c,volume=v)
            for (o,h,l,c),v in zip(series.ohlc,series.volume))))
        layout=ChartLayout(700,600,12,620,608/80,20,100,70,
            price=(58,360),volume=(310,360),panels=(('rsi',366,506),),axis_top=550,
            price_range=(8,20),price_scale=(58,350))
        crop=46
        seen=set()
        for focus in ('ema','rsi'):
            with patch.object(A,'values_for',side_effect=lambda s,keys:{k:values[k] for k in keys}):
                annotations=A.case_annotations(series,('ema','rsi'),70,'ko',width=700,legend_top=12,
                                               layout=layout,crop=crop,focus=focus)
            finite=[a for a in annotations if a.value is not None]
            self.assertTrue(finite)
            for a in finite:
                seen.add(a.key)
                self.assertLessEqual(layout.start,a.index);self.assertLess(a.index,layout.stop)
                self.assertAlmostEqual(a.x,layout.x_of(a.index))
                self.assertEqual(a.value,values[a.key][a.line_id][a.index])
                if a.key=='ema':self.assertAlmostEqual(a.y,layout.y_of_price(a.value)-crop)
                elif a.key=='rsi':
                    top=366+PANEL_HEAD;bottom=506-4
                    self.assertAlmostEqual(a.y,bottom-a.value/100*(bottom-top)-crop)
        self.assertEqual(seen,{'ema','rsi'})

    def test_absent_and_nonfinite_values_never_make_fake_anchor(self):
        from quantgen_desktop import guide_case_annotations as A
        series,values=self._display_inputs()
        with patch.object(A,'values_for',return_value={}):
            absent=A.case_annotations(series,('ema',),80,'en',width=700,legend_top=12)
        self.assertTrue(absent)
        self.assertTrue(all(a.value is None and a.x is None and a.y is None for a in absent))
        empty={'ema':{line:tuple(math.nan for _ in seq) for line,seq in values['ema'].items()}}
        with patch.object(A,'values_for',return_value=empty):
            unavailable=A.case_annotations(series,('ema',),80,'ko',width=700,legend_top=12)
        self.assertTrue(unavailable)
        self.assertTrue(all(a.value is None and a.x is None and a.y is None for a in unavailable))

    def test_annotations_preserve_original_input_and_avoid_advice(self):
        from quantgen_desktop import guide_case_annotations as A
        series,values=self._display_inputs()
        before=(series.dates,series.closes,series.ohlc,series.volume,series.supply)
        advisory=re.compile(r'매수\s*(추천|신호|타이밍)|매도\s*(추천|신호|타이밍)|매수하세요|매도하세요|'
                            r'buy signal|sell signal|buy now|sell now|guaranteed',re.I)
        for language in ('ko','en'):
            with patch.object(A,'values_for',side_effect=lambda s,keys:{k:values[k] for k in keys}):
                for key in values:
                    labels=A.case_annotations(series,(key,),80,language,width=350,legend_top=12)
                    self.assertFalse(advisory.search(' '.join(' '.join(a.text) for a in labels)))
        self.assertEqual((series.dates,series.closes,series.ohlc,series.volume,series.supply),before)


if __name__=='__main__':unittest.main()
