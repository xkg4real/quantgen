"""Native yield curve, swaps, rate options and short-rate simulation."""
import math
from core.ficc.curves import CURVE_METHODS, EXACT_METHODS, METHOD_NAMES
from core.research.rates_analysis import RatesRequest
from .bonds import group_digits
from .model_narrative_language import localize_columns, show_as
from .tools import ToolPane, number, fmt

# What each curve construction method assumes and when to use it (owner issue 08). The English text is
# the Flet Rates page's (ui/rates_page.py `_METHOD_TEXT`); its reviewed Korean lives in
# core/ui_page_messages/rates.py and reaches these captions through the shared catalogue.
METHOD_TEXT = {
    "bootstrap": "Solves the zero rate at each quoted maturity in turn so every quoted yield is "
                 "repriced exactly; between maturities the forward rate is held flat. The standard "
                 "choice for pricing: the swap, option and simulation tools always use it.",
    "cubic_spline": "Draws a natural cubic spline through the quoted par yields, reads a yield at "
                    "every half-year and bootstraps them. Smooth and exact at every quote, but it "
                    "can swing between widely spaced long maturities.",
    "pchip": "Like the cubic spline, but with a shape-preserving monotone cubic (PCHIP) that never "
             "overshoots the quotes, so it adds no bumps the market does not show. A safe smooth "
             "choice for sparse or kinked curves.",
    "monotone_convex": "Hagan and West's method: forward rates are continuous and stay positive, and "
                       "a change in one quote moves the curve only nearby, while every quote is "
                       "repriced exactly. The U.S. Treasury has used it for its official par yield "
                       "curve since December 2021.",
    "smith_wilson": "The method EIOPA has used for the Solvency II risk-free interest rate curves (its "
                    "extrapolation method is due to change from 30 January 2027). It passes exactly "
                    "through every quote and, beyond the last one, bends the forward rate toward an "
                    "assumed ultimate forward rate of 3.30% (convergence speed alpha 0.10). Both "
                    "values are assumptions, not estimates. The curve is computed out to 60 years "
                    "and held flat beyond, so values past 60 years are not Smith-Wilson.",
    "nelson_siegel": "Fits three factors (level, slope and curvature) plus one decay parameter by "
                     "least squares. Smooth and easy to read, but it misses individual quotes; the "
                     "fit error is shown with the result.",
    "diebold_li": "Nelson-Siegel with the decay fixed at 0.0609 per month (Diebold and Li, 2006), so "
                  "the three factors come from a plain regression and can be compared from day to "
                  "day. Built for tracking and forecasting the curve; it fits single quotes more "
                  "loosely.",
    "svensson": "Nelson-Siegel with a second hump term (six parameters). It follows long-end shapes "
                "better; many central banks publish curves fitted this way.",
    "bjork_christensen": "Nelson-Siegel plus a second slope term that decays twice as fast (five "
                         "parameters, Björk and Christensen, 1999). It starts from the Nelson-Siegel "
                         "fit, so it never fits worse than Nelson-Siegel.",
}
KIND_TEXT = {True: "Exact fit: reprices every quoted yield", False: "Smooth fit: the fit error is shown"}

# Display captions for metric rows whose own words are raw keys or ambiguous single words (owner issues
# 07/14). Only the shown text changes; the exported rows keep the original words.
_METRIC_CAPTIONS = {
    'Shape': 'Curve shape', 'Lookback': 'Change window · sessions', '2s5s10s_fly': '2s5s10s fly',
    'level': 'Level (2/5/10y)', '1y_fwd_1y_ahead': '1y fwd vs 1y', 'Fixed': 'Fixed rate',
    'Forward': 'Forward swap rate', 'Kappa · /year': 'Mean reversion (kappa) · per year',
    'Theta': 'Long-run mean (theta)', 'Sigma': 'Volatility (sigma)', 'Initial rate': 'Current rate (r0)',
    'Threshold': 'Threshold rate',
}
_SHAPE_CAPTIONS = {'normal': 'Upward (normal) curve', 'inverted': 'Inverted curve', 'humped': 'Humped curve',
                   'flat': 'Flat curve'}
_KIND_NAMES = {'swaption': 'Swaption', 'cap': 'Cap', 'floor': 'Floor'}
_MODEL_NAMES = {'vasicek': 'Vasicek', 'cir': 'CIR', 'hull_white': 'Hull-White'}
_AMOUNT_FIELDS = (('swap', 'notional'), ('option', 'notional'), ('sim', 'n_paths'))


