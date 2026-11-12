"""Native Derivatives, ETF, Crypto and KRX panes using shared workflows.

Owner UI port (issues 03, 04, 11, 14; 2026-11-10): the Korean window reads these results in Korean
(headings, row names, codes beside their meaning), numbers carry thousands separators, the derivatives
board is chosen automatically, and every narrative is headed bullets. Display only: `pane.sections`,
`pane.report` and every request stay exactly as before.
"""
from dataclasses import asdict
import math
import re
import numpy as np
from PyQt6.QtCore import Qt

from core.research.market_analysis import DerivativesRequest, ETFRequest, CryptoRequest, KRXRequest
from core.research.funding_disclosure import funding_text
from core.research.letf_disclosure import letf_text, letf_unavailable_text
from core.research.decay_disclosure import decay_value, decay_text
from core.research.quote_coverage import quote_coverage_text
from core.research.sleeve_disclosure import conventions_text, sharpe_note
from .market_narrative_language import display_conventions_korean, display_sharpe_note_korean
from core.research.option_disclosure import box_computed, hedge_korean, hedge_text, mfiv_strip
from core.research.crypto_workflow import cost_basis_text, holdings_summary
from .tools import ToolPane, number, fmt
from .market_diagnostics_language import decay_korean, funding_korean, coverage_korean
from .market_narrative_language import market_variants, letf_korean, letf_unavailable_korean
from .market_narrative_language import display_korean, display_variants

# Raw field keys shown as row names or column titles: an English label for the screen (the Korean
# comes from the catalogue, owner_ui_language/market.py). The export keeps the keys.
FIELD_LABELS = {
    'ticker': 'Code', 'code': 'Code', 'name': 'Name', 'price': 'Last price', 'change': 'Change',
    'change_pct': 'Change %', 'volume': 'Volume', 'market_cap': 'Market cap', 'open': 'Open', 'high': 'High',
    'low': 'Low', 'close': 'Close', 'currency': 'Currency', 'per': 'PER', 'eps': 'EPS', 'sector': 'Sector',
    'listed_shares': 'Listed shares', 'source': 'Source', 'as_of': 'As of', 'date': 'Date',
    'nav': 'NAV', 'premium_pct': 'Premium %', 'tracking_error_pct': 'Tracking error %', 'aum': 'AUM',
    'cu_units': 'CU shares', 'shares': 'Shares outstanding', 'lp_holding_pct': 'LP holding %', 'listed': 'Listed',
    'target_index': 'Target index', 'dividend_cycle': 'Dividend cycle', 'type': 'Type', 'turnover': 'Turnover',
    'market': 'Market', 'level': 'Level', 'title': 'Title', 'filer': 'Filer', 'receipt_no': 'Receipt',
    'corp_name': 'Company', 'statement': 'Statement', 'account': 'Account', 'this_term': 'This term',
    'prev_term': 'Prev term', 'n': 'Observations (n)', 'last_ratio': 'Last ETH/BTC ratio',
    'adf_p': 'ADF p-value', 'z_2y': '2-year z-score', 'verdict': 'Unit-root test',
    'last': 'Last premium %', 'mean': 'Mean premium %', 'sd': 'Premium SD %', 'z': 'Premium z',
    'abs_mean': 'Mean |premium| %',
}
FIELD_ROLE = Qt.ItemDataRole.UserRole + 811  # the raw key of a relabelled row
SLEEVE_LABELS = {'trend': 'Trend switch', 'vol_target': 'Vol target', 'buy_hold': 'Buy & hold'}
ENGINE_LABELS = {'gbm': 'GBM', 'garch_t': 'GARCH-t'}
# Board/workflow labels in the derivatives header line (as the Flet page shows them, PR #98).
_VALUE_KO = {'synthetic': '합성', 'assumed': '가정', 'DEMO': '시연용', 'input': '직접 입력',
             'CD 91d (KIS)': 'CD 91일물 (KIS)', 'kis': 'KIS', 'SYNTHETIC': '합성 데이터'}
