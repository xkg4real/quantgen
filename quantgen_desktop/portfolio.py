"""Native portfolio editor and result tables, backed by existing core solvers.

Owner UI review (2026-11-10; issues 13, 04/12, 14, 11), ported from Claude's Flet fix (PR #98,
ui/portfolio_page.py) into GPT's compact native layout:
  * the app chooses the data source (`source="best"`); the selector stays in the tree, hidden, so tests
    and scripts can still pick a provider, and the result names the provider that answered;
  * the result opens with the selected objective's read (verdict first), objective names and yes/no are
    display words, tables are as tall as their rows, and the notes are headed bullets with the full
    paragraph folded underneath;
  * before the first run the page says what to do instead of showing empty tables.
Display only: the request, every number and the export payload are unchanged.
"""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QComboBox, QDoubleSpinBox, QPushButton

from core.research.portfolio_analysis import PortfolioRequest
from core.research.portfolio_disclosure import cap_label, portfolio_disclosure
from .charts import FrontierChart
from .bonds_portfolio_narrative import (portfolio_notes, portfolio_scope_korean,
                                       model_note_korean, display_variants)
from .risk_display import (OBJECTIVE_LABELS, portfolio_sections, portfolio_summary, provenance_line,
                           synthetic_line)

# "best" first: the app's own routing (keyless Yahoo before a labelled synthetic fallback).
SOURCES = (("best", "Auto"), ("auto", "Auto (keyed providers only)"), ("fmp", "FMP"), ("kis", "KIS · KRX"),
           ("yfinance", "Yahoo (total return)"), ("synthetic", "Synthetic demo"))
SCOPE_HINT = "선택한 목적에만 입력 상한이 적용됩니다. 나머지 목적·Frontier·무작위 구름의 종목당 상한은 100%입니다."
EMPTY_STATE = ("Enter symbols separated by commas, pick an objective and press [Run portfolio analysis]. "
               "All four objectives are computed and marked on the frontier, so their trade-offs are "
               "visible side by side.")


