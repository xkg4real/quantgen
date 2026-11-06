"""§10 NEW-M6-04 and NEW-M6-05: what the ETF sleeve numbers are, without changing them.

* NEW-M6-04: a sleeve whose daily P&L does not vary has a standard deviation of 0, so its Sharpe is
  undefined (for a cash-only sleeve a positive mean over 0, not 0/0). It used to show as about 1e16,
  or 0.00 where float rounding cancels; it is now n/a / '—' / 계산 불가 / null with a status and a
  note on every surface.
* NEW-M6-05: the cash warm-up, the fixed 3% cash assumption, the full-window Sharpe on raw (not
  excess-of-cash) returns after the sleeve cost, the invested-share window, costless constant-weight
  rebalancing (K-e) and the family-card verdicts (or that the cards were not loaded) are stated on
  every surface, in English and Korean with the same number tokens.

For every P&L that varies, every existing number, key and sentence is unchanged: the narratives
differ only by the inserted sentences. Offline: synthetic and injected histories only; no provider,
card store, AI service or network call.
"""
from copy import deepcopy
from fractions import Fraction
from io import BytesIO
import json
import math
import os
import re
import socket
import unittest
from unittest.mock import Mock, patch
from zipfile import ZipFile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import dotenv
with patch.object(dotenv, 'load_dotenv', return_value=False):
    import numpy as np
    from core.quant import insights
    from core.quant import strategies as S
    from core.quant.history import History
    from core.research import etf_workflow as wf
    from core.research import sleeve_disclosure as SD
    from core.research.ai_payload import filter_analysis_fields
    from core.research.decay_disclosure import decay_text
    from core.research.letf_disclosure import letf_text, letf_unavailable_text
    from core.research.market_analysis import ETFRequest, MarketOutput, execute_etf
    from core.research.tool_export import report_bytes
    from quantgen_desktop.market_diagnostics_language import decay_korean
    from quantgen_desktop.market_narrative_language import (etf_korean, letf_korean, letf_unavailable_korean,
                                                            market_variants, display_sharpe_note_korean,
                                                            display_conventions_korean)
    from ui import etf_page
import flet as ft
from tests.desktop_fx_language_acceptance import numbers

RF = 0.03 / 252
# The shipped 251340 / 400 trend Sharpe was 4.642314207434303e16: '46423142074343032.00' on the Flet tile and in
# the narratives, 4.642314207434303e+16 in JSON, '46,423,142,074,343,032.0000' in the native table. A bare '4642'
# also occurs by chance in the exported price arrays, so the check matches the value's leading digits in each of
# those formats, and any e16 exponent.
# Require a whole numeric token: report metadata can legitimately contain a
# hexadecimal commit ending in "e16" or beginning with the defect's digits.
DEFECT = re.compile(r'(?<![A-Za-z0-9_.])(?:4\.?642,?314[\d,.]*|46,423,142[\d,.]*|[-+]?\d+(?:\.\d+)?[eE]\+?16)(?![A-Za-z0-9_.])')
SEED_2_DEFECT = re.compile(r'3\.?482,?646|34,826,467|[eE]\+?16\b')     # 3.4826467946423224e16
PCT_NUMBERS = re.compile(r'[-+]?\d[\d,]*(?:\.\d+)?%?')


def walk(seed, closes=505):
    """The register's driftless walk (MODEL_LIMITS M6-13 probe): 19 %/yr, zero drift in log price."""
    rng = np.random.default_rng(seed)
    return 100 * np.exp(np.cumsum(rng.normal(-0.5 * 0.012 ** 2, 0.012, closes)))


def analyze(px, code='069500'):
    dates = tuple(f'2020-{i:05d}' for i in range(len(px)))
    h = History(code, 'SYNTHETIC', dates, tuple(float(x) for x in px), note='injected walk')
    return wf.analyze(code, source='synthetic', days=len(px), history_loader=lambda *a, **k: h,
                      card_loader=lambda path: [])


def output(px, code='069500'):
    d = analyze(px, code)
    return MarketOutput(ETFRequest(source='synthetic', code=code, days=len(px)), d, wf.narrative(d))


def shipped_251340():
    """The shipped Synthetic demo, code 251340, 400 sessions: its trend switch never holds the fund."""
    return execute_etf(ETFRequest(source='synthetic', code='251340', days=400))


# The recipe and the narratives as they were at a32106b, copied verbatim, so the "unchanged for valid
# inputs" checks compare with the old code rather than with itself.
def old_sleeves(px, is_krx):
    rf = 0.03 / 252
    W_t = S.trend_switch(px[:, None], rule="sma", lookback=210, step=21, cash_rate_daily=rf)
    W_v = S.vol_target(px[:, None], target=0.12, window=22, step=21)
    cost = 3.0 if is_krx else 50.0
    pt, _ = S.simulate(px[:, None], W_t, cost_bps=cost, cash_daily=rf)
    pv, _ = S.simulate(px[:, None], W_v, cost_bps=cost, cash_daily=rf)
    bh = px[1:] / px[:-1] - 1.0
    return {"trend": S.summary(pt), "vol_target": S.summary(pv), "buy_hold": S.summary(bh),
            "equity_trend": S.equity_curve(pt), "equity_bh": S.equity_curve(bh), "cost_bps": cost,
            "exposure_trend": float(W_t[210:].mean()) if px.size > 210 else float("nan")}