_STUDY_KO = {'NOT_LOADED': '불러오지 않음(NOT_LOADED)', 'PROVIDED': '불러옴'}


def _vk(value):
    return _VALUE_KO.get(str(value), str(value))


def number_text(value):
    """A number as the screen shows it (owner issue 03): thousands separators, at most four decimals,
    small ratios to four significant figures; None and non-finite values as —."""
    if value is None:
        return '—'
    v = float(value)
    if not math.isfinite(v):
        return '—'
    if v.is_integer() and abs(v) < 1e15:
        return f'{int(v):,}'
    if abs(v) >= 1:
        return f'{v:,.4f}'.rstrip('0').rstrip('.')
    return f'{v:.4g}'


def show_cells(table, rows, *, labels=None, label_columns=(0,), numbers=True):
    """Screen-only cell text for a result table built from raw rows; the rows (and the export) are untouched.

    Typed numbers get `number_text` (and lose any caption role, so a language switch cannot put the
    raw value back); None shows —; a raw key in `label_columns` found in `labels` is shown by its
    English label, which the catalogue translates."""
    from .localization import CAPTION_ROLE
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            item = table.item(r, c)
            if item is None:
                continue
            if labels and c in label_columns and isinstance(value, str) and value in labels:
                item.setData(FIELD_ROLE, value)
                item.setData(CAPTION_ROLE, labels[value])
                continue
            if value is None or (numbers and isinstance(value, (int, float, np.integer, np.floating))
                                 and not isinstance(value, (bool, np.bool_))):
                item.setData(CAPTION_ROLE, None)
                item.setText(number_text(value))
                if value is not None:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


def label_headers(table, labels=FIELD_LABELS):
    """Raw-key column titles by their English labels; the catalogue gives the Korean."""
    for c in range(table.columnCount()):
        item = table.horizontalHeaderItem(c)
        if item is not None and item.text() in labels:
            item.setText(labels[item.text()])


def hide_rows(table, fields):
    """Hide Field/Value rows on screen only; the report sections keep every row."""
    for row in range(table.rowCount()):
        item = table.item(row, 0)
        if item is not None and (item.data(FIELD_ROLE) or item.text()) in fields:
            table.setRowHidden(row, True)


