"""Shared native form and result widgets for the FICC tool panes."""
from .translations import display
import math
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLineEdit, QPushButton, QSizePolicy, QVBoxLayout, QWidget
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


class CurrentPageStack(QWidget):
    """Shows one form page and sizes to that page alone (owner UI-6a).

    A QStackedWidget measures every page, and the fixed height taken at construction
    missed the theme's taller inputs, so the last row of the Rates and KRX forms was
    cut off. Hidden pages here take no space: the layout measures the visible form
    after styles apply, height-for-width included, and re-lays out when it changes.
    """
    currentChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pages, self._index = [], -1
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

    def addWidget(self, page):
        self._pages.append(page)
        self._layout.addWidget(page)
        if self._index < 0:
            self._index = 0
            self.currentChanged.emit(0)
        else:
            page.hide()
        return len(self._pages) - 1

    def count(self):
        return len(self._pages)

    def widget(self, index):
        return self._pages[index] if 0 <= index < len(self._pages) else None

    def currentIndex(self):
        return self._index

    def currentWidget(self):
        return self.widget(self._index)

    def setCurrentIndex(self, index):
        if not 0 <= index < len(self._pages) or index == self._index:
            return
        self._pages[self._index].hide()
        self._index = index
        self._pages[index].show()
        self.currentChanged.emit(index)


