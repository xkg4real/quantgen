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
            'etf': ['ETF 종목코드', '레버리지 ETF 비교 기준', '분석'],
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


if __name__ == '__main__':
    unittest.main()