class DerivativesPane(ToolPane):
    def __init__(self):
        super().__init__('KOSPI200 board', [('board', 'Options, futures & hedge P&L')],
            [('kis', 'KIS · option board'), ('synthetic', 'Synthetic demo')],
            {'board': [('expiry', 'Expiry · blank = nearest', ''), ('rate', 'Rate % · blank = provider', ''),
                       ('engine', 'Hedge engine', [('gbm', 'GBM'), ('garch_t', 'GARCH-t')]),
                       ('paths', 'Simulation paths', 3000), ('horizon', 'Horizon sessions · blank = expiry', '')]})

    @staticmethod
    def automatic_board():
        """KIS when its keys are set, else the labelled synthetic demo board (as the Flet page, PR #98)."""
        import config
        return 'kis' if config.kis_ready() else 'synthetic'

    def hide_source(self):
        """No board selector (owner issues 04/12): the app picks the board itself instead of failing on a
        KIS board without keys that the user can no longer switch away from."""
        super().hide_source()
        self._auto_board = self.automatic_board()
        self.source.setCurrentIndex(max(0, self.source.findData(self._auto_board)))

    def make_request(self):
        v = self.values()
        source = self.source.currentData()
        if self.source.isHidden() and source == getattr(self, '_auto_board', None):
            # Keys set (or removed) after start-up count: re-pick while the choice is still automatic.
            source = self._auto_board = self.automatic_board()
            self.source.setCurrentIndex(max(0, self.source.findData(source)))
        return DerivativesRequest(source, v['expiry'].strip(), number(v['rate'], optional=True),
            v['engine'], number(v['paths'], integer=True), number(v['horizon'], optional=True, integer=True))

    def show_result(self, out):
        self.clear_result()
        s = out.data
        b, fit, sim = s['basis'], s['svi'], s['hedge']
        header = (f"{s['source']} · expiry {s['expiry']} → {s['expiry_date']} · as of {s['as_of']}\n"
                  f"Session {s['session']} · {s['n_quotes']} strikes · rate {s['rate']:.3%} ({s['rate_source']})")
        self.text(header, localized={'en': header, 'ko':
            f"{_vk(s['source'])} · 만기 {_vk(s['expiry'])} → {s['expiry_date']} · 기준 {_vk(s['as_of'])}\n"
            f"가격 세션 {_vk(s['session'])} · 행사가격 {s['n_quotes']}개 · 금리 {s['rate']:.3%} ({_vk(s['rate_source'])})"})
        if s['source'] == 'synthetic':
            self.text('SYNTHETIC · 모든 시세는 합성 데이터입니다.', localized={
                'en': 'Synthetic board: a smile-shaped demo chain, not market quotes.',
                'ko': '합성 보드: 스마일 모양으로 만든 시연용 옵션 체인이며 시장 호가가 아닙니다.'})
        if not s.get('live_quotes', True):
            self.text('Last prints only · 장외/마감 시 호가는 동시 체결 가능한 가격이 아닙니다.', localized={
                'en': 'Last prints only · off-hours and closed-market prints are not simultaneously tradable prices.',
                'ko': '마지막 체결가만 · 장외/마감 시 호가는 동시 체결 가능한 가격이 아닙니다.'})
        if s.get('quotes_note'):
            self.text(s['quotes_note'], localized={'en': s['quotes_note'], 'ko': s['quotes_note']})
        strip, chk = mfiv_strip(s), s.get('box_check') or {}
        self.result_table('Futures & volatility', ['Metric', 'Value'], [
            ('Parity forward', fmt(s['F'])), ('Future', fmt(s['futures']['price'])), ('Basis · points', fmt(b.basis_pts)),
            ('Fair value', fmt(b.fair)), ('Mispricing · bp of spot', fmt(b.mispricing_bp)),
            ('Implied funding', fmt(b.implied_rate, 'pct')), ('KIS theoretical gap · points', fmt(b.theo_gap_pts)),
            ('ATM IV', fmt(s['atm'].iv, 'pct')), ('Model-free IV', fmt(s['mfiv'].get('vol'), 'pct')),
            # §10 M4-N9: the strip's strike range; outside it the omitted wings bias MFIV downward
            ('Model-free IV strike range · % of forward',
             f"{fmt(strip['lower_moneyness'], 'pct')} / {fmt(strip['upper_moneyness'], 'pct')}"
             if strip['status'] == 'COMPUTED' else 'UNAVAILABLE'),
            ('SVI RMSE · vol points', fmt(fit.rmse_volpts)), ('SVI rho', fmt(fit.rho)),
            ('Butterfly arbitrage free', str(fit.arbitrage_free)), ('IV reconciliation gap · vol points', fmt(s['reconcile']['median_volpts'])),
            # §10 M4-N4: an adjacent-strike box is a quote-quality check, not a funding rate
            ('Box rate · adjacent strikes, mid quotes', fmt(s['box']['rate'], 'pct') if s['box'] else 'UNAVAILABLE'),
            ('Box rate at quotes · bought / sold',
             f"{fmt(chk.get('rate_bought_at_quotes'), 'pct')} / {fmt(chk.get('rate_sold_at_quotes'), 'pct')}"
             if box_computed(s) else 'UNAVAILABLE'),
            ('Box sensitivity · bp per 0.01 point', fmt(chk['bp_per_0_01pt']) if box_computed(s) else 'UNAVAILABLE'),
            ('RND integral', fmt(s['rnd']['integral']))], localized_columns=[0, 1])
        from core.ficc.equity_deriv import svi_vol
        points = sorted(s['points'], key=lambda p:p.strike)
        self.line('Implied volatility smile', [p.strike for p in points],
            [('Black-76 IV %', [p.iv*100 for p in points]),
             ('SVI IV %', svi_vol(fit, np.array([p.log_moneyness for p in points]))*100)], 'Strike', 'Volatility · %')
        rnd = s['rnd']
        self.line('Risk-neutral density', rnd['strikes'], [('Q density', rnd['density'])], 'Index points', 'Density')
        self.result_table('Hedge simulation', ['Metric', 'Value'], [
            ('Engine', sim.engine), ('Paths / sessions', f'{sim.n_paths} / {sim.horizon}'),
            ('Mean P&L · bp', fmt(sim.mean_pnl_bp)), ('SE · bp', fmt(sim.se_bp)), ('CVaR95 · bp', fmt(sim.cvar95_bp)),
            ('Hedge volatility', fmt(sim.sigma_hedge, 'pct')), ('Break-even realised vol', fmt(sim.breakeven_vol, 'pct')),
            ('Identity slope / R²', f'{sim.identity_slope:.4f} / {sim.identity_r2:.4f}')], localized_columns=[0, 1])
        engine = self.tables['Hedge simulation'].item(0, 1)
        if engine is not None and sim.engine in ENGINE_LABELS:  # 'gbm' -> 'GBM' on screen only
            from .localization import CAPTION_ROLE
            engine.setData(CAPTION_ROLE, ENGINE_LABELS[sim.engine]); engine.setText(ENGINE_LABELS[sim.engine])
        coverage = s['quote_coverage']
        self.result_table('Static arbitrage checks', ['Check', 'Violations', 'Tests', 'Status'],
            [(key, str(check['violations']) if check['tests'] else 'NOT_RUN', check['tests'], check['status'])
             for key, check in coverage['static'].items()], localized_columns=[0, 1, 3])
        coverage_source = quote_coverage_text(coverage)
        self.text(coverage_source, localized={'en': coverage_source, 'ko': display_korean(coverage_korean(coverage))})
        self.sections.append({'type': 'quote_coverage', **coverage})
        hedge_note = hedge_text(s)
        if hedge_note:  # §10 M4-N7
            self.text(hedge_note, localized={'en': hedge_note, 'ko': hedge_korean(s)})
        for kind, value in (('hedge_scope', s.get('hedge_scope')), ('box_check', s.get('box_check')),
                            ('mfiv_strip', strip)):
            if value is not None:
                self.sections.append({'type': kind, **value})
        self.finished(out.narrative, localized=display_variants(market_variants(out, 'derivatives')))


