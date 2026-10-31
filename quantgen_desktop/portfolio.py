"""Native portfolio editor and result tables, backed by existing core solvers."""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLineEdit, QComboBox, QDoubleSpinBox, QPushButton

from core.research.portfolio_analysis import PortfolioRequest
from core.research.portfolio_disclosure import cap_label, portfolio_disclosure
from .charts import FrontierChart


class PortfolioPane(QWidget):
    requested = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        # Imported here to avoid a module-level UI dependency cycle.
        from .app import label, table, panel
        self.setObjectName("portfolio-pane")
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(20)
        box,inner=panel("포트폴리오 최적화")
        inputs=QGridLayout()
        for column in range(3):inputs.setColumnStretch(column,1)
        self.symbols=QLineEdit("AAPL, MSFT, NVDA, TLT")
        self.source=QComboBox()
        for v in ("auto","fmp","kis","yfinance","synthetic"):self.source.addItem(v,v)
        self.objective=QComboBox()
        for v in ("max_sharpe","min_vol","risk_parity","equal_weight"):self.objective.addItem(v,v)
        self.cap=QDoubleSpinBox();self.cap.setRange(.01,1);self.cap.setSingleStep(.05);self.cap.setValue(1)
        self.rf=QDoubleSpinBox();self.rf.setRange(-100,100);self.rf.setValue(3);self.rf.setSuffix(" %")
        for i,(name,w) in enumerate((("Symbols · comma separated",self.symbols),("Source",self.source),
            ("Objective",self.objective),("Max weight / asset",self.cap),("Risk-free",self.rf))):
            w.setAccessibleName(name);inputs.addWidget(label(name,"caption"),2*(i//3),i%3);inputs.addWidget(w,2*(i//3)+1,i%3)
        inner.addLayout(inputs)
        self.run=QPushButton("포트폴리오 분석 실행");self.run.setProperty("primary",True);self.run.clicked.connect(self.submit)
        inner.addWidget(self.run)
        self.status=label("동일 관측일의 이력을 정렬한 후 네 가지 목적함수를 비교합니다.","muted")
        inner.addWidget(self.status);layout.addWidget(box)
        self.scope=label("선택한 목적에만 입력 상한이 적용됩니다. 나머지 목적·Frontier·무작위 구름의 종목당 상한은 100%입니다.","caption")
        layout.addWidget(self.scope)
        self.chart=FrontierChart();layout.addWidget(self.chart)
        self.comparison=table(["Objective","연율 수익률","연율 변동성","Sharpe","수렴","종목당 상한 / 범위"]);self.comparison.setMinimumHeight(200);layout.addWidget(self.comparison)
        self.weights=table(["Symbol","Weight","Risk contribution"]);self.weights.setMinimumHeight(230);layout.addWidget(self.weights)
        self.correlation=table([]);self.correlation.setMinimumHeight(220);layout.addWidget(label("상관행렬","heading"));layout.addWidget(self.correlation)
        self.notes=label("아직 실행한 분석이 없습니다.","muted");layout.addWidget(self.notes)
        layout.addWidget(label("과거 표본에 대한 최적화이며 미래 수익 보장이나 공식 게이트 판정이 아닙니다. 모든 결과는 롱온리·완전투자이며 equal_weight는 1/N 고정 비중입니다.","caption"))
        from .report_actions import ReportActions
        self.exports = ReportActions(self.status)
        layout.addWidget(self.exports)

    def submit(self):
        request=PortfolioRequest(tuple(s.strip().upper() for s in self.symbols.text().split(',') if s.strip()),
            self.source.currentData(),self.objective.currentData(),self.cap.value(),self.rf.value()/100)
        try:request.validate()
        except ValueError:
            self.clear_result()
            self.status.setText("서로 다른 2–15개 심볼과 유효한 비중·금리를 입력하세요.")
            return
        self.requested.emit(request)

    def show_result(self, output):
        from .app import table_rows
        self.chart.set_output(output)
        chosen=output.portfolios[output.request.objective]
        disclosure=portfolio_disclosure(output.portfolios,output.request.objective)
        self.scope.setText(disclosure['summary'] + "\n" + output.portfolios['max_sharpe'].note)
        table_rows(self.comparison,[[o,f"{p.ann_return:.2%}",f"{p.ann_vol:.2%}",f"{p.sharpe:.3f}",str(p.converged),
            cap_label(p)+(" · selected" if o==output.request.objective else " · comparison")] for o,p in output.portfolios.items()])
        table_rows(self.weights,[[s,f"{float(w):.2%}",f"{float(r):.2%}"] for s,w,r in zip(chosen.symbols,chosen.weights,chosen.risk_contrib)])
        self.correlation.setColumnCount(len(chosen.symbols)+1)
        self.correlation.setHorizontalHeaderLabels(["Symbol",*chosen.symbols])
        table_rows(self.correlation,[[s,*[f"{v:.3f}" for v in row]] for s,row in zip(chosen.symbols,output.stats.corr)])
        sources=[f"{h.symbol}: {h.source} · {h.first_date} → {h.last_date} · {h.note}" for h in output.histories]
        synthetic=[h.symbol for h in output.histories if h.source=='SYNTHETIC']
        notes=[f"공통 {output.stats.sessions} sessions", *sources, output.convention_warning,
            *[f"{o}: {p.note}" for o,p in output.portfolios.items() if p.note], output.narrative, disclosure['summary']]
        if synthetic:notes.insert(0,"합성 데이터: "+", ".join(synthetic)+" · 투자 배분이 아닌 계산 시연입니다.")
        self.notes.setText("\n".join(n for n in notes if n))
        self.status.setText("계산 완료 · solver converged="+str(chosen.converged)+" · 공식 투자 판정 없음")
        self.exports.set_result('portfolio', output.request, [
            {'type': 'provenance', 'histories': [{'symbol': h.symbol, 'source': h.source,
                'first_date': h.first_date, 'last_date': h.last_date, 'note': h.note} for h in output.histories]},
            {'type': 'portfolios', 'data': output.portfolios},
            {'type': 'constraint_scope', 'data': disclosure},
            {'type': 'frontier', 'data': output.frontier},
            {'type': 'correlation', 'symbols': chosen.symbols, 'values': output.stats.corr},
            {'type': 'text', 'text': self.notes.source_text}])

    def clear_result(self):
        self.exports.clear()
        self.chart.set_output(None)
        self.scope.setText('선택한 목적에만 입력 상한이 적용됩니다. 나머지 목적·Frontier·무작위 구름의 종목당 상한은 100%입니다.')
        for widget in (self.comparison, self.weights, self.correlation):
            widget.setRowCount(0)
        self.notes.setText('')