def old_narrative(a: dict) -> str:
    parts = []
    q = a.get("quote")
    if q:
        parts.append(f"{a['code']} trades at {q['price']:,.0f} against an NAV of {q['nav']:,.2f}, a premium of "
                     f"{q['premium_pct']:+.2f} % with tracking error {q['tracking_error_pct']:.2f} %, "
                     f"{q['cu_units']:,.0f} shares per creation unit and LPs holding {q['lp_holding_pct']:.1f} %.")
    ps = a.get("premium_stats")
    if ps:
        parts.append(f"Over {len(a['dates'])} sessions the premium averaged {ps['mean']:+.2f} % (|premium| {ps['abs_mean']:.2f} %), "
                     f"today's reading sits {ps['z']:+.1f} standard deviations from that mean; ADF p = {ps['adf_p']:.3f}. "
                     + decay_text(ps.get('decay')))
    sl = a.get("sleeves")
    if sl:
        parts.append(f"On this fund's own history the 10-month trend switch earned Sharpe {sl['trend']['sharpe']:.2f} "
                     f"(max drawdown {sl['trend']['max_drawdown']:.0%}, {sl['exposure_trend']:.0%} invested) against buy-and-hold "
                     f"{sl['buy_hold']['sharpe']:.2f} ({sl['buy_hold']['max_drawdown']:.0%}); the 12 % vol target earned "
                     f"{sl['vol_target']['sharpe']:.2f}. These are in-sample descriptive numbers; the validation study's verdict "
                     f"for this family is trend: {a['verdicts']['trend']}, vol target: {a['verdicts']['vol']}. "
                     f"Price basis for these sleeve numbers: {a.get('sleeve_basis', a.get('data_source'))}.")
    lt = a.get("letf")
    if lt and "rows" in lt:
        r63 = next(r for r in lt["rows"] if r["sessions"] == 63)
        parts.append(f"{lt['name']} ({lt['beta']:+.0f}×): prior-quarter variance AZ proxy "
                     f"{lt['last_quarter_drag_bp']:+.0f} bp over 63 observations; GARCH variance proxy "
                     f"{r63['drag_bp']:+.0f} bp over 63 observations. " + letf_text(lt))
    elif lt:
        parts.append(letf_unavailable_text(lt))
    if a.get("data_source") == "SYNTHETIC":
        parts.append("The series is SYNTHETIC; nothing above is market data.")
    return " ".join(parts) or "No history could be loaded."


def old_etf_korean(a):
    parts = []
    q = a.get('quote')
    if q:
        parts.append(f"{a['code']}의 가격은 {q['price']:,.0f}, NAV는 {q['nav']:,.2f}, "
                     f"프리미엄은 {q['premium_pct']:+.2f} %, 추적 오차는 {q['tracking_error_pct']:.2f} %, "
                     f"설정 단위당 주식 수는 {q['cu_units']:,.0f}, LP 보유 비율은 {q['lp_holding_pct']:.1f} %입니다.")
    ps = a.get('premium_stats')
    if ps:
        parts.append(f"{len(a['dates'])}개 거래일 동안 평균 프리미엄은 {ps['mean']:+.2f} % "
                     f"(|프리미엄| {ps['abs_mean']:.2f} %)이며, 오늘 값은 평균에서 "
                     f"{ps['z']:+.1f} 표준편차 떨어져 있습니다. ADF p = {ps['adf_p']:.3f}. "
                     + decay_korean(ps.get('decay')))
    sl = a.get('sleeves')
    if sl:
        parts.append(f"이 펀드의 자체 이력에서 10개월 추세 전환의 샤프 지수는 {sl['trend']['sharpe']:.2f} "
                     f"(최대 낙폭 {sl['trend']['max_drawdown']:.0%}, 투자 비중 {sl['exposure_trend']:.0%})이며, "
                     f"매수 후 보유는 {sl['buy_hold']['sharpe']:.2f} ({sl['buy_hold']['max_drawdown']:.0%}), "
                     f"12 % 변동성 목표는 {sl['vol_target']['sharpe']:.2f}입니다. 이는 표본 내 기술통계입니다. "
                     f"이 계열의 검증 연구 판정은 추세: {a['verdicts']['trend']}, 변동성 목표: {a['verdicts']['vol']}입니다. "
                     f"이 전략별 수치의 가격 기준: {a.get('sleeve_basis', a.get('data_source'))}.")
    lt = a.get('letf')
    if lt and 'rows' in lt:
        r63 = next(r for r in lt['rows'] if r['sessions'] == 63)
        parts.append(f"{lt['name']} ({lt['beta']:+.0f}×): 직전 분기 분산 AZ 대용값은 "
                     f"63개 관측에 걸쳐 {lt['last_quarter_drag_bp']:+.0f} bp, GARCH 분산 대용값은 "
                     f"63개 관측에 걸쳐 {r63['drag_bp']:+.0f} bp입니다. " + letf_korean(lt))
    elif lt:
        parts.append(letf_unavailable_korean(lt))
    if a.get('data_source') == 'SYNTHETIC':
        parts.append('시계열은 SYNTHETIC이며 위 수치는 시장 데이터가 아닙니다.')
    return ' '.join(parts) or '이력을 불러오지 못했습니다.'


def without_insertions(text, sl, korean=False):
    """The narrative with the NEW-M6-04 note and the NEW-M6-05 conventions removed."""
    conventions = (display_conventions_korean if korean else SD.conventions_text)(sl['conventions'])
    assert text.count(' ' + conventions) == 1
    text = text.replace(' ' + conventions, '')
    note = (display_sharpe_note_korean if korean else SD.sharpe_note)(sl)
    if note:
        assert text.count(' ' + note) == 1
    return text.replace(' ' + note, '') if note else text


def same_value(x, y):
    if isinstance(x, float) and isinstance(y, float):
        return (math.isnan(x) and math.isnan(y)) or (x == y and math.copysign(1, x) == math.copysign(1, y))
    return type(x) is type(y) and x == y


def controls(root):
    yield root
    for child in getattr(root, 'controls', None) or []:
        yield from controls(child)
    content = getattr(root, 'content', None)
    if isinstance(content, ft.Control):
        yield from controls(content)


def tiles(root):
    """{label: (value, tooltip)} of every stat tile."""
    out = {}
    for c in controls(root):
        col = getattr(c, 'content', None)
        if isinstance(c, ft.Container) and isinstance(col, ft.Column) and len(col.controls) == 2 \
                and all(isinstance(t, ft.Text) for t in col.controls):
            out[col.controls[0].value] = (col.controls[1].value, c.tooltip)
    return out


def notice_texts(root):
    """Texts of the `ui.components.notice` banners (an icon, then the text) under `root`."""
    out = []
    for c in controls(root):
        row = getattr(c, 'content', None)
        if isinstance(c, ft.Container) and isinstance(row, ft.Row) and row.controls \
                and isinstance(row.controls[0], ft.Icon):
            out += [t.value for t in row.controls if isinstance(t, ft.Text)]
    return out


def block_after_sleeve_row(root):
    """The block placed directly after the row of sleeve stat tiles."""
    for c in controls(root):
        kids = list(getattr(c, 'controls', None) or [])
        for i, k in enumerate(kids):
            if isinstance(k, ft.Row) and 'Trend switch Sharpe' in tiles(k):
                return kids[i + 1]
    raise AssertionError('no sleeve row')


