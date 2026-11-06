"""Approved A1 display terms; synthetic results keep their canonical evidence."""
from copy import deepcopy
from dataclasses import replace
import unittest
from unittest.mock import patch

import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from quantgen_desktop.app import ResearchWindow, label
    from quantgen_desktop.commentary import commentary_payload
    from tests.desktop_acceptance import bond_fixture
from PyQt6.QtWidgets import QApplication
from core.i18n import LocaleContext
from core.research.bond_analysis import BondRequest
from core.research.tool_export import report_bytes


class A1TermsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        deny=patch('requests.sessions.Session.request',side_effect=AssertionError('network forbidden'))
        deny.start();self.addCleanup(deny.stop)

    def window(self):
        window=ResearchWindow(auto_refresh=False,language='en')
        self.addCleanup(window.deleteLater)
        return window

    def test_approved_captions_round_trip_from_their_original_sources(self):
        window=self.window()
        pairs=(
            ('Build & Test','설계/검증'),('Portfolio & Risk','분석'),
            ('Signals','기술적 분석'),('Paper Trading','모의투자'),
            ('Metric','항목'),('Field','항목'),('Metrics','주요 지표'),
            ('Sharpe','샤프 지수'),('Convexity','컨벡시티'),
            ('Macaulay duration','맥컬리 듀레이션'),('Zero rate','무이표 금리'),
            ('Provider','제공처'),('Monte Carlo','몬테카를로'),
            ('Horizon · sessions','분석 기간(거래일)'),('Sessions','거래일 수'),
            ('Macro sheet','매크로 지표'),('Macro v2','매크로 v2'),
        )
        captions=[]
        for english,korean in pairs:
            widget=label(english);window.fx.result_layout.addWidget(widget)
            captions.append((widget,english,korean))
        with patch.object(window.jobs,'start',side_effect=AssertionError('translation must not start work')):
            for language in ('en','ko','en'):
                window.set_language(language);self.app.processEvents()
                for widget,english,korean in captions:
                    with self.subTest(language=language,source=english):
                        # The existing English tool-menu alias is "Macro";
                        # A1 changes its Korean caption, not that English name.
                        shown_english='Macro' if english=='Macro sheet' else english
                        self.assertEqual(widget.text(),korean if language=='ko' else shown_english)
                        self.assertEqual(widget.source_text,english)
        # Metric and Field share a Korean caption, but must restore their own English source.
        self.assertNotEqual(captions[4][0].text(),captions[5][0].text())

    def test_existing_korean_chrome_sources_use_the_approved_aliases(self):
        window=self.window()
        aliases=(
            ('설계 및 검증','Build & Test','설계/검증'),
            ('설계·검증','Build & Test','설계/검증'),
            ('포트폴리오 및 위험','Portfolio & Risk','분석'),
            ('포트폴리오·위험','Portfolio & Risk','분석'),
            ('신호','Signals','기술적 분석'),('모의매매','Paper Trading','모의투자'),
            ('측정 항목','Metric','항목'),('측정값','Metrics','주요 지표'),
            ('공급자','Provider','제공처'),('공급처','Provider','제공처'),
            ('거시 지표표','Macro sheet','매크로 지표'),
        )
        captions=[]
        for source,english,korean in aliases:
            widget=label(source);window.fx.result_layout.addWidget(widget)
            captions.append((widget,source,english,korean))
        for language in ('ko','en','ko'):
            window.set_language(language);self.app.processEvents()
            for widget,source,english,korean in captions:
                with self.subTest(language=language,source=source):
                    self.assertEqual(widget.text(),korean if language=='ko' else english)
                    self.assertEqual(widget.source_text,source)

    def test_shared_catalog_keeps_the_same_terms_for_the_named_flet_headers(self):
        context=LocaleContext('ko_KR')
        for key,value in (('build','설계/검증'),('risk','분석'),
                          ('signals','기술적 분석'),('provider','제공처')):
            with self.subTest(key=key):self.assertEqual(context.t(key),value)
        for english,korean in (('Metric','항목'),('Field','항목'),('Metrics','주요 지표'),
                               ('Provider','제공처'),('Paper Trading','모의투자'),
                               ('Macro sheet','매크로 지표'),('Macro v2','매크로 v2')):
            with self.subTest(caption=english):self.assertEqual(context.text(english),korean)
        self.assertEqual(context.text('지표'),'지표')
        self.assertEqual(LocaleContext('en_US').text('지표'),'Indicator')

    def test_authored_provider_and_zero_rate_templates_keep_their_context_and_sources(self):
        window=self.window()
        source='95% of principal at 5y, DF 0.91 (zero 3.25%)'
        unknown='FRED original wording: Zero · stress and Provider remain quoted, value 17.50.'
        examples=(
            ('Provider: FRED','제공처: FRED','Provider: FRED'),
            ('공급자: FRED','제공처: FRED','Provider: FRED'),
            ('Zero · stress','0 · 스트레스 가정','Zero · stress'),
            ('Zero-rate reference','금리 0 비교 기준','Zero-rate reference'),
            (source,'5y에 원금의 95%, DF 0.91 (무이표 금리 3.25%)',source),
            (unknown,unknown,unknown),
        )
        captions=[]
        for raw,korean,english in examples:
            widget=label(raw);window.fx.result_layout.addWidget(widget)
            captions.append((widget,raw,korean,english))
        for language in ('ko','en','ko'):
            window.set_language(language);self.app.processEvents()
            for widget,raw,korean,english in captions:
                with self.subTest(language=language,source=raw):
                    self.assertEqual(widget.text(),korean if language=='ko' else english)
                    self.assertEqual(widget.source_text,raw)

    def test_model_labels_and_bond_terms_do_not_change_requests_reports_or_ai_payloads(self):
        window=self.window()
        method=window.rates.fields['curve']['method']
        method.setCurrentIndex(method.findData('nelson_siegel'))
        window.rates.tool.setCurrentIndex(window.rates.tool.findData('sim'))
        model=window.rates.fields['sim']['model']
        model.setCurrentIndex(model.findData('hull_white'))
        request=window.rates.make_request()
        item_data={name:[combo.itemData(i) for i in range(combo.count())]
                   for name,combo in (('method',method),('model',model))}
        raw='ISSUER source: Provider 17.50; 샤프비율 is original wording.'
        output=replace(bond_fixture(BondRequest(source='synthetic')),narrative=raw)
        window.bonds.show_result(output)
        report=deepcopy(window.bonds.exports.report)
        original=window.bonds.notes.source_text
        export=report_bytes(report)
        payload=commentary_payload(report)
        values=[window.bonds.metrics.item(i,1).text() for i in range(window.bonds.metrics.rowCount())]
        with patch.object(window.jobs,'start',side_effect=AssertionError('translation must not recalculate')):
            for language in ('ko','en','ko'):
                window.set_language(language);self.app.processEvents()
                self.assertEqual(window.rates.make_request(),request)
                self.assertEqual(method.currentData(),'nelson_siegel')
                self.assertEqual(model.currentData(),'hull_white')
                for name,combo in (('method',method),('model',model)):
                    self.assertEqual([combo.itemData(i) for i in range(combo.count())],item_data[name])
                if language=='ko':
                    self.assertEqual(method.currentText(),'Nelson-Siegel')
                    self.assertEqual(model.currentText(),'Hull-White')
                    names=[window.bonds.metrics.item(i,0).text() for i in range(window.bonds.metrics.rowCount())]
                    self.assertIn('맥컬리 듀레이션',names);self.assertIn('컨벡시티',names)
                self.assertIn(raw,window.bonds.notes.text())
                self.assertEqual(window.bonds.notes.source_text,original)
                self.assertEqual(window.bonds.exports.report,report)
                self.assertEqual(report_bytes(window.bonds.exports.report),export)
                self.assertEqual(commentary_payload(window.bonds.exports.report),payload)
                self.assertEqual(window.bonds.exports.report['verdict'],'NOT_RUN')
                self.assertEqual([window.bonds.metrics.item(i,1).text() for i in range(window.bonds.metrics.rowCount())],values)


if __name__=='__main__':unittest.main()
