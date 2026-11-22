"""Original-case-first and compact visual legend contracts on offline inputs.

Actual SVG renderers supply the independent stroke oracle. Explicit immutable
values bypass calculation; neither a provider nor an indicator engine runs.
"""
from contextlib import contextmanager
from dataclasses import FrozenInstanceError, replace
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
        from PyQt6.QtWidgets import QApplication
        from quantgen_desktop.font_policy import configure_interface_font, INTERFACE_FAMILY
        cls.app=QApplication.instance() or QApplication(['guide-case-contract','-platform','offscreen'])
        previous_font=cls.app.font()
        cls.addClassCleanup(cls.app.setFont,previous_font)
        family=configure_interface_font(cls.app,Path(__file__).resolve().parents[1]/'assets/fonts')
        if family!=INTERFACE_FAMILY:
            raise AssertionError('The production QG font bundle is required for guide layout contracts')

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
            self.assertTrue(original.legend_samples)
            self.assertEqual(tuple(s.line_id for s in original.legend_samples),('CLOSE',))
            self.assertEqual(original.legend_samples[0].style,'solid')
            self._assert_compact_legend(original)
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
                            self.assertTrue(original.legend_samples)
                            self._assert_compact_legend(original)
                            if ctx.language=='en':
                                self.assertFalse(re.search('[가-힣]',' '.join(a.label for a in original.legend_samples)))
                            self.assertEqual((guide.keys,guide.focus,guide.series,dict(guide.meta),guide.cursor),before)

    def _assert_compact_legend(self,chart):
        from PyQt6.QtCore import QRectF
        samples=chart.legend_samples
        plot=QRectF()
        left,top,right,bottom=chart._legend_panel(samples[0].key)
        plot.setCoords(left,top,right,bottom)
        self.assertTrue(plot.contains(chart.legend_rect))
        self.assertAlmostEqual(chart.legend_rect.right(),plot.right()-5)
        self.assertAlmostEqual(chart.legend_rect.bottom(),plot.bottom()-5)
        self.assertEqual(len(chart.legend_boxes),len(samples))
        for i,box in enumerate(chart.legend_boxes):
            self.assertTrue(chart.legend_rect.contains(box))
            for other in chart.legend_boxes[i+1:]:
                self.assertFalse(box.intersects(other))
        for sample in samples:
            # A legend identifies a stroke; it is not a callout to a date/value.
            self.assertFalse(hasattr(sample,'index'))
            self.assertFalse(hasattr(sample,'value'))
            self.assertFalse(re.search(r'실선|점선|solid line|dotted line|buy signal|sell signal',sample.label,re.I))

    def test_default_case_constructor_never_shows_a_temporary_window(self):
        from PyQt6.QtCore import QObject,QEvent,QCoreApplication
        from PyQt6.QtWidgets import QWidget

        class Observer(QObject):
            def __init__(self):
                super().__init__();self.windows=[]
            def eventFilter(self,watched,event):
                if event.type()==QEvent.Type.Show and isinstance(watched,QWidget) and watched.isWindow():
                    self.windows.append((type(watched).__name__,watched.objectName()))
                return False

        # The exact same fixed 120 closes seed both paths. The default constructor
        # really uses history=None; only its historical-case loader is replaced.
        with self._guide() as (seed,app):
            from quantgen_desktop import indicator_guide as guide_module
            supplied=('2020',seed.series,dict(seed.meta))
            observer=Observer();app.installEventFilter(observer)
            guide=None
            try:
                with patch.object(guide_module,'historical_case',return_value=supplied) as loader:
                    guide=guide_module.IndicatorGuide(history=None)
                    for _ in range(4):app.processEvents()
                    self.assertTrue(loader.called)
                    self.assertEqual(observer.windows,[])
                    self.assertTrue(guide.isHidden())
                    self.assertIsNone(guide.external)
                    self.assertIs(guide.case.parentWidget(),guide.selection_box)
                    self.assertFalse(guide.case.isWindow())
                    self.assertIs(guide.series,supplied[1])
                    self.assertEqual(guide.meta,supplied[2])
                app.removeEventFilter(observer)
                guide.resize(1000,800);guide.show()
                for _ in range(4):app.processEvents()
                self.assertTrue(guide.case.isVisible())
            finally:
                app.removeEventFilter(observer)
                if guide is not None:
                    guide.close();guide.deleteLater()
                    QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete.value)
                    app.processEvents()

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

    def test_all_27_reference_samples_match_original_svg_strokes(self):
        from core.i18n import LocaleContext
        from core.theme import DARK,LIGHT
        from core.education import catalog,indicators as I
        from quantgen_desktop import guide_case_annotations as A
        series,values=self._display_inputs()
        def fixed_values(s,keys):
            self.assertIs(s.dates,series.dates)
            self.assertIs(s.closes,series.closes)
            return {key:values[key] for key in keys}
        with patch.object(catalog,'values_for',side_effect=fixed_values):
            self.assertEqual(len(I.STUDIES),27)
            for spec in I.STUDIES:
                display=replace(series,interval='1d') if spec.needs in ('kis_flows','kis_shorts') else series
                for language in ('ko','en'):
                    for width in (350,700):
                        for dark in (False,True):
                            with self.subTest(key=spec.key,language=language,width=width,dark=dark):
                                samples=A.line_legend(display,(spec.key,),language,dark=dark)
                                self.assertEqual(tuple(s.line_id for s in samples),tuple(l.id for l in spec.lines))
                                svg=catalog.chart_svg(display,(spec.key,),locale=LocaleContext(language),
                                    colors=DARK if dark else LIGHT,width=width,legend=False)
                                nodes=list(ET.fromstring(svg).iter())
                                # The reference chart draws the base price first,
                                # then registry lines in order. Siblings can share
                                # a colour, so colour alone cannot identify a line.
                                paths=[n for n in nodes if n.tag.endswith('path') and
                                       n.attrib.get('stroke-width')=='1.6']
                                self.assertEqual(len(paths),1+sum(l.style!='bars' for l in spec.lines))
                                study_paths=iter(paths[1:])
                                for sample,line in zip(samples,spec.lines):
                                    bars=[n for n in nodes if n.tag.endswith('line')
                                          and n.attrib.get('stroke')==sample.color
                                          and n.attrib.get('stroke-width')=='2']
                                    if line.style=='bars':
                                        self.assertTrue(bars)
                                        self.assertEqual(sample.style,'bars')
                                        self.assertEqual(sample.dash,())
                                    else:
                                        # The reference renderer actually draws SAR dots
                                        # as a solid path; its visible stroke is the oracle.
                                        actual=next(study_paths)
                                        self.assertEqual(actual.attrib.get('stroke'),sample.color)
                                        dash=actual.attrib.get('stroke-dasharray','')
                                        self.assertEqual(sample.dash,tuple(float(x) for x in dash.split()))
                                        self.assertEqual(sample.style,'dash' if dash else 'solid')
                                    self.assertTrue(sample.label)
                                    if language=='en':self.assertFalse(re.search('[가-힣]',sample.label))

    def test_all_27_candle_samples_match_actual_markers_bars_and_fills(self):
        from core.education import indicators as I
        from core.market.detail_svg import CANDLES,render
        from quantgen_desktop import guide_case_annotations as A
        series,values=self._display_inputs()
        candles=tuple(SimpleNamespace(timestamp=d,open=o,high=h,low=l,close=c,volume=v)
            for d,(o,h,l,c),v in zip(series.dates,series.ohlc,series.volume))
        for spec in I.STUDIES:
            display=replace(series,interval='1d') if spec.needs in ('kis_flows','kis_shorts') else series
            snapshot=SimpleNamespace(candles=candles,request=SimpleNamespace(interval=display.interval,
                instrument=SimpleNamespace(asset='domestic_stock')))
            for dark in (False,True):
                with self.subTest(key=spec.key,dark=dark):
                    svg,_=render(snapshot,studies=(spec.key,),width=700,height=600,
                        dark=dark,supply=series.supply,values={spec.key:values[spec.key]})
                    nodes=list(ET.fromstring(svg).iter())
                    for language in ('ko','en'):
                        samples=A.line_legend(display,(spec.key,),language,dark=dark,renderer='candles')
                        self.assertEqual(tuple(s.line_id for s in samples[:len(spec.lines)]),
                                         tuple(l.id for l in spec.lines))
                        for sample,line in zip(samples,spec.lines):
                            self.assertEqual(sample.style,line.style)
                            if line.style=='bars':
                                self.assertEqual((sample.color,sample.secondary_color),CANDLES[dark])
                                self.assertEqual(sample.opacity,.55)
                                self.assertTrue(any(n.tag.endswith('rect') and
                                    n.attrib.get('fill') in CANDLES[dark] and
                                    n.attrib.get('fill-opacity')=='0.55' for n in nodes))
                            elif line.style=='dots':
                                self.assertTrue(any(n.tag.endswith('circle') and
                                    n.attrib.get('fill')==sample.color for n in nodes))
                            else:
                                paths=[n for n in nodes if n.tag.endswith('polyline') and
                                       n.attrib.get('stroke')==sample.color]
                                self.assertTrue(paths)
                                expected='5 4' if sample.style=='dash' else ''
                                self.assertTrue(any(n.attrib.get('stroke-dasharray','')==expected for n in paths))
                                self.assertEqual(sample.dash,tuple(float(x) for x in expected.split()))
                        for sample in samples[len(spec.lines):]:
                            self.assertEqual(sample.style,'band')
                            self.assertIn(sample.line_id,('BAND','CLOUD'))
                            self.assertTrue(any(n.attrib.get('fill') in (sample.color,sample.secondary_color) and
                                n.attrib.get('fill-opacity')==str(sample.opacity) for n in nodes))
                            self.assertEqual(sample.opacity,.07 if sample.line_id=='BAND' else .13)
                    self.assertEqual(len(samples),len(spec.lines)+(spec.key in ('bb','ichimoku')))

    def test_missing_study_never_makes_fake_samples_or_mutates_inputs(self):
        from core.education import indicators as I
        from quantgen_desktop import guide_case_annotations as A
        series,values=self._display_inputs()
        before=(series.dates,series.closes,series.ohlc,series.volume,series.supply)
        for renderer in ('reference','candles'):
            self.assertEqual(A.line_legend(None,(),renderer=renderer),())
            self.assertEqual(A.line_legend(replace(series,closes=()),(),renderer=renderer),())
            self.assertEqual(A.line_legend(series,('ema',),unavailable=('ema',),renderer=renderer),())
            self.assertEqual(A.line_legend(replace(series,ohlc=()),('atr',),renderer=renderer),())
            for language in ('ko','en'):
                for spec in I.STUDIES:
                    display=replace(series,interval='1d') if spec.needs in ('kis_flows','kis_shorts') else series
                    samples=A.line_legend(display,(spec.key,),language,renderer=renderer)
                    self.assertTrue(samples)
                    for sample in samples:
                        self.assertFalse(hasattr(sample,'value'))
                        self.assertFalse(hasattr(sample,'index'))
                        self.assertFalse(re.search(r'매수\s*(추천|신호|타이밍)|매도\s*(추천|신호|타이밍)|'
                            r'매수하세요|매도하세요|buy signal|sell signal|buy now|sell now|guaranteed',sample.label,re.I))
                    with self.assertRaises(FrozenInstanceError):samples[0].color='#000000'
        self.assertEqual((series.dates,series.closes,series.ohlc,series.volume,series.supply),before)

    def test_compact_legend_geometry_stays_bottom_right_without_collisions(self):
        from core.education import indicators as I
        from quantgen_desktop import guide_case_annotations as A
        series,_values=self._display_inputs()
        for width in (350,700):
            for language in ('ko','en'):
                for dark in (False,True):
                    for spec in I.STUDIES:
                        display=replace(series,interval='1d') if spec.needs in ('kis_flows','kis_shorts') else series
                        for renderer in ('reference','candles'):
                            with self.subTest(width=width,language=language,key=spec.key,renderer=renderer):
                                samples=A.line_legend(display,(spec.key,),language,dark=dark,renderer=renderer)
                                # Deliberately use a lower-panel height as well as a
                                # narrow width: all original line identities must fit.
                                panel=(18.,34.,float(width-100),126.)
                                measure=lambda label:len(label)*6.
                                box,rows=A.legend_layout(samples,panel,measure)
                                self.assertIsNotNone(box)
                                self.assertEqual(tuple(s for s,_w,_l in rows),samples)
                                x,y,w,h=box
                                self.assertAlmostEqual(x+w,panel[2]-5)
                                self.assertAlmostEqual(y+h,panel[3]-5)
                                self.assertGreaterEqual(x,panel[0]+5)
                                self.assertGreaterEqual(y,panel[1]+5)
                                self.assertLessEqual(w,panel[2]-panel[0]-10)
                                rects=[]
                                for sample,swatch,label in rows:
                                    self.assertGreaterEqual(swatch[2],28)
                                    self.assertGreaterEqual(label[2],measure(sample.label))
                                    self.assertGreaterEqual(label[0],swatch[0]+swatch[2]+8)
                                    row=(swatch[0],swatch[1],label[0]+label[2],label[1]+label[3])
                                    for previous in rects:
                                        self.assertTrue(row[2]<=previous[0] or previous[2]<=row[0] or
                                                        row[3]<=previous[1] or previous[3]<=row[1])
                                    rects.append(row)
        self.assertEqual(A.legend_layout(samples,(0,0,50,20),lambda _:100),(None,()))
        self.assertEqual(A.legend_layout((),(0,0,350,200),lambda _:10),(None,()))


if __name__=='__main__':unittest.main()