class RatesPane(ToolPane):
    def __init__(self):
        super().__init__('Rates · yield curve and rate risk',
            [('curve','Yield curve'),('swap','Swap pricer'),('option','Swaption / cap-floor'),('sim','Rate simulation')],
            [('auto','Auto · FRED / synthetic fallback'),('fred','FRED'),('synthetic','Synthetic demo')], {
            'curve': [('method','Curve method',[(v,METHOD_NAMES[v]) for v in CURVE_METHODS]),('lookback','Lookback (sessions)','20')],
            'swap': [('tenor','Tenor · 10y or 5y5y','10y'),('fixed_rate','Fixed % · blank = par',''),
                ('notional','Notional','1000000'),('pay_fixed','Side',[(True,'Pay fixed'),(False,'Receive fixed')])],
            'option': [('kind','Instrument',list(_KIND_NAMES.items())),('expiry','Expiry · swaption only','1y'),
                ('tenor','Underlying tenor','5y'),('strike','Strike % · blank = ATM',''),
                ('pay_fixed','Swaption side',[(True,'Payer'),(False,'Receiver')]),
                ('option_model','Model',[('bachelier','Bachelier · normal'),('black','Black-76')]),
                ('vol','Normal volatility · bp','80'),('notional','Notional','1000000')],
            'sim': [('model','Model',list(_MODEL_NAMES.items())),('horizon','Horizon · years','1'),
                ('n_paths','Paths · 100–100000','5000'),('threshold','Threshold % · optional',''),
                ('instrument','Revalue',[('none','Nothing'),('bond','Bond'),('swap','Payer swap')]),
                ('tenor','Instrument tenor','10y'),('coupon','Bond coupon %','4')]})
        self.fields['option']['option_model'].currentIndexChanged.connect(self.vol_unit)
        self.fields['option']['kind'].currentIndexChanged.connect(self.option_fields)
        # Owner issue 03: amounts read with thousands separators (1,000,000); number() strips them.
        for tool, key in _AMOUNT_FIELDS:
            field = self.fields[tool][key]
            field.setText(group_digits(field.text()))
            field.editingFinished.connect(lambda field=field: field.setText(group_digits(field.text())))
        self._method_info()

    def _method_info(self):
        """Owner issue 08: what the chosen curve method assumes, under the form, for the curve tool."""
        from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
        from .app import label
        self.method_info = QWidget()
        self.method_info.setObjectName('curveMethodInfo')
        # An inset note on the page colour, as the Flet page's method box (theme rules give the colour).
        self.method_info.setStyleSheet('QWidget#curveMethodInfo { border-radius: 8px; }')
        column = QVBoxLayout(self.method_info)
        column.setContentsMargins(12, 10, 12, 10)
        column.setSpacing(4)
        head = QHBoxLayout()
        head.setSpacing(10)
        self.method_name, self.method_kind = label('', 'cardTitle'), label('', 'eyebrow')
        head.addWidget(self.method_name)
        head.addWidget(self.method_kind, 1)
        column.addLayout(head)
        self.method_text = label('', 'caption')
        column.addWidget(self.method_text)
        inner = self.input_box.layout()
        inner.insertWidget(inner.indexOf(self.forms) + 1, self.method_info)
        self.fields['curve']['method'].currentIndexChanged.connect(self.describe_method)
        self.tool.currentIndexChanged.connect(self.describe_method)
        self.describe_method()

    def describe_method(self):
        method = self.fields['curve']['method'].currentData() or 'bootstrap'
        self.method_name.setText(METHOD_NAMES.get(method, method))
        self.method_kind.setText(KIND_TEXT[method in EXACT_METHODS])
        self.method_text.setText(METHOD_TEXT.get(method, ''))
        self.method_info.setVisible(self.tool.currentData() == 'curve')

    def vol_unit(self):
        # Deliberately reset when changing units so 80bp cannot silently become 80%.
        model = self.fields['option']['option_model'].currentData()
        field = self.fields['option']['vol']
        field.setText('80' if model == 'bachelier' else '30')
        field.setAccessibleName('Normal volatility · bp' if model == 'bachelier' else 'Black volatility · %')
        from PyQt6.QtWidgets import QLabel
        for label in self.forms.widget(2).findChildren(QLabel):
            # Match the caption's English source: its shown text may be Korean.
            if 'volatility ·' in getattr(label, 'source_text', label.text()): label.setText(field.accessibleName())

    def option_fields(self):
        is_swaption = self.fields['option']['kind'].currentData() == 'swaption'
        for key in ('expiry','pay_fixed'): self.fields['option'][key].setEnabled(is_swaption)

    def _metric_captions(self, metrics, report):
        """Readable captions for raw keys and codes in the Metrics table (display only, owner issues 07/14)."""
        cells = []
        for row, (name, value) in enumerate(metrics):
            caption = (f'Curve move · last {report.lookback} sessions' if name == 'Regime'
                       else _METRIC_CAPTIONS.get(name))
            if caption:
                cells.append((row, 0, caption))
            if name == 'Shape' and value in _SHAPE_CAPTIONS:
                cells.append((row, 1, _SHAPE_CAPTIONS[value]))
            elif name == 'Instrument' and value in _KIND_NAMES:
                cells.append((row, 1, _KIND_NAMES[value]))
            elif name == 'Model' and value in _MODEL_NAMES:
                cells.append((row, 1, _MODEL_NAMES[value]))
            elif name == 'Swap':
                cells.append((row, 1, f'{value} swap'))
            elif name in ('Regime', 'Sigma'):
                cells.append((row, 1, value))
        show_as(self.tables['Metrics'], cells=cells)

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
        source_summary = ('합성 곡선 · 현재 시장 데이터 아님\n' if p.source=='SYNTHETIC' else '')+\
                         f'{p.source} · {c.date} · {len(p)} observations · {c.method}\n{p.note}\n{c.note}'
        # Author only the UI metadata. Embedded provider/model notes are literal
        # in both languages; the original mixed-language export stays unchanged.
        # A curve built from the panel repeats the panel's note: show it once.
        notes = p.note if p.note == c.note else f'{p.note}\n{c.note}'
        self.text(source_summary, localized={
            'en': ('Synthetic curve · not current market data\n' if p.source=='SYNTHETIC' else '')+
                  f'{p.source} · {c.date} · {len(p)} observations · {c.method}\n{notes}',
            'ko': ('합성 곡선 · 현재 시장 데이터 아님\n' if p.source=='SYNTHETIC' else '')+
                  f'{p.source} · {c.date} · 관측 {len(p)}개 · {c.method}\n{notes}',
        })
        metrics = []
        if q.tool == 'curve':
            from core.ficc.forward_conventions import (FIVE_YEAR_SIMPLE_LABEL, FIVE_YEAR_SIMPLE_NOTE,
                FIVE_YEAR_SIMPLE_NOTE_KO, curve_descriptor_conventions)
            metrics = [('Shape',r.shape),('Regime',r.regime),('Lookback',str(r.lookback)),('NS/NSS fit RMSE',fmt(r.ns.rmse,'bp'))]
            pct = {'level','1y1y','2y1y','5y5y'}
            metrics += [(FIVE_YEAR_SIMPLE_LABEL if k == '5y5y' else k,
                         fmt(v,'pct' if k in pct else 'bp')) for k,v in r.descriptors.items()]
            self.text(FIVE_YEAR_SIMPLE_NOTE, localized={'ko': FIVE_YEAR_SIMPLE_NOTE_KO})
            self.sections.append({'type': 'descriptor_conventions', 'values': curve_descriptor_conventions()})
            rows = c.table()
            # Smooth exact methods keep a dense knot grid; plot them at the quoted tenors.
            quoted = np.array(r.snapshot.tenors, dtype=float)
            xs, zs = (quoted, c.zero(quoted)) if c.pillars else (c.tenors, c.zeros)
            self.line('수익률 곡선', xs, [('Zero',np.array(zs)*100),('Par',np.array(r.snapshot.par_yields)*100)], 'Maturity · years','Yield · %')
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
                # Factor names (level/slope/curvature) read in the window language, as on the chart.
                localize_columns(self.tables['PCA variance'], (0,))
                show_as(self.tables['PCA variance'], headers=[(0, 'PCA factor')])
            else: self.text('PCA 미실행 · 60개 이상의 관측이 필요합니다.')
        elif q.tool == 'swap':
            metrics = [('Swap',r.swap.label),('Par rate',fmt(r.par_rate,'pct')),('Fixed',fmt(r.par_rate if q.fixed_rate is None else q.fixed_rate,'pct')),
                ('PV',fmt(r.pv)),('DV01 · +1bp P&L',fmt(r.dv01)),('Annuity',fmt(r.annuity)),
                ('Carry · first period',fmt(r.carry_1y)),('Roll-down · 1y',fmt(r.rolldown_1y))]
            self.result_table('Key-rate DV01', ['Tenor','Currency / bp'], [[tenor_label(t),fmt(v)] for t,v in r.krd.items()])
            self.result_table('Forward swaps', ['Swap','Par rate'], [[k,fmt(v,'pct')] for k,v in r.fwd_rates.items()])
            swap_terms = f'{q.notional:,.0f} notional · {r.swap.freq} payments/year · single curve · ACT/365F\n{r.note}'
            self.text(swap_terms, localized={
                'en': swap_terms,
                'ko': f'명목금액 {q.notional:,.0f} · 연 {r.swap.freq}회 지급 · 단일 곡선 · ACT/365F\n{r.note}',
            })
        elif q.tool == 'option':
            metrics = [('Instrument',q.kind),('Strike',fmt(r.strike,'pct')),('Premium',fmt(r.premium)),('Premium / notional',f'{r.premium_bp:.2f} bp')]
            option_terms = f'{q.option_model} · '+(fmt(q.vol,'bp')+' normal' if q.option_model=='bachelier' else fmt(q.vol,'pct')+' Black')+\
                           f' · {q.notional:,.0f} notional\n{r.note}'
            self.text(option_terms, localized={
                'en': option_terms,
                'ko': f'{q.option_model} · '+(fmt(q.vol,'bp')+' 정규' if q.option_model=='bachelier' else fmt(q.vol,'pct')+' Black')+
                      f' · 명목금액 {q.notional:,.0f}\n{r.note}',
            })
            if q.kind == 'swaption':
                self.sections.append({'type':'comparison_volatility',
                    'status':r.other_model_status, 'reason':r.other_model_reason,
                    'value':r.other_model_vol if math.isfinite(r.other_model_vol) else None})
                metrics += [('Forward',fmt(r.forward,'pct')),('Annuity',fmt(r.annuity)),('Delta · per +1bp',fmt(r.delta)),
                    ('Gamma · per bp²',fmt(r.gamma)),(f'Vega · {r.vega_unit}',fmt(r.vega)),('Theta · 1 day',fmt(r.theta_1d)),
                    ('Other-model vol',fmt(r.other_model_vol,'pct' if q.option_model=='bachelier' else 'bp'))]
                option_side = f'{q.expiry} × {q.tenor} · '+('Payer' if q.pay_fixed else 'Receiver')
                self.text(option_side, localized={
                    'en': option_side,
                    'ko': f'{q.expiry} × {q.tenor} · '+('고정금리 지급형' if q.pay_fixed else '고정금리 수취형'),
                })
            else:
                metrics += [('ATM par swap',fmt(r.atm_strike,'pct')),('Caplets',str(len(r.caplets)))]
                self.result_table('Caplets', ['Start · y','End · y','Forward','Premium'],
                    [[fmt(a),fmt(b),fmt(f,'pct'),fmt(v)] for a,b,f,v in r.caplets])
                # The caplet's forward rate, not an FX forward (the catalogue's 'Forward' is 선물환).
                show_as(self.tables['Caplets'], headers=[(2, 'Forward rate')])
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
            simulation_source = ('합성 단기금리 · ' if s.source=='SYNTHETIC' else '')+f'{s.id} · {s.source} · {s.first_date} → {s.last_date}\n{s.note}\n{params.note}\n{r.note}\nSeed 7 · {r.n_paths} paths'
            self.text(simulation_source, localized={
                'en': ('Synthetic short rate · ' if s.source=='SYNTHETIC' else '')+
                      f'{s.id} · {s.source} · {s.first_date} → {s.last_date}\n{s.note}\n{params.note}\n{r.note}\nSeed 7 · {r.n_paths} paths',
                'ko': ('합성 단기금리 · ' if s.source=='SYNTHETIC' else '')+
                      f'{s.id} · {s.source} · {s.first_date} → {s.last_date}\n{s.note}\n{params.note}\n{r.note}\n시드 7 · 경로 {r.n_paths}개',
            })
            if out.horizon_pv is not None:
                hp = out.horizon_pv
                metrics += [(f'{q.instrument} mean PV',fmt(hp.mean)),('PV P5 / P95',fmt(hp.p05)+' / '+fmt(hp.p95)),
                            ('VaR 95 · loss',fmt(hp.var95)),('CVaR 95 · loss',fmt(hp.cvar95))]
                counts, edges = np.histogram(hp.pvs,bins=24)
                self.line('Horizon PV distribution', (edges[:-1]+edges[1:])/2, [('Count',counts)], 'PV','Paths per bin')
                self.text(hp.note)
        self.result_table('Metrics', ['Metric','Value'], metrics)
        self._metric_captions(metrics, r)
        from .rates_narrative import rates_korean
        korean = rates_korean(out)
        self.finished(out.narrative, localized={'ko': korean} if korean is not None else None)
