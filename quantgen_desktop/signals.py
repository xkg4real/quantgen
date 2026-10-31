"""Native context-only technical signals; no live book or order connection."""
from core.research.signals_analysis import SignalsRequest
from .tools import ToolPane, number, fmt


class SignalsPane(ToolPane):
    def __init__(self):
        fields=[('symbol','Symbol','AAPL'),('fast','Fast / lookback / RSI period','20'),('slow','Slow / RSI exit · unused for momentum','50'),('cost_bps','Cost · bp per side','10')]
        super().__init__('Signals · 기술적 관측과 비용 포함 백테스트',
            [('ma_cross','MA crossover'),('momentum','Momentum'),('rsi_revert','RSI mean reversion')],
            [('auto','Auto'),('fmp','FMP'),('kis','KIS · KRX'),('synthetic','Synthetic demo')],
            {k:fields for k in ('ma_cross','momentum','rsi_revert')})
        self.status.setText('Context only — not a v2 signal (DO-NOT-BUILD TF-12). Nothing here feeds a book.')

    def make_request(self):
        v=self.values()
        return SignalsRequest(tool=self.tool.currentData(),source=self.source.currentData(),symbol=v['symbol'],
            fast=number(v['fast'],integer=True),slow=number(v['slow']) if self.tool.currentData()!='momentum' else 50,
            cost_bps=number(v['cost_bps']))

    def show_result(self,out):
        self.clear_result()
        h,r,b=out.history,out.report,out.backtest
        self.text('Context only — not a v2 signal (DO-NOT-BUILD TF-12). Nothing here feeds a book.')
        self.text(('합성 데이터 · ' if h.source=='SYNTHETIC' else '')+f'{h.symbol} · {h.source} · {h.first_date} → {h.last_date}\n{h.note}')
        self.result_table('Composite',['Score · -100…100','Stance'],[[f'{r.composite:+.2f}',r.stance]])
        self.bars('Component scores · -100…100',[(c.label,c.score) for c in r.components],limit=100)
        self.result_table('Signal components',['Component','Signed score','Weight','Observed value','Reason'],
            [[c.label,f'{c.score:+.2f}',fmt(c.weight,'pct'),c.value,c.reason] for c in r.components])
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
            ('Exposure',fmt(b.exposure,'pct')),('Trades',str(b.n_trades)),('Win rate',fmt(b.win_rate,'pct'))])
        self.finished(out.narrative)
