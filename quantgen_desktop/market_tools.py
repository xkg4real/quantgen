"""Native Derivatives, ETF, Crypto and KRX panes using shared workflows."""
from dataclasses import asdict
import numpy as np

from core.research.market_analysis import DerivativesRequest, ETFRequest, CryptoRequest, KRXRequest
from core.research.decay_disclosure import decay_value, decay_text
from .tools import ToolPane, number, fmt


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
        if s.get('quotes_note'): self.text(s['quotes_note'])
        self.result_table('Futures & volatility', ['Metric', 'Value'], [
            ('Parity forward', fmt(s['F'])), ('Future', fmt(s['futures']['price'])), ('Basis · points', fmt(b.basis_pts)),
            ('Fair value', fmt(b.fair)), ('Mispricing · bp of spot', fmt(b.mispricing_bp)),
            ('Implied funding', fmt(b.implied_rate, 'pct')), ('KIS theoretical gap · points', fmt(b.theo_gap_pts)),
            ('ATM IV', fmt(s['atm'].iv, 'pct')), ('Model-free IV', fmt(s['mfiv'].get('vol'), 'pct')),
            ('SVI RMSE · vol points', fmt(fit.rmse_volpts)), ('SVI rho', fmt(fit.rho)),
            ('Butterfly arbitrage free', str(fit.arbitrage_free)), ('IV reconciliation gap · vol points', fmt(s['reconcile']['median_volpts'])),
            ('Box funding', fmt(s['box']['rate'], 'pct') if s['box'] else 'UNAVAILABLE'), ('RND integral', fmt(s['rnd']['integral']))])
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
        self.result_table('Static arbitrage checks', ['Check', 'Value'], list(s['arbitrage'].items()))
        self.finished(out.narrative)


class ETFPane(ToolPane):
    def __init__(self):
        super().__init__('ETF structure', [('etf', 'NAV, basket & sleeve rules')],
            [('auto', 'Auto · KIS / FMP'), ('kis', 'KIS'), ('fmp', 'FMP'), ('yfinance', 'Yahoo'), ('synthetic', 'Synthetic demo')],
            {'etf': [('code', 'ETF code', '069500'), ('days', 'Sessions', 504)]})

    def make_request(self):
        v = self.values()
        return ETFRequest(self.source.currentData(), v['code'], number(v['days'], integer=True))

    def show_result(self, out):
        self.clear_result()
        d = out.data
        self.text(f"{d['code']} · {d['data_source']} · {d['dates'][0]} → {d['dates'][-1]}\n"
                  f"Sleeve price basis: {d['sleeve_basis']} · study cards: {out.study_status}")
        if d['data_source'] == 'SYNTHETIC': self.text('SYNTHETIC · 시장 관측값이 아닙니다.')
        series = [('Price', d['price'])]
        if d.get('nav') is not None: series.append(('NAV', d['nav']))
        self.line('ETF price / NAV', range(len(d['dates'])), series, 'Observations', 'Price / NAV')
        if d.get('quote'): self.result_table('Quote', ['Field', 'Value'], list(d['quote'].items()))
        if d.get('premium_stats'):
            self.line('NAV premium', range(len(d['dates'])), [('Premium %', d['premium_pct'])], 'Observations', 'Premium · %')
            ps = d['premium_stats']
            self.result_table('Premium statistics', ['Metric', 'Value'],
                [(k, fmt(v)) for k,v in ps.items() if k not in {'decay','half_life'}] +
                [('AR(1) amplitude half-life · observations',decay_value(ps.get('decay')))])
            self.text(decay_text(ps.get('decay')))
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
            self.result_table('Leveraged fund drag · bp', ['Sessions', 'Drag', 'Variance term', 'Fee term'],
                [[r['sessions'], fmt(r['drag_bp']), fmt(r['variance_bp']), fmt(r['fee_bp'])] for r in lt['rows']])
            self.text(f"Index: {lt['index_source']} · prior-quarter drag {lt['last_quarter_drag_bp']:.2f} bp · GARCH converged={lt['converged']}")
        elif lt: self.text('Leveraged drag unavailable · provider or model error. Other results remain available.')
        self.finished(out.narrative)


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
        self.text(decay_text(getattr(kp, "decay", None)))
        self.text('ETH/BTC: ' + decay_text(d['ethbtc'].get('decay')))
        self.result_table('Premium / volatility', ['Metric', 'Value'], [
            ('Kimchi premium · %',fmt(kp.last_pct)), ('Premium z',fmt(kp.last_z)),
            ('AR(1) amplitude half-life · observations',decay_value(getattr(kp, "decay", None))),
            ('Funding annualized · %', fmt(fc.last_ann_pct) if fc else 'UNAVAILABLE'),
            ('Funding percentile', fmt(fc.percentile,'pct') if fc else 'UNAVAILABLE'),
            ('BTC conditional vol · 365 days',fmt(g['cond_vol_365'],'pct')), ('GARCH nu',fmt(g['nu'])),
            ('GARCH persistence',fmt(g['persistence'])), ('Converged',str(g['converged'])), ('At bound',', '.join(g['at_bound']))])
        self.line('Kimchi premium', range(len(kp.dates)), [('Premium %',kp.premium_pct)], 'Days', 'Premium · %')
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
                [[b['currency'],fmt(b['total']),fmt(b['avg_buy_price']),fmt(b['krw_value'])] for b in d['balances']])
        elif out.request.include_balances: self.text('Holdings unavailable · verify the configured read-only connection. No account values loaded.')
        self.finished(out.narrative)


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
        self.text(f'Provider: {a.source or "UNAVAILABLE"}')
        if not a.ok:
            from core.research.presentation import safe_detail
            self.text(safe_detail(a.reason))
            self.status.setText('UNAVAILABLE · 공급자 응답을 확인하세요. 대체 값을 생성하지 않습니다.')
            return
        data = a.data
        if out.request.tool == 'quote':
            self.result_table('Quote', ['Field','Value'], list(asdict(data).items()))
        elif data:
            keys = list(dict.fromkeys(k for row in data for k in row))
            self.result_table('Observations',keys,[[r.get(k,'—') for k in keys] for r in data[:300]])
            self.text(f'{len(data)} rows · first 300 displayed')
        else: self.text('EMPTY · 공급자가 빈 결과를 반환했습니다.')
        self.finished('Read-only market observations; no order or account operation.')
