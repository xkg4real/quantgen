"""Owner UI review 2026-11-10, area E: the Structuring, FX, Bonds, Derivatives, ETF,
Crypto and KRX pages read as Korean financial screens.

* Large numbers show thousands separators (1,000,000) and are read back exactly.
* Data-source selectors are hidden; the control still exists and keeps a value
  that is one of its options (the app chooses the provider itself).
* No `expand` child inside a wrapping row (Flutter paints a grey box instead).
* The page chrome is Korean in ko_KR and returns to English in en_US.

Offline: synthetic curves and histories, inert charts, no provider or AI call.
"""
from contextlib import ExitStack
import os
import re
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    import flet as ft
    from core.ficc.common import FICCError
    from core.ficc.data import synthetic_curve_panel
    from core.i18n import LocaleContext
    from core.quant.history import synthetic_history
    from ui import (bonds_page, crypto_page, derivatives_page, etf_page, fx_page, krx_page,
                    structuring_page)
    from ui.components import group_digits, parse_number
    from ui.localization import translate_controls

HANGUL = re.compile(r'[가-힣]')
KO, EN = LocaleContext('ko_KR'), LocaleContext('en_US')


def walk(control, seen=None):
    seen = set() if seen is None else seen
    if not isinstance(control, ft.Control) or id(control) in seen:
        return
    seen.add(id(control))
    yield control
    for name in ('controls', 'content', 'title', 'subtitle', 'actions', 'leading', 'trailing',
                 'label', 'rows', 'cells', 'columns', 'tabs', 'options'):
        value = getattr(control, name, None)
        if isinstance(value, (list, tuple)):
            for child in value:
                yield from walk(child, seen)
        else:
            yield from walk(value, seen)


def page():
    return SimpleNamespace(qg_locale=LocaleContext('en_US'), update=lambda: None,
                           run_thread=lambda fn: fn())


def gateway():
    g = Mock()
    g.status.return_value = [{'provider': 'KIS', 'ready': False, 'reason': 'Offline fixture'}]
    return g


BUILDERS = {
    'structuring': lambda: structuring_page.build_structuring_page(page()),
    'fx': lambda: fx_page.build_fx_page(page()),
    'bonds': lambda: bonds_page.build_bonds_page(page()),
    'derivatives': lambda: derivatives_page.build_derivatives_page(page()),
    'etf': lambda: etf_page.build_etf_page(page()),
    'crypto': lambda: crypto_page.build_crypto_page(page()),
    'krx': lambda: krx_page.build_krx_page(page(), gateway()),
}

# (page, selector label, value the hidden selector must keep)
SELECTORS = [('structuring', 'Curve source', 'auto'), ('fx', 'Data source', 'auto'),
             ('bonds', 'Curve source', 'auto'), ('etf', 'Source', 'auto'), ('crypto', 'Source', 'live')]


def field(root, label, cls=(ft.TextField, ft.Dropdown)):
    return next(c for c in walk(root) if isinstance(c, cls) and c.label == label)


def button(root, label):
    return next(c for c in walk(root) if isinstance(c, ft.Button) and c.content == label)


def texts(root):
    return [c.value for c in walk(root) if isinstance(c, ft.Text) and isinstance(c.value, str)]


class Offline(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch('requests.sessions.Session.request',
                                       side_effect=AssertionError('No provider API')))

    def capture(self, module):
        payloads = []

        def panel(_page, **kw):
            payloads.append(kw['payload_fn']())
            return ft.Text('Offline analysis fixture')
        self.stack.enter_context(patch.object(module, 'analysis_panel', side_effect=panel))
        return payloads

    def inert(self, charts, *names):
        for name in names:
            self.stack.enter_context(patch.object(charts, name, side_effect=lambda *a, **k: ft.Text('Chart')))