def all_strings(root):
    for c in controls(root):
        for attr in ('value', 'tooltip', 'label', 'content'):
            v = getattr(c, attr, None)
            if isinstance(v, str):
                yield v
            elif v is not None and not isinstance(v, ft.Control) and isinstance(getattr(v, 'message', None), str):
                yield v.message


class OfflineCase(unittest.TestCase):
    def setUp(self):
        for target, kw in (('socket.socket.connect', {'side_effect': OSError('network forbidden')}),
                           ('requests.sessions.Session.request', {'side_effect': AssertionError('live I/O forbidden')}),
                           ('core.quant.validate.load_cards', {'side_effect': AssertionError('no card store')}),
                           ('core.quant.gate_ledger.family_ledger', {'side_effect': AssertionError('no ledger')})):
            p = patch(target, **kw)
            p.start()
            self.addCleanup(p.stop)


class UndefinedSharpeTests(OfflineCase):
    def test_defect_probe_matches_numeric_values_not_commit_metadata(self):
        for value in ('1e16','-1.23e+16','46423142074343032.00','46,423,142,074,343,032.0000'):
            self.assertRegex(value,DEFECT)
        for commit in ('e79ef2c1160242ddf86d5b381e1005f2ad627e16',
                       '4642314abcdef0123456789abcdef0123456789abc'):
            self.assertNotRegex(json.dumps({'commit':commit}),DEFECT)

    def test_constant_cash_pnl_is_undefined_at_both_rounding_outcomes(self):
        for closes, numpy_sd_is_zero in ((505, False), (547, True)):
            with self.subTest(closes=closes):
                p = np.full(closes - 1, RF)          # what simulate books on every session of a cash-only sleeve
                exact = [Fraction(float(x)) for x in p]
                mean = sum(exact) / len(exact)
                # Exact sample variance 0 with a positive mean: mean x 252 / (0 x √252) is a positive number
                # over 0, undefined (not 0/0, which only a P&L of 0 throughout gives).
                self.assertEqual(sum((x - mean) ** 2 for x in exact), 0)
                self.assertGreater(mean, 0)
                sd = float(np.std(p, ddof=1))
                old = S.summary(p)
                if numpy_sd_is_zero:   # rounding cancels: the old screens showed 0.00
                    self.assertEqual(sd, 0.0); self.assertEqual(old['sharpe'], 0.0)
                else:                  # rounding residue: the old screens showed about 1e16
                    self.assertGreater(sd, 0.0); self.assertLess(sd, 1e-18); self.assertGreater(old['sharpe'], 1e15)
                new = SD.sleeve_summary(p)
                self.assertIsNone(new['sharpe'])
                self.assertEqual(new['sharpe_status'], SD.NO_VARIATION)
                self.assertEqual({k: v for k, v in new.items() if k not in ('sharpe', 'sharpe_status')},
                                 {k: v for k, v in old.items() if k != 'sharpe'})
                self.assertIsNone(SD.sharpe_text(new))
                self.assertIn('standard deviation is 0 and the Sharpe ratio is undefined', SD.sharpe_tooltip(new))

    def test_tolerance_rule_and_non_finite(self):
        # The documented numerical rule: relative sd at or below 1e-10 counts as no variation.
        self.assertEqual(SD.RELATIVE_SD_TOLERANCE, 1e-10)
        tiny = np.r_[np.full(300, RF), RF + 1e-12]
        self.assertGreater(np.std(tiny, ddof=1), 0)
        self.assertEqual(SD.sleeve_summary(tiny)['sharpe_status'], SD.NO_VARIATION)
        varied = np.r_[np.full(300, RF), RF + 1e-3]
        s = SD.sleeve_summary(varied)
        self.assertEqual((s['sharpe_status'], s['sharpe']), (SD.COMPUTED, S.summary(varied)['sharpe']))
        for bad in (np.r_[0.01, np.nan, 0.02], np.r_[0.01, np.inf, -0.02]):
            s = SD.sleeve_summary(bad)
            self.assertEqual((s['sharpe'], s['sharpe_status']), (None, SD.NON_FINITE))
            self.assertEqual(S.summary(bad)['sharpe'], 0.0)     # what the screens used to show
        for short in ([], [0.01]):
            self.assertEqual(SD.sleeve_summary(short)['sharpe_status'], SD.NO_VARIATION)

    def test_register_seed_2_walk_trend_is_na_and_the_rest_is_unchanged(self):
        px = walk(2)
        for code, vol_target in (('069500', -0.7151), ('SPY', -0.7516)):
            with self.subTest(code=code):
                out = output(px, code)
                d, old = out.data, old_sleeves(px, code == '069500')
                self.assertEqual(old['trend']['sharpe'], 3.4826467946423224e16)   # the defect, as the register measured
                self.assertRegex(f"{old['trend']['sharpe']:.2f}", SEED_2_DEFECT)
                trend = d['sleeves']['trend']
                self.assertEqual((trend['sharpe'], trend['sharpe_status']), (None, SD.NO_VARIATION))
                self.assertEqual(trend['max_drawdown'], 0.0)
                self.assertAlmostEqual(trend['total_return'], 0.061833, places=6)
                self.assertAlmostEqual(d['sleeves']['vol_target']['sharpe'], vol_target, places=4)
                self.assertAlmostEqual(d['sleeves']['buy_hold']['sharpe'], -0.8407, places=4)
                for k in ('vol_target', 'buy_hold'):
                    self.assertEqual(d['sleeves'][k]['sharpe'], old[k]['sharpe'])
                en, ko = out.narrative, etf_korean(d)
                self.assertIn('earned Sharpe n/a (max drawdown 0%, 0% invested)', en)
                self.assertIn('Sharpe n/a for the trend switch: the daily P&L did not vary', en)
                self.assertIn('샤프 지수는 계산 불가 (최대 낙폭 0%, 투자 비중 0%)', ko)
                self.assertIn('추세 전환의 샤프 지수는 계산 불가입니다', ko)
                for text in (en, ko, json.dumps(wf.payload(d), allow_nan=False)):
                    self.assertNotRegex(text, SEED_2_DEFECT)
                self.assertEqual(numbers(en), numbers(ko))
                self.assertEqual(market_variants(out, 'etf')['ko'], ko)
                # "These are in-sample..." still follows the numbers; the note comes after the price basis and
                # before the conventions.
                self.assertRegex(en, r'the 12 % vol target earned -0\.\d\d\. These are in-sample descriptive numbers')
                self.assertRegex(ko, r'12 % 변동성 목표는 -0\.\d\d입니다\. 이는 표본 내 기술통계입니다\.')
                self.assertLess(en.index('Price basis for these sleeve numbers:'), en.index('Sharpe n/a for'))
                self.assertLess(en.index('Sharpe n/a for'), en.index('Sleeve conventions:'))
                self.assertLess(ko.index('이 전략별 수치의 가격 기준:'), ko.index('추세 전환의 샤프 지수는 계산 불가입니다'))
                self.assertLess(ko.index('추세 전환의 샤프 지수는 계산 불가입니다'), ko.index('전략 계산 관례:'))

    def test_flat_price_at_100_all_three_are_na_with_one_note(self):
        out = output(np.full(505, 100.0))
        sl = out.data['sleeves']
        self.assertEqual([sl[k]['sharpe_status'] for k in SD.SLEEVES], [SD.NO_VARIATION] * 3)
        en, ko = out.narrative, etf_korean(out.data)
        self.assertIn('earned Sharpe n/a', en); self.assertIn('against buy-and-hold n/a (0%)', en)
        self.assertIn('the 12 % vol target earned n/a. These are in-sample', en)
        self.assertIn('Sharpe n/a for the trend switch, the vol target and buy-and-hold:', en)
        self.assertIn('추세 전환, 변동성 목표, 매수 후 보유의 샤프 지수는 계산 불가입니다', ko)
        self.assertIn('12 % 변동성 목표는 계산 불가입니다. 이는 표본 내', ko)
        self.assertIn('the standard deviation is 0 and the ratio is undefined', en)
        self.assertIn('표준편차가 0이므로 비율이 정의되지 않습니다', ko)
        for text in (en, ko):
            self.assertNotIn('large positive', text); self.assertNotIn('큰 양의', text)
        # Degenerate-case parity: each note carries the same two '0's in both languages.
        self.assertEqual(numbers(en), numbers(ko))
        self.assertEqual(numbers(SD.sharpe_note(sl)), numbers(SD.sharpe_note_korean(sl)))
        self.assertEqual(numbers(SD.sharpe_note(sl)), numbers('0 0'))
        json.dumps(wf.payload(out.data), allow_nan=False)
        two = {'trend': {'sharpe_status': SD.NO_VARIATION}, 'vol_target': {'sharpe_status': SD.NO_VARIATION},
               'buy_hold': {'sharpe_status': SD.COMPUTED}}
        self.assertIn('Sharpe n/a for the trend switch and the vol target:', SD.sharpe_note(two))
        self.assertIn('추세 전환, 변동성 목표의 샤프비율', SD.sharpe_note_korean(two))
        self.assertIsNone(SD.sharpe_note({k: {'sharpe_status': SD.COMPUTED} for k in SD.SLEEVES}))

    def test_flat_price_at_other_levels_the_trend_sharpe_can_be_defined(self):
        # Float rounding of the 210-session average can put the trend switch in a flat fund on some rows, so its
        # P&L moves between 0 and the cash rate: a defined Sharpe, the same number as before. The other two are n/a.
        px = np.full(505, 100.37)
        out = output(px)
        sl, old = out.data['sleeves'], old_sleeves(px, True)
        self.assertEqual((sl['trend']['sharpe_status'], sl['trend']['sharpe']), (SD.COMPUTED, old['trend']['sharpe']))
        self.assertAlmostEqual(sl['trend']['sharpe'], 20.8006, places=4)
        self.assertGreater(sl['exposure_trend'], 0)
        self.assertEqual([sl[k]['sharpe_status'] for k in ('vol_target', 'buy_hold')], [SD.NO_VARIATION] * 2)
        en, ko = out.narrative, etf_korean(out.data)
        self.assertIn('earned Sharpe 20.80', en)
        self.assertIn('Sharpe n/a for the vol target and buy-and-hold:', en)
        self.assertIn('변동성 목표, 매수 후 보유의 샤프 지수는 계산 불가입니다', ko)
        self.assertEqual(numbers(en), numbers(ko))

    def test_nan_close_is_non_finite_not_no_variation(self):
        px = walk(5)
        px[300] = np.nan
        out = output(px)
        sl = out.data['sleeves']
        for k in SD.SLEEVES:
            self.assertEqual((sl[k]['sharpe'], sl[k]['sharpe_status']), (None, SD.NON_FINITE))
        self.assertIn('the daily P&L contains non-finite values', out.narrative)
        self.assertIn('유한하지 않은 값이 있습니다', etf_korean(out.data))
        self.assertEqual(numbers(out.narrative), numbers(etf_korean(out.data)))


