"""Native context-only technical signals; no live book or order connection."""
from core.research.signals_analysis import SignalsRequest
from .tools import ToolPane, number, fmt
from .model_narrative_language import signals_variants, localize_columns, localize_cell, SIGNAL_STANCES
from .translations import translate


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
        origin = f'{h.symbol} · {h.source} · {h.first_date} → {h.last_date}\n{h.note}'
        original = ('합성 데이터 · ' if h.source == 'SYNTHETIC' else '') + origin
        self.text(original, localized={'en': ('Synthetic data · ' if h.source == 'SYNTHETIC' else '') + origin,
                                       'ko': original})
        self.result_table('Composite',['Score · -100…100','Stance'],[[f'{r.composite:+.2f}',r.stance]])
        if r.stance in SIGNAL_STANCES:
            localize_cell(self.tables['Composite'], 0, 1)
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
            ('Exposure',fmt(b.exposure,'pct')),('Trades',str(b.n_trades)),('Win rate',fmt(b.win_rate,'pct'))])
        self.finished(out.narrative, localized=signals_variants(out))
