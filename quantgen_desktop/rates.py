"""Native yield curve, swaps, rate options and short-rate simulation."""
import math
from core.research.rates_analysis import RatesRequest
from .tools import ToolPane, number, fmt


class RatesPane(ToolPane):
    def __init__(self):
        super().__init__('Rates · 수익률 곡선과 금리 위험',
            [('curve','Yield curve'),('swap','Swap pricer'),('option','Swaption / cap-floor'),('sim','Rate simulation')],
            [('auto','Auto · FRED / synthetic fallback'),('fred','FRED'),('synthetic','Synthetic demo')], {
            'curve': [('method','Method',[(v,v) for v in ('bootstrap','nelson_siegel','svensson')]),('lookback','Lookback · sessions','20')],
            'swap': [('tenor','Tenor · 10y or 5y5y','10y'),('fixed_rate','Fixed % · blank = par',''),
                ('notional','Notional','1000000'),('pay_fixed','Side',[(True,'Pay fixed'),(False,'Receive fixed')])],
            'option': [('kind','Instrument',[(v,v) for v in ('swaption','cap','floor')]),('expiry','Expiry · swaption only','1y'),
                ('tenor','Underlying tenor','5y'),('strike','Strike % · blank = ATM',''),
                ('pay_fixed','Swaption side',[(True,'Payer'),(False,'Receiver')]),
                ('option_model','Model',[('bachelier','Bachelier · normal'),('black','Black-76')]),
                ('vol','Normal volatility · bp','80'),('notional','Notional','1000000')],
            'sim': [('model','Model',[(v,v) for v in ('vasicek','cir','hull_white')]),('horizon','Horizon · years','1'),
                ('n_paths','Paths · 100–100000','5000'),('threshold','Threshold % · optional',''),
                ('instrument','Revalue',[(v,v) for v in ('none','bond','swap')]),('tenor','Instrument tenor','10y'),('coupon','Bond coupon %','4')]})
        self.fields['option']['option_model'].currentIndexChanged.connect(self.vol_unit)
        self.fields['option']['kind'].currentIndexChanged.connect(self.option_fields)

    def vol_unit(self):
        # Deliberately reset when changing units so 80bp cannot silently become 80%.
        model = self.fields['option']['option_model'].currentData()
        field = self.fields['option']['vol']
        field.setText('80' if model == 'bachelier' else '30')
        field.setAccessibleName('Normal volatility · bp' if model == 'bachelier' else 'Black volatility · %')
        from PyQt6.QtWidgets import QLabel
        for label in self.forms.widget(2).findChildren(QLabel):
            if 'volatility ·' in label.text(): label.setText(field.accessibleName())

    def option_fields(self):
        is_swaption = self.fields['option']['kind'].currentData() == 'swaption'
        for key in ('expiry','pay_fixed'): self.fields['option'][key].setEnabled(is_swaption)

    def make_request(self):
        v = self.values(); tool = self.tool.currentData()
        if tool == 'curve': v['lookback'] = number(v['lookback'], integer=True)
        if tool in ('swap','option'):
            v['notional'] = number(v['notional'])
            field = 'fixed_rate' if tool == 'swap' else 'strike'
            v[field] = number(v[field], optional=True, scale=.01)
        if tool == 'option': v['vol'] = number(v['vol'], scale=.0001 if v['option_model']=='bachelier' else .01)
        if tool == 'sim':
            v['horizon'] = number(v['horizon']); v['n_paths'] = number(v['n_paths'], integer=True)
            v['threshold'] = number(v['threshold'], optional=True, scale=.01)
            v['coupon'] = number(v['coupon'], scale=.01) if v['instrument']=='bond' else .04
        return RatesRequest(tool=tool, source=self.source.currentData(), **v)

    def show_result(self, out):
        from core.ficc.common import tenor_label
        import numpy as np
        self.clear_result()
        q, r, p, c = out.request, out.report, out.panel, out.curve
        self.text(('합성 곡선 · 현재 시장 데이터 아님\n' if p.source=='SYNTHETIC' else '')+
                  f'{p.source} · {c.date} · {len(p)} observations · {c.method}\n{p.note}\n{c.note}')
        metrics = []
        if q.tool == 'curve':
            metrics = [('Shape',r.shape),('Regime',r.regime),('Lookback',str(r.lookback)),('NS/NSS fit RMSE',fmt(r.ns.rmse,'bp'))]
            pct = {'level','1y1y','2y1y','5y5y'}
            metrics += [(k,fmt(v,'pct' if k in pct else 'bp')) for k,v in r.descriptors.items()]
            rows = c.table()
            self.line('수익률 곡선', c.tenors, [('Zero',np.array(c.zeros)*100),('Par',np.array(r.snapshot.par_yields)*100)], 'Maturity · years','Yield · %')
            self.result_table('Curve table', ['Tenor','Zero','DF','Par','1y forward',f'Change · {r.lookback}d'],
                [[v['label'],fmt(v['zero'],'pct'),fmt(v['df']),fmt(v['par'],'pct'),fmt(v['fwd_1y'],'pct'),fmt(r.changes.get(v['label']),'bp')] for v in rows])
            # Each line uses an observed tenor; no extrapolated history is invented.
            indices = sorted({int(np.argmin(abs(np.array(p.tenors)-t))) for t in (.25,2,10,30)})
            self.line('관측 금리 이력', range(len(p)), [(tenor_label(p.tenors[i]),p.yields[:,i]*100) for i in indices],
                      f'Observations · {p.dates[0]} → {p.dates[-1]}', 'Par yield · %')
            if out.pca is not None:
                pc = out.pca
                self.line('PCA loadings', pc.tenors, [(name,pc.loadings[:,i]) for i,name in enumerate(pc.labels)], 'Tenor · years','Loading')
                self.result_table('PCA variance', ['Component','Explained','Latest score'],
                                  [[name,fmt(pc.explained[i],'pct'),fmt(pc.latest_scores[i])] for i,name in enumerate(pc.labels)])
            else: self.text('PCA 미실행 · 60개 이상의 관측이 필요합니다.')
        elif q.tool == 'swap':
            metrics = [('Swap',r.swap.label),('Par rate',fmt(r.par_rate,'pct')),('Fixed',fmt(r.par_rate if q.fixed_rate is None else q.fixed_rate,'pct')),
                ('PV',fmt(r.pv)),('DV01 · +1bp P&L',fmt(r.dv01)),('Annuity',fmt(r.annuity)),
                ('Carry · first period',fmt(r.carry_1y)),('Roll-down · 1y',fmt(r.rolldown_1y))]
            self.result_table('Key-rate DV01', ['Tenor','Currency / bp'], [[tenor_label(t),fmt(v)] for t,v in r.krd.items()])
            self.result_table('Forward swaps', ['Swap','Par rate'], [[k,fmt(v,'pct')] for k,v in r.fwd_rates.items()])
            self.text(f'{q.notional:,.0f} notional · {r.swap.freq} payments/year · single curve · ACT/365F\n{r.note}')
        elif q.tool == 'option':
            metrics = [('Instrument',q.kind),('Strike',fmt(r.strike,'pct')),('Premium',fmt(r.premium)),('Premium / notional',f'{r.premium_bp:.2f} bp')]
            self.text(f'{q.option_model} · '+(fmt(q.vol,'bp')+' normal' if q.option_model=='bachelier' else fmt(q.vol,'pct')+' Black')+
                      f' · {q.notional:,.0f} notional\n{r.note}')
            if q.kind == 'swaption':
                self.sections.append({'type':'comparison_volatility',
                    'status':r.other_model_status, 'reason':r.other_model_reason,
                    'value':r.other_model_vol if math.isfinite(r.other_model_vol) else None})
                metrics += [('Forward',fmt(r.forward,'pct')),('Annuity',fmt(r.annuity)),('Delta · per +1bp',fmt(r.delta)),
                    ('Gamma · per bp²',fmt(r.gamma)),(f'Vega · {r.vega_unit}',fmt(r.vega)),('Theta · 1 day',fmt(r.theta_1d)),
                    ('Other-model vol',fmt(r.other_model_vol,'pct' if q.option_model=='bachelier' else 'bp'))]
                self.text(f'{q.expiry} × {q.tenor} · '+('Payer' if q.pay_fixed else 'Receiver'))
            else:
                metrics += [('ATM par swap',fmt(r.atm_strike,'pct')),('Caplets',str(len(r.caplets)))]
                self.result_table('Caplets', ['Start · y','End · y','Forward','Premium'],
                    [[fmt(a),fmt(b),fmt(f,'pct'),fmt(v)] for a,b,f,v in r.caplets])
                self.line('Caplet premium', [b for a,b,f,v in r.caplets], [('Premium',[v for a,b,f,v in r.caplets])], 'End · years','Premium')
        else:
            params = r.params
            metrics = [('Model',q.model),('Kappa · /year',fmt(params.kappa)),('Half-life · years',fmt(math.log(2)/params.kappa)),
                ('Theta',fmt(params.theta,'pct')),('Sigma',fmt(params.sigma)+(' sqrt-r' if q.model=='cir' else ' decimal / sqrt-year')),
                ('Initial rate',fmt(params.r0,'pct')),('Terminal mean',fmt(r.mean_terminal,'pct')),('P5 / P95',fmt(r.p05,'pct')+' / '+fmt(r.p95,'pct')),
                ('P(terminal > threshold)',fmt(r.prob_above,'pct')),('Threshold',fmt(q.threshold,'pct'))]
            self.line('금리 분포 · 중앙 90%', r.times, [(f'P{k}',r.fan[k]*100) for k in (5,25,50,75,95)], 'Years','Short rate · %')
            self.result_table('Horizon curve · median path', ['Tenor','Model zero'], [[tenor_label(t),fmt(z,'pct')] for t,z in r.model_curve_at_horizon])
            s = out.series
            self.text(('합성 단기금리 · ' if s.source=='SYNTHETIC' else '')+f'{s.id} · {s.source} · {s.first_date} → {s.last_date}\n{s.note}\n{params.note}\n{r.note}\nSeed 7 · {r.n_paths} paths')
            if out.horizon_pv is not None:
                hp = out.horizon_pv
                metrics += [(f'{q.instrument} mean PV',fmt(hp.mean)),('PV P5 / P95',fmt(hp.p05)+' / '+fmt(hp.p95)),
                            ('VaR 95 · loss',fmt(hp.var95)),('CVaR 95 · loss',fmt(hp.cvar95))]
                counts, edges = np.histogram(hp.pvs,bins=24)
                self.line('Horizon PV distribution', (edges[:-1]+edges[1:])/2, [('Count',counts)], 'PV','Paths per bin')
                self.text(hp.note)
        self.result_table('Metrics', ['Metric','Value'], metrics)
        self.finished(out.narrative)
