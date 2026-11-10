"""Native context-only technical signals; no live book or order connection.

Owner UI review (2026-11-10; issues 04/12, 14, 11), from Claude's Flet fix (PR #98, ui/signals_page.py):
the app chooses the data source (`best`, selector hidden), the result opens with the composite in words
and whether the costed strategy beat buy-and-hold, strategy ids, parameters and booleans read as words,
and the tables are as tall as their rows. Display only: the request, the numbers and `self.sections`
(the export) are unchanged.
"""
from core.research.signals_analysis import SignalsRequest, PENDING_LABELS, trade_statistics, trade_statistics_labels
from .tools import ToolPane, number, fmt
from .model_narrative_language import signals_variants, localize_columns, localize_cell, SIGNAL_STANCES
from .translations import translate
from .risk_display import STRATEGY_LABELS, parameters_text, signals_summary, source_name


class SignalsPane(ToolPane):
    def __init__(self):
        fields=[('symbol','Symbol','AAPL'),('fast','Fast / lookback / RSI period','20'),('slow','Slow / RSI exit · unused for momentum','50'),('cost_bps','Cost · bp per side','10')]
        super().__init__('Signals · 기술적 관측과 비용 포함 백테스트',
            [('ma_cross','MA crossover'),('momentum','Momentum'),('rsi_revert','RSI mean reversion')],
            [('best','Auto'),('auto','Auto (keyed providers only)'),('fmp','FMP'),('kis','KIS · KRX'),('synthetic','Synthetic demo')],
            {k:fields for k in ('ma_cross','momentum','rsi_revert')})
        self.hide_source()   # owner issues 04/12: the app fetches by itself ("best")
        self.status.setText('Context only — not a v2 signal (DO-NOT-BUILD TF-12). Nothing here feeds a book.')

    def make_request(self):
        v=self.values()
        return SignalsRequest(tool=self.tool.currentData(),source=self.source.currentData(),symbol=v['symbol'],
            fast=number(v['fast'],integer=True),slow=number(v['slow']) if self.tool.currentData()!='momentum' else 50,
            cost_bps=number(v['cost_bps']))

    def _summary(self, out):
        """Verdict first; display widgets only, never an export section."""
        from .app import label, panel
        box, inner = panel('')
        en, ko = signals_summary(out, 'en'), signals_summary(out, 'ko')
        lines = []
        for index, role in enumerate(('cardTitle', '', 'caption')):
            widget = label(en[index], role)
            widget.localized_text = {'en': en[index], 'ko': ko[index]}
            inner.addWidget(widget)
            lines.append(widget)
        self._place_result_widget(box)
        for widget in lines:   # placed in the window now: show the window language
            widget.setProperty('reading_help_keep_visible', True)
            widget.retranslate()
        self.summary_box = box

    def show_result(self,out):
        from .result_layout import fit_result_table
        self.clear_result()
        h,r,b=out.history,out.report,out.backtest
        count_label, win_label, count_note = trade_statistics_labels(b)
        self._summary(out)
        self.text('Context only — not a v2 signal (DO-NOT-BUILD TF-12). Nothing here feeds a book.')
        origin = f'{h.symbol} · {h.source} · {h.first_date} → {h.last_date}\n{h.note}'
        original = ('합성 데이터 · ' if h.source == 'SYNTHETIC' else '') + origin
        from .source_notes import note_korean
        korean = (f'합성 데이터 · {h.symbol} · {h.first_date} → {h.last_date}\n{note_korean(h.note)}' if h.source == 'SYNTHETIC'
                  else f"{h.symbol} · {source_name(h.source, 'ko')} · {h.first_date} → {h.last_date}\n{note_korean(h.note)}")
        self.text(original, localized={'en': ('Synthetic data · ' if h.source == 'SYNTHETIC' else '') + origin,
                                       'ko': korean})
        self.result_table('Composite',['Score · -100…100','Stance'],[[f'{r.composite:+.2f}',r.stance]])
        if r.stance in SIGNAL_STANCES:
            localize_cell(self.tables['Composite'], 0, 1)
        fit_result_table(self.tables['Composite'])
        self.bars('Component scores · -100…100',[(c.label,c.score) for c in r.components],limit=100)
        authored = {'trend50': 'Price vs 50-day SMA', 'trend200': 'Price vs 200-day SMA',
                    'momentum': '3-month momentum', 'vol': 'Volatility regime'}
        self.charts['Component scores · -100…100'].localized_labels = {
            index: {'ko': translate(c.label, 'ko')} for index, c in enumerate(r.components)
            if authored.get(c.key) == c.label}
        self.result_table('Signal components',['Component','Signed score','Weight','Observed value','Reason'],
            [[c.label,f'{c.score:+.2f}',fmt(c.weight,'pct'),c.value,c.reason] for c in r.components])
        localize_columns(self.tables['Signal components'], (0, 4))
        self.line('Price history',range(len(h.dates)),[('Close',h.closes)],'Observations','Price')
        from .indicator_guide import IndicatorGuide
        self.indicator_explorer=IndicatorGuide(locale=getattr(self.window(),'ctx',None),history=h)
        self.result_layout.addWidget(self.indicator_explorer)
        self.line('Costed backtest',range(len(b.dates)),[('Strategy',b.equity),('Buy & hold',b.bench_equity)],
                  f'Sessions · {b.dates[0]} → {b.dates[-1]}','Equity · starts at 1')
        self.result_table('Backtest metrics',['Metric','Value'],[
            ('Strategy',b.strategy),('Parameters',str(b.params)),('Cost / side',f'{b.cost_bps:g} bp'),
            ('Return',fmt(b.total_return,'pct')),('Buy & hold',fmt(b.bench_return,'pct')),('Beat benchmark',str(b.beat_benchmark)),
            ('Annual return',fmt(b.ann_return,'pct')),('Annual volatility',fmt(b.ann_vol,'pct')),('Sharpe',fmt(b.sharpe)),
            ('Max drawdown',fmt(b.max_drawdown,'pct')),('Benchmark drawdown',fmt(b.bench_max_drawdown,'pct')),
            ('Exposure',fmt(b.exposure,'pct')),(count_label,str(b.n_trades)),
            ('Completed round trips',str(b.completed_round_trips) if b.completed_round_trips is not None else '—'),
            ('Final-close signal',PENDING_LABELS.get(b.pending_last_signal,b.pending_last_signal)),
            (win_label,fmt(b.win_rate,'pct'))])
        table = self.tables['Backtest metrics']
        localize_cell(table, table.rowCount()-2, 1)
        # Owner issue 14: the strategy id, the parameter dict and True/False read as words (the export
        # rows above keep the raw values).
        words = {0: STRATEGY_LABELS.get(b.strategy), 1: parameters_text(b.params),
                 5: {'True': 'Yes', 'False': 'No'}.get(str(b.beat_benchmark))}
        for row, text in words.items():
            if text:
                table.item(row, 1).setText(text)
                localize_cell(table, row, 1)
        fit_result_table(table)
        self.text(count_note)
        self.sections.append({'type': 'trade_statistics', **trade_statistics(b)})
        self.finished(out.narrative, localized=signals_variants(out))