class ToolPane(QWidget):
    requested = pyqtSignal(object)

    def __init__(self, title, tools, sources, fields):
        super().__init__()
        from .app import label, panel
        from .form_layout import CompactFieldGrid, bound_input_panel, add_compact_action
        self.has_result = False
        self.report = None
        self.sections = []
        self.tables = {}
        self.charts = {}
        self._details_fold = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(26)  # owner 2026-11-11: roomy blocks with light lines
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.input_box, inner = panel(title)
        bound_input_panel(self.input_box)
        # Preferred, not Maximum: a Maximum height is capped at the size hint, which Qt takes at the panel's
        # preferred width. Where captions wrap more at the real width (Windows fonts), that cap cut the
        # last form row (owner UI-6a). The pane's top alignment still keeps the panel from stretching.
        self.input_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        top = QGridLayout()
        self.tool, self.source = QComboBox(), QComboBox()
        for key, text in tools: self.tool.addItem(text, key)
        for key, text in sources: self.source.addItem(text, key)
        for i, (name, w) in enumerate((('Tool', self.tool), ('Data source', self.source))):
            w.setAccessibleName(name)
            # Long translated options remain in the popup/tooltip without
            # making the two-column header wider than a narrow viewport.
            w.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            w.setMinimumContentsLength(12)
            w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            w.setToolTip(w.currentText())
            w.currentTextChanged.connect(w.setToolTip)
            w.model().dataChanged.connect(lambda *args, combo=w: combo.setToolTip(combo.currentText()))
            caption = label(name, 'caption')
            if w is self.source:
                self.source_label = caption
            top.addWidget(caption, 0, i)
            top.addWidget(w, 1, i)
            top.setColumnStretch(i, 1)
        self._top_grid = top
        inner.addLayout(top)
        self.forms, self.fields = CurrentPageStack(), {}
        for key, _ in tools:
            pairs = []
            controls = {}
            for i, (name, text, default) in enumerate(fields[key]):
                if isinstance(default, list):
                    w = QComboBox()
                    for value, display in default: w.addItem(display, value)
                else: w = QLineEdit(str(default))
                w.setAccessibleName(text)
                controls[name] = w
                pairs.append((label(text, 'caption'), w))
            self.fields[key] = controls
            self.forms.addWidget(CompactFieldGrid(pairs))
        inner.addWidget(self.forms)
        self.run = QPushButton('분석 실행')
        self.run.setProperty('primary', True)
        self.run.clicked.connect(self.submit)
        add_compact_action(inner, self.run)
        layout.addWidget(self.input_box)
        self.prompt = '도구와 출처를 선택한 후 실행하세요.'  # the status with nothing run yet
        self.status = label(self.prompt, 'muted')
        self.status.setProperty('reading_help_keep_visible', True)
        layout.addWidget(self.status)
        self.result = QWidget()
        self.result_layout = QVBoxLayout(self.result)
        self.result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_layout.setSpacing(22)
        self.result_reading=QWidget()
        self.result_reading_layout=QVBoxLayout(self.result_reading)
        self.result_reading_layout.setContentsMargins(0,0,0,0)
        from .chart_study import ChartStudy
        self.study=ChartStudy(self.result,self.result_reading)
        layout.addWidget(self.study)
        self.result_reading.hide()
        exports = QHBoxLayout()
        self.export_json, self.export_zip = QPushButton('분석 JSON 저장'), QPushButton('보고서 ZIP 저장')
        for button, bundle in ((self.export_json, False), (self.export_zip, True)):
            button.setEnabled(False)
            button.clicked.connect(lambda checked=False, b=bundle:self.export_result(b))
            exports.addWidget(button)
        layout.addLayout(exports)
        self.tool.currentIndexChanged.connect(self.switch)

    def hide_source(self):
        """Markets panes choose providers automatically (owner UI-8): no 데이터 출처 selector.

        The combo keeps its first (automatic) value for requests, exports and fixtures;
        every result still names the provider that actually answered.
        """
        self.source.setCurrentIndex(0)
        self.source.hide()
        self.source_label.hide()
        self._top_grid.setColumnStretch(1, 0)
        # With no selector the prompt must not ask for a source (owner issues 04/12).
        self.prompt = 'Choose a tool, then run.'
        if self.status.source_text == '도구와 출처를 선택한 후 실행하세요.':
            self.status.setText(self.prompt)

    def set_source_caption(self, text):
        self.source_label.setText(text)
        self.source.setAccessibleName(text)

    def switch(self, index):
        self.forms.setCurrentIndex(index)
        self.clear_result()
        self.status.setText('도구가 변경됐습니다. 다시 실행하세요.')

    def select_tool(self, key):
        """Show one tool's form as a destination (the rail's 시장 menu, owner ruling UI-D11): with no result shown,
        the status keeps the plain prompt rather than 'Tool changed. Run again.', which reads as a stale result on a
        pane nobody ran (UI-D11 review). With a result shown, the switch says it is gone as a picker change does."""
        index = self.tool.findData(key)
        if index < 0:
            raise ValueError(f"Unknown tool {key!r}")
        had_result = self.has_result
        self.tool.setCurrentIndex(index)
        if not had_result:
            self.status.setText(self.prompt)
        return True

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
        reading_help = getattr(self.window(), '_reading_help', None)
        if reading_help is not None:
            reading_help.invalidate_source(self)
        self.has_result = False
        self.report = None
        self.sections = []
        self.export_json.setEnabled(False)
        self.export_zip.setEnabled(False)
        self.tables, self.charts = {}, {}
        self._details_fold = None
        while self.result_reading_layout.count():
            item=self.result_reading_layout.takeAt(0)
            if item.widget():item.widget().hide();item.widget().deleteLater()
        self.result_reading.hide()
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

    def _place_result_widget(self, widget, display_role=None):
        # A role is display metadata only. Unclassified/mixed blocks, assumptions,
        # synthetic/delayed notices and failures always remain in the main body.
        widget.setProperty('display_role', display_role)
        widget.setProperty('reading_help_keep_visible', display_role != 'provenance')
        if display_role == 'provenance':
            if self._details_fold is None:
                from .reading_panel import DetailsFold
                self._details_fold = DetailsFold(getattr(self.window(), 'ctx', None))
                self.result_layout.addWidget(self._details_fold)
            self._details_fold.add_widget(widget)
        else:
            self.result_layout.addWidget(widget)

    def text(self, text, role='muted', *, localized=None, name=None, display_role=None):
        """`name` labels the export section; a private name (e.g. holdings) keeps it out of AI commentary."""
        from .app import label
        from core.research.presentation import safe_detail
        text = safe_detail(text, limit=None)
        self.sections.append({'type':'text','text':text, **({'name': name} if name else {})})
        widget = label(text, role)
        if localized:
            widget.localized_text = {key: safe_detail(value, limit=None) for key, value in localized.items()}
        self._place_result_widget(widget, display_role)
        widget.retranslate()
        return widget

    def result_table(self, name, headers, rows, *, localized_columns=None, display_role=None):
        from .app import label, table, table_rows
        self.sections.append({'type':'table','name':name,'headers':headers,'rows':rows})
        heading = label(name, 'heading')
        self._place_result_widget(heading, display_role)
        widget = table(headers)
        if localized_columns is not None:
            widget.setProperty('localized_columns', list(localized_columns))
        elif headers and headers[0] == 'Metric':
            widget.setProperty('localized_columns', [0])
        table_rows(widget, rows)
        widget.setMinimumHeight(min(400, max(120, 45+len(rows)*32)))
        # Ordinary result tables may be covered by the narrow help panel; their
        # values remain unchanged. Important notice/assumption tables opt out.
        self._place_result_widget(widget, display_role)
        if display_role is None:
            widget.setProperty('reading_help_keep_visible', False)
            heading.setProperty('reading_help_keep_visible', False)
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
        self._add_chart_reading(name, chart)

    def _add_chart_reading(self, name, chart):
        """'How to read this chart' under a chart with an authored guide (owner issue 02); display only."""
        from .chart_study import chart_reading
        chart.reading = chart_reading(name)
        if chart.reading is not None:
            self.result_layout.addWidget(chart.reading)

    def finished(self, narrative, *, localized=None, sections=None):
        """Show the narrative as headed bullets (owner issue 11), the full paragraph folded below.

        `localized` gives reviewed per-language texts ({'ko': ...}); `sections` optionally gives ready
        headed bullets per language ({'ko': [(heading, [line, ...]), ...]}). Export text is unchanged."""
        from .app import label
        from .narrative_view import FullTextFold, NarrativeView
        notice = ('Analysis narrative · display language; original retained in export' if localized else
                  'Analysis narrative · original source language retained')
        self.result_reading_layout.addWidget(label(notice, 'caption'))
        narrative_widget=self.text(narrative, localized=localized)
        self.result_layout.removeWidget(narrative_widget)
        variants = {'en': narrative_widget.source_text}
        if localized:
            variants.update({k: v for k, v in narrative_widget.localized_text.items() if v})
        if sections:
            variants.update(sections)
        self.narrative_view = NarrativeView(variants)
        self.result_reading_layout.addWidget(self.narrative_view)
        # The folded paragraph is secondary: closed by default, so it does not ask to stay visible.
        narrative_widget.setProperty('reading_help_keep_visible', False)
        self.result_reading_layout.addWidget(FullTextFold(narrative_widget))
        narrative_widget.retranslate()  # it was reparented through the fold before the fold joined the window
        self.result_reading.show()
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
        self._add_chart_reading(name, chart)

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
        filename, _ = QFileDialog.getSaveFileName(self, display(self, '분석 결과 저장'), f"quantgen-{self.report['tool']}.{extension}", f'Report (*.{extension})')
        if not filename: return
        try:
            save_desktop_export(filename, report_bytes(self.report, bundle=bundle,locale=getattr(self.window(),'ctx',None)), extension=extension)
        except (OSError, ValueError, TypeError) as exc:
            self.status.setText(f'저장 실패 · {type(exc).__name__} · 경로와 확장자를 확인하세요.')
            return
        self.status.setText('저장 완료 · '+Path(filename).name)
