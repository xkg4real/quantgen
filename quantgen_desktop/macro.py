"""Native descriptive macro sheet, daily commentary and weekly rates/FX note."""
from core.research.macro_analysis import MacroRequest
from .tools import ToolPane, fmt
from .macro_narrative_language import (macro_korean, summary_korean, sheet_note_korean, indicator_caption,
                                       chart_caption_korean, descriptive_read_lines, synthetic_notice,
                                       GROUP_NAMES, Z_CHART_TEXTS)
from .localization import CAPTION_ROLE

Z_CHART = '1y z-scores · descriptive only'


def level(row):
    if row.unit=='pct':return fmt(row.last,'pct')
    if row.unit=='bp':return fmt(row.last,'bp')
    return fmt(row.last)


def change(row,value):
    return fmt(value,'bp' if row.unit in ('pct','bp') else 'number')


def fit_rows(table):
    """Every row visible without an inner scroll (GPT's `result_layout.ContentTableHeight`), keeping each
    cell's own alignment: these tables hold words and names, not a metric/value pair."""
    from .result_layout import ContentTableHeight

    class _RowsHeight(ContentTableHeight):
        def measure(self):
            self.pending = False
            self.measuring = True
            try:
                self.table.resizeRowsToContents()
                height = self.content_height()
                if self.table.minimumHeight() != height or self.table.maximumHeight() != height:
                    self.table.setFixedHeight(height)
                    self.table.updateGeometry()
            finally:
                self.measuring = False
            if self.table.height() != self.content_height():
                self.schedule()

    if not hasattr(table, '_content_height_controller'):
        table._content_height_controller = _RowsHeight(table)
    return table


def localize_columns(table, columns):
    """Register authored captions after the shared table builder populates cells."""
    table.setProperty('localized_columns', list(columns))
    for row in range(table.rowCount()):
        for column in columns:
            item = table.item(row, column)
            if item is not None:
                item.setData(CAPTION_ROLE, item.text())


