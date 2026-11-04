"""Native Derivatives, ETF, Crypto and KRX panes using shared workflows."""
from dataclasses import asdict
import numpy as np

from core.research.market_analysis import DerivativesRequest, ETFRequest, CryptoRequest, KRXRequest
from core.research.funding_disclosure import funding_text
from core.research.letf_disclosure import letf_text, letf_unavailable_text
from core.research.decay_disclosure import decay_value, decay_text
from core.research.quote_coverage import quote_coverage_text
from core.research.option_disclosure import box_computed, hedge_korean, hedge_text, mfiv_strip
from core.research.crypto_workflow import cost_basis_text, holdings_summary
from .tools import ToolPane, number, fmt
from .market_diagnostics_language import decay_korean, funding_korean, coverage_korean
from .market_narrative_language import market_variants, letf_korean, letf_unavailable_korean


def hide_rows(table, fields):
    """Hide Field/Value rows on screen only; the report sections keep every row."""
    for row in range(table.rowCount()):
        item = table.item(row, 0)
        if item is not None and item.text() in fields:
            table.setRowHidden(row, True)


class DerivativesPane(ToolPane):
    def __init__(self):
        super().__init__('KOSPI200 board', [('board', 'Options, futures & hedge P&L')],
            [('kis', 'KIS · option board'), ('synthetic', 'Synthetic demo')],
            {'board': [('expiry', 'Expiry · blank = nearest', ''), ('rate', 'Rate % · blank = provider', ''),
                       ('engine', 'Hedge engine', [('gbm', 'GBM'), ('garch_t', 'GARCH-t')]),
                       ('paths', 'Simulation paths', 3000), ('horizon', 'Horizon sessions · blank = expiry', '')]})

    def make_request(self):
        v = self.values()
        return DerivativesRequest(self.source.currentData(), v['expiry'].strip(), number(v['rate'], optional=True),
            v['engine'], number(v['paths'], integer=True), number(v['horizon'], optional=True, integer=True))

    def show_result(self, out):
        self.clear_result()
        s = out.data
        b, fit, sim = s['basis'], s['svi'], s['hedge']
        self.text(f"{s['source']} · expiry {s['expiry']} → {s['expiry_date']} · as of {s['as_of']}\n"
                  f"Session {s['session']} · {s['n_quotes']} strikes · rate {s['rate']:.3%} ({s['rate_source']})")
        if s['source'] == 'synthetic': self.text('SYNTHETIC · 모든 시세는 합성 데이터입니다.')
        if not s.get('live_quotes', True): self.text('Last prints only · 장외/마감 시 호가는 동시 체결 가능한 가격이 아닙니다.')
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
            ('RND integral', fmt(s['rnd']['integral']))])
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
            ('Identity slope / R²', f'{sim.identity_slope:.4f} / {sim.identity_r2:.4f}')])
        coverage = s['quote_coverage']
        self.result_table('Static arbitrage checks', ['Check', 'Violations', 'Tests', 'Status'],
            [(key, str(check['violations']) if check['tests'] else 'NOT_RUN', check['tests'], check['status'])
             for key, check in coverage['static'].items()])
        coverage_source = quote_coverage_text(coverage)
        self.text(coverage_source, localized={'en': coverage_source, 'ko': coverage_korean(coverage)})
        self.sections.append({'type': 'quote_coverage', **coverage})
        hedge_note = hedge_text(s)
        if hedge_note:  # §10 M4-N7
            self.text(hedge_note, localized={'en': hedge_note, 'ko': hedge_korean(s)})
        for kind, value in (('hedge_scope', s.get('hedge_scope')), ('box_check', s.get('box_check')),
                            ('mfiv_strip', strip)):
            if value is not None:
                self.sections.append({'type': kind, **value})
        self.finished(out.narrative, localized=market_variants(out, 'derivatives'))


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
        self.text(f"{d['code']} · {d['data_source']} · {d['dates'][0]} → {d['dates'][-1]}\n"
                  f"Sleeve price basis: {d['sleeve_basis']} · study cards: {out.study_status}")
        if d['data_source'] == 'SYNTHETIC': self.text('SYNTHETIC · 시장 관측값이 아닙니다.')
        series = [('Price', d['price'])]
        if d.get('nav') is not None: series.append(('NAV', d['nav']))
        self.line('ETF price / NAV', range(len(d['dates'])), series, 'Observations', 'Price / NAV')
        # Owner, 2026-11-04: no observation-date row on screen (as_of is the request date); the export keeps it.
        if d.get('quote'):
            self.result_table('Quote', ['Field', 'Value'], list(d['quote'].items()))
            hide_rows(self.tables['Quote'], ('as_of',))
        if d.get('premium_stats'):
            self.line('NAV premium', range(len(d['dates'])), [('Premium %', d['premium_pct'])], 'Observations', 'Premium · %')
            ps = d['premium_stats']
            self.result_table('Premium statistics', ['Metric', 'Value'],
                [(k, fmt(v)) for k,v in ps.items() if k not in {'decay','half_life'}] +
                [('AR(1) amplitude half-life · observations',decay_value(ps.get('decay')))])
            decay_source = decay_text(ps.get('decay'))
            self.text(decay_source, localized={'en': decay_source, 'ko': decay_korean(ps.get('decay'))})
        sleeves = d.get('sleeves')
        if sleeves:
            self.result_table('Descriptive sleeve backtests', ['Sleeve', 'Sharpe', 'Max drawdown', 'Study decision'],
                [[key, fmt(sleeves[key]['sharpe']), fmt(sleeves[key]['max_drawdown'], 'pct'),
                  d['verdicts'].get('vol' if key == 'vol_target' else key, 'NOT_APPLICABLE') if out.study_status=='PROVIDED' else 'NOT_LOADED']
                 for key in ('trend', 'vol_target', 'buy_hold')])
            self.line('Trend switch vs buy & hold', range(len(sleeves['equity_trend'])),
                [('Trend', sleeves['equity_trend']), ('Buy & hold', sleeves['equity_bh'])], 'Sessions', 'Equity · starts at 1')
            self.text(f"{sleeves['cost_bps']:g} bp per side · in-sample descriptive results, not a new study decision.")
        if d.get('components'):
            rows = sorted(d['components'], key=lambda c:-(c.get('weight_pct') or 0))
            self.result_table('Constituents', ['Code', 'Name', 'Weight %'], [[r['code'],r['name'],fmt(r['weight_pct'])] for r in rows])
        lt = d.get('letf')
        if lt and lt.get('rows'):
            self.result_table('AZ variance proxies · bp',
                ['Sessions', 'Proxy', 'Variance term', 'Funding term', 'Fee assumption term', 'Dividend term', 'Zero-rate reference'],
                [[r['sessions'], fmt(r['drag_bp']), fmt(r['variance_bp']), fmt(r.get('funding_bp')),
                  fmt(r['fee_bp']), fmt(r.get('dividend_bp')), fmt(r.get('reference_drag_bp'))] for r in lt['rows']])
            self.text(f"Index: {lt['index_source']} · prior-quarter variance AZ proxy {lt['last_quarter_drag_bp']:.2f} bp · GARCH converged={lt['converged']}")
            self.text(letf_text(lt), localized={'en': letf_text(lt), 'ko': letf_korean(lt)})
            self.sections.append({'type':'letf_interpretation', **lt['interpretation']})
        elif lt:
            self.text(letf_unavailable_text(lt), localized={'en': letf_unavailable_text(lt),
                                                         'ko': letf_unavailable_korean(lt)})
            self.sections.append({'type': 'letf_unavailable', **lt})
        self.finished(out.narrative, localized=market_variants(out, 'etf'))


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
        self.text(f"{d['source']} · USD/KRW: {d['usdkrw_source']} · {d['btc_dates'][0]} → {d['btc_dates'][-1]}\n"
                  f"Public market analysis · no order submission · study cards: {out.study_status}")
        if d['source']=='SYNTHETIC': self.text('SYNTHETIC · 모든 시계열은 합성 데이터입니다.')
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
            ('GARCH persistence',fmt(g['persistence'])), ('Converged',str(g['converged'])), ('At bound',', '.join(g['at_bound']))])
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
        self.result_table('ETH/BTC', ['Metric','Value'],
            [(k,v) for k,v in d['ethbtc'].items() if k not in {'decay','half_life_days'}] +
            [('AR(1) amplitude half-life · observations',decay_value(d['ethbtc'].get('decay')))])
        self.result_table('Weekday observations', ['Day','n','Mean return %','Vol %','Mean volume'],
            [[r['day'],r['n'],fmt(r['mean_ret_pct']),fmt(r['vol_pct']),fmt(r['mean_volume'])] for r in d['weekday']['rows']])
        self.text(f"Weekday Bonferroni p={d['weekday']['return_effect_p_bonferroni']:.4g} · weekend volume ratio={d['weekday']['weekend_volume_ratio']:.3f}")
        if d.get('balances'):
            self.result_table('Upbit holdings · read only', ['Currency','Total','Average buy price','KRW value'],
                [[b['currency'],fmt(b['total']),cost_basis_text(b),fmt(b['krw_value'])]
                 for b in d['balances']])
            held = holdings_summary(d['balances'])
            if not held['complete']:  # §10 NEW-M6-14/22: a missing price is shown as missing, never as 0
                names = ', '.join(held['unvalued'])
                partial = f'No KRW price for {names}: their value is not shown and is not in any total.'
                # Named as a holdings section: like the holdings table, it never enters AI commentary (NEW-M6-18).
                self.text(partial, name='Upbit holdings note',
                          localized={'en': partial,
                                     'ko': f'{names}의 원화 시세가 없어 평가액을 표시하지 않으며 합계에도 넣지 않습니다.'})
        elif out.request.include_balances: self.text('Holdings unavailable · verify the configured read-only connection. No account values loaded.')
        self.finished(out.narrative, localized=market_variants(out, 'crypto'))


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
            self.text(reason, localized={'en': reason, 'ko': reason})
            self.status.setText('UNAVAILABLE · 공급자 응답을 확인하세요. 대체 값을 생성하지 않습니다.')
            return
        data = a.data
        if out.request.tool == 'quote':
            # Owner, 2026-11-04: no provider or time rows on screen; the export keeps both (attribution).
            # A KRX fallback is a previous session's close, so its date stays visible.
            self.result_table('Quote', ['Field','Value'], list(asdict(data).items()))
            kis = (a.source or '').upper() == 'KIS'
            hide_rows(self.tables['Quote'], ('source', 'as_of') if kis else ('source',))
        elif data:
            keys = list(dict.fromkeys(k for row in data for k in row))
            self.result_table('Observations',keys,[[r.get(k,'—') for k in keys] for r in data[:300]])
            self.text(f'{len(data)} rows · first 300 displayed')
        else: self.text('EMPTY · 공급자가 빈 결과를 반환했습니다.')
        self.finished('Read-only market observations; no order or account operation.')