class UnchangedForValidInputsTests(OfflineCase):
    def test_seeded_walks_and_costs_keep_every_key_and_every_sentence(self):
        checked = 0
        for seed in range(120):
            px = walk(seed)
            for code in ('069500', 'SPY'):
                a = analyze(px, code)
                new, old = a['sleeves'], old_sleeves(px, code == '069500')
                self.assertEqual(set(new) - set(old), {'conventions'})
                for k in ('equity_trend', 'equity_bh'):
                    self.assertTrue(np.array_equal(new[k], old[k]))
                for k in ('cost_bps', 'exposure_trend'):
                    self.assertTrue(same_value(new[k], old[k]), (seed, code, k))
                for k in SD.SLEEVES:
                    self.assertEqual(list(new[k])[:-1], list(old[k]))            # same keys, same order
                    for key, value in old[k].items():
                        if key == 'sharpe' and new[k]['sharpe_status'] != SD.COMPUTED:
                            self.assertIsNone(new[k]['sharpe'])
                            continue
                        self.assertTrue(same_value(new[k][key], value), (seed, code, k, key))
                if all(new[k]['sharpe_status'] == SD.COMPUTED for k in SD.SLEEVES):
                    before = {**a, 'sleeves': old}
                    self.assertEqual(without_insertions(wf.narrative(a), new), old_narrative(before))
                    self.assertEqual(without_insertions(etf_korean(a), new, korean=True), old_etf_korean(before))
                    checked += 1
        self.assertGreater(checked, 200)

    def test_shipped_fixtures_read_as_before_plus_the_conventions(self):
        from tests.ar1_decay_acceptance import etf_fixture
        from tests.letf_disclosure_acceptance import fixture as letf_fixture
        cases = [etf_fixture(), letf_fixture()] + [execute_etf(ETFRequest(source='synthetic', code=c, days=n))
                                                   for c, n in (('069500', 504), ('SPY', 504), ('QQQ', 1000),
                                                                ('122630', 504), ('252670', 400), ('DEMO', 400))]
        for out in cases:
            with self.subTest(code=out.data['code'], sessions=len(out.data['price'])):
                sl = out.data['sleeves']
                self.assertTrue(all(sl[k]['sharpe_status'] == SD.COMPUTED for k in SD.SLEEVES))
                before = deepcopy(out.data)
                for k in SD.SLEEVES:
                    before['sleeves'][k] = {key: v for key, v in sl[k].items() if key != 'sharpe_status'}
                del before['sleeves']['conventions']
                self.assertEqual(without_insertions(out.narrative, sl), old_narrative(before))
                self.assertEqual(without_insertions(etf_korean(out.data), sl, korean=True), old_etf_korean(before))
                self.assertEqual(numbers(out.narrative), numbers(etf_korean(out.data)))
                payload = wf.payload(out.data)
                # The sleeves are strict JSON. (A synthetic LETF index can fit GARCH nu = inf, outside this item.)
                json.dumps(payload['sleeves'], allow_nan=False)
                if 'letf' not in out.data:
                    json.dumps(payload, allow_nan=False)
                self.assertEqual(filter_analysis_fields(payload)['sleeves']['conventions'], sl['conventions'])


