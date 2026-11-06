"""Native descriptive macro sheet, daily commentary and weekly rates/FX note."""
from core.research.macro_analysis import MacroRequest
from .tools import ToolPane, fmt
from .macro_narrative_language import macro_korean, summary_korean, sheet_note_korean, indicator_caption
from .localization import CAPTION_ROLE


def level(row):
    if row.unit=='pct':return fmt(row.last,'pct')
    if row.unit=='bp':return fmt(row.last,'bp')
    return fmt(row.last)


def change(row,value):
    return fmt(value,'bp' if row.unit in ('pct','bp') else 'number')


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
        self.status.setText('이 탭은 descriptive macro sheet입니다. v2 Overlay·Model cards·Research register는 분석 도구의 매크로 v2에서 확인합니다.')

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
            self.text('합성 데이터 포함: '+', '.join(s.synthetic_ids),
                      localized={'en':'Includes synthetic data: '+', '.join(s.synthetic_ids)})
        self.text(s.note, localized={'ko':sheet_note_korean(s.note)})
        self.result_table('Descriptive read',['Curve','Risk','Dollar','Breakevens','Real yields'],[[r.curve,r.risk,r.dollar,r.inflation,r.real_rates]])
        localize_columns(self.tables['Descriptive read'], range(5))
        self.text(r.summary, localized={'ko':summary_korean(r.summary)})
        self.bars('1y z-scores · descriptive only',[(a.label+(' · SYNTHETIC' if a.source=='SYNTHETIC' else ''),a.z_1y) for a in s.rows])
        chart = self.charts['1y z-scores · descriptive only']
        chart.localized_labels = {
            index: {'ko': indicator_caption(a) + (' · SYNTHETIC' if a.source == 'SYNTHETIC' else '')}
            for index, a in enumerate(s.rows) if indicator_caption(a) != a.label}
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
        self.text('금리·스프레드의 변화는 bp, 다른 지표의 변화는 원 단위입니다. 분류는 설명용이며 검증 게이트나 포지션을 바꾸지 않습니다.')
        korean=macro_korean(out)
        self.finished(out.narrative, localized={'ko':korean} if korean is not None else None)
