"""Owner UI port, FICC tools (owner screenshots 2026-11-10, issues 03, 04/12, 08, 11, 14).

Native Bonds, Rates, Structuring and FX panes: thousands separators in amount inputs, no data-source
selector (the automatic source is requested), all nine curve methods explained under the selector, no
English headings, columns or raw keys in the Korean window, the bond narrative as headed bullets, and
the export unchanged by any of it or by a language switch. Offline fixtures; no network.
"""
import json
import os
import re
import unittest
from copy import deepcopy
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    from quantgen_desktop.app import ResearchWindow
    from tests.desktop_acceptance import bond_fixture, rates_fixture, structuring_fixture
from PyQt6.QtCore import QEvent
from PyQt6.QtWidgets import QApplication, QComboBox, QLabel, QTableWidget
from core.ficc.curves import CURVE_METHODS, EXACT_METHODS, METHOD_NAMES
from core.research.bond_analysis import BondRequest
from core.research.rates_analysis import RatesRequest
from core.research.structuring_analysis import StructuringRequest
from core.research.tool_export import report_bytes
from core.ui_page_messages.rates import EN_TO_KO as FLET_RATES_KO
from quantgen_desktop.localization import CAPTION_ROLE
from quantgen_desktop.rates import KIND_TEXT, METHOD_TEXT
from tests.qt_fixture_cleanup import delete_owned_widget

HANGUL = re.compile(r'[가-힣]')


class OwnerUiFiccTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        for name in ('requests.sessions.Session.request', 'core.quant.gate_ledger.family_ledger'):
            guard = patch(name, side_effect=AssertionError('external I/O forbidden'))
            guard.start(); self.addCleanup(guard.stop)
        self.window = ResearchWindow(auto_refresh=False, language='ko')
        self.window.resize(1360, 900)
        self.window.show()
        self.addCleanup(self.dispose)
        self.settle()

    def dispose(self):
        self.window.hide()
        delete_owned_widget(self.window)
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def settle(self):
        for _ in range(8):
            self.app.processEvents()

    def language(self, code):
        self.window.set_language(code)
        self.settle()

    @staticmethod
    def column(table, index):
        return [table.item(row, index).text() for row in range(table.rowCount())]

    @staticmethod
    def headers(table):
        return [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]

    def heading_texts(self, pane):
        return [label.text() for label in pane.findChildren(QLabel)
                if label.property('role') == 'heading' and label.isVisibleTo(pane)]

    # ------------------------------------------------------------------ issue 03
    def test_amount_inputs_show_thousands_separators_and_requests_keep_the_number(self):
        w = self.window
        rates, structuring = w.rates, w.structuring
        for tool in ('swap', 'option'):
            self.assertEqual(rates.fields[tool]['notional'].text(), '1,000,000')
        self.assertEqual(rates.fields['sim']['n_paths'].text(), '5,000')
        for tool in ('ppn', 'rc', 'dcd', 'steep'):
            self.assertEqual(structuring.fields[tool]['notional'].text(), '1,000,000')
        self.assertEqual(structuring.fields['dcd']['spot'].text(), '1,350')
        self.assertEqual(structuring.fields['dcd']['strike'].text(), '1,300')
        rates.tool.setCurrentIndex(rates.tool.findData('swap'))
        field = rates.fields['swap']['notional']
        field.setText('2500000'); field.editingFinished.emit()
        self.assertEqual(field.text(), '2,500,000')
        self.assertEqual(rates.make_request().notional, 2_500_000.0)
        structuring.tool.setCurrentIndex(structuring.tool.findData('dcd'))
        request = structuring.make_request()
        self.assertEqual((request.notional, request.spot, request.strike), (1e6, 1350.0, 1300.0))
        # The DV01 input caption says what it is and that it is optional, in one line of Korean.
        caption = next(label for label in structuring.forms.widget(0).findChildren(QLabel)
                       if getattr(label, 'source_text', '') == 'Futures DV01 / contract · optional')
        self.assertEqual(caption.text(), '선물 계약당 DV01 · 선택 입력')

    def test_structuring_notional_reads_as_typed_and_export_keeps_its_own_text(self):
        pane = self.window.structuring
        out = structuring_fixture(StructuringRequest(source='synthetic'))
        pane.show_result(out); pane.bind_output('structuring', out)
        table = pane.tables['Metrics']
        self.assertEqual(table.item(6, 1).text(), '1,000,000 USD')
        exported = next(s for s in pane.report['sections'] if s.get('name') == 'Metrics')
        self.assertEqual(exported['rows'][6][1], '1,000,000.0000 USD')

    # -------------------------------------------------------------- issue 04/12
    def test_no_data_source_selector_and_requests_use_the_automatic_source(self):
        w = self.window
        for pane in (w.rates, w.fx, w.structuring):
            self.assertFalse(pane.source.isVisibleTo(pane))
            self.assertFalse(pane.source_label.isVisibleTo(pane))
            self.assertEqual(pane.source.currentData(), 'auto')
            self.assertGreaterEqual(pane.source.findData('synthetic'), 0)  # kept for fixtures
            request = pane.make_request(); request.validate()
            self.assertEqual(request.source, 'auto')
        self.assertFalse(w.bonds.source.isVisibleTo(w.bonds))
        self.assertEqual(w.bonds.source.currentData(), 'auto')
        sent = []
        w.bonds.requested.disconnect(w.run_bond); w.bonds.requested.connect(sent.append)
        try:
            w.bonds.submit()
        finally:
            w.bonds.requested.disconnect(sent.append); w.bonds.requested.connect(w.run_bond)
        self.assertEqual(sent[-1].source, 'auto')

    # ------------------------------------------------------------------ issue 08
    def test_every_curve_method_is_explained_in_the_window_language(self):
        pane = self.window.rates
        self.window.show_market_pane(pane)
        pane.tool.setCurrentIndex(pane.tool.findData('curve')); self.settle()
        method = pane.fields['curve']['method']
        self.assertEqual([method.itemData(i) for i in range(method.count())], list(CURVE_METHODS))
        self.assertEqual(len(CURVE_METHODS), 9)
        self.assertEqual(set(METHOD_TEXT), set(CURVE_METHODS))
        for index, key in enumerate(CURVE_METHODS):
            method.setCurrentIndex(index); self.settle()
            self.assertTrue(pane.method_info.isVisibleTo(pane))
            ko = FLET_RATES_KO[METHOD_TEXT[key]]           # the Flet page's reviewed Korean
            self.assertEqual(pane.method_text.text(), ko)
            self.assertEqual(pane.method_kind.text(), FLET_RATES_KO[KIND_TEXT[key in EXACT_METHODS]])
            self.assertTrue(HANGUL.search(pane.method_name.text()) or key not in ('bootstrap', 'cubic_spline'))
        self.language('en')                                   # the shown method follows the switch
        self.assertEqual(pane.method_text.text(), METHOD_TEXT[CURVE_METHODS[-1]])
        for index, key in enumerate(CURVE_METHODS):
            method.setCurrentIndex(index); self.settle()
            self.assertEqual(pane.method_text.text(), METHOD_TEXT[key])
            self.assertEqual(pane.method_name.text(), METHOD_NAMES[key])
            self.assertEqual(pane.method_kind.text(), KIND_TEXT[key in EXACT_METHODS])
        self.language('ko')
        self.assertEqual(pane.method_text.text(), FLET_RATES_KO[METHOD_TEXT[CURVE_METHODS[-1]]])
        pane.tool.setCurrentIndex(pane.tool.findData('swap')); self.settle()
        self.assertFalse(pane.method_info.isVisibleTo(pane))
        pane.tool.setCurrentIndex(pane.tool.findData('curve')); self.settle()
        self.assertTrue(pane.method_info.isVisibleTo(pane))
        # The selected method is what the request carries.
        method.setCurrentIndex(method.findData('smith_wilson'))
        self.assertEqual(pane.make_request().method, 'smith_wilson')

    # ------------------------------------------------------------------ issue 14
    def test_rates_curve_result_reads_korean_and_english_and_export_is_unchanged(self):
        pane = self.window.rates
        self.window.show_market_pane(pane)
        out = rates_fixture(RatesRequest(source='synthetic'))
        pane.show_result(out); pane.bind_output('rates', out); self.settle()
        report, exported = deepcopy(pane.report), report_bytes(pane.report)
        metrics, curve, pca = pane.tables['Metrics'], pane.tables['Curve table'], pane.tables['PCA variance']
        self.assertEqual(pane.input_box.findChild(QLabel).text(), '금리 · 수익률 곡선과 금리 위험')
        for heading in ('만기별 금리표', 'PCA 요인 적재값', 'PCA 설명 분산', '주요 지표'):
            self.assertIn(heading, self.heading_texts(pane))
        self.assertEqual(self.headers(curve)[1:5], ['무이표 금리', '할인계수', '파 금리', '1년 선도금리'])
        self.assertEqual(self.headers(curve)[5], '최근 20거래일 변화')
        self.assertEqual(self.headers(pca), ['PCA 요인', '설명 비율', '최근 점수'])
        self.assertEqual(self.column(pca, 0), ['수준', '기울기', '곡률'])
        names = self.column(metrics, 0)
        for caption in ('곡선 형태', '최근 20거래일 곡선 변화', '변화 비교 기간 · 거래일',
                        '2s5s10s 버터플라이', '금리 수준 (2·5·10년 평균)'):
            self.assertIn(caption, names)
        values = dict(zip(names, self.column(metrics, 1)))
        self.assertEqual(values['곡선 형태'], '역전')
        self.assertEqual(values['최근 20거래일 곡선 변화'], '평행 하락')
        for raw in ('Shape', 'Regime', 'Lookback', 'level', '2s5s10s_fly', '1y_fwd_1y_ahead'):
            self.assertNotIn(raw, names)
        chart = pane.charts['수익률 곡선']
        self.assertEqual(chart._legend_names(), ['무이표 금리', '파 금리'])
        self.assertEqual(pane.charts['PCA loadings']._legend_names(), ['수준', '기울기', '곡률'])
        # The rows given to the export keep their own words.
        rows = next(s for s in report['sections'] if s.get('name') == 'Metrics')['rows']
        self.assertEqual([r[0] for r in rows[:2]], ['Shape', 'Regime'])
        self.assertIn('2s5s10s_fly', [r[0] for r in rows])
        self.language('en')
        self.assertEqual(pane.input_box.findChild(QLabel).text(), 'Rates · yield curve and rate risk')
        names = self.column(metrics, 0)
        self.assertIn('Curve shape', names); self.assertIn('Level (2/5/10y)', names)
        self.assertEqual(dict(zip(names, self.column(metrics, 1)))['Curve shape'], 'Inverted curve')
        self.assertEqual(self.headers(curve)[1], 'Zero')
        self.assertEqual(self.column(pca, 0), ['level', 'slope', 'curvature'])
        for table in pane.findChildren(QTableWidget):
            for text in self.headers(table) + [table.item(r, c).text() for r in range(table.rowCount())
                                               for c in range(table.columnCount()) if table.item(r, c)]:
                self.assertIsNone(HANGUL.search(text), text)
        self.assertEqual(pane.report, report)
        self.assertEqual(report_bytes(pane.report), exported)

    def test_rates_other_tools_show_no_raw_codes_in_korean(self):
        pane = self.window.rates
        cases = [(RatesRequest(tool='swap', source='synthetic'), {'스왑': '10y 고정금리 지급 스왑'}),
                 (RatesRequest(tool='option', source='synthetic'), {'상품': '스왑션'}),
                 (RatesRequest(tool='option', kind='cap', source='synthetic'), {'상품': '캡'}),
                 (RatesRequest(tool='sim', source='synthetic', horizon=.25, n_paths=100, threshold=.05),
                  {'모델': 'Vasicek'})]
        for request, expected in cases:
            with self.subTest(tool=request.tool, kind=request.kind):
                out = rates_fixture(request)
                pane.show_result(out); pane.bind_output('rates', out); self.settle()
                before = json.dumps(pane.report, sort_keys=True, default=str)
                metrics = pane.tables['Metrics']
                values = dict(zip(self.column(metrics, 0), self.column(metrics, 1)))
                for name, value in expected.items():
                    self.assertEqual(values[name], value)
                if request.kind == 'cap':
                    self.assertEqual(self.headers(pane.tables['Caplets'])[2], '선도금리')
                for raw in ('Fixed', 'Forward', 'Theta', 'Sigma', 'Kappa · /year', 'Initial rate'):
                    self.assertNotIn(raw, values)
                self.language('en'); self.language('ko')
                self.assertEqual(json.dumps(pane.report, sort_keys=True, default=str), before)
        combos = {k: [pane.fields[t][k].itemText(i) for i in range(pane.fields[t][k].count())]
                  for t, k in (('option', 'kind'), ('sim', 'instrument'))}
        self.assertEqual(combos['kind'], ['스왑션', '캡', '플로어'])
        self.assertEqual(combos['instrument'], ['없음', '채권', '고정금리 지급 스왑'])
        self.assertEqual([pane.fields['option']['kind'].itemData(i) for i in range(3)], ['swaption', 'cap', 'floor'])

    def test_black_volatility_caption_follows_the_model_in_a_korean_window(self):
        pane = self.window.rates
        pane.tool.setCurrentIndex(pane.tool.findData('option'))
        pane.fields['option']['option_model'].setCurrentIndex(1); self.settle()
        captions = [label.text() for label in pane.forms.widget(2).findChildren(QLabel)]
        self.assertIn('Black 변동성 · %', captions)
        self.assertEqual(pane.fields['option']['vol'].text(), '30')

    def test_structuring_result_reads_korean(self):
        pane = self.window.structuring
        for tool in ('ppn', 'rc', 'dcd', 'steep'):
            with self.subTest(tool=tool):
                out = structuring_fixture(StructuringRequest(tool=tool, source='synthetic'))
                pane.show_result(out); pane.bind_output('structuring', out); self.settle()
                report = deepcopy(pane.report)
                headings = self.heading_texts(pane)
                for heading in ('민감도 (그릭스)', '만기 손익', '구성요소 분해', '헤지표'):
                    self.assertIn(heading, headings)
                kinds = self.column(pane.tables['Leg decomposition'], 1)
                self.assertTrue(all(HANGUL.search(kind) for kind in kinds), kinds)
                self.assertEqual(pane.charts['Maturity payoff']._legend_names(), ['만기 지급액'])
                legs = next(s for s in report['sections'] if s.get('name') == 'Leg decomposition')
                self.assertEqual([r[1] for r in legs['rows']], [leg.kind for leg in out.report.legs])
                self.language('en')
                self.assertEqual(self.column(pane.tables['Leg decomposition'], 1), [l.kind for l in out.report.legs])
                self.assertIn('Greeks', self.heading_texts(pane))
                self.language('ko')
                self.assertEqual(pane.report, report)
        self.assertEqual(pane.input_box.findChild(QLabel).text(), '구조화 상품 · 상품 구조·만기 손익·위험')

    def test_bond_narrative_is_headed_bullets_and_values_are_language_neutral(self):
        pane = self.window.bonds
        self.window.show_market_pane(pane)
        out = bond_fixture(BondRequest(source='synthetic'))
        pane.show_result(out); self.settle()
        report, raw = deepcopy(pane.exports.report), pane.notes.source_text
        values = self.column(pane.metrics, 1)
        self.assertNotIn('years', ' '.join(values)); self.assertNotIn('currency', ' '.join(values))
        names = self.column(pane.metrics, 0)
        self.assertIn('DV01 (금리 1bp당 통화 금액)', names)
        self.assertIn('캐리 · 0.25년', names)
        self.assertEqual(self.headers(pane.krd), ['기준 만기 · 년', 'DV01 · 1bp당 통화 금액'])
        text = pane.notes.text()
        self.assertIn('\n\n요약\n', text); self.assertIn('\n\n핵심 수치\n• ', text)
        self.assertIn('합성 곡선', text)
        # The curve repeats the panel's note: shown once, in Korean (source_notes, owner issue 14).
        from quantgen_desktop.source_notes import note_korean
        self.assertEqual(text.count(note_korean(out.panel.note)), 1)
        self.assertNotIn('no market data provider', text)
        hint = next(label for label in pane.findChildren(QLabel) if getattr(label, 'source_text', '')
                    .startswith('Enter either price or yield'))
        self.assertNotIn('Price', hint.text()); self.assertNotIn('Yield', hint.text())
        self.language('en')
        self.assertIn('\n\nSummary\n', pane.notes.text()); self.assertIn('\n\nKey figures\n• ', pane.notes.text())
        self.assertEqual(self.column(pane.metrics, 1), values)
        self.assertIn('DV01 · currency per bp', self.column(pane.metrics, 0))
        self.assertEqual(pane.exports.report, report)
        self.assertEqual(pane.notes.source_text, raw)
        self.assertIn(out.narrative, raw)                       # the export text is the paragraph
        out = bond_fixture(BondRequest(source='synthetic', tool='scenarios'))
        self.language('ko'); pane.show_result(out); self.settle()
        scenarios = self.column(pane.scenarios, 0)
        self.assertIn('+25bp 평행 이동', scenarios); self.assertIn('2년-5년-10년 버터플라이', scenarios)
        self.assertEqual(pane.scenarios.item(0, 0).data(CAPTION_ROLE), out.scenarios[0].name)

    def test_fx_typed_rates_note_has_no_english_word_in_korean(self):
        from core.research.fx_analysis import FXRequest
        from tests.desktop_acceptance import fx_fixture
        pane = self.window.fx
        out = fx_fixture(FXRequest(source='synthetic'))
        pane.show_result(out); pane.bind_output('fx', out); self.settle()
        note = next(l for l in pane.findChildren(QLabel) if getattr(l, 'source_text', '').startswith('Flat rates'))
        self.assertEqual(note.text(), '모든 만기에 동일 금리 적용 · 직접 입력한 금리: 없음')
        self.assertEqual(pane.input_box.findChild(QLabel).text(), '외환 · 현물·선물환·옵션·캐리')
        self.language('en')
        self.assertEqual(note.text(), 'Flat rates across tenors · typed rates: none')
        self.assertIn({'type': 'text', 'text': 'Flat rates across tenors · typed rates: none'}, pane.sections)

    def test_combo_items_and_visible_captions_stay_english_in_an_english_window(self):
        self.language('en')
        for pane in (self.window.rates, self.window.structuring, self.window.fx, self.window.bonds):
            for widget in pane.findChildren(QLabel) + pane.findChildren(QComboBox):
                texts = [widget.text()] if isinstance(widget, QLabel) else \
                    [widget.itemText(i) for i in range(widget.count())]
                for text in texts:
                    self.assertIsNone(HANGUL.search(text), text)


if __name__ == '__main__':
    unittest.main()
