"""Shared native form and result widgets for the FICC tool panes."""
import math
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLineEdit, QPushButton, QStackedWidget, QVBoxLayout, QWidget
from .charts import LineChart, SignedBars
from core.ficc.common import FICCError


def number(value, *, optional=False, integer=False, scale=1):
    text = str(value).strip().replace(',', '')
    if optional and not text: return None
    x = float(text)
    if not math.isfinite(x) or (integer and not x.is_integer()): raise ValueError('Invalid number')
    return int(x) if integer else x * scale


def fmt(value, mode='number'):
    if value is None or not math.isfinite(float(value)): return '—'
    if mode == 'pct': return f'{value:.3%}'
    if mode == 'bp': return f'{value*10000:+.2f} bp'
    return f'{value:,.4f}'


class ToolPane(QWidget):
    requested = pyqtSignal(object)

    def __init__(self, title, tools, sources, fields):
        super().__init__()
        from .app import label, panel
        self.has_result = False
        self.report = None
        self.sections = []
        self.tables = {}
        self.charts = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(18)
        self.input_box, inner = panel(title)
        top = QGridLayout()
        self.tool, self.source = QComboBox(), QComboBox()
        for key, text in tools: self.tool.addItem(text, key)
        for key, text in sources: self.source.addItem(text, key)
        for i, (name, w) in enumerate((('Tool', self.tool), ('Data source', self.source))):
            w.setAccessibleName(name)
            top.addWidget(label(name, 'caption'), 0, i)
            top.addWidget(w, 1, i)
        inner.addLayout(top)
        self.forms, self.fields = QStackedWidget(), {}
        for key, _ in tools:
            host = QWidget()
            form = QGridLayout(host)
            controls = {}
            for i, (name, text, default) in enumerate(fields[key]):
                if isinstance(default, list):
                    w = QComboBox()
                    for value, display in default: w.addItem(display, value)
                else: w = QLineEdit(str(default))
                w.setAccessibleName(text)
                controls[name] = w
                row, col = (i//3)*2, i%3
                form.addWidget(label(text, 'caption'), row, col)
                form.addWidget(w, row+1, col)
                form.setColumnStretch(col, 1)
            self.fields[key] = controls
            self.forms.addWidget(host)
        inner.addWidget(self.forms)
        self.run = QPushButton('분석 실행')
        self.run.setProperty('primary', True)
        self.run.clicked.connect(self.submit)
        inner.addWidget(self.run)
        layout.addWidget(self.input_box)
        self.status = label('도구와 출처를 선택한 후 실행하세요.', 'muted')
        layout.addWidget(self.status)
        self.result = QWidget()
        self.result_layout = QVBoxLayout(self.result)
        self.result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_layout.setSpacing(16)
        layout.addWidget(self.result)
        exports = QHBoxLayout()
        self.export_json, self.export_zip = QPushButton('분석 JSON 저장'), QPushButton('보고서 ZIP 저장')
        for button, bundle in ((self.export_json, False), (self.export_zip, True)):
            button.setEnabled(False)
            button.clicked.connect(lambda checked=False, b=bundle:self.export_result(b))
            exports.addWidget(button)
        layout.addLayout(exports)
        self.tool.currentIndexChanged.connect(self.switch)
        self.forms.setFixedHeight(self.forms.currentWidget().sizeHint().height())

    def switch(self, index):
        self.forms.setCurrentIndex(index)
        self.forms.setFixedHeight(self.forms.currentWidget().sizeHint().height())
        self.clear_result()
        self.status.setText('도구가 변경됐습니다. 다시 실행하세요.')

    def values(self):
        return {k:w.currentData() if isinstance(w, QComboBox) else w.text()
                for k,w in self.fields[self.tool.currentData()].items()}

    def submit(self):
        try:
            request = self.make_request()
            request.validate()
        except (ValueError, TypeError, OverflowError, FICCError):
            self.clear_result()
            self.status.setText('입력 오류 · 숫자, 단위, 만기 및 선택한 도구의 조건을 확인하세요.')
            return
        self.requested.emit(request)

    def clear_result(self):
        self.has_result = False
        self.report = None
        self.sections = []
        self.export_json.setEnabled(False)
        self.export_zip.setEnabled(False)
        self.tables, self.charts = {}, {}
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

    def text(self, text, role='muted'):
        from .app import label
        from core.research.presentation import safe_detail
        text = safe_detail(text, limit=None)
        self.sections.append({'type':'text','text':text})
        self.result_layout.addWidget(label(text, role))

    def result_table(self, name, headers, rows):
        from .app import label, table, table_rows
        self.sections.append({'type':'table','name':name,'headers':headers,'rows':rows})
        self.result_layout.addWidget(label(name, 'heading'))
        widget = table(headers)
        table_rows(widget, rows)
        widget.setMinimumHeight(min(400, max(120, 45+len(rows)*32)))
        self.result_layout.addWidget(widget)
        self.tables[name] = widget

    def line(self, name, x, series, x_label, y_label):
        from .app import label
        x, series = list(x), [(n,list(v)) for n,v in series]
        self.sections.append({'type':'line','name':name,'x':x,'series':series,'x_label':x_label,'y_label':y_label})
        self.result_layout.addWidget(label(name, 'heading'))
        chart = LineChart(x_label, y_label)
        chart.colors = self.window().colors
        chart.set_series(x, series)
        self.result_layout.addWidget(chart)
        self.charts[name] = chart

    def finished(self, narrative):
        self.text(narrative)
        self.has_result = True
        self.status.setText('계산 완료 · 출처·관측일·가정을 확인하세요. 공식 검증 판정은 별도입니다.')

    def bars(self,name,rows,limit=None):
        from .app import label
        self.sections.append({'type':'bars','name':name,'rows':rows,'limit':limit})
        self.result_layout.addWidget(label(name,'heading'))
        chart=SignedBars(rows,limit=limit)
        chart.colors=self.window().colors
        self.result_layout.addWidget(chart)
        self.charts[name]=chart

    def bind_output(self, name, output):
        if not self.has_result: return
        from core.research.tool_export import make_report
        self.report = make_report(name, output.request, self.sections)
        self.export_json.setEnabled(True)
        self.export_zip.setEnabled(True)

    def export_result(self, bundle):
        if self.report is None: return
        from pathlib import Path
        from core.research.export import save_desktop_export
        from core.research.tool_export import report_bytes
        extension = 'zip' if bundle else 'json'
        filename, _ = QFileDialog.getSaveFileName(self, '분석 결과 저장', f"quantgen-{self.report['tool']}.{extension}", f'Report (*.{extension})')
        if not filename: return
        try:
            save_desktop_export(filename, report_bytes(self.report, bundle=bundle), extension=extension)
        except (OSError, ValueError, TypeError) as exc:
            self.status.setText(f'저장 실패 · {type(exc).__name__} · 경로와 확장자를 확인하세요.')
            return
        self.status.setText('저장 완료 · '+Path(filename).name)