class GroupedNumbers(Offline):
    def test_helpers_round_trip(self):
        for typed, value, shown in (('1000000', 1e6, '1,000,000'), ('1,350', 1350.0, '1,350'),
                                    ('1.10', 1.1, '1.10'), ('-2500.5', -2500.5, '-2,500.5')):
            self.assertEqual(parse_number(typed), value)
            self.assertEqual(group_digits(typed), shown)
            self.assertEqual(parse_number(group_digits(typed)), value)
        for text in ('ATM', '25d', ''):
            self.assertEqual(group_digits(text), text)

    def test_structuring_defaults_are_grouped_and_priced_exactly(self):
        payloads = self.capture(structuring_page)
        self.inert(structuring_page.fcharts, 'payoff_chart')
        self.stack.enter_context(patch.object(structuring_page, 'load_treasury_curve',
                                              return_value=synthetic_curve_panel(days=30, seed=42)))
        root = structuring_page.build_structuring_page(page())
        notional = field(root, 'Notional')
        self.assertEqual(notional.value, '1,000,000')
        self.assertEqual(notional.text_align, ft.TextAlign.RIGHT)
        notional.value = '2,500,000'
        field(root, 'Futures DV01 / contract').value = '1,250'
        button(root, 'Price').on_click(None)
        self.assertEqual(payloads[-1]['notional'], 2_500_000.0)
        self.assertTrue(payloads[-1]['hedge'])
        product = field(root, 'Product')
        product.value = 'dcd'
        product.on_select(None)
        shown = {c.label: c.value for c in walk(root) if isinstance(c, ft.TextField) and c.visible}
        self.assertEqual((shown['Spot'], shown['Strike']), ('1,350', '1,300'))
        button(root, 'Price').on_click(None)
        self.assertEqual((payloads[-1]['spot'], payloads[-1]['strike']), (1350.0, 1300.0))

    def test_bonds_notional_and_position_dv01_accept_separators(self):
        payloads = self.capture(bonds_page)
        self.stack.enter_context(patch.object(bonds_page, 'load_treasury_curve',
                                              return_value=synthetic_curve_panel(days=30, seed=42)))
        root = bonds_page.build_bonds_page(page())
        self.assertEqual(field(root, 'Notional').value, '1,000,000')
        tool = field(root, 'Tool')
        tool.value = 'hedge'
        tool.on_select(None)
        self.assertTrue(field(root, 'Position DV01').visible)
        field(root, 'Notional').value = '2,000,000'
        field(root, 'Position DV01').value = '12,345'
        button(root, 'Run').on_click(None)
        self.assertEqual(payloads[-1]['bond']['notional'], 2_000_000.0)
        self.assertEqual(payloads[-1]['hedge']['position_dv01'], 12_345.0)

    def test_fx_strike_and_market_forward_accept_separators(self):
        self.assertEqual(fx_page._strike('1,300', 1350.0, 0.25, 0.03, 0.04, 0.1, True), 1300.0)
        root = fx_page.build_fx_page(page())
        forward = field(root, 'Market forward (optional)')
        forward.value = '1,350.25'
        self.assertEqual(fx_page._num(forward), 1350.25)
        self.assertEqual(field(root, 'Strike').value, 'ATM')

    def test_derivatives_paths_are_grouped_and_read_back(self):
        seen = {}

        def snapshot(**kw):
            seen.update(kw)
            raise FICCError('fixture stop')
        self.stack.enter_context(patch.object(derivatives_page, 'snapshot', side_effect=snapshot))
        root = derivatives_page.build_derivatives_page(page())
        paths = field(root, 'Paths')
        self.assertEqual(paths.value, '3,000')
        paths.value = '12,000'
        button(root, 'Load').on_click(None)
        self.assertEqual(seen['n_paths'], 12_000)
        self.assertIn('fixture stop', texts(root))


class HiddenSelectors(Offline):
    def test_source_selectors_are_hidden_with_a_valid_value(self):
        for name, label, value in SELECTORS:
            with self.subTest(page=name):
                dd = field(BUILDERS[name](), label, ft.Dropdown)
                self.assertFalse(dd.visible)
                self.assertEqual(dd.value, value)
                self.assertIn(dd.value, [o.key for o in dd.options])
        board = field(BUILDERS['derivatives'](), 'Board', ft.Dropdown)
        self.assertFalse(board.visible)
        self.assertIn(board.value, [o.key for o in board.options])

    def test_etf_auto_history_asks_best_and_explicit_sources_pass_through(self):
        calls = []

        def history(symbol, *, source, days):
            calls.append(source)
            return synthetic_history(symbol, days=days)
        self.stack.enter_context(patch.object(etf_page, 'load_history', side_effect=history))
        self.stack.enter_context(patch.object(etf_page, 'load_cards', return_value=()))
        with patch.object(etf_page.config, 'kis_ready', return_value=False):
            etf_page.analyze('SPY', days=320, source='auto')
            etf_page.analyze('SPY', days=320, source='synthetic')
        self.assertEqual(calls, ['best', 'synthetic'])

    def test_results_still_name_the_provider(self):
        self.capture(structuring_page)
        self.inert(structuring_page.fcharts, 'payoff_chart')
        self.stack.enter_context(patch.object(structuring_page, 'load_treasury_curve',
                                              return_value=synthetic_curve_panel(days=30, seed=42)))
        root = structuring_page.build_structuring_page(page())
        button(root, 'Price').on_click(None)
        translate_controls(root, KO)
        self.assertIn('곡선 출처: 합성 데이터', texts(root))
        translate_controls(root, EN)
        self.assertIn('curve: SYNTHETIC', texts(root))


