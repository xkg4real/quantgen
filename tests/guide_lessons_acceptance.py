"""Pure educational SVG contracts; no QApplication, observed data or model run.

PyQt6 is needed to import the native module; these tests belong after the native
runtime dependency step. The guarded UI capture/integration checks are separate.
"""
from contextlib import ExitStack
import importlib.util
import math
from pathlib import Path
import socket
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


@unittest.skipUnless(importlib.util.find_spec('PyQt6'), 'native Qt runtime required')
class GuideLessonContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stack=ExitStack();cls.addClassCleanup(cls.stack.close);cls.denied=[]
        def blocked(*a,**kw):
            cls.denied.append('external access');raise AssertionError('lesson tests forbid external access')
        fake=types.ModuleType('keyring')
        for name in ('get_password','set_password','delete_password','get_keyring','set_keyring'):setattr(fake,name,blocked)
        cls.stack.enter_context(patch.dict(sys.modules,{'keyring':fake}))
        folder=cls.stack.enter_context(tempfile.TemporaryDirectory(prefix='guide-lessons-contract-'))
        cls.stack.enter_context(patch.object(Path,'home',return_value=Path(folder)))
        cls.stack.enter_context(patch.object(socket,'has_ipv6',False))
        for name in ('connect','connect_ex','bind','listen'):
            cls.stack.enter_context(patch.object(socket.socket,name,side_effect=blocked))
        for name in ('create_connection','getaddrinfo','gethostbyname','gethostbyname_ex'):
            cls.stack.enter_context(patch.object(socket,name,side_effect=blocked))
        import dotenv
        cls.stack.enter_context(patch.object(dotenv,'load_dotenv',return_value=False))
        import requests
        cls.stack.enter_context(patch.object(requests.sessions.Session,'request',side_effect=blocked))
        # Definitions only, then blank config seams before the target/history
        # module import. No environment is copied, read or modified by the test.
        from core import credentials
        cls.stack.enter_context(patch.object(credentials,'_lookup',side_effect=blocked))
        cls.stack.enter_context(patch.object(credentials,'read_setting',return_value=''))
        cls.stack.enter_context(patch.object(credentials,'load_dotenv_for_development',return_value=None))
        from quantgen_desktop import guide_lessons
        from core.education.indicators import STUDIES
        cls.lesson=guide_lessons;cls.studies=STUDIES

    @classmethod
    def tearDownClass(cls):
        if cls.denied:raise AssertionError('unexpected external access in lesson contract tests')

    def test_all_27_registered_lines_have_finite_svg_points(self):
        L=self.lesson
        self.assertEqual(set(L.LESSONS),{s.key for s in self.studies})
        self.assertEqual(len(L.LESSONS),27)
        for spec in self.studies:
            with self.subTest(indicator=spec.key):
                svg,info=L.lesson_svg(spec.key,0,'ko',width=700)
                ET.fromstring(svg)
                bars,values=L.lesson_values(spec.key)
                self.assertEqual(tuple(values),tuple(line.id for line in spec.lines))
                for line in spec.lines:
                    points=info['paths'][line.id]
                    self.assertTrue(points)
                    self.assertEqual(len(points),sum(math.isfinite(float(v)) for v in values[line.id]))
                for anchor in info['anchors']:
                    value=float(values[anchor['line']][anchor['index']])
                    self.assertTrue(math.isfinite(value))
                    self.assertEqual(value,anchor['value'])
                    self.assertEqual(info['plot'].point(anchor['index'],value),anchor['point'])
                self.assertIn(bars.interval,('1d','5m'))

    def test_registered_domains_are_exact_without_clamping_unbounded_studies(self):
        L=self.lesson
        for spec in self.studies:
            with self.subTest(indicator=spec.key):
                _,info=L.lesson_svg(spec.key,1,'en',width=480)
                plot=info['plot']
                if spec.bounds:self.assertEqual((plot.low,plot.high),tuple(float(v) for v in spec.bounds))
                else:
                    _,values=L.lesson_values(spec.key)
                    finite=[float(v) for arr in values.values() for v in arr if math.isfinite(float(v))]
                    self.assertLess(plot.low,min(finite));self.assertGreater(plot.high,max(finite))
                if spec.key in ('cci','roc','percent_b'):self.assertFalse(info['registered_axis_bounds'])

    def test_ema_keeps_weighted_seed_and_recurrence(self):
        bars,values=self.lesson.lesson_values('ema')
        for span,name in ((12,'EMA12'),(26,'EMA26')):
            with self.subTest(span=span):
                seed=math.fsum(bars.close[:span])/span
                self.assertTrue(all(math.isnan(float(v)) for v in values[name][:span-1]))
                self.assertAlmostEqual(float(values[name][span-1]),seed,places=11)
                expected=seed+2/(span+1)*(bars.close[span]-seed)
                self.assertAlmostEqual(float(values[name][span]),expected,places=11)
                last_window_mean=math.fsum(bars.close[-span:])/span
                self.assertFalse(math.isclose(float(values[name][-1]),last_window_mean,rel_tol=1e-8))

    def test_nan_gap_is_separate_in_actual_svg_and_never_a_crossing(self):
        L=self.lesson;bars,values=L.lesson_values('sma')
        gapped=tuple(math.nan if i==80 else float(v) for i,v in enumerate(values['SMA20']))
        with patch.object(L,'lesson_values',return_value=(bars,{'SMA20':gapped})):
            svg,info=L.lesson_svg('sma',0,'en',width=700)
        color=L.study_colors('sma')['SMA20']
        paths=[n for n in ET.fromstring(svg).iter('{http://www.w3.org/2000/svg}path')
               if n.attrib.get('stroke')==color and n.attrib.get('stroke-width')=='2' and n.attrib.get('fill')=='none']
        self.assertEqual(len(paths),2)
        x,y=info['plot'].point(81,gapped[81])
        self.assertTrue(paths[1].attrib['d'].startswith(f'M {x:.3f} {y:.3f}'))
        self.assertIsNone(L.crossing((-1,math.nan,1),(0,0,0)))
        self.assertIsNone(L.crossing((-1,0,-1),(0,0,0)))
        self.assertEqual(L.crossing((-1,1),(0,0)),1)

    def test_teaching_only_interface_and_primary_ema_line_roles(self):
        L=self.lesson
        _,info=L.lesson_svg('ema',0,'ko',width=350)
        self.assertIn('더 빨리',info['anchors'][0]['label'])
        self.assertIn('천천히',info['anchors'][1]['label'])
        self.assertEqual(L.study('ema').line('EMA26').style,'dash')
        svg,_=L.lesson_svg('ema',1,'en',width=700)
        self.assertIn('stroke-dasharray="6 4"',svg)
        bars,values=L.lesson_values('ema')
        self.assertIsInstance(bars.close,tuple)
        self.assertTrue(all(not arr.flags.writeable for arr in values.values()))
        with self.assertRaises(TypeError):L.lesson_svg('ema',0,'ko',history=object())
        with self.assertRaises(TypeError):L.lesson_values('ema',object())


if __name__=='__main__':unittest.main()
