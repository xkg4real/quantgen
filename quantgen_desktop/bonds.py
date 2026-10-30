"""Native Bonds calculator, full-revaluation scenarios and hedge sizing."""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QGridLayout,QLineEdit,QComboBox,QPushButton
from core.research.bond_analysis import BondRequest
from .charts import LineChart


class BondsPane(QWidget):
    requested=pyqtSignal(object)

    def __init__(self):
        super().__init__()
        from .app import label,panel,table
        layout=QVBoxLayout(self);layout.setContentsMargins(0,12,0,0);layout.setSpacing(18)
        box,inner=panel('Bonds · 가격·위험·시나리오·선물 헤지')
        form=QGridLayout();self.fields={}
        fields=[('Coupon %','4.50'),('Maturity · years','10'),('Notional','1000000'),
                ('Price · per 100',''),('Yield %','4.50'),('Position DV01 · optional',''),
                ('CTD DV01 / contract','65'),('Conversion factor','0.8')]
        for i,(name,value) in enumerate(fields):
            w=QLineEdit(value);w.setAccessibleName(name);self.fields[name]=w
            form.addWidget(label(name,'caption'),2*(i//4),i%4);form.addWidget(w,2*(i//4)+1,i%4)
        self.frequency=QComboBox()
        for text,value in [('Annual',1),('Semi-annual',2),('Quarterly',4)]:self.frequency.addItem(text,value)
        self.frequency.setCurrentIndex(1)
        self.source=QComboBox()
        for v in ('auto','fred','synthetic'):self.source.addItem(v,v)
        self.tool=QComboBox()
        for text,value in [('Calculator & risk','calc'),('Scenarios','scenarios'),('Futures hedge','hedge')]:self.tool.addItem(text,value)
        for i,(name,w) in enumerate((('Coupons / year',self.frequency),('Curve source',self.source),('Tool',self.tool))):
            w.setAccessibleName(name);form.addWidget(label(name,'caption'),4,i);form.addWidget(w,5,i)
        inner.addLayout(form)
        inner.addWidget(label('가격과 수익률 중 하나만 입력하세요. Price를 입력할 때는 Yield를 비웁니다.','caption'))
        self.run=QPushButton('채권 분석 실행');self.run.setProperty('primary',True);self.run.clicked.connect(self.submit);inner.addWidget(self.run)
        self.status=label('곡선 출처와 관측일을 함께 표시합니다.','muted');inner.addWidget(self.status);layout.addWidget(box)
        self.metrics=table(['Metric','Value']);self.metrics.setMinimumHeight(360);layout.addWidget(self.metrics)
        self.chart=LineChart('Yield (%)','Price per 100');layout.addWidget(self.chart)
        self.krd=table(['Key tenor · years','DV01 · currency / bp']);self.krd.setMinimumHeight(260);layout.addWidget(self.krd)
        self.scenarios=table(['Scenario','Shock · bp','New price','P&L','P&L %']);self.scenarios.setMinimumHeight(310);layout.addWidget(self.scenarios);self.scenarios.hide()
        self.hedge=label('');layout.addWidget(self.hedge)
        self.notes=label('','muted');layout.addWidget(self.notes)
        from .report_actions import ReportActions
        self.exports = ReportActions(self.status)
        layout.addWidget(self.exports)

    def submit(self):
        def number(name,default=None):
            s=self.fields[name].text().strip().replace(',','')
            return float(s) if s else default
        try:
            y=number('Yield %')
            q=BondRequest(coupon=number('Coupon %',0)/100,maturity=number('Maturity · years',10),
                frequency=self.frequency.currentData(),notional=number('Notional',1e6),price=number('Price · per 100'),
                yield_rate=y/100 if y is not None else None,source=self.source.currentData(),tool=self.tool.currentData(),
                position_dv01=number('Position DV01 · optional'),ctd_dv01=number('CTD DV01 / contract',65),conversion_factor=number('Conversion factor',1))
            q.validate()
        except (ValueError,TypeError):
            self.clear_result()
            self.status.setText('입력 오류 · 유한한 수치와 유효한 만기·금액을 입력하고 Price/Yield 중 하나만 남기세요.');return
        self.requested.emit(q)

    def show_result(self,o):
        from .app import table_rows
        a=o.analytics;cr=a.carry_roll
        table_rows(self.metrics,[('Price',f'{a.price:.3f}'),('Yield',f'{a.ytm:.3%}'),
            ('Macaulay duration',f'{a.macaulay:.3f} years'),('Modified duration',f'{a.modified:.3f}'),
            ('Convexity',f'{a.convexity:.3f}'),('DV01',f'{a.dv01:,.2f} currency / bp'),
            ('z-spread',f'{a.z_spread*10000:.2f} bp'),('Curve price',f'{a.curve_price:.3f}'),
            (f'Carry · {cr.horizon:g} years',f'{cr.carry:+.3f}'),('Roll-down',f'{cr.rolldown:+.3f}'),
            ('Carry + roll',f'{cr.total:+.3f}'),('Breakeven',f'{cr.breakeven_bp:+.2f} bp')])
        self.chart.set_series(o.yield_axis,[('Price',o.price_curve),('Duration tangent',o.duration_tangent)])
        table_rows(self.krd,[[f'{k:g}',f'{v:,.2f}'] for k,v in sorted(a.krd.items())])
        table_rows(self.scenarios,[[r.name,str(r.shock_bp),f'{r.new_price:.3f}',f'{r.pnl:+,.2f}',f'{r.pnl_pct:+.2%}'] for r in o.scenarios])
        self.scenarios.setVisible(bool(o.scenarios))
        self.hedge.setText('')
        if o.hedge:
            pos,ctd,cf,n=o.hedge
            self.hedge.setText(f'선물 매도 {n:,.2f} contracts · 반올림 {round(n):,}\n'
                f'Position DV01 {pos:,.2f} × CF {cf:.4f} / CTD DV01 {ctd:,.2f}\n'
                f'반올림 후 잔여 DV01 {pos-round(n)*ctd/cf:+,.2f} per bp · 실제 주문 없음')
        self.notes.setText('\n'.join(n for n in [
            ('합성 곡선 · 현재 시장 데이터 아님' if o.panel.source=='SYNTHETIC' else o.panel.source),
            f'{o.curve.source} · {o.curve.date} · {o.curve.method} · {len(o.panel)} sessions',
            o.panel.note,o.curve.note,a.note,o.narrative] if n))
        self.status.setText('계산 완료 · 곡선 및 채권 가정을 확인하세요.')
        self.exports.set_result('bonds', o.request, [
            {'type': 'provenance', 'source': o.panel.source, 'date': o.curve.date,
             'curve_source': o.curve.source, 'method': o.curve.method, 'note': o.panel.note},
            {'type': 'analytics', 'data': a}, {'type': 'scenarios', 'data': o.scenarios},
            {'type': 'hedge', 'data': o.hedge},
            {'type': 'price_yield', 'yield_pct': o.yield_axis, 'price': o.price_curve, 'tangent': o.duration_tangent},
            {'type': 'text', 'text': self.notes.text()}])

    def clear_result(self):
        self.exports.clear()
        for widget in (self.metrics, self.krd, self.scenarios):
            widget.setRowCount(0)
        self.chart.set_series([], [])
        self.hedge.setText('')
        self.notes.setText('')