class NoExpandInWrap(Offline):
    def assert_clean(self, root, name):
        for row in walk(root):
            if isinstance(row, ft.Row) and row.wrap:
                for child in row.controls:
                    self.assertFalse(getattr(child, 'expand', None),
                                     f'{name}: {type(child).__name__} expands inside a wrapping row')

    def test_built_pages_and_results(self):
        for name, build in BUILDERS.items():
            with self.subTest(page=name):
                self.assert_clean(build(), name)
        self.capture(structuring_page)
        self.capture(bonds_page)
        self.capture(fx_page)
        self.inert(structuring_page.fcharts, 'payoff_chart', 'price_yield_chart', 'krd_chart',
                   'fx_spot_chart')
        panel = synthetic_curve_panel(days=30, seed=42)
        self.stack.enter_context(patch.object(structuring_page, 'load_treasury_curve', return_value=panel))
        self.stack.enter_context(patch.object(bonds_page, 'load_treasury_curve', return_value=panel))
        for name, root, label in (('structuring', structuring_page.build_structuring_page(page()), 'Price'),
                                  ('bonds', bonds_page.build_bonds_page(page()), 'Run'),
                                  ('fx', fx_page.build_fx_page(page()), 'Run')):
            with self.subTest(result=name):
                for dd in walk(root):
                    if isinstance(dd, ft.Dropdown) and dd.label in ('Data source', 'Curve source'):
                        dd.value = 'synthetic'
                button(root, label).on_click(None)
                self.assertFalse([t for t in texts(root) if t.startswith(('ValueError', 'FICCError', 'TypeError'))])
                self.assert_clean(root, name)


class KoreanChrome(Offline):
    # Names that are the same in both languages: tickers, page codes, model abbreviations.
    SAME = {'ETF', 'KRX', '25d RR %', '25d BF %'}

    def chrome(self, root):
        out = []
        for c in walk(root):
            if getattr(c, 'visible', True) is False:
                continue
            if isinstance(c, (ft.TextField, ft.Dropdown)) and isinstance(c.label, str):
                out.append(c.label)
                if isinstance(getattr(c, 'helper', None), str):
                    out.append(c.helper)
            if isinstance(c, ft.Dropdown):
                out += [o.text for o in c.options if isinstance(o.text, str)]
            if isinstance(c, ft.Button) and isinstance(c.content, str):
                out.append(c.content)
            if isinstance(c, ft.Text) and isinstance(c.value, str) and c.value.strip():
                out.append(c.value)
        return out

    def test_every_page_chrome_is_korean_and_returns_to_english(self):
        for name, build in BUILDERS.items():
            with self.subTest(page=name):
                root = build()
                english = self.chrome(root)
                translate_controls(root, KO)
                korean = self.chrome(root)
                self.assertGreater(len(korean), 5, name)
                # Anything without Hangul that still holds an English word is untranslated chrome.
                missing = [t for t in korean if not HANGUL.search(t) and t not in self.SAME
                           and re.search(r'[A-Za-z]{3,}', t)]
                self.assertEqual(missing, [], name)
                translate_controls(root, EN)
                self.assertEqual(self.chrome(root), english)

    def test_key_captions(self):
        cases = {
            'structuring': ['원금보장형 노트', '계약당 선물 DV01', '선택 입력', '발행가격', '명목금액'],
            'fx': ['통화쌍', '상대통화 금리 %', '빈칸이면 최신 단기금리', '실행'],
            'bonds': ['가격 (액면 100당)', '연간 이자 지급 횟수', '빈칸이면 수익률로 계산'],
            'derivatives': ['만기월 (YYYYMM)', '헤지 시뮬레이션 엔진', '불러오기'],
            'etf': ['ETF 종목코드', '레버리지 ETF 비교 기준', '분석 실행'],
            'crypto': ['기간 (일)', '새로고침'],
            'krx': ['종목코드', '현재가', '이 빌드에는 주문이나 계좌를 변경하는 기능이 없습니다.'],
        }
        for name, expected in cases.items():
            with self.subTest(page=name):
                root = BUILDERS[name]()
                translate_controls(root, KO)
                shown = KoreanChrome.chrome(self, root) + [o.text for c in walk(root) if isinstance(c, ft.Dropdown)
                                                           for o in c.options]
                for caption in expected:
                    self.assertIn(caption, shown)

    def test_structuring_results_read_in_korean(self):
        self.capture(structuring_page)
        self.inert(structuring_page.fcharts, 'payoff_chart')
        self.stack.enter_context(patch.object(structuring_page, 'load_treasury_curve',
                                              return_value=synthetic_curve_panel(days=30, seed=42)))
        root = structuring_page.build_structuring_page(page())
        button(root, 'Price').on_click(None)
        translate_controls(root, KO)
        shown = texts(root)
        for caption in ('공정가치', '발행가격', '참여율', '델타 (현물 +1%당)',
                        '구성요소 (명목 100당, 보유자 기준 부호)'):
            self.assertIn(caption, shown)
        self.assertTrue(any(t.startswith('합성 데이터: 금리 곡선을 FRED에서 받지 못해') for t in shown))
        translate_controls(root, EN)
        self.assertIn('Fair value', texts(root))
        self.assertTrue(any(t.startswith('Synthetic data: ') for t in texts(root)))