class ETFPane(ToolPane):
    def __init__(self):
        super().__init__('ETF structure', [('etf', 'NAV, basket & sleeve rules')],
            [('auto', 'Auto · KIS / FMP'), ('kis', 'KIS'), ('fmp', 'FMP'), ('yfinance', 'Yahoo'), ('synthetic', 'Synthetic demo')],
            {'etf': [('code', 'ETF code', '069500'), ('days', 'Sessions', 504),
                     ('letf_benchmark', 'LETF comparison', [
                         ('zero_rate_reference', 'Zero-rate reference'),
                         ('total_return', 'Total-return scenario'), ('price_return', 'Price-return scenario')]),
                     ('letf_funding_rate', 'Funding rate % · continuous annual', ''),
                     ('letf_annual_fee', 'Fee % · continuous annual', ''),
                     ('letf_dividend_yield', 'Dividend yield % · price-return only', '')]})
        from .app import label
        self.input_box.layout().addWidget(label(
            'LETF only: leave rates blank for the zero-rate reference. Scenarios require funding and fee inputs; '
            'add a dividend yield only for a price-return comparison. Inputs are assumptions, not verified fund costs.', 'caption'))

    def make_request(self):
        v = self.values()
        return ETFRequest(self.source.currentData(), v['code'], number(v['days'], integer=True),
            letf_funding_rate=number(v['letf_funding_rate'], optional=True, scale=.01),
            letf_annual_fee=number(v['letf_annual_fee'], optional=True, scale=.01),
            letf_benchmark=v['letf_benchmark'],
            letf_dividend_yield=number(v['letf_dividend_yield'], optional=True, scale=.01))

    def show_result(self, out):
        self.clear_result()
        d = out.data
        header = (f"{d['code']} · {d['data_source']} · {d['dates'][0]} → {d['dates'][-1]}\n"
                  f"Sleeve price basis: {d['sleeve_basis']} · study cards: {out.study_status}")
        self.text(header, localized={'en': header, 'ko':
            f"{d['code']} · {_vk(d['data_source'])} · {d['dates'][0]} → {d['dates'][-1]}\n"
            f"전략별 가격 기준: {display_korean(str(d['sleeve_basis']))} · 연구 카드: "
            f"{_STUDY_KO.get(out.study_status, out.study_status)}"})
        if d['data_source'] == 'SYNTHETIC':
            self.text('SYNTHETIC · 시장 관측값이 아닙니다.', localized={
                'en': 'Synthetic data: a simulated series, not market observations.',
                'ko': '합성 데이터: 시뮬레이션한 시계열이며 시장 관측값이 아닙니다.'})
        series = [('Price', d['price'])]
        if d.get('nav') is not None: series.append(('NAV', d['nav']))
        self.line('ETF price / NAV', range(len(d['dates'])), series, 'Observations', 'Price / NAV')
        # Owner, 2026-11-04: no observation-date row on screen (as_of is the request date); the export keeps it.
        if d.get('quote'):
            rows = list(d['quote'].items())
            self.result_table('Quote', ['Field', 'Value'], rows, localized_columns=[0])
            show_cells(self.tables['Quote'], rows, labels=FIELD_LABELS)
            hide_rows(self.tables['Quote'], ('as_of',))
        if d.get('premium_stats'):
            self.line('NAV premium', range(len(d['dates'])), [('Premium %', d['premium_pct'])], 'Observations', 'Premium · %')
            ps = d['premium_stats']
            rows = ([(k, fmt(v)) for k,v in ps.items() if k not in {'decay','half_life'}] +
                    [('AR(1) amplitude half-life · observations',decay_value(ps.get('decay')))])
            self.result_table('Premium statistics', ['Metric', 'Value'], rows, localized_columns=[0, 1])
            show_cells(self.tables['Premium statistics'], rows, labels=FIELD_LABELS, numbers=False)
            decay_source = decay_text(ps.get('decay'))
            self.text(decay_source, localized={'en': decay_source, 'ko': decay_korean(ps.get('decay'))})
        sleeves = d.get('sleeves')
        if sleeves:
            rows = [[key, fmt(sleeves[key]['sharpe']), fmt(sleeves[key]['max_drawdown'], 'pct'),
                     d['verdicts'].get('vol' if key == 'vol_target' else key, 'NOT_APPLICABLE') if out.study_status=='PROVIDED' else 'NOT_LOADED']
                    for key in ('trend', 'vol_target', 'buy_hold')]
            self.result_table('Descriptive sleeve backtests', ['Sleeve', 'Sharpe', 'Max drawdown', 'Study decision'],
                              rows, localized_columns=[0, 3])
            show_cells(self.tables['Descriptive sleeve backtests'], rows, labels=SLEEVE_LABELS, numbers=False)
            self.line('Trend switch vs buy & hold', range(len(sleeves['equity_trend'])),
                [('Trend', sleeves['equity_trend']), ('Buy & hold', sleeves['equity_bh'])], 'Sessions', 'Equity · starts at 1')
            self.text(f"{sleeves['cost_bps']:g} bp per side · in-sample descriptive results, not a new study decision.")
            # §10 NEW-M6-04: the table shows '—' for an undefined Sharpe; this line says why (also in the export
            # and the AI commentary, which carry the sections, not the sleeve dicts).
            note = sharpe_note(sleeves)
            if note:
                self.text(note, localized={'en': note, 'ko': display_korean(display_sharpe_note_korean(sleeves))})
            # §10 NEW-M6-05: the conventions behind these numbers, as text and as an export section.
            c = sleeves.get('conventions')
            if c:
                conventions = conventions_text(c)
                self.text(conventions, localized={'en': conventions, 'ko': display_korean(display_conventions_korean(c))})
                self.sections.append({'type': 'sleeve_conventions', **c})
        if d.get('components'):
            rows = sorted(d['components'], key=lambda c:-(c.get('weight_pct') or 0))
            self.result_table('Constituents', ['Code', 'Name', 'Weight %'], [[r['code'],r['name'],fmt(r['weight_pct'])] for r in rows])
        lt = d.get('letf')
        if lt and lt.get('rows'):
            self.result_table('AZ variance proxies · bp',
                ['Sessions', 'Proxy', 'Variance term', 'Funding term', 'Fee assumption term', 'Dividend term', 'Zero-rate reference'],
                [[r['sessions'], fmt(r['drag_bp']), fmt(r['variance_bp']), fmt(r.get('funding_bp')),
                  fmt(r['fee_bp']), fmt(r.get('dividend_bp')), fmt(r.get('reference_drag_bp'))] for r in lt['rows']])
            index_line = (f"Index: {lt['index_source']} · prior-quarter variance AZ proxy "
                          f"{lt['last_quarter_drag_bp']:.2f} bp · GARCH converged={lt['converged']}")
            self.text(index_line, localized={'en': index_line, 'ko':
                f"지수: {lt['index_source']} · 직전 분기 분산 AZ 대용값 {lt['last_quarter_drag_bp']:.2f} bp · "
                f"GARCH 수렴={'예' if lt['converged'] else '아니오'}"})
            self.text(letf_text(lt), localized={'en': letf_text(lt), 'ko': letf_korean(lt)})
            self.sections.append({'type':'letf_interpretation', **lt['interpretation']})
        elif lt:
            self.text(letf_unavailable_text(lt), localized={'en': letf_unavailable_text(lt),
                                                         'ko': letf_unavailable_korean(lt)})
            self.sections.append({'type': 'letf_unavailable', **lt})
        self.finished(out.narrative, localized=display_variants(market_variants(out, 'etf')))


