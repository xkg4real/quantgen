"""Native descriptive macro sheet, daily commentary and weekly rates/FX note."""
from core.research.macro_analysis import MacroRequest
from .tools import ToolPane, fmt


def level(row):
    if row.unit=='pct':return fmt(row.last,'pct')
    if row.unit=='bp':return fmt(row.last,'bp')
    return fmt(row.last)


def change(row,value):
    return fmt(value,'bp' if row.unit in ('pct','bp') else 'number')


class MacroPane(ToolPane):
    def __init__(self):
        super().__init__('Macro · 시장 관측과 로컬 해설',
            [('sheet','Macro sheet'),('daily','Daily commentary'),('weekly','Weekly rates & FX')],
            [('auto','Auto · synthetic fallback'),('fred','Live providers only · no fallback'),('synthetic','Synthetic demo')],
            {k:[] for k in ('sheet','daily','weekly')})
        self.status.setText('이 탭은 descriptive macro sheet입니다. v2 Overlay·Model cards·Research register는 Markets의 Macro v2 탭에서 확인합니다.')

    def make_request(self):
        return MacroRequest(tool=self.tool.currentData(),source=self.source.currentData())

    def show_result(self,out):
        from core.ficc.macro import DESCRIPTIVE_READ_NOTE
        self.clear_result()
        s=out.sheet; r=s.regime
        self.text(DESCRIPTIVE_READ_NOTE)
        self.text(f'As of {s.as_of} · '+', '.join(f'{k}: {v}' for k,v in s.sources.items()))
        if s.synthetic_ids:self.text('합성 데이터 포함: '+', '.join(s.synthetic_ids))
        self.text(s.note)
        self.result_table('Descriptive read',['Curve','Risk','Dollar','Breakevens','Real yields'],[[r.curve,r.risk,r.dollar,r.inflation,r.real_rates]])
        self.text(r.summary)
        self.bars('1y z-scores · descriptive only',[(a.label+(' · SYNTHETIC' if a.source=='SYNTHETIC' else ''),a.z_1y) for a in s.rows])
        self.result_table('Macro indicators',['Group','Indicator','Last','1d','1w','1m','3m','1y z-score','1y percentile','Source','Observed date'],
            [[a.group,a.label,level(a),change(a,a.chg_1d),change(a,a.chg_1w),change(a,a.chg_1m),change(a,a.chg_3m),
              fmt(a.z_1y),fmt(a.pct_1y,'pct'),a.source,a.last_date] for a in s.rows])
        self.text('금리·스프레드의 변화는 bp, 다른 지표의 변화는 원 단위입니다. 분류는 설명용이며 검증 게이트나 포지션을 바꾸지 않습니다.')
        self.finished(out.narrative)