def numbers(text):
    return sorted(re.findall(r'[+-]?\d+(?:[.,]\d+)*(?:e[+-]?\d+)?', str(text)))


def table_text(table, row=None):
    rows = table.rows if row is None else [table.rows[row]]
    return [[c.content.value for c in r.cells] for r in rows]


class SecondReview(Offline):
    """Owner UI review 2026-11-10, second pass (group f-ficc): what the four reviewers still found."""

    def structuring(self, product='ppn', futures='65'):
        self.capture(structuring_page)
        self.inert(structuring_page.fcharts, 'payoff_chart')
        self.stack.enter_context(patch.object(structuring_page, 'load_treasury_curve',
                                              return_value=synthetic_curve_panel(days=30, seed=42)))
        root = structuring_page.build_structuring_page(page())
        tool = field(root, 'Product')
        tool.value = product
        tool.on_select(None)
        field(root, 'Futures DV01 / contract').value = futures
        button(root, 'Price').on_click(None)
        return root

    def test_structuring_legs_and_hedge_tables_read_in_korean_with_the_same_numbers(self):
        for product in ('ppn', 'rc', 'dcd', 'steep'):
            with self.subTest(product=product):
                root = self.structuring(product)
                tables = [c for c in walk(root) if isinstance(c, ft.DataTable)]
                self.assertEqual(len(tables), 2)
                english = [table_text(t) for t in tables]
                translate_controls(root, KO)
                korean = [table_text(t) for t in tables]
                self.assertEqual([[c.label.value for c in t.columns] for t in tables],
                                 [['구성요소', '유형', '값', '상세'], ['상품', '수량', '단위', '근거']])
                for en_rows, ko_rows in zip(english, korean):
                    for en_row, ko_row in zip(en_rows, ko_rows):
                        self.assertEqual(numbers(' '.join(en_row)), numbers(' '.join(ko_row)), ko_row)
                        # every authored cell is Korean; a unit like 'USD' or a value stays as it is
                        for en_cell, ko_cell in zip(en_row, ko_row):
                            if re.search(r'[A-Za-z]{4,}', en_cell) and en_cell not in ('USD', 'KRW'):
                                self.assertRegex(ko_cell, HANGUL, (en_cell, ko_cell))
                kinds = {row[1] for row in korean[0]}
                self.assertTrue(kinds <= {'무이표채', '이표채', '옵션', '스왑'}, kinds)
                # one ~40 px line per row that grows only when a sentence wraps, full card width
                for t in tables:
                    self.assertEqual(t.data_row_min_height, 40)
                    self.assertTrue(t.expand)
                translate_controls(root, EN)
                self.assertEqual([table_text(t) for t in tables], english)

    def test_structuring_chips_name_the_curve_method_and_underlying_in_korean(self):
        root = self.structuring('ppn')
        translate_controls(root, KO)
        shown = texts(root)
        self.assertIn('부트스트랩 무이표 곡선', shown)
        self.assertIn('외환', shown)
        self.assertNotIn('bootstrap 무이표 곡선', shown)
        translate_controls(root, EN)
        self.assertIn('bootstrap zeros', texts(root))
        self.assertIn('FX', texts(root))

    def test_structuring_inputs_fill_a_12_column_grid_and_price_never_stands_alone(self):
        self.stack.enter_context(patch.object(structuring_page, 'load_treasury_curve',
                                              return_value=synthetic_curve_panel(days=30, seed=42)))
        root = structuring_page.build_structuring_page(page())
        inputs, sheet = root.controls[1], root.controls[2]
        self.assertIsInstance(inputs, ft.ResponsiveRow)
        self.assertIsInstance(sheet, ft.ResponsiveRow)
        tool = field(root, 'Product')
        for product in ('ppn', 'rc', 'dcd', 'steep'):
            with self.subTest(product=product):
                tool.value = product
                tool.on_select(None)
                for grid in (inputs, sheet):
                    shown = [c for c in grid.controls if c.visible is not False]
                    for bp in ('xs', 'sm', 'md', 'lg', 'xl', 'xxl'):
                        spans = [c.col[bp] for c in shown]
                        lines, total = [], 0
                        for s in spans:                 # break into lines as the grid does
                            if total + s > 12:
                                lines.append(total)
                                total = 0
                            total += s
                        lines.append(total)
                        self.assertTrue(all(t == 12 for t in lines), (product, bp, spans))
                        # the Price button shares the last line with at least one field
                        if grid is sheet and bp not in ('xs',):
                            self.assertGreater(spans[-1], 0)
                            self.assertLess(spans[-1], 12, (product, bp, spans))
                dropdowns = [c for c in inputs.controls if isinstance(c, ft.Dropdown) and c.visible]
                self.assertTrue(all(d.width == float('inf') for d in dropdowns))

    def test_crypto_notices_and_study_chips_read_in_korean(self):
        from core.research import crypto_workflow
        self.capture(crypto_page)
        self.inert(crypto_page.xc, 'lines_chart')
        data = crypto_workflow.analyze(source='synthetic')
        self.stack.enter_context(patch.object(crypto_page, 'analyze', return_value=data))
        root = crypto_page.build_crypto_page(page())
        button(root, 'Refresh').on_click(None)
        english = texts(root)
        self.assertTrue(any(t.startswith('AR(1) phi=') for t in english))
        self.assertTrue(any(t.startswith('Retrospective full-sample deciles') for t in english))
        translate_controls(root, KO)
        shown = texts(root)
        for prefix in ('AR(1) phi=', 'ETH/BTC: AR(1) phi=', 'Retrospective full-sample deciles'):
            self.assertFalse([t for t in shown if t.startswith(prefix) and not HANGUL.search(t)], prefix)
        self.assertTrue(any(t.startswith('전체 표본을 사후적으로 나눈 십분위') for t in shown))
        self.assertIn('USD/KRW 환율 출처: 합성 데이터', shown)
        # study verdicts: the card's plain name and the verdict in both words, never a raw id
        for card_id, verdict in data['verdicts'].items():
            name = crypto_page.CARDS[card_id].name[0]
            chip_text = next(t for t in shown if t.startswith(name + ': '))
            if verdict in ('PASS', 'REVISE', 'REJECT', 'INSUFFICIENT_DATA'):
                self.assertIn(f' · {verdict}', chip_text)
            self.assertFalse(any(card_id.split('_', 2)[-1] + ':' in t for t in shown), card_id)
        translate_controls(root, EN)
        self.assertEqual(texts(root), english)

    def test_study_chip_wording(self):
        def chip_words(c):
            translate_controls(c, KO)
            ko = c.content.value
            translate_controls(c, EN)
            return ko, c.content.value
        self.assertEqual(chip_words(crypto_page.study_chip('M_C1_kimchi', 'REVISE')),
                         ('김치 프리미엄 신호: 보완 필요 · REVISE', 'Kimchi premium signal: REVISE'))
        self.assertEqual(chip_words(crypto_page.study_chip('S_C3_crypto_trend_btcusd', 'not run'))[0],
                         '비트코인 단기 추세 추종 (달러 BTC-USD): 미실행 · NOT_RUN')
        ko, en = chip_words(crypto_page.study_chip('M_C4_funding', 'PASS'))
        self.assertTrue(ko.endswith('과거 연구 결과, 재검증 안 됨') and en.endswith('historical, not revalidated'))
        self.assertEqual(chip_words(crypto_page.study_chip('X_unknown', 'PASS')), ('X_unknown: 통과 · PASS',
                                                                                 'X_unknown: PASS'))

    def test_krx_provider_bar_never_claims_a_connection(self):
        g = Mock()
        g.status.return_value = [{'provider': 'KIS', 'ready': True, 'reason': ''},
                                 {'provider': 'OpenDART', 'ready': False, 'reason': 'OPENDART_API_KEY not set'},
                                 {'provider': 'KRX', 'ready': False, 'reason': 'no KRX_API_KEY; the keyless export is '
                                                                             'blocked by KRX'}]
        root = krx_page.build_krx_page(page(), g)
        translate_controls(root, KO)
        shown = texts(root)
        self.assertIn('KIS: 키 설정됨', shown)
        self.assertIn('OpenDART: 미설정', shown)
        self.assertFalse([t for t in shown if '연결됨' in t or '응답 확인' in t])
        tips = [c.tooltip for c in walk(root) if isinstance(getattr(c, 'tooltip', None), str) and c.tooltip]
        self.assertIn('OPENDART_API_KEY가 설정되지 않았습니다', tips)
        translate_controls(root, EN)
        self.assertIn('KIS: Key set', texts(root))
        self.assertIn('OpenDART: Not set', texts(root))

    def test_krx_failure_reads_in_korean_with_the_provider_message_one_click_away(self):
        g = gateway()
        g.quote.return_value = SimpleNamespace(ok=False, data=None, source='',
                                               reason='no provider returned 005930 (KIS not configured)')
        root = krx_page.build_krx_page(page(), g)
        field(root, 'KRX code').value = '005930'
        button(root, 'Run').on_click(None)
        translate_controls(root, KO)
        shown = texts(root)
        self.assertIn('현재가: 제공처(KIS, KRX)가 응답하지 않았습니다 — KIS, KRX 키 미설정.', shown)
        tile = next(c for c in walk(root) if isinstance(c, ft.ExpansionTile))
        self.assertEqual(tile.title.value, '제공처 메시지 (원문)')
        self.assertIn('no provider returned 005930 (KIS not configured)',
                      [c.value for c in walk(tile.controls[0]) if isinstance(c, ft.Text)])
        translate_controls(root, EN)
        self.assertIn('Quote: no provider (KIS, KRX) returned data — KIS, KRX key not set.', texts(root))

    def test_derivatives_parity_notice_and_chip_values_read_in_korean(self):
        from core.research import derivatives_workflow
        from core.research.quote_coverage import quote_coverage_text, quote_coverage_text_ko
        self.capture(derivatives_page)
        self.inert(derivatives_page.xc, 'smile_chart', 'density_chart')
        board = derivatives_workflow.snapshot(source='synthetic', n_paths=400)
        self.stack.enter_context(patch.object(derivatives_page, 'snapshot', return_value=board))
        root = derivatives_page.build_derivatives_page(page())
        button(root, 'Load').on_click(None)
        english = texts(root)
        self.assertIn(quote_coverage_text(board['quote_coverage']), english)
        translate_controls(root, KO)
        shown = texts(root)
        ko = quote_coverage_text_ko(board['quote_coverage'])
        self.assertIn(ko, shown)
        self.assertEqual(numbers(ko), numbers(quote_coverage_text(board['quote_coverage'])))
        self.assertNotIn('call_vertical', ko)
        for chip_text in (f"만기 시연용 → {board['expiry_date']}", '기준 합성', '합성 가격',
                          f"금리 {board['rate']:.2%} (가정)"):
            self.assertIn(chip_text, shown)
        self.assertFalse([t for t in shown if t.endswith(' pts') or t.endswith(' of F')])
        translate_controls(root, EN)
        self.assertEqual(texts(root), english)

    def test_quote_coverage_korean_twin_keeps_not_run(self):
        from core.research.quote_coverage import quote_coverage, quote_coverage_text, quote_coverage_text_ko
        cov = quote_coverage({'n_calls': 1, 'n_puts': 3, 'call_vertical': 0, 'call_butterfly': 0,
                              'put_vertical': 1, 'put_butterfly': 0}, [{'within': None}])
        ko, en = quote_coverage_text_ko(cov), quote_coverage_text(cov)
        self.assertIn('풋–콜 패리티 미실행 (NOT_RUN)', ko)
        self.assertIn('콜 수직 스프레드: 미실행 (NOT_RUN', ko)
        self.assertIn('풋 수직 스프레드: 위반 1건 / 검사 2회', ko)
        self.assertEqual(numbers(ko), numbers(en))

    def test_fx_short_rate_series_names_read_in_korean(self):
        self.assertEqual(fx_page._label_ko('USD short rate (SOFR)'), 'USD 단기금리 (SOFR)')
        self.assertEqual(fx_page._label_ko('EUR short rate (ECB deposit facility rate)'), 'EUR 단기금리 (ECB 예금금리)')
        self.assertEqual(fx_page._label_ko('KRW short rate (3m interbank)'), 'KRW 단기금리 (3개월 은행간 금리)')
        self.assertEqual(fx_page._label_ko('EUR/USD'), 'EUR/USD')
        self.capture(fx_page)
        self.inert(fx_page.fcharts, 'fx_spot_chart')
        root = fx_page.build_fx_page(page())
        field(root, 'Data source').value = 'synthetic'
        button(root, 'Run').on_click(None)
        translate_controls(root, KO)
        shown = texts(root)
        self.assertTrue(any(t.startswith('USD 단기금리 (SOFR): 합성 데이터') for t in shown), shown)
        self.assertFalse([t for t in shown if 'short rate' in t])
        # an input the page cannot read is reported in Korean too
        translate_controls(root, EN)
        field(root, 'Quote-ccy rate %').value = 'x'
        button(root, 'Run').on_click(None)
        translate_controls(root, KO)
        self.assertTrue(any('숫자가 아닙니다' in t for t in texts(root)), texts(root))

    def test_etf_notices_read_in_korean_and_the_chart_reads_as_the_etf_backtest(self):
        from core.research import etf_workflow
        self.capture(etf_page)
        readings = []
        real = etf_page.xc.equity_chart

        def chart(*args, **kwargs):
            readings.append(kwargs.get('reading'))
            return ft.Text('Chart')
        self.stack.enter_context(patch.object(etf_page.xc, 'equity_chart', side_effect=chart))
        self.inert(etf_page.xc, 'premium_chart')
        data = etf_workflow.analyze('122630', days=504, source='synthetic')
        self.stack.enter_context(patch.object(etf_page, 'analyze', return_value=data))
        root = etf_page.build_etf_page(page())
        button(root, 'Analyze').on_click(None)
        translate_controls(root, KO)
        shown = texts(root)
        self.assertFalse([t for t in shown if t.startswith(('AR(1) phi=', 'AZ variance proxy', 'LETF '))
                          and not HANGUL.search(t)])
        self.assertTrue(any(t.startswith('AZ 분산 대용값') for t in shown))
        (reading,) = readings
        meaning_ko, meaning_en = reading['meaning']
        self.assertNotIn('Strategy Lab', meaning_en + reading['limit'][1])
        self.assertNotIn('전략 실험실', meaning_ko)
        self.assertIn('예측이 아닙니다', reading['limit'][0])
        warmup = data['sleeves']['conventions']['trend_warmup_daily_returns']
        self.assertIn(f'처음 {warmup}거래일', reading['look'][0])
        self.assertIn('1.0', reading['look'][0])
        self.assertTrue(callable(real))
        translate_controls(root, EN)

    def test_shared_words(self):
        from core.ui_page_messages.ficc_pages import EN_TO_KO
        from ui.ficc_widgets import VERDICT_KO, verdict_ko
        import ui.xcharts as xc
        self.assertEqual(VERDICT_KO['NOT_RUN'], '미실행')
        self.assertEqual(verdict_ko('NOT_RUN'), '미실행 · NOT_RUN')
        self.assertEqual(EN_TO_KO['not run'], '미실행')
        self.assertEqual(EN_TO_KO['Reverse convertible'], '역전환형 노트')
        self.assertIn('레버리지 ETF 성과 저하(드래그)', EN_TO_KO['NAV premium, basket, leveraged-fund drag, sleeve rules.'])
        self.assertNotIn('보유비용', ' '.join(EN_TO_KO.values()))
        self.assertIn('전략 실험실에서는', xc.EQUITY_READING['meaning'][0])
        self.assertNotIn('Strategy Lab에서는', xc.EQUITY_READING['meaning'][0])


if __name__ == '__main__':
    unittest.main()