class MacroPane(ToolPane):
    def __init__(self):
        super().__init__('Macro · 시장 관측과 로컬 해설',
            [('sheet','Macro sheet'),('daily','Daily commentary'),('weekly','Weekly rates & FX')],
            [('auto','Auto · synthetic fallback'),('fred','Live providers only · no fallback'),('synthetic','Synthetic demo')],
            {k:[] for k in ('sheet','daily','weekly')})
        # Owner issue 14 (2026-11-10): English source, all-Korean display (no "descriptive macro sheet" in Korean).
        self.status.setText('This tab is a descriptive macro sheet. See Analysis tools → Macro v2 for the v2 Overlay, '
                            'Model cards and Research register.')
        # Owner issue 02 (long horizontal scroll): the indicator table spans the page width below the
        # chart/commentary columns, so all nine columns show; its export section is unchanged.
        from PyQt6.QtWidgets import QVBoxLayout, QWidget
        self.wide = QWidget()
        self.wide_layout = QVBoxLayout(self.wide)
        self.wide_layout.setContentsMargins(0, 0, 0, 0)
        self.wide_layout.setSpacing(16)
        main = self.layout()
        main.insertWidget(main.indexOf(self.study) + 1, self.wide)

    def clear_result(self):
        super().clear_result()
        layout = getattr(self, 'wide_layout', None)
        while layout is not None and layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()

    def make_request(self):
        return MacroRequest(tool=self.tool.currentData(),source=self.source.currentData())

    def show_result(self,out):
        from core.ficc.macro import DESCRIPTIVE_READ_NOTE
        self.clear_result()
        s=out.sheet; r=s.regime
        self.text(DESCRIPTIVE_READ_NOTE)
        source_counts=', '.join(f'{k}: {v}' for k,v in s.sources.items())
        self.text(f'As of {s.as_of} · '+source_counts,
                  localized={'ko':f'기준일 {s.as_of} · '+source_counts}, display_role='provenance')
        if s.synthetic_ids:
            # Owner issue 02: the synthetic status is said once (the notice below, hatched bars in the chart);
            # the id list stays in the export and under Details.
            self.text('합성 데이터 포함: '+', '.join(s.synthetic_ids),
                      localized={'en':'Includes synthetic data: '+', '.join(s.synthetic_ids)}, display_role='provenance')
        notice = synthetic_notice(s)
        self.text(s.note, localized=notice or {'ko':sheet_note_korean(s.note)})
        self.result_table('Descriptive read',['Curve','Risk','Dollar','Breakevens','Real yields'],[[r.curve,r.risk,r.dollar,r.inflation,r.real_rates]])
        localize_columns(self.tables['Descriptive read'], range(5))
        fit_rows(self.tables['Descriptive read'])  # one row: no empty table body below it
        # Each word with its meaning and the summary's own numbers; the export keeps the core's summary.
        self.text(r.summary, localized=descriptive_read_lines(r) or {'ko':summary_korean(r.summary)})
        self.bars(Z_CHART,[(a.label+(' · SYNTHETIC' if a.source=='SYNTHETIC' else ''),a.z_1y) for a in s.rows])
        self._present_zscores(s)
        self.result_table('Macro indicators',['Group','Indicator','Last','1d','1w','1m','3m','1y z-score','1y percentile','Source','Observed date'],
            [[a.group,a.label,level(a),change(a,a.chg_1d),change(a,a.chg_1w),change(a,a.chg_1m),change(a,a.chg_3m),
              fmt(a.z_1y),fmt(a.pct_1y,'pct'),a.source,a.last_date] for a in s.rows])
        indicators = self.tables['Macro indicators']
        localize_columns(indicators, [0])
        # Provider/custom captions never enter the display catalogue implicitly.
        indicators.setProperty('localized_columns', [0, 1])
        for index, a in enumerate(s.rows):
            if indicator_caption(a) != a.label:
                indicators.item(index, 1).setData(CAPTION_ROLE, a.label)
            # Owner, 2026-11-04: no Source / Observed date columns on screen; the export keeps both.
            indicators.item(index, 1).setToolTip(f'{a.source} · {a.last_date}')
        for column in (9, 10):
            indicators.setColumnHidden(column, True)
        fit_rows(indicators)  # every indicator row visible, no inner scroll
        units = self.text('금리·스프레드의 변화는 bp, 다른 지표의 변화는 원 단위입니다. 분류는 설명용이며 검증 게이트나 포지션을 바꾸지 않습니다.')
        heading = self.result_layout.itemAt(self.result_layout.indexOf(indicators) - 1).widget()
        for widget in (heading, indicators, units):
            self.result_layout.removeWidget(widget)
            self.wide_layout.addWidget(widget)
        korean=macro_korean(out)
        self.finished(out.narrative, localized={'ko':korean} if korean is not None else None)

    def _present_zscores(self, s):
        """Owner issue 02: the z-score bars read like the Flet chart (PR #98) in the window language.

        Rows keep their source labels and values (the export); only the drawing and the captions change."""
        from .chart_study import LocalLabel
        chart = self.charts[Z_CHART]
        # Plain-language names with the code; the synthetic status is the hatching and one legend entry.
        chart.localized_labels = {index: {'ko': chart_caption_korean(a), 'en': a.label}
                                  for index, a in enumerate(s.rows)}
        chart.show_zscores(groups=[a.group for a in s.rows], group_names=GROUP_NAMES, texts=Z_CHART_TEXTS,
                           hatched=[i for i, a in enumerate(s.rows) if a.source == 'SYNTHETIC'])
        # The heading's Korean is the Flet chart title (macro_narrative_language.PAIRS); this caption is
        # display-only, so it is not a UiLabel (those are the export's text sections).
        caption = LocalLabel({'ko': f'기준일 {s.as_of} · 막대 끝 숫자 = z-점수',
                              'en': f'As of {s.as_of} · number at bar end = z-score'}, 'muted')
        self.result_layout.insertWidget(self.result_layout.indexOf(chart), caption)