class CryptoPane(ToolPane):
    def __init__(self):
        super().__init__('Crypto research', [('crypto', 'Premium, funding & volatility')],
            [('live', 'Upbit + Binance · public data'), ('synthetic', 'Synthetic demo')],
            {'crypto': [('days', 'Calendar days', 730), ('balances', 'Upbit account read', [(False, 'Off · public data only'), (True, 'Read holdings with configured read-only key')])]})

    def make_request(self):
        v = self.values()
        return CryptoRequest(self.source.currentData(), number(v['days'], integer=True), v['balances'])

    def show_result(self, out):
        self.clear_result()
        d, g = out.data, out.data['garch']
        kp, fc = d['kimchi'], d['funding']
        header = (f"{d['source']} · USD/KRW: {d['usdkrw_source']} · {d['btc_dates'][0]} → {d['btc_dates'][-1]}\n"
                  f"Public market analysis · no order submission · study cards: {out.study_status}")
        self.text(header, localized={'en': header, 'ko':
            f"{_vk(d['source'])} · USD/KRW 환율: {_vk(d['usdkrw_source'])} · {d['btc_dates'][0]} → {d['btc_dates'][-1]}\n"
            f"공개 시장 분석 · 주문 제출 없음 · 연구 카드: {_STUDY_KO.get(out.study_status, out.study_status)}"})
        if d['source']=='SYNTHETIC':
            self.text('SYNTHETIC · 모든 시계열은 합성 데이터입니다.', localized={
                'en': 'Synthetic data: every series here is simulated.',
                'ko': '합성 데이터: 이 화면의 모든 시계열은 시뮬레이션입니다.'})
        decay_source = decay_text(getattr(kp, "decay", None))
        self.text(decay_source, localized={'en': decay_source, 'ko': decay_korean(getattr(kp, 'decay', None))})
        eth_decay_source = 'ETH/BTC: ' + decay_text(d['ethbtc'].get('decay'))
        self.text(eth_decay_source, localized={'en': eth_decay_source,
                                             'ko': 'ETH/BTC: ' + decay_korean(d['ethbtc'].get('decay'))})
        self.result_table('Premium / volatility', ['Metric', 'Value'], [
            ('Kimchi premium · %',fmt(kp.last_pct)), ('Premium z',fmt(kp.last_z)),
            ('AR(1) amplitude half-life · observations',decay_value(getattr(kp, "decay", None))),
            ('Funding annualized · %', fmt(fc.last_ann_pct) if fc else 'UNAVAILABLE'),
            ('Funding percentile', fmt(fc.percentile,'pct') if fc else 'UNAVAILABLE'),
            ('BTC conditional vol · 365 days',fmt(g['cond_vol_365'],'pct')), ('GARCH nu',fmt(g['nu'])),
            ('GARCH persistence',fmt(g['persistence'])), ('Converged',str(g['converged'])), ('At bound',', '.join(g['at_bound']))],
            localized_columns=[0, 1])
        self.line('Kimchi premium', range(len(kp.dates)), [('Premium %',kp.premium_pct)], 'Days', 'Premium · %')
        if fc:
            funding_source = funding_text(fc)
            self.text(funding_source, localized={'en': funding_source, 'ko': funding_korean(fc)})
            self.sections.append({'type': 'funding_diagnostic', 'bootstrap_p': None,
                                  'bootstrap_status': 'RETIRED_INVALID_IID',
                                  'diagnostic': getattr(fc, 'diagnostic', {})})
        if fc: self.line('Perpetual funding', range(len(fc.dates)), [('7-day mean annualized %',fc.carry_ann_pct)], 'Days', 'Annualized · %')
        else: self.text('Funding unavailable · insufficient or invalid funding history.')
        px = d['btc']; series=[('BTCUSDT',px)]
        for n in (50,200):
            if len(px)>=n: series.append((f'SMA{n}', np.r_[np.full(n-1,np.nan),np.convolve(px,np.ones(n)/n,mode='valid')]))
        self.line('Bitcoin',range(len(px)),series,'Calendar days','USDT per BTC')
        rows = ([(k,v) for k,v in d['ethbtc'].items() if k not in {'decay','half_life_days'}] +
                [('AR(1) amplitude half-life · observations',decay_value(d['ethbtc'].get('decay')))])
        self.result_table('ETH/BTC', ['Metric','Value'], rows, localized_columns=[0, 1])
        show_cells(self.tables['ETH/BTC'], rows, labels=FIELD_LABELS)
        rows = [[r['day'],r['n'],fmt(r['mean_ret_pct']),fmt(r['vol_pct']),fmt(r['mean_volume'])] for r in d['weekday']['rows']]
        self.result_table('Weekday observations', ['Day','n','Mean return %','Vol %','Mean volume'], rows,
                          localized_columns=[0])
        label_headers(self.tables['Weekday observations'], {'n': 'Observations (n)'})
        self.text(f"Weekday Bonferroni p={d['weekday']['return_effect_p_bonferroni']:.4g} · weekend volume ratio={d['weekday']['weekend_volume_ratio']:.3f}")
        if d.get('balances'):
            self.result_table('Upbit holdings · read only', ['Currency','Total','Average buy price','KRW value'],
                [[b['currency'],fmt(b['total']),cost_basis_text(b),fmt(b['krw_value'])]
                 for b in d['balances']])
            label_headers(self.tables['Upbit holdings · read only'], {'Total': 'Total quantity'})
            held = holdings_summary(d['balances'])
            if not held['complete']:  # §10 NEW-M6-14/22: a missing price is shown as missing, never as 0
                names = ', '.join(held['unvalued'])
                partial = f'No KRW price for {names}: their value is not shown and is not in any total.'
                # Named as a holdings section: like the holdings table, it never enters AI commentary (NEW-M6-18).
                self.text(partial, name='Upbit holdings note',
                          localized={'en': partial,
                                     'ko': f'{names}의 원화 시세가 없어 평가액을 표시하지 않으며 합계에도 넣지 않습니다.'})
        elif out.request.include_balances: self.text('Holdings unavailable · verify the configured read-only connection. No account values loaded.')
        self.finished(out.narrative, localized=display_variants(market_variants(out, 'crypto')))


