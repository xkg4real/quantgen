"""Market-owned index charts and asset workspaces; never redirect the left rail."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox

from core.i18n import LocaleContext
from core.theme import LIGHT
from .jobs import Jobs
from .stock_detail_style import label, sheet
from .home_view import HistoryChart, MarketInfo, load_market_history


SERIES = {
    '^KS11': ('KOSPI', '코스피', 'yfinance', 'pt'),
    '^KQ11': ('KOSDAQ', '코스닥', 'yfinance', 'pt'),
    '^GSPC': ('S&P 500', 'S&P 500', 'yfinance', 'pt'),
    '^IXIC': ('NASDAQ Composite', '나스닥 종합', 'yfinance', 'pt'),
    'VIXCLS': ('VIX', 'VIX', 'fred', 'pt'),
    'DEXKOUS': ('USD / KRW', '달러 / 원', 'fred', 'KRW/USD'),
    'DGS10': ('US 10-year yield', '미국 10년 국채 금리', 'fred', '%'),
}


class MarketSeriesPage(QWidget):
    def __init__(self, *, ctx, auto_load, loader=None):
        super().__init__()
        self.ctx, self.auto_load, self.loader = ctx, auto_load, loader
        self.colors = LIGHT
        self.symbol, self.category = '^KS11', 'indices'
        self.histories, self.pending = {}, None
        self.epoch = 0
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._loaded)
        self.jobs.failed.connect(self._failed)
        self.jobs.busy_changed.connect(self._busy)
        column = QVBoxLayout(self);column.setContentsMargins(0,0,0,0);column.setSpacing(16)
        self.title = label('name');column.addWidget(self.title)
        toolbar=QHBoxLayout()
        self.selector=QComboBox();self.selector.setObjectName('sdInterval')
        self.selector.activated.connect(lambda: self.select(self.category, self.selector.currentData()))
        toolbar.addWidget(self.selector)
        self.note=label('hint');toolbar.addWidget(self.note,1)
        self.refresh_button=QPushButton();self.refresh_button.setProperty('sd','text')
        self.refresh_button.clicked.connect(self.refresh);toolbar.addWidget(self.refresh_button)
        column.addLayout(toolbar)
        self.price=label('name',selectable=True);column.addWidget(self.price)
        self.chart=HistoryChart();column.addWidget(self.chart)
        self.status=label('hint',wrap=True);column.addWidget(self.status)
        column.addStretch()
        self.set_theme(LIGHT)

    def select(self, category, symbol):
        self.category, self.symbol = category, symbol or '^KS11'
        choices = ('^KS11','^KQ11','^GSPC','^IXIC','VIXCLS') if category=='indices' else (self.symbol,)
        self.selector.blockSignals(True);self.selector.clear()
        for key in choices:self.selector.addItem(SERIES[key][1 if self.ctx.language=='ko' else 0],key)
        self.selector.setCurrentIndex(self.selector.findData(self.symbol));self.selector.blockSignals(False)
        self.render()
        if self.auto_load and self.symbol not in self.histories:self.refresh()

    def refresh(self):
        if self.jobs.busy:
            self.pending=self.symbol
            return
        symbol, epoch = self.symbol, self.epoch
        _en,_ko,provider,unit=SERIES[symbol]
        self.jobs.start(lambda: (epoch,load_market_history(MarketInfo(symbol,provider,unit),loader=self.loader)))
        self.render()

    def _loaded(self, value):
        epoch,history=value
        if epoch==self.epoch:self.histories[history.symbol]=history
        self.render()

    def _failed(self, _code):
        self.status.setText('자료를 가져오지 못했어요. 새로고침으로 다시 조회하세요.' if self.ctx.language=='ko' else
                            'Data could not be loaded. Use Refresh to try again.')

    def _busy(self, busy):
        self.refresh_button.setEnabled(not busy)
        if not busy and self.pending:
            self.pending=None;self.refresh()

    def render(self):
        from .shell_rail import market_section_text
        ko=self.ctx.language=='ko'
        self.title.setText(('시장 / ' if ko else 'Markets / ')+market_section_text(self.category,self.ctx.language))
        self.refresh_button.setText('새로고침' if ko else 'Refresh')
        self.note.setText('지연 · 일별 자료' if ko else 'Delayed · daily observations')
        known=self.histories.get(self.symbol)
        values=known.values if known and known.ok else ()
        dates=known.dates if known and known.ok else ()
        self.chart.set_style(self.colors,self.ctx)
        self.chart.set_series(dates,values,range_key='1y',message=('자료 조회 중…' if ko else 'Loading…') if self.jobs.busy
                              else ('새로고침을 눌러 이력을 조회하세요.' if ko else 'Refresh to load history.'))
        self.price.setText(self.ctx.number(values[-1],2)+' '+SERIES[self.symbol][3] if values else '—')
        self.status.setText((self.ctx.date(dates[-1])+' · '+known.source) if values else
                            ('이 공급자의 자료를 아직 받지 못했어요.' if ko else 'No observations from this provider yet.'))
        self.chart.setToolTip(self.status.text())

    def set_locale(self, ctx):
        self.ctx=ctx
        automatic=self.auto_load;self.auto_load=False
        try:self.select(self.category,self.symbol)
        finally:self.auto_load=automatic

    def set_theme(self, colors):
        from .typography import is_dark
        self.colors=colors;self.setStyleSheet(sheet(colors,is_dark(colors)));self.render()

    def stop(self):
        self.epoch+=1;self.pending=None


class MarketToolPage(QWidget):
    """Independent input/result state for a market asset's existing calculator."""
    def __init__(self, window, name, category):
        super().__init__()
        from .bonds import BondsPane
        from .rates import RatesPane
        from .fx import FXPane
        from .macro import MacroPane
        from .market_tools import DerivativesPane
        self.owner,self.name,self.category=window,name,category
        self.pane={'bonds':BondsPane,'rates':RatesPane,'fx':FXPane,'macro':MacroPane,'derivatives':DerivativesPane}[name]()
        if hasattr(self.pane,'hide_source'):self.pane.hide_source()
        self.jobs=Jobs(self);self.jobs.succeeded.connect(self._loaded);self.jobs.failed.connect(self._failed)
        self.pane.requested.connect(self.run)
        column=QVBoxLayout(self);column.setContentsMargins(0,0,0,0);column.setSpacing(14)
        self.title=label('name');column.addWidget(self.title)
        from .workspace_guide import WorkspaceGuide
        self.guide=WorkspaceGuide(name);column.addWidget(self.guide)
        column.addWidget(self.pane);column.addStretch()
        self.set_locale(window.ctx)
        self.set_theme(window.colors)

    def run(self, request):
        if self.jobs.busy:return
        self.pane.clear_result()
        self.pane.status.setText('조회·계산 중…' if self.owner.ctx.language=='ko' else 'Loading and calculating…')
        runner=getattr(self.owner,'bond_runner' if self.name=='bonds' else self.name+'_runner')
        self.jobs.start(lambda:runner(request))

    def _loaded(self,value):
        try:
            self.pane.show_result(value)
            if hasattr(self.pane,'bind_output'):self.pane.bind_output(self.name,value)
        except (ValueError,TypeError,KeyError,AttributeError):self._failed('display')

    def _failed(self,_code):
        self.pane.status.setText('조회·계산을 완료하지 못했어요. 입력과 연결을 확인하세요.' if self.owner.ctx.language=='ko'
                                else 'Could not finish. Check inputs and connection.')

    def select(self, sub):
        if sub and hasattr(self.pane,'select_tool'):self.pane.select_tool(sub)

    def set_locale(self,ctx):
        from .shell_rail import market_section_text
        self.title.setText(('시장 / ' if ctx.language=='ko' else 'Markets / ')+market_section_text(self.category,ctx.language))
        self.guide.set_key(self.name)

    def set_theme(self,colors):
        from .research_style import apply
        from .typography import is_dark
        apply(self,colors,is_dark(colors))