class ConventionsTests(OfflineCase):
    def test_record_values_from_the_strategy_arguments(self):
        for code, cards in (('069500', ('S_E1_trend_krx', 'S_E2_voltarget_kodex200')),
                            ('SPY', ('S_E1_trend_us', 'S_E2_voltarget_spy'))):
            out = execute_etf(ETFRequest(source='synthetic', code=code, days=504))
            c = out.data['sleeves']['conventions']
            self.assertEqual(len(out.data['price']), 504)
            self.assertEqual((c['window_daily_returns'], c['trend_warmup_daily_returns'],
                              c['vol_target_warmup_daily_returns'], c['cash_rate_annual']), (503, 210, 23, 0.03))
            self.assertEqual(c['window_daily_returns'], out.data['sleeves']['trend']['sessions'])
            self.assertEqual(c['trend_warmup_share'], 210 / 503)
            self.assertEqual((c['trend_card'], c['vol_target_card']), cards)
            self.assertEqual(out.study_status, 'NOT_LOADED')                      # the Native path loads no card
            self.assertEqual((c['trend_card_loaded'], c['vol_target_card_loaded']), (False, False))
            self.assertEqual((c['sharpe_basis'], c['sharpe_window'], c['cash_rate_basis'], c['comparison']),
                             ('RAW_RETURN_NOT_EXCESS_OF_CASH_AFTER_SLEEVE_COST', 'FULL_WINDOW_INCLUDING_WARMUP',
                              'FIXED_ASSUMPTION_NOT_OBSERVED', 'NOT_LIKE_FOR_LIKE'))
            self.assertEqual((c['exposure_first_row'], c['exposure_window']),
                             (210, 'WARMUP_END_TO_LAST_ROW_INCLUDING_UNHELD_FINAL_ROW'))
            self.assertEqual(filter_analysis_fields(c), c)                       # no private field name
            self.assertEqual(wf.payload(out.data)['sleeves']['conventions'], c)
        self.assertEqual((wf.SLEEVE_TREND_LOOKBACK, wf.SLEEVE_VOL_WINDOW, wf.SLEEVE_CASH_RATE), (210, 22, 0.03))
        with self.assertRaises(ValueError):
            SD.sleeve_conventions(window_sessions=200, trend_lookback=210, vol_window=22, cash_rate_annual=0.03)

    def test_texts_say_each_convention_with_the_same_numbers_in_both_languages(self):
        out = execute_etf(ETFRequest(source='synthetic', code='069500', days=504))
        c = out.data['sleeves']['conventions']
        en, ko = SD.conventions_text(c), SD.conventions_korean(c)
        for phrase in ('after 210 sessions (the length of its 10-month moving average)',
                       'first 210 of these 503 daily returns (42%)', "vol target's first 23",
                       'fixed 3% a year (assumption: 3% / 252 per session)', 'not an observed rate',
                       'whole window, warm-up included', 'raw returns, not returns in excess of the cash rate',
                       'the trend switch and vol target returns are after their per-side trading cost',
                       'buy-and-hold has no warm-up, no cash and no cost',
                       "replaces the fund's return with the fixed cash return on those sessions",
                       'lowers the measured volatility', 'not like-for-like',
                       "including the last close's weight, which is never held",
                       'A vol-target weight below 1 is reset to that weight every session at no cost',
                       # this screen loaded no study card, so its "not run" is not a card's verdict
                       'The family study cards (S_E1_trend_krx and S_E2_voltarget_kodex200) were not loaded here, '
                       'so no study verdict is shown for them (not run); a card\'s verdict covers the rule family, '
                       'not this fund.'):
            self.assertIn(phrase, en)
        for phrase in ('210거래일(10개월 이동평균 기간)', '503개 일별 수익률 가운데 처음 210개(42%)',
                       '변동성 목표도 처음 23개는 현금으로 보유한 준비 구간입니다', '연 3% 고정', '가정: 거래일당 3% / 252',
                       '관측 금리가 아니며', '준비 구간을 포함한 전체 기간', '현금 금리를 빼지 않은 수익률 기준',
                       '추세 전환과 변동성 목표의 수익률은 편도 거래 비용을 뺀 값',
                       '매수 후 보유에는 준비 구간, 현금, 비용이 없습니다', '고정 현금 수익률로 대신하고',
                       '측정 변동성을 낮추므로', '같은 조건의 비교가 아닙니다', '보유하지 않는 마지막 종가의 비중도 포함',
                       '비용 없이 그 비중으로 다시 맞춘다',
                       '계열 연구 카드(S_E1_trend_krx, S_E2_voltarget_kodex200)를 여기서 불러오지 않아 연구 판정이 표시되지 않습니다(not run)'):
            self.assertIn(phrase, ko)
        # "gross" reads as "before costs" and 총수익 as "with distributions"; neither is what the Sharpe is.
        self.assertNotIn('gross', en.lower()); self.assertNotIn('총수익', ko)
        self.assertNotIn('are those of the family card', en); self.assertNotIn('의 판정이며', ko)
        self.assertEqual(numbers(en), numbers(ko))
        self.assertEqual(sorted(PCT_NUMBERS.findall(en)), sorted(PCT_NUMBERS.findall(ko)))
        # Counted in daily returns, so it cannot clash with the 504-session premium sentence.
        self.assertNotIn('504', en); self.assertNotIn('504', ko)
        # A mechanism, not a direction of bias.
        for word in ('flatter', 'inflate', 'overstate', 'understate', 'biased', 'favour', 'favor', 'raises'):
            self.assertNotIn(word, en.lower())
        for closes, share in ((301, '70%'), (359, '59%'), (505, '42%'), (1009, '21%')):
            text = SD.conventions_text(SD.sleeve_conventions(window_sessions=closes - 1, trend_lookback=210,
                                                             vol_window=22, cash_rate_annual=0.03))
            self.assertIn(f'of these {closes - 1} daily returns ({share})', text)

    def test_verdict_clause_follows_which_family_cards_were_loaded(self):
        px = walk(7)
        card = lambda cid: {'card_id': cid, 'decision': 'REJECT', 'decision_reason': 'fixture'}
        for loaded, en_clause, ko_clause in (
                (('S_E1_trend_krx', 'S_E2_voltarget_kodex200'),
                 'The study verdicts are those of the family cards (S_E1_trend_krx and S_E2_voltarget_kodex200), '
                 'not a test of this fund.',
                 '연구 판정은 계열 카드(S_E1_trend_krx, S_E2_voltarget_kodex200)의 판정이며 이 펀드를 검정한 것이 아닙니다.'),
                (('S_E1_trend_krx',),
                 'The study verdicts are those of the family card (S_E1_trend_krx), not a test of this fund. '
                 'The family study card (S_E2_voltarget_kodex200) was not loaded here, so no study verdict is shown '
                 'for it (not run);',
                 '계열 연구 카드(S_E2_voltarget_kodex200)를 여기서 불러오지 않아 연구 판정이 표시되지 않습니다(not run).'),
                ((), 'were not loaded here, so no study verdict is shown for them (not run)',
                 '계열 연구 카드(S_E1_trend_krx, S_E2_voltarget_kodex200)를 여기서 불러오지 않아')):
            with self.subTest(loaded=loaded):
                dates = tuple(f'2020-{i:05d}' for i in range(len(px)))
                h = History('069500', 'SYNTHETIC', dates, tuple(float(x) for x in px), note='injected walk')
                a = wf.analyze('069500', source='synthetic', days=len(px), history_loader=lambda *x, **k: h,
                               card_loader=lambda path: [card(cid) for cid in loaded])
                c = a['sleeves']['conventions']
                self.assertEqual((c['trend_card_loaded'], c['vol_target_card_loaded']),
                                 ('S_E1_trend_krx' in loaded, 'S_E2_voltarget_kodex200' in loaded))
                self.assertEqual(a['verdicts'], {'trend': 'REJECT' if 'S_E1_trend_krx' in loaded else 'not run',
                                                 'vol': 'REJECT' if 'S_E2_voltarget_kodex200' in loaded else 'not run'})
                en, ko = wf.narrative(a), etf_korean(a)
                self.assertIn(en_clause, en); self.assertIn(ko_clause, ko)
                self.assertEqual(numbers(en), numbers(ko))
                self.assertEqual(numbers(SD.conventions_text(c)), numbers(SD.conventions_korean(c)))
                self.assertEqual(list(c), list(SD.sleeve_conventions(window_sessions=504, trend_lookback=210,
                                                                     vol_window=22, cash_rate_annual=0.03)))
        # A record built without a card status (None) keeps the plain clause.
        plain = SD.sleeve_conventions(window_sessions=504, trend_lookback=210, vol_window=22, cash_rate_annual=0.03,
                                      trend_card='S_E1_trend_us', vol_target_card='S_E2_voltarget_spy')
        self.assertIn('family cards (S_E1_trend_us and S_E2_voltarget_spy), not a test of this fund.',
                      SD.conventions_text(plain))
        self.assertTrue(SD.conventions_text(SD.sleeve_conventions(
            window_sessions=504, trend_lookback=210, vol_window=22, cash_rate_annual=0.03)).endswith(
            'The study verdicts are those of the family cards, not a test of this fund.'))

    def test_warmups_are_pinned_against_the_strategy_functions(self):
        lookback, window = wf.SLEEVE_TREND_LOOKBACK, wf.SLEEVE_VOL_WINDOW
        c = SD.sleeve_conventions(window_sessions=504, trend_lookback=lookback, vol_window=window, cash_rate_annual=0.03)
        rising = 100 * np.exp(np.cumsum(np.r_[0.0, np.full(504, 0.001) + 0.004 * (-1) ** np.arange(504)]))
        for px in [rising] + [walk(seed) for seed in range(20)]:
            W_t = S.trend_switch(px[:, None], rule='sma', lookback=lookback, step=21, cash_rate_daily=RF)
            W_v = S.vol_target(px[:, None], target=0.12, window=window, step=21)
            self.assertTrue(np.all(W_t[:c['trend_warmup_daily_returns']] == 0))
            first_v = int(np.argmax(W_v[:, 0] > 0))
            self.assertEqual(first_v, c['vol_target_warmup_daily_returns'])      # first nonzero vol-target weight row
            pt, _ = S.simulate(px[:, None], W_t, cost_bps=3.0, cash_daily=RF)
            pv, _ = S.simulate(px[:, None], W_v, cost_bps=3.0, cash_daily=RF)
            self.assertTrue(np.all(pt[:c['trend_warmup_daily_returns']] == RF))
            self.assertTrue(np.all(pv[:c['vol_target_warmup_daily_returns']] == RF))
        W_t = S.trend_switch(rising[:, None], rule='sma', lookback=lookback, step=21, cash_rate_daily=RF)
        self.assertEqual(int(np.argmax(W_t[:, 0] > 0)), c['trend_warmup_daily_returns'])  # first decision at row 210
        # 'invested' runs from row 210 to the last row, which is never held
        a = analyze(rising)
        self.assertEqual(a['sleeves']['exposure_trend'], float(W_t[lookback:].mean()))
        self.assertEqual(W_t.shape[0] - 1, a['sleeves']['trend']['sessions'])

    def test_short_history_has_no_sleeves_and_no_conventions(self):
        out = output(walk(3, closes=300))
        self.assertNotIn('sleeves', out.data)
        self.assertNotIn('Sleeve conventions', out.narrative)
        self.assertNotIn('전략 계산 관례', etf_korean(out.data))