class KRXPane(ToolPane):
    def __init__(self):
        tools=[('quote','Quote'),('daily','Daily OHLCV'),('filings','DART disclosures'),
               ('financials','DART financials'),('snapshot','Whole market'),('indices','Indices')]
        super().__init__('KRX · read only', tools, [('gateway','Existing provider routing')],
                         {k:[('code','Six digit KRX code','005930')] for k,_ in tools})

    def make_request(self):
        return KRXRequest(self.tool.currentData(), self.values()['code'].strip())

    def show_result(self, out):
        self.clear_result()
        a = out.answer
        # Owner, 2026-11-04: no provider line or rows; only an unavailable or non-KIS source is named.
        if not a.ok or (a.source or '').upper() != 'KIS':
            self.text(f'Provider: {a.source or "UNAVAILABLE"}')
        if not a.ok:
            from core.research.presentation import safe_detail
            reason = safe_detail(a.reason)
            self.text(reason, localized={'en': reason, 'ko': krx_reason_korean(reason)})
            self.status.setText('UNAVAILABLE · 공급자 응답을 확인하세요. 대체 값을 생성하지 않습니다.')
            return
        data = a.data
        if out.request.tool == 'quote':
            # Owner, 2026-11-04: no provider or time rows on screen; the export keeps both (attribution).
            # A KRX fallback is a previous session's close, so its date stays visible.
            rows = list(asdict(data).items())
            self.result_table('Quote', ['Field','Value'], rows, localized_columns=[0])
            show_cells(self.tables['Quote'], rows, labels=FIELD_LABELS)
            kis = (a.source or '').upper() == 'KIS'
            hide_rows(self.tables['Quote'], ('source', 'as_of') if kis else ('source',))
        elif data:
            keys = list(dict.fromkeys(k for row in data for k in row))
            rows = [[r.get(k,'—') for k in keys] for r in data[:300]]
            self.result_table('Observations',keys,rows)
            show_cells(self.tables['Observations'], rows)
            label_headers(self.tables['Observations'])
            self.text(f'{len(data)} rows · first 300 displayed')
        else: self.text('EMPTY · 공급자가 빈 결과를 반환했습니다.')
        closing = 'Read-only market observations; no order or account operation.'
        self.finished(closing, localized={'en': closing,
                                          'ko': '시장 관측 조회 전용이며 주문이나 계좌 조작을 수행하지 않습니다.'})


_KRX_REASONS = (
    (re.compile(r'no provider returned (\S+) \((.+)\)'),
     lambda m: f"{m[1]}: 응답한 제공처가 없습니다 ({m[2].replace('KIS not configured', 'KIS 미설정')})"),
    (re.compile(r'no index provider responded'), lambda m: '지수 시세를 응답한 제공처가 없습니다'),
    (re.compile(r'(filings|financials) need OPENDART_API_KEY \(free from dart\.fss\.or\.kr\)'),
     lambda m: ('공시' if m[1] == 'filings' else '재무제표') + ' 조회에는 OPENDART_API_KEY가 필요합니다 (dart.fss.or.kr에서 무료 발급)'),
)


def krx_reason_korean(reason):
    """The gateway's authored refusal sentences in Korean; a provider's own message stays verbatim."""
    for pattern, render in _KRX_REASONS:
        m = pattern.fullmatch(reason)
        if m:
            return render(m)
    return reason
