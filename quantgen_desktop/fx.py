"""Native forward/carry, SABR-smile option and G10+KRW carry basket."""
from core.research.fx_analysis import FXRequest
from .tools import ToolPane, number, fmt
from .fx_narrative import fx_korean, sabr_korean


class FXPane(ToolPane):
    def __init__(self):
        from core.quant.validate import cost_bp
        common = [('pair','Pair · base/quote','EURUSD'),('domestic_rate','Quote/domestic rate % · blank = provider',''),
                  ('foreign_rate','Base/foreign rate % · blank = provider','')]
        super().__init__('FX · 현물·선물환·옵션·캐리',
            [('forward','Spot, forward & carry'),('option','Option & smile'),('carry','Carry basket')],
            [('auto','Auto · Yahoo spot / FRED rates'),('yfinance','Yahoo spot'),('synthetic','Synthetic demo')], {
            'forward': common+[('tenor','Tenor','3m'),('market_forward','Market forward · optional','')],
            'option': common+[('tenor','Expiry','3m'),('strike','Strike · ATM / 25d / level','ATM'),('call','Side',[(True,'Call'),(False,'Put')]),
                ('atm','ATM volatility %','8'),('rr','25d risk reversal · vol points','0.5'),('bf','25d butterfly · vol points','0.3')],
            'carry': [('top_n','Top/bottom N · core caps at half universe','3'),('cost_bps','Cost · bp per side',str(cost_bp('fx'))),
                ('rebalance_days','Rebalance · sessions','21'),('days','History · observations','504')]})

    def make_request(self):
        v = self.values(); tool = self.tool.currentData()
        if tool == 'carry':
            for k in ('top_n','rebalance_days','days'): v[k] = number(v[k],integer=True)
            v['cost_bps'] = number(v['cost_bps'])
        else:
            for k in ('domestic_rate','foreign_rate'): v[k] = number(v[k],optional=True,scale=.01)
            if tool == 'forward': v['market_forward'] = number(v['market_forward'],optional=True)
            else:
                for k in ('atm','rr','bf'): v[k] = number(v[k],scale=.01)
        return FXRequest(tool=tool,source=self.source.currentData(),**v)

    def show_result(self,out):
        from core.ficc.common import tenor_label
        self.clear_result()
        q,d = out.request,out.data
        if any(s.source=='SYNTHETIC' for s in out.sources): self.text('합성 데이터 포함 · 현재 시장 데이터가 아닙니다.')
        self.result_table('Data sources', ['Series','Provider','First','Last','Note'],
                          [[s.id,s.source,s.first_date,s.last_date,s.note] for s in out.sources])
        if q.tool == 'carry':
            rows,bt = d['rows'],d['backtest']
            best,hi = rows[0],max(rows,key=lambda x:x.carry)
            metrics = [('Best score',f'{best.ccy} {best.score:+.3f}'),('Highest carry',f'{hi.ccy} {hi.carry:.3%}'),
                ('Basket return',fmt(float(bt.equity[-1])-1,'pct')),('Annual return',fmt(bt.ann_return,'pct')),('Annual vol',fmt(bt.ann_vol,'pct')),
                ('Sharpe',fmt(bt.sharpe)),('Max drawdown',fmt(bt.max_drawdown,'pct')),('Equal-weight long return',fmt(float(bt.bench_equity[-1])-1,'pct'))]
            self.result_table('Carry ranking', ['Pair','CCY','Spot','Rate','USD rate','Carry','3m vol','Carry/vol','3m momentum','Score','Rate date','Stale'],
                [[r.pair,r.ccy,fmt(r.spot),fmt(r.rate_ccy,'pct'),fmt(r.rate_usd,'pct'),fmt(r.carry,'pct'),fmt(r.vol_3m,'pct'),
                  fmt(r.carry_to_vol),fmt(r.mom_3m,'pct'),fmt(r.score),r.rate_date,str(r.rate_stale)] for r in rows])
            self.line('Carry equity', range(len(bt.dates)), [('Basket',bt.equity),('Equal-weight long',bt.bench_equity)],
                      f'Sessions · {bt.dates[0]} → {bt.dates[-1]}','Equity · starts at 1')
            _,longs,shorts = bt.positions[-1]
            self.text(f'Long: {", ".join(longs)}\nShort: {", ".join(shorts)}\n{bt.n_rebalances} rebalances · every {q.rebalance_days} sessions · {bt.cost_bps:g} bp per side · top/bottom {bt.top_n}\n{bt.note}')
        else:
            metrics = [('Pair',d['pair']),('Spot',fmt(d['S'])),('Forward',fmt(d['forward'])),
                       (f"{d['quote']} domestic rate",fmt(d['rd'],'pct')),(f"{d['base']} foreign rate",fmt(d['rf'],'pct'))]
            typed = [ccy for ccy,v in ((d['quote'],q.domestic_rate),(d['base'],q.foreign_rate)) if v is not None]
            self.text('Flat rates across tenors · typed rates: '+(', '.join(typed) if typed else 'none'))
            if q.tool == 'forward':
                metrics += [('Forward points',fmt(d['points'])),('Pip size','0.01' if d['S']>20 else '0.0001'),
                            (f"Carry · long {d['base']} / year",fmt(d['carry'],'pct')),('Implied basis',fmt(d['basis'],'bp'))]
                if q.market_forward is not None: metrics.append(('Market forward',fmt(q.market_forward)))
                spot = d['spot']
                self.line('Spot history',range(len(spot)),[('Spot',spot.values)],f'Observations · {spot.first_date} → {spot.last_date}','Quote per base')
                self.line('Forward curve',[t for t,v in d['curve']],[('Forward',[v for t,v in d['curve']])],'Tenor · years','Quote per base')
                from core.ficc.fx import forward_points
                self.result_table('Forwards',['Tenor','Forward','Points'],[[tenor_label(t),fmt(v),fmt(forward_points(d['S'],v))] for t,v in d['curve']])
            else:
                r,fit = d['report'],d['fit']
                metrics += [('Premium · quote / base',fmt(r.price)),('Premium % of spot',fmt(r.price_pct_spot,'pct')),('Premium / 1m base',fmt(r.price*1e6)+' '+d['quote']),
                    ('Strike',fmt(r.strike)),('Volatility used',fmt(r.vol,'pct')),('Delta · spot',fmt(r.delta_spot)),('Delta · forward',fmt(r.delta_fwd)),
                    ('Gamma / 1% spot',fmt(r.gamma_1pct)),('Vega / vol point',fmt(r.vega)),('Theta / day',fmt(r.theta_1d)),
                    ('Domestic rho / bp',fmt(r.rho_dom*.0001)),('Foreign rho / bp',fmt(r.rho_for*.0001))]
                self.line('SABR smile',d['grid'],[('Volatility',d['vols']*100)],'Strike','Volatility · %')
                self.result_table('Smile quotes',['Point','Strike','Volatility','Spot delta'],[[p.label,fmt(p.strike),fmt(p.vol,'pct'),fmt(p.delta)] for p in d['points']])
                from core.ficc.sabr_diagnostics import diagnostic_text
                diag = d['sabr_diagnostics']
                self.result_table('SABR quote residuals', ['Point','Strike','Quoted vol %','Fitted vol %','Residual · vol points'],
                    [[p['label'],fmt(p['strike']),f"{p['quoted_vol']*100:.6f}",f"{p['fitted_vol']*100:.6f}",
                      f"{p['residual_vol_points']:+.6f}"] for p in diag['residuals']])
                self.text(diagnostic_text(diag), localized={'ko': sabr_korean(diag)})
                self.sections.append(dict(type='sabr_diagnostics', **diag))
                self.text(f'SABR beta=1 · alpha={fit.alpha:.5f} · rho={fit.rho:.5f} · nu={fit.nu:.5f}\n'
                          'Delta strike uses ATM vol, then reprices at SABR vol. ATM means delta-neutral straddle.')
        self.result_table('Metrics',['Metric','Value'],metrics)
        korean = fx_korean(out)
        self.finished(out.narrative, localized={'ko': korean} if korean is not None else None)
