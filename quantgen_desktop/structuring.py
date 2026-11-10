"""Native term sheets, payoff, leg decomposition and first-order hedge sheets."""
from core.research.structuring_analysis import StructuringRequest
from core.research.structured_disclosure import cms_coupon_context
from .bonds import group_digits
from .tools import ToolPane, number, fmt
from .model_narrative_language import structured_variants, localize_columns, localize_cell, show_as
from .translations import translate

# Owner issue 03: amounts and price levels read with thousands separators (1,000,000 · 1,350).
_GROUPED = ('notional', 'futures_dv01', 'spot', 'strike')
_UNDERLYING_NAMES = {'FX': 'FX', 'EQ': 'Equity'}


class StructuringPane(ToolPane):
    def __init__(self):
        def common(maturity,underlying=True):
            fields=[('maturity','Maturity',maturity),('notional','Notional','1000000'),('futures_dv01','Futures DV01 / contract · optional','')]
            if underlying:fields.append(('underlying','Underlying',[('FX','FX'),('EQ','Equity')]))
            return fields
        super().__init__('Structuring · product structure, maturity payoff and risk',
            [('ppn','Principal-protected note'),('rc','Reverse convertible'),('dcd','Dual-currency deposit'),('steep','CMS steepener')],
            [('auto','Auto · FRED / synthetic fallback'),('fred','FRED'),('synthetic','Synthetic demo')], {
            'ppn':common('3y')+[('spot','Spot','1.10'),('vol','Volatility %','8'),('r_for','Foreign rate / dividend %','2'),
                ('protection','Protection %','100'),('issue','Issue price · per 100','100'),('margin','Margin · per 100','1')],
            'rc':common('1y')+[('spot','Spot','1.10'),('vol','Volatility %','10'),('r_for','Foreign rate / dividend %','2'),
                ('strike_pct','Strike % of spot','95'),('coupon','Coupon % · blank = solve',''),('issue','Issue price · per 100','100'),('margin','Margin · per 100','1')],
            'dcd':common('3m',False)+[('base_ccy','Base currency','USD'),('quote_ccy','Quote currency','KRW'),('spot','Spot','1350'),('strike','Strike','1300'),
                ('vol','Volatility %','9'),('r_for','Base currency rate %','4.5'),('margin','Margin · per 100','0.25')],
            'steep':common('5y',False)+[('leverage','Leverage · ×','4'),('floor','Floor %','0'),('cap','Cap % · blank = none',''),
                ('frequency','Coupons per year','1'),('issue','Issue price · per 100','100')]})
        for controls in self.fields.values():
            for key in _GROUPED:
                field = controls.get(key)
                if field is not None:  # number() strips the separators again
                    field.setText(group_digits(field.text()))
                    field.editingFinished.connect(lambda field=field: field.setText(group_digits(field.text())))

    def make_request(self):
        values=self.values()
        pct={'vol','r_for','protection','strike_pct','coupon','floor','cap'}
        for key,value in values.items():
            if key in {'maturity','underlying'}:continue
            if key in {'base_ccy','quote_ccy'}:values[key]=value.strip().upper();continue
            values[key]=number(value,optional=key in {'coupon','cap','futures_dv01'},integer=key=='frequency',scale=.01 if key in pct else 1)
        return StructuringRequest(tool=self.tool.currentData(),source=self.source.currentData(),**values)

    def show_result(self,out):
        self.clear_result()
        r,c,p=out.report,out.curve,out.panel
        cms=r.underlying.startswith('CMS')
        origin = f'{p.source} · {c.date} · {c.method}\n{p.note}\n{c.note}'
        original = ('합성 곡선 · 현재 시장 데이터 아님\n' if p.source == 'SYNTHETIC' else '') + origin
        # Shown once when the curve repeats the panel's note; the export keeps both lines.
        shown = origin if p.note != c.note else f'{p.source} · {c.date} · {c.method}\n{p.note}'
        self.text(original, localized={'en': ('Synthetic curve · not current market data\n'
                                             if p.source == 'SYNTHETIC' else '') + shown,
                                       'ko': ('합성 곡선 · 현재 시장 데이터 아님\n'
                                              if p.source == 'SYNTHETIC' else '') + shown})
        self.text('모든 상품에 동일한 UST 곡선을 사용합니다. KRW 상품도 이 곡선으로 할인하는 구조 예시이며 KRW 시장 호가가 아닙니다.')
        metrics=[('Product',r.product),('Underlying',r.underlying),('Fair value · per 100',fmt(r.fair_value)),
            ('Issue price',fmt(r.issue_price)),('Margin · per 100',fmt(r.margin)),('Maturity · years',fmt(r.maturity)),
            ('Notional',fmt(r.notional)+' '+r.currency)]
        if r.participation is not None:metrics.append(('Leverage' if cms else 'Participation',fmt(r.participation)+ ' ×' if cms else fmt(r.participation,'pct')))
        if r.coupon is not None:
            coupon_label = ('First-period expected coupon · p.a.' if cms else
                            'Enhanced yield · simple' if out.request.tool == 'dcd' else 'Coupon / year')
            metrics.append((coupon_label, fmt(r.coupon, 'pct')))
            if cms:self.sections.append({'type': 'coupon_interpretation', **cms_coupon_context(r)})
        for name,value in (('Spot',r.spot),('Strike',r.strike)):
            if value is not None:metrics.append((name,fmt(value)))
        if r.vol is not None:metrics.append(('Volatility',fmt(r.vol,'pct')))
        self.result_table('Metrics',['Metric','Value'],metrics)
        localize_cell(self.tables['Metrics'], 0, 1)  # Authored product name only.
        if r.underlying in _UNDERLYING_NAMES:  # 'FX' reads 외환 in Korean, as the Underlying selector does
            show_as(self.tables['Metrics'], cells=[(1, 1, _UNDERLYING_NAMES[r.underlying])])
        # The notional as typed (1,000,000 USD), not 1,000,000.0000 USD; the export keeps fmt's text.
        notional = self.tables['Metrics'].item(6, 1)
        if notional is not None:
            amount = f'{r.notional:,.0f}' if float(r.notional).is_integer() else f'{r.notional:,.2f}'
            notional.setText(f'{amount} {r.currency}')
        labels={'delta':'Delta · per +1% spot','gamma':'Gamma · per +1% spot','vega':'Vega · per vol point',
                'dv01':'DV01 · per -1bp','dv01_2s10s':'2s10s DV01 · per +1bp'}
        self.result_table('Greeks',['Risk','Value · '+r.currency],[[labels.get(k,k),fmt(v)] for k,v in r.greeks.items()])
        localize_columns(self.tables['Greeks'], (0,))
        self.line('Maturity payoff',[x*10000 if cms else x for x,y in r.payoff_grid],
                  [('Payoff',[y for x,y in r.payoff_grid])], 'Realized 10y–2y spread · bp' if cms else 'Underlying at maturity','Per 100 notional')
        if cms:self.text('CMS 차트는 각 쿠폰 기간에 같은 스프레드가 실현된다고 가정합니다.')
        self.result_table('Leg decomposition',['Leg','Kind','Value · per 100','Detail'],[[l.name,l.kind,fmt(l.value),l.detail] for l in r.legs])
        # Leg kinds (zcb, option, ...) read in the window language too (owner issue 14).
        localize_columns(self.tables['Leg decomposition'], (0, 1, 3))
        self.result_table('Hedge sheet',['Instrument','Quantity','Unit','Rationale'],[[h.instrument,fmt(h.quantity),h.unit,h.rationale] for h in r.hedge])
        localize_columns(self.tables['Hedge sheet'], (0, 2, 3))
        hedge_notice = 'Hedge 부호: + 매수 / 고정금리 지급, − 매도 / 고정금리 수취. 실제 주문을 실행하지 않습니다.'
        self.text(hedge_notice + '\n' + r.note,
                  localized={'en': translate(hedge_notice, 'en') + '\n' + r.note,
                             'ko': hedge_notice + '\n' + translate(r.note, 'ko')})
        self.finished(out.narrative, localized=structured_variants(out))