class PortfolioPane(QWidget):
    requested = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        # Imported here to avoid a module-level UI dependency cycle.
        from .app import label, table, panel
        from .form_layout import CompactFieldGrid,bound_input_panel,add_compact_action
        from .result_layout import fit_result_table
        from .narrative_view import FullTextFold
        self.setObjectName("portfolio-pane")
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(20)
        box,inner=panel("포트폴리오 최적화")
        bound_input_panel(box)
        pairs=[]
        self.symbols=QLineEdit("AAPL, MSFT, NVDA, TLT")
        # Owner issues 04/12: no data-source selector; the app fetches by itself.
        self.source=QComboBox()
        for v,text in SOURCES:self.source.addItem(text,v)
        self.source.setAccessibleName("Source")
        self.objective=QComboBox()
        for v in ("max_sharpe","min_vol","risk_parity","equal_weight"):self.objective.addItem(OBJECTIVE_LABELS[v],v)
        self.cap=QDoubleSpinBox();self.cap.setRange(.01,1);self.cap.setSingleStep(.05);self.cap.setValue(1)
        self.rf=QDoubleSpinBox();self.rf.setRange(-100,100);self.rf.setValue(3);self.rf.setSuffix(" %")
        for i,(name,w) in enumerate((("Symbols · comma separated",self.symbols),
            ("Objective",self.objective),("Max weight / asset",self.cap),("Risk-free",self.rf))):
            w.setAccessibleName(name);pairs.append((label(name,"caption"),w))
        self.form=CompactFieldGrid(pairs,max_columns=4)
        inner.addWidget(self.form)
        inner.addWidget(self.source);self.source.hide()
        self.run=QPushButton("포트폴리오 분석 실행");self.run.setProperty("primary",True);self.run.clicked.connect(self.submit)
        add_compact_action(inner,self.run)
        self.status=label("동일 관측일의 이력을 정렬한 후 네 가지 목적함수를 비교합니다.","muted")
        self.status.setProperty("reading_help_keep_visible", True)
        inner.addWidget(self.status);layout.addWidget(box)
        self.empty=label(EMPTY_STATE,"muted")
        self.empty.localized_text = {
            'ko': '종목과 목적함수를 정한 뒤 분석을 실행하세요. 결과에서 네 가지 배분 방식과 위험을 비교할 수 있어요.',
            'en': 'Choose assets and an objective, then run the analysis to compare four allocations and their risks.'}
        self.empty.retranslate()
        self.empty.setMaximumWidth(960)
        self.empty.setProperty("reading_help_keep_visible", True)
        layout.addWidget(self.empty)

        # Everything below appears once a result exists.
        self.result=QWidget();result=QVBoxLayout(self.result);result.setContentsMargins(0,0,0,0);result.setSpacing(16)
        summary,summary_layout=panel("")
        self.summary_title=label("","cardTitle")
        self.summary=label("")
        self.synthetic=label("","muted")
        self.provenance=label("","caption")
        for widget in (self.summary_title,self.summary,self.synthetic,self.provenance):
            widget.setProperty("reading_help_keep_visible", True);summary_layout.addWidget(widget)
        result.addWidget(summary)
        self.scope=label(SCOPE_HINT,"caption")
        self.scope.setProperty("reading_help_keep_visible", True)
        result.addWidget(self.scope)
        self.chart=FrontierChart()
        # Reading pane beside the chart: headed bullets, the full notes paragraph folded below them.
        self.reading=QWidget();self.reading_layout=QVBoxLayout(self.reading)
        self.reading_layout.setContentsMargins(0,0,0,0);self.reading_layout.setSpacing(8)
        self.reading_layout.addWidget(label("Analysis narrative · display language; original retained in export","caption"))
        self.narrative_view=None
        self.notes=label("아직 실행한 분석이 없습니다.","muted")
        self.notes.setProperty("reading_help_keep_visible", False)
        self.notes_fold=FullTextFold(self.notes)
        self.reading_layout.addWidget(self.notes_fold)
        from .chart_study import ChartStudy
        result.addWidget(ChartStudy(self.chart,self.reading))
        self.comparison=table(["Objective","연율 수익률","연율 변동성","Sharpe","수렴","종목당 상한 / 범위"])
        self.comparison.setProperty("localized_columns",[0,4,5])
        self.weights=table(["Symbol","Weight","Risk contribution"])
        self.correlation=table([])
        for title,widget in (("All four objectives compared",self.comparison),
                             ("Weights and risk contributions",self.weights),
                             ("Correlation of daily returns",self.correlation)):
            fit_result_table(widget)  # every row visible, no empty body below the last one
            result.addWidget(label(title,"heading"));result.addWidget(widget)
        notice=label("Historical-sample optimization, not a future return guarantee or official gate verdict. "
                     "All results are long-only and fully invested; equal weight fixes each weight at 1/N.","caption")
        notice.setProperty("reading_help_keep_visible", True)
        result.addWidget(notice)
        from .report_actions import ReportActions
        self.exports = ReportActions(self.status)
        result.addWidget(self.exports)
        layout.addWidget(self.result)
        self.result.hide()
        layout.addStretch()   # before a result, keep the form and the empty-state line together at the top

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
        from .narrative_view import NarrativeView
        from ui.narrative_sections import ko_terms
        self.chart.set_output(output)
        chosen=output.portfolios[output.request.objective]
        disclosure=portfolio_disclosure(output.portfolios,output.request.objective)
        self.scope.setText(disclosure['summary'] + "\n" + output.portfolios['max_sharpe'].note)
        table_rows(self.comparison,[[OBJECTIVE_LABELS.get(o,o),f"{p.ann_return:.2%}",f"{p.ann_vol:.2%}",f"{p.sharpe:.3f}",
            "Yes" if p.converged else "No",
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
        # Owner issue 14: raw ids (equal_weight, risk_parity, ...) read as their Korean names in Korean.
        notes_ko=portfolio_notes(output,'ko',disclosure)
        display_variants(self.notes, portfolio_notes(output,'en',disclosure), ko_terms(notes_ko))
        display_variants(self.scope, self.scope.source_text,
                         ko_terms(portfolio_scope_korean(output.portfolios,output.request.objective)
                                  + '\n' + model_note_korean(output.portfolios['max_sharpe'].note)))
        (title_en,text_en),(title_ko,text_ko)=portfolio_summary(output,'en'),portfolio_summary(output,'ko')
        for widget,en,ko in ((self.summary_title,title_en,title_ko),(self.summary,text_en,text_ko),
                             (self.synthetic,synthetic_line(output.histories,'en'),synthetic_line(output.histories,'ko')),
                             (self.provenance,provenance_line(output.histories,'en'),provenance_line(output.histories,'ko'))):
            widget.setText(en);display_variants(widget,en,ko)
        self.synthetic.setVisible(bool(synthetic))
        if self.narrative_view is not None:
            self.narrative_view.hide();self.narrative_view.deleteLater()
        self.narrative_view=NarrativeView(portfolio_sections(output))
        self.reading_layout.insertWidget(1,self.narrative_view)
        self.notes.retranslate()
        self.status.setText("Calculation complete · no official investment verdict" if chosen.converged else
                            "Calculation complete · the solver did not report convergence; treat the weights as "
                            "approximate · no official investment verdict")
        self.empty.hide();self.result.show()
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
        self.scope.setText(SCOPE_HINT)
        for widget in (self.comparison, self.weights, self.correlation):
            widget.setRowCount(0)
        self.notes.setText('')
        if self.narrative_view is not None:
            self.narrative_view.hide();self.narrative_view.deleteLater();self.narrative_view=None
        self.result.hide();self.empty.show()