class NativePaneTests(OfflineCase):
    """Both Native checks share one window: in this process a second ResearchWindow, built after the first
    was deleted, fails inside quantgen_desktop/wheel_guard.py (its shared event filter is gone)."""
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        from quantgen_desktop.app import ResearchWindow
        cls.app = QApplication.instance() or QApplication([])
        with patch('socket.socket.connect', side_effect=OSError('network forbidden')), \
             patch('requests.sessions.Session.request', side_effect=AssertionError('live I/O forbidden')):
            cls.window = ResearchWindow(auto_refresh=False, language='ko')

    @classmethod
    def tearDownClass(cls):
        from PyQt6.QtCore import QEvent
        cls.window.etf.clear_result()
        cls.window.deleteLater(); cls.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def setUp(self):
        super().setUp()
        self.window.set_language('ko')
        self.window.etf.clear_result()
        self.addCleanup(self.window.etf.clear_result)

    def test_shipped_251340_native_pane_export_and_commentary_carry_no_1e16(self):
        from quantgen_desktop.commentary import commentary_payload
        from quantgen_desktop.localization import UiLabel
        from quantgen_desktop.tools import fmt
        old_value = 4.642314207434303e16          # what every surface carried before
        for shown in (f'{old_value:.2f}', json.dumps(old_value), fmt(old_value), str(old_value)):
            self.assertRegex(shown, DEFECT)
        out = shipped_251340()
        self.assertEqual(old_sleeves(np.asarray(out.data['price'], float), True)['trend']['sharpe'], old_value)
        sl = out.data['sleeves']
        self.assertEqual((sl['trend']['sharpe'], sl['trend']['sharpe_status']), (None, SD.NO_VARIATION))
        self.assertEqual([sl[k]['sharpe_status'] for k in ('vol_target', 'buy_hold')], [SD.COMPUTED] * 2)
        variants = market_variants(out, 'etf')
        w = self.window
        pane = w.etf
        pane.show_result(out); pane.bind_output('etf', out)
        table = pane.tables['Descriptive sleeve backtests']
        self.assertEqual([table.item(0, 0).text(), table.item(0, 1).text()], ['trend', '—'])
        self.assertNotEqual(table.item(1, 1).text(), '—')
        texts = [s['text'] for s in pane.sections if s['type'] == 'text']
        note, conventions = SD.sharpe_note(sl), SD.conventions_text(sl['conventions'])
        self.assertIn(note, texts); self.assertIn(conventions, texts)
        # after the sleeve table and its 'bp per side' line, before the narrative
        order = [s.get('name') or s.get('text') or s['type'] for s in pane.sections]
        bp = next(i for i, x in enumerate(order) if 'bp per side' in x)
        self.assertEqual(order.index('Descriptive sleeve backtests') < bp < order.index(note)
                         < order.index(conventions) < order.index('sleeve_conventions'), True)
        self.assertIn({'type': 'sleeve_conventions', **sl['conventions']}, pane.sections)
        labels = {x.source_text: x for x in pane.findChildren(UiLabel) if getattr(x, 'localized_text', {})}
        self.assertEqual(labels[note].localized_text, {'en': note, 'ko': display_sharpe_note_korean(sl)})
        self.assertEqual(labels[conventions].localized_text,
                         {'en': conventions, 'ko': display_conventions_korean(sl['conventions'])})
        report = deepcopy(pane.report)
        sections = json.dumps(pane.sections, sort_keys=True, default=lambda v: v.item())
        with patch.object(w.jobs, 'start', side_effect=AssertionError('no recomputation')):
            for language in ('en', 'ko', 'en'):
                w.set_language(language)
                self.assertEqual(labels[note].text(), labels[note].localized_text[language])
                self.assertEqual(pane.report, report)
                self.assertEqual(json.dumps(pane.sections, sort_keys=True, default=lambda v: v.item()), sections)
        raw = report_bytes(pane.report).decode()
        self.assertIn('"sleeve_conventions"', raw)
        json.dumps(wf.payload(out.data)['sleeves'], allow_nan=False)
        blobs = [raw, json.dumps(commentary_payload(pane.report), ensure_ascii=False), out.narrative,
                 variants['ko'], json.dumps(wf.payload(out.data))]
        for locale in (None, 'ko_KR'):
            with ZipFile(BytesIO(report_bytes(pane.report, bundle=True, locale=locale))) as z:
                blobs += [z.read(n).decode() for n in z.namelist()]
        blobs.append('\n'.join(x.text() for x in pane.findChildren(UiLabel)))
        for blob in blobs:
            self.assertNotRegex(blob, DEFECT)
        commentary = commentary_payload(pane.report)
        self.assertIn(note, [s.get('text') for s in commentary['sections']])
        self.assertIn('sleeve_conventions', [s['type'] for s in commentary['sections']])
        # The Korean-locale HTML export keeps these dynamic notes in English (as the decay and LETF notes).
        with ZipFile(BytesIO(report_bytes(pane.report, bundle=True, locale='ko_KR'))) as z:
            html = z.read('report.html').decode()
        self.assertIn('Sharpe n/a for the trend switch', html)
        self.assertIn('Sleeve conventions:', html)

    def test_native_pane_valid_input_states_the_conventions_without_a_note(self):
        # The usual case: every Sharpe defined, so no n/a note, but the conventions text and section are there.
        from quantgen_desktop.commentary import commentary_payload
        from quantgen_desktop.localization import UiLabel
        from quantgen_desktop.tools import fmt
        out = execute_etf(ETFRequest(source='synthetic', code='069500', days=504))
        sl = out.data['sleeves']
        self.assertTrue(all(sl[k]['sharpe_status'] == SD.COMPUTED for k in SD.SLEEVES))
        w = self.window
        pane = w.etf
        pane.show_result(out); pane.bind_output('etf', out)
        table = pane.tables['Descriptive sleeve backtests']
        self.assertEqual([table.item(r, 1).text() for r in range(3)],
                         [fmt(sl[k]['sharpe']) for k in ('trend', 'vol_target', 'buy_hold')])
        texts = [s['text'] for s in pane.sections if s['type'] == 'text']
        conventions = SD.conventions_text(sl['conventions'])
        self.assertIn(conventions, texts)
        self.assertFalse(any(t.startswith('Sharpe n/a') for t in texts))
        self.assertEqual([s for s in pane.sections if s['type'] == 'sleeve_conventions'],
                         [{'type': 'sleeve_conventions', **sl['conventions']}])
        order = [s.get('name') or s.get('text') or s['type'] for s in pane.sections]
        bp = next(i for i, x in enumerate(order) if 'bp per side' in x)
        self.assertEqual(order.index('Descriptive sleeve backtests') < bp < order.index(conventions)
                         < order.index('sleeve_conventions'), True)
        labels = {x.source_text: x for x in pane.findChildren(UiLabel) if getattr(x, 'localized_text', {})}
        self.assertEqual(labels[conventions].localized_text,
                         {'en': conventions, 'ko': display_conventions_korean(sl['conventions'])})
        commentary = commentary_payload(pane.report)
        self.assertIn(conventions, [s.get('text') for s in commentary['sections']])
        self.assertIn('sleeve_conventions', [s['type'] for s in commentary['sections']])
        self.assertIn('"sleeve_conventions"', report_bytes(pane.report).decode())


class FletPageTests(OfflineCase):
    def flet_run(self, code, sessions):
        runner = Mock(return_value=insights.Analysis('Synthetic commentary', 'fixture-model'))
        page = Mock()
        page.run_thread.side_effect = lambda worker: worker()
        with patch.object(etf_page, 'load_cards', return_value=()), \
             patch.object(insights, 'ai_ready', return_value=True), \
             patch.object(insights, 'deep_analysis', runner):
            root = etf_page.build_etf_page(page)
            fields = {c.label: c for c in controls(root) if isinstance(c, (ft.TextField, ft.Dropdown))}
            fields['Source'].value = 'synthetic'
            fields['ETF code'].value = code
            fields['Sessions'].value = str(sessions)
            next(c for c in controls(root) if isinstance(c, ft.Button) and c.content == 'Analyze').on_click(None)
            next(c for c in controls(root) if isinstance(c, ft.Button) and c.content == 'Deep analysis').on_click(None)
        runner.assert_called_once()
        return root, runner.call_args.args[1]

    def test_real_flet_page_251340_tile_is_na_and_the_ai_payload_has_no_1e16(self):
        root, payload = self.flet_run('251340', 400)
        t = tiles(root)
        value, tooltip = t['Trend switch Sharpe']
        self.assertEqual(value, 'n/a')
        self.assertTrue(tooltip.startswith('Not defined: the daily P&L did not vary'))
        for label in ('Vol-target Sharpe', 'Buy & hold Sharpe'):
            self.assertRegex(t[label][0], r'^-?\d+\.\d\d$')
            self.assertEqual(t[label][1], SD.SHARPE_CONVENTIONS_POINTER)   # a pointer, not the paragraph again
        texts = list(all_strings(root))
        for s in texts:
            self.assertNotRegex(s, DEFECT)
        self.assertTrue(any(s.startswith('Sleeve conventions: the trend switch first decides') for s in texts))
        self.assertTrue(any('Sharpe n/a for the trend switch' in s for s in texts))     # the narrative
        # the notice under the sleeve row (a banner, not only the tile tooltips)
        self.assertEqual(notice_texts(block_after_sleeve_row(root)),
                         [SD.conventions_text(payload['sleeves']['conventions'])])
        self.assertIsNone(payload['sleeves']['trend']['sharpe'])
        self.assertEqual(payload['sleeves']['trend']['sharpe_status'], SD.NO_VARIATION)
        self.assertEqual(payload['sleeves']['conventions']['window_daily_returns'], 399)
        json.dumps(payload['sleeves'], allow_nan=False)
        raw = json.dumps(payload)
        self.assertNotRegex(raw, DEFECT)

    def test_real_flet_page_valid_tiles_keep_their_values(self):
        root, payload = self.flet_run('069500', 504)
        expected = execute_etf(ETFRequest(source='synthetic', code='069500', days=504)).data['sleeves']
        t = tiles(root)
        conventions = SD.conventions_text(expected['conventions'])
        for label, key in (('Trend switch Sharpe', 'trend'), ('Vol-target Sharpe', 'vol_target'),
                           ('Buy & hold Sharpe', 'buy_hold')):
            self.assertEqual(t[label], (f"{expected[key]['sharpe']:.2f}", SD.SHARPE_CONVENTIONS_POINTER))
        self.assertEqual(t['Trend MDD'][0], f"{expected['trend']['max_drawdown']:.0%}")
        self.assertIsNone(t['Trend MDD'][1])
        # The notice directly under the sleeve row is a banner with the conventions text, not only the tooltips.
        self.assertEqual(notice_texts(block_after_sleeve_row(root)), [conventions])
        self.assertEqual(notice_texts(root).count(conventions), 1)
        self.assertEqual(payload['sleeves']['trend']['sharpe'], expected['trend']['sharpe'])
        self.assertEqual(payload['sleeves']['trend']['sharpe_status'], SD.COMPUTED)


    def test_defined_sharpe_tooltip_is_a_short_pointer_with_a_korean_pair(self):
        from core.ui_legacy_messages import static_text
        pointer, korean = SD.SHARPE_CONVENTIONS_POINTER, SD.SHARPE_CONVENTIONS_POINTER_KO
        display_korean=('준비 구간을 포함한 전체 기간의 샤프 지수이며, 현금 금리를 뺀 초과 수익 기준이 '
                        '아닙니다. 계산 관례는 이 줄 아래 안내에 있습니다.')
        self.assertLess(len(pointer), 160)                      # not the whole conventions paragraph again
        self.assertEqual(static_text(pointer, 'ko'), display_korean)  # display-only approved terminology
        self.assertEqual(static_text(display_korean, 'en'), pointer)
        self.assertIn('샤프비율이며', korean)  # the core source text remains unchanged
        self.assertEqual(static_text(korean, 'en'), pointer)

if __name__ == '__main__':
    unittest.main()
