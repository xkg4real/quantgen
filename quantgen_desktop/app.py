"""Native desktop research workspace. Run with python -m quantgen_desktop.

This first migration slice is deliberately opt-in. Existing Flet routes remain
available unchanged while their native equivalents are ported and verified.
"""
from __future__ import annotations

import logging
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QByteArray, QSettings
from PyQt6.QtGui import QFont, QFontDatabase, QFontMetrics, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QFileDialog,
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSpinBox, QStackedWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QTabWidget, QButtonGroup)

from core.app_paths import application_root
from core.research.analysis import AnalysisRequest, execute_analysis
from core.research.export import bundle_bytes, save_desktop_export
from core.research.watchlist import load_home_markets, default_home_rows
from core.research.provenance import code_evidence, runtime_evidence
from core.research.portfolio_analysis import execute_portfolio
from core.research.mc_disclosure import bootstrap_disclosure, volatility_disclosure
from core.research.bond_analysis import execute_bond
from core.research.rates_analysis import execute_rates
from core.research.fx_analysis import execute_fx
from core.research.structuring_analysis import execute_structuring
from core.research.signals_analysis import execute_signals
from core.research.macro_analysis import execute_macro
from core.research.market_analysis import execute_derivatives, execute_etf, execute_crypto, execute_krx
from core.research.connections import execute_connections
from core.research.strategy_analysis import execute_strategy
from core.research.runs import SessionResearch, new_run, failed, export_bytes
from core.theme import LIGHT, DARK
from core.i18n import LocaleContext
from tools.status.snapshot import verify
from .charts import FanChart, FrontierChart, LineChart, SignedBars
from .jobs import Jobs
from .localization import UiLabel, LanguageController, CAPTION_ROLE
from .translations import display
from .chart_study import CurrentPageTabs
from .macro_records import execute_macro_records
from . import typography

log = logging.getLogger(__name__)


# Analysis tools (owner, 2026-11-04): reached from their own page through a visible grid,
# not a scrolling tab strip on Markets. (attribute, button title) in display order.
TOOL_PANES = (('bonds', 'Bonds'), ('rates', 'Rates'), ('structuring', 'Structuring'), ('fx', 'FX'),
              ('derivatives', 'Derivatives'), ('etf', 'ETF'), ('krx', 'KRX'), ('crypto', 'Crypto'),
              ('macro', 'Macro sheet'), ('macro_records', 'Macro v2'))


def _production_card_router():
    """Watchlist cards: their own KIS service, KIS first and Yahoo for stocks when KIS cannot answer."""
    from core.market.routing import default_chart_router
    from data.kis_workspace import MarketDataService
    service = MarketDataService()
    return default_chart_router(lambda: service)


class _ProductionProfileLoader:
    """One stock's profile from existing allowlisted KIS calls; daily bars fall back to Yahoo for stocks."""

    def __init__(self):
        self._service = None
        self._lock = threading.Lock()

    def __call__(self, instrument):
        from core.market.routing import default_chart_router
        from core.research.stock_profile import load_profile
        from data.kis_workspace import MarketDataService
        with self._lock:
            if self._service is None:
                self._service = MarketDataService()
            service = self._service
        domestic = instrument.asset == "domestic_stock" and service.ready
        return load_profile(instrument, router=default_chart_router(lambda: service),
                            quote_client=service.client if domestic else None,
                            markets=service.markets if domestic else None)


def app_icon():
    """Multi-size icon for the window and the Windows taskbar (owner UI-17).

    The .ico carries 16-256 px images, so the taskbar gets a native size instead of
    falling back to the Python interpreter's icon; the PNGs cover other platforms.
    """
    icon = QIcon()
    assets = application_root() / "assets"
    for name in ("icon.ico", "icon_192.png", "icon_512.png", "icon.png"):
        if (assets / name).is_file():
            icon.addFile(str(assets / name))
    return icon


def label(text, role="", *, wrap=True):
    w = UiLabel(text)
    w.setTextFormat(Qt.TextFormat.PlainText)
    w.setWordWrap(wrap)
    w.setProperty("role", role)
    w.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return w


def load_interface_fonts(app):
    """Register bundled real weights; retain the platform font if unavailable.

    A missing or unreadable file is logged: the window then falls back to the
    platform font, which changes Hangul shapes and widths.
    """
    family = None
    for filename in ("qg-interface.otf", "qg-interface-medium.otf", "qg-interface-semibold.otf"):
        path = application_root() / "assets/fonts" / filename
        font_id = QFontDatabase.addApplicationFont(str(path))
        families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
        if not families:
            log.warning("QUANTGEN interface font did not load: %s", path)
        if families and family is None:
            family = families[0]
    if family is not None:
        font = QFont(family, 10)
        font.setWeight(QFont.Weight.Normal)
        # Keep changing prices aligned without giving Korean labels a monospace face.
        font.setFeature(QFont.Tag.fromString("tnum"), 1)
        app.setFont(font)
    else:
        log.warning("QUANTGEN interface font unavailable; using the platform font")
    return family


def panel(title):
    box = QFrame()
    box.setObjectName("panel")
    layout = QVBoxLayout(box)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(12)
    if title:
        layout.addWidget(label(title, "heading"))
    return box, layout


def table(headers):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    if len(headers) <= 7:
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    else:
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for column,header in enumerate(headers):t.setColumnWidth(column,max(100,min(220,12+len(header)*8)))
    t.verticalHeader().hide()
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    t.setAlternatingRowColors(True)
    return t


def table_rows(t, rows, ids=None):
    t.setRowCount(len(rows))
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            item = QTableWidgetItem(str(value))
            if j in (t.property('localized_columns') or ()):
                item.setData(CAPTION_ROLE, str(value))
            if ids:
                item.setData(Qt.ItemDataRole.UserRole, ids[i])
            t.setItem(i, j, item)
    t.resizeRowsToContents()


class ResearchWindow(QMainWindow):
    def __init__(self, *, session=None, market_loader=load_home_markets,
                 analysis_runner=execute_analysis, portfolio_runner=execute_portfolio, bond_runner=execute_bond,
                 rates_runner=execute_rates, fx_runner=execute_fx, structuring_runner=execute_structuring,
                 signals_runner=execute_signals, macro_runner=execute_macro,
                 derivatives_runner=execute_derivatives, etf_runner=execute_etf,
                 crypto_runner=execute_crypto, krx_runner=execute_krx,
                 connections_runner=execute_connections, strategy_runner=execute_strategy,
                 macro_records_runner=execute_macro_records, paper_factory=None, commentary_runner=None, auto_refresh=True, language="en", language_store=None, locale=None, theme_mode="light",
                 symbol_directory=None, watchlist_store=None, card_router_factory=None, profile_loader=None):
        super().__init__()
        self.ctx = LocaleContext(locale or ("ko_KR" if language == "ko" else "en_US"))
        self.auto_refresh = auto_refresh
        self.ui_language = self.ctx.language
        self.language_store = language_store
        self.session = session or SessionResearch()
        self.market_loader, self.analysis_runner = market_loader, analysis_runner
        self.portfolio_runner = portfolio_runner
        self.bond_runner = bond_runner
        self.rates_runner, self.fx_runner = rates_runner, fx_runner
        self.structuring_runner = structuring_runner
        self.signals_runner, self.macro_runner = signals_runner, macro_runner
        self.derivatives_runner, self.etf_runner = derivatives_runner, etf_runner
        self.crypto_runner, self.krx_runner = crypto_runner, krx_runner
        self.connections_runner = connections_runner
        self.strategy_runner = strategy_runner
        self.macro_records_runner = macro_records_runner
        self.commentary_runner = commentary_runner
        self.symbol_directory = symbol_directory
        self.watchlist_store = watchlist_store
        self.card_router_factory = card_router_factory
        self.profile_loader = profile_loader
        self.tool_names = ('rates','fx','structuring','signals','macro','derivatives','etf','crypto','krx','connections','strategy','macro_records')
        self.outputs = {}
        self.active_run = None
        self.pending = None
        self.colors = LIGHT
        from .paper import PaperSession, default_session
        self.paper_session = PaperSession(self, factory=paper_factory or default_session)
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self.job_succeeded)
        self.jobs.failed.connect(self.job_failed)
        self.jobs.busy_changed.connect(self.busy_changed)
        self.setWindowTitle("QUANTGEN — Research Desktop")
        self.setWindowIcon(app_icon())
        self.resize(1360, 940)
        self.setMinimumSize(1000, 700)
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        self.sidebar = sidebar
        # Owner 2026-11-04: a thinner rail, sized from its widest label (fit_sidebar).
        sidebar.setFixedWidth(typography.SIDEBAR_WIDTH_RANGE[1])
        rail = QVBoxLayout(sidebar)
        rail.setContentsMargins(*typography.RAIL_MARGINS)
        rail.setSpacing(typography.RAIL_SPACING)
        brand = QHBoxLayout()
        icon = QSvgWidget(str(application_root()/"assets/branding/f1-symbol.svg"))
        self.brand_symbol = icon
        self.brand_symbol_svg = (application_root()/"assets/branding/f1-symbol.svg").read_bytes()
        icon.setFixedSize(38, 38)
        brand.addWidget(icon)
        brand.addWidget(label("QUANTGEN", "brand", wrap=False))
        rail.addLayout(brand)
        rail.addSpacing(10)
        self.stack = QStackedWidget()
        self.nav = {}
        routes = (("home", "Research Home"), ("markets", "Markets"), ("tools", "Analysis tools"),
                  ("guide", "Indicator guide"),
                  ("quant", "Build & Test"), ("risk", "Portfolio & Risk"),
                  ("library", "Research Library"), ("system", "System"))
        self.route_indices = {route:i for i,(route,_) in enumerate(routes)}
        for route, title in routes:
            b = QPushButton(title.replace('&','&&'))
            b.setCheckable(True)
            b.setProperty("nav", True)
            b.clicked.connect(lambda checked=False, r=route:self.navigate(r))
            rail.addWidget(b)
            self.nav[route] = b
        rail.addStretch()
        self.paper_halt = QPushButton('모의 엔진 긴급 정지')
        self.paper_halt.setEnabled(False)
        self.paper_halt.clicked.connect(lambda: self.paper_session.runtime.halt() if self.paper_session.runtime else None)
        self.paper_session.changed.connect(lambda: self.paper_halt.setEnabled(self.paper_session.runtime is not None))
        rail.addWidget(self.paper_halt)
        self.theme = QComboBox()
        self.theme.addItems(["Light", "Dark"])
        self.theme.setAccessibleName("Theme")
        self.theme.setCurrentIndex(1 if theme_mode=="dark" else 0)
        self.theme.currentIndexChanged.connect(self.change_theme)
        rail.addWidget(self.theme)
        rail.addWidget(label("Language", "caption"))
        self.language = QComboBox()
        self.language.addItem("English", "en")
        self.language.addItem("한국어", "ko")
        self.language.setAccessibleName("Language")
        self.language.setCurrentIndex(self.language.findData(self.ui_language))
        self.language.currentIndexChanged.connect(lambda: self.set_language(self.language.currentData()))
        rail.addWidget(self.language)
        outer.addWidget(sidebar)
        outer.addWidget(self.stack, 1)
        self.make_home()
        self.make_markets()
        self.make_tools()
        self.make_indicator_guide()
        self.make_quant()
        self.make_risk()
        self.make_library()
        self.make_system()
        self.attach_symbol_searches()
        self.setup_live_watchlist()
        self.change_theme(self.theme.currentIndex())
        self.navigate("home")
        self.localizer = LanguageController(self)
        self.refresh_views()
        self.fit_sidebar()
        if auto_refresh:
            QTimer.singleShot(0, self.refresh_markets)

    def set_language(self, language):
        if language not in ("en", "ko"):
            raise ValueError("Unsupported UI language")
        value = "ko_KR" if language == "ko" else "en_US"
        index = self.locale_picker.findData(value)
        self.locale_picker.blockSignals(True)
        self.locale_picker.setCurrentIndex(index)
        self.locale_picker.blockSignals(False)
        self.change_language(index)

    def fit_sidebar(self):
        """Size the rail from its widest nav label in the current language.

        Measured at the checked nav font (14px / 600) plus the nav padding, the rail
        margins and a little air, never below what the paper-halt button and the
        theme/language selectors need, and clamped to SIDEBAR_WIDTH_RANGE.
        """
        left, _, right, _ = typography.RAIL_MARGINS
        frame = self.sidebar.frameWidth() + 1  # right-hand border
        low, high = typography.SIDEBAR_WIDTH_RANGE
        font = typography.scaled_font(next(iter(self.nav.values())).font(), 14, 600)
        metrics = QFontMetrics(font)
        widest = max(metrics.horizontalAdvance(button.text().replace("&&", "&")) for button in self.nav.values())
        needed = widest + 2 * typography.NAV_PADDING[1] + typography.NAV_SLACK
        for widget in (self.paper_halt, self.theme, self.language):
            needed = max(needed, widget.sizeHint().width())
        width = max(low, min(high, needed + left + right + frame))
        if self.sidebar.width() != width or self.sidebar.minimumWidth() != width:
            self.sidebar.setFixedWidth(width)
        return width

    def page(self, title, subtitle):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 28, 30, 28)
        layout.setSpacing(20)
        layout.addWidget(label(title, "title"))
        layout.addWidget(label(subtitle, "muted"))
        scroll.setWidget(content)
        self.stack.addWidget(scroll)
        return layout

    def make_home(self):
        layout = self.page("Research Home", "관측된 시장과 내가 실행한 연구를 한눈에 확인하세요.")
        from .watchlist import WatchlistPanel
        self.watchlist = WatchlistPanel(locale=self.ctx)
        self.watchlist.refresh_requested.connect(self.refresh_markets)
        self.watchlist.chart_requested.connect(self.open_stock_chart)
        self.home_markets = self.watchlist.table
        layout.addWidget(self.watchlist)
        summary = QHBoxLayout()
        self.count_labels = []
        for title in ("완료한 분석", "진행 중", "확인할 실행"):
            box, inner = panel(title)
            number = label("0", "number")
            inner.addWidget(number)
            inner.addWidget(label("이번 세션의 Monte Carlo · 투자 판정과 별개", "caption"))
            summary.addWidget(box)
            self.count_labels.append(number)
        layout.addLayout(summary)
        rights_button=QPushButton(self.ctx.t('data_rights'))
        rights_button.clicked.connect(self.open_data_rights)
        layout.addWidget(rights_button)
        box, inner = panel("가능성을 하나의 숫자로 좁히지 마세요")
        self.home_chart = FanChart()
        self.home_summary = label("분석을 실행하면 최신 결과와 데이터 근거가 연결됩니다.")
        from .chart_study import ChartStudy
        inner.addWidget(ChartStudy(self.home_chart,self.home_summary))
        b = QPushButton("Quant Lab에서 연구 시작 →")
        b.clicked.connect(lambda:self.navigate("quant"))
        inner.addWidget(b)
        inner.addWidget(label("P5–P95는 시뮬레이션 분포의 중앙 90% 구간입니다. 수익 보장이나 95% 신뢰구간이 아닙니다.", "caption"))
        layout.addWidget(box)
        layout.addStretch()

    def make_indicator_guide(self):
        from .indicator_guide import IndicatorGuide
        layout = self.page("Technical indicator guide", self.ctx.t('search_intro'))
        self.guide_subtitle = layout.itemAt(1).widget()
        self.indicator_guide = IndicatorGuide(locale=self.ctx)
        self.indicator_guide.intro.hide()
        layout.addWidget(self.indicator_guide)
        layout.addStretch()

    def make_markets(self):
        from .market_chart import MarketChartPane
        from .markets_view import DirectoryLoader, MarketsWorkspace, WatchlistStore
        from core.market.directory import default_directory
        layout = self.page("Markets", "관심종목 차트와 종목 한 화면 보기")
        self.market_subtitle = layout.itemAt(1).widget()
        self.market_subtitle.localized_text = {
            "ko": "관심종목 차트를 한눈에 보고, 종목 코드나 이름으로 검색해 그 종목의 모든 것을 한 화면에서 확인합니다.",
            "en": "Your watchlist charts at a glance; search a stock by code or name to see everything about it on one screen."}
        self.market_subtitle.retranslate()
        # Owner, 2026-11-04: no indicator board (UI-7) and no asset-class tab strip (UI-8) here.
        self.market_chart = MarketChartPane(locale=self.ctx)
        self.market_chart.setObjectName('marketChart')
        if self.symbol_directory is None:
            self.symbol_directory = default_directory()
        self.directory_loader = DirectoryLoader(self.symbol_directory, enabled=self.auto_refresh)
        if self.watchlist_store is None:
            self.watchlist_store = WatchlistStore(self.language_store)
        self.markets_view = MarketsWorkspace(
            self.market_chart, store=self.watchlist_store, directory=self.symbol_directory,
            directory_loader=self.directory_loader,
            card_router_factory=self.card_router_factory or _production_card_router,
            profile_loader=self.profile_loader or _ProductionProfileLoader(),
            locale=self.ctx, auto_load=self.auto_refresh)
        layout.addWidget(self.markets_view)
        layout.addStretch()

    def make_tools(self):
        """Analysis tools on their own page: a visible button grid, no scrolling tabs (owner, 2026-11-04)."""
        from .bonds import BondsPane
        from .rates import RatesPane
        from .fx import FXPane
        from .structuring import StructuringPane
        from .macro import MacroPane
        from .macro_records import MacroRecordsPane
        from .market_tools import DerivativesPane, ETFPane, CryptoPane, KRXPane
        from .tools import CurrentPageStack
        layout = self.page("Analysis tools", "채권·금리·외환·파생·ETF·KRX·가상자산·매크로 분석 도구")
        self.tools_subtitle = layout.itemAt(1).widget()
        self.tools_subtitle.localized_text = {
            "ko": "채권·금리·외환·파생·ETF·KRX·가상자산·매크로 분석 도구입니다. 아래에서 하나를 고르세요.",
            "en": "Bonds, rates, FX, derivatives, ETF, KRX, crypto and macro tools. Pick one below."}
        self.tools_subtitle.retranslate()
        self.bonds=BondsPane();self.bonds.requested.connect(self.run_bond)
        self.rates=RatesPane(); self.rates.requested.connect(lambda q:self.run_tool('rates',q))
        self.fx=FXPane(); self.fx.requested.connect(lambda q:self.run_tool('fx',q))
        self.structuring=StructuringPane(); self.structuring.requested.connect(lambda q:self.run_tool('structuring',q))
        self.macro=MacroPane(); self.macro.requested.connect(lambda q:self.run_tool('macro',q))
        self.macro_records = MacroRecordsPane()
        self.macro_records.requested.connect(lambda q:self.run_tool('macro_records',q))
        for name, pane_type in (('derivatives', DerivativesPane), ('etf', ETFPane), ('crypto', CryptoPane), ('krx', KRXPane)):
            pane = pane_type()
            pane.requested.connect(lambda q, n=name:self.run_tool(n,q))
            setattr(self, name, pane)
        for pane in (self.rates,self.fx,self.structuring,self.macro,self.derivatives,self.etf,self.crypto,self.krx):
            pane.hide_source()
        self.macro_records.set_source_caption('Record set')
        picker = QWidget()
        picker.setObjectName('toolPicker')
        grid = QGridLayout(picker)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)
        self.tool_group = QButtonGroup(self)
        self.tool_group.setExclusive(True)
        self.tool_host = CurrentPageStack()
        self.tool_host.setObjectName('toolHost')
        self.tool_buttons = {}
        columns = 5
        for index, (name, title) in enumerate(TOOL_PANES):
            pane = getattr(self, name)
            button = QPushButton(title)
            button.setCheckable(True)
            button.setProperty('tool', True)
            button.setAccessibleName(title)
            button.clicked.connect(lambda checked=False, p=pane: self.show_tool(p))
            self.tool_group.addButton(button)
            grid.addWidget(button, index // columns, index % columns)
            self.tool_buttons[name] = button
            self.tool_host.addWidget(pane)
        for column in range(columns):
            grid.setColumnStretch(column, 1)
        self.tool_buttons[TOOL_PANES[0][0]].setChecked(True)
        layout.addWidget(picker)
        layout.addWidget(self.tool_host)
        layout.addStretch()

    def attach_symbol_searches(self):
        """Code-or-name search on every symbol field that loads a chart or one instrument's data
        (owner, 2026-11-04). Choosing a row writes the code, so each pane's own routing is unchanged."""
        from .markets_view import STOCK_ASSETS, US_EXCHANGES, attach_symbol_search
        directory, loader = self.symbol_directory, self.directory_loader
        targets = [(self.symbol, {}), (self.portfolio.symbols, {"multi": True})]
        for pane, field, options in ((self.signals, "symbol", {}), (self.strategy, "symbols", {"multi": True}),
                                     (self.etf, "code", {"assets": ("domestic_stock",), "kinds": ("etf",)}),
                                     (self.krx, "code", {"assets": ("domestic_stock",)})):
            for controls in pane.fields.values():
                if isinstance(controls.get(field), QLineEdit):
                    targets.append((controls[field], options))
        self.symbol_completers = [self.markets_view.completer]
        for edit, options in targets:
            # Writing a code drops the exchange, so only listings whose bare code loads the same security.
            options = {"assets": STOCK_ASSETS, "exchanges": US_EXCHANGES, **options}
            self.symbol_completers.append(attach_symbol_search(edit, directory, locale=self.ctx, loader=loader,
                                                               **options))

    def show_tool(self, pane):
        """Show one analysis tool on the tools page (does not navigate)."""
        for index in range(self.tool_host.count()):
            if self.tool_host.widget(index) is pane:
                self.tool_host.setCurrentIndex(index)
                for name, button in self.tool_buttons.items():
                    button.setChecked(getattr(self, name) is pane)
                return pane
        raise ValueError('Pane is not one of the analysis tools')

    def show_market_pane(self, pane):
        """Kept for callers of the former Markets tabs: the chart opens Markets, a tool opens its page."""
        if pane is self.market_chart:
            self.navigate('markets')
            if not self.markets_view.showing_stock():
                self.markets_view.stock.adopt_chart()
                self.markets_view.pages.setCurrentIndex(1)
            return pane
        self.show_tool(pane)
        self.navigate('tools')
        return pane

    def current_market_pane(self):
        if self.stack.currentIndex() == self.route_indices['tools']:
            return self.tool_host.currentWidget()
        return self.market_chart if self.markets_view.showing_stock() else self.markets_view.grid

    def make_quant(self):
        outer = self.page("Build & Test", "Quant Lab · 기존 계산 엔진으로 가격 분포 분석")
        self.quant_tabs = QTabWidget()
        outer.addWidget(self.quant_tabs)
        host = QWidget()
        layout = QVBoxLayout(host)
        self.quant_tabs.addTab(host, 'Monte Carlo')
        from .strategy import StrategyPane
        self.strategy = StrategyPane()
        self.strategy.requested.connect(lambda q: self.run_tool('strategy', q))
        self.quant_tabs.addTab(self.strategy, 'Strategy Lab')
        box, inner = panel("분석 설정")
        form = QGridLayout()
        self.symbol = QLineEdit("AAPL")
        self.symbol.setMaxLength(120)
        self.source = QComboBox()
        for text, value in [("Auto · KIS / FMP", "auto"), ("FMP", "fmp"), ("KIS · KRX", "kis"), ("Synthetic demo", "synthetic")]:
            self.source.addItem(text, value)
        self.model = QComboBox()
        for text, value in [("GARCH(1,1)-t", "garch_t"), ("GBM", "gbm"), ("Jump diffusion", "jump"), ("Block bootstrap", "bootstrap")]:
            self.model.addItem(text, value)
        self.drift = QComboBox()
        for text, value in [("Risk premium · rf + ERP", "premium"), ("Zero · stress", "zero"), ("Risk-neutral · rf", "rf"), ("Sample mean · noisy", "sample")]:
            self.drift.addItem(text, value)
        self.horizon = QSpinBox(); self.horizon.setRange(5, 1260); self.horizon.setValue(126)
        self.paths = QSpinBox(); self.paths.setRange(200, 100000); self.paths.setValue(5000); self.paths.setSingleStep(500)
        self.seed = QSpinBox(); self.seed.setRange(0, 2147483647); self.seed.setValue(7)
        self.erp = QDoubleSpinBox(); self.erp.setRange(-100, 100); self.erp.setDecimals(2); self.erp.setValue(4)
        self.target = QLineEdit(); self.target.setPlaceholderText("선택 입력")
        fields = (("Symbol", self.symbol), ("Data source", self.source), ("Model", self.model),
                  ("Drift", self.drift), ("Horizon · sessions", self.horizon), ("Paths", self.paths),
                  ("Seed", self.seed), ("ERP · %", self.erp), ("Target price", self.target))
        for i, (name, widget) in enumerate(fields):
            col, row = i%3, (i//3)*2
            widget.setAccessibleName(name)
            form.addWidget(label(name, "caption"), row, col)
            form.addWidget(widget, row+1, col)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)
        inner.addLayout(form)
        self.run_button = QPushButton("분포 분석 실행")
        self.run_button.setProperty("primary", True)
        self.run_button.clicked.connect(self.run_analysis)
        inner.addWidget(self.run_button)
        self.analysis_status = label("데이터 출처·시드·모델 가정을 기록합니다.", "muted")
        inner.addWidget(self.analysis_status)
        layout.addWidget(box)
        box, inner = panel("분포와 근거")
        self.quant_chart = FanChart()
        self.quant_metrics = table(["지표", "값"])
        self.quant_metrics.setProperty("localized_columns", [0])
        self.quant_metrics.setMinimumHeight(280)
        inner.addWidget(self.quant_metrics)
        self.quant_notes = label("아직 실행한 분석이 없습니다.", "muted")
        from .chart_study import ChartStudy
        inner.insertWidget(0, ChartStudy(self.quant_chart,self.quant_notes))
        inner.addWidget(label("계산 완료 ≠ 투자 검증. 이 화면은 NOT_RUN 판정을 유지하며 주문이나 전략 원장을 생성하지 않습니다.", "caption"))
        layout.addWidget(box)
        layout.addStretch()

    def make_risk(self):
        from .portfolio import PortfolioPane
        from .signals import SignalsPane
        layout = self.page("Portfolio & Risk", "현재 세션 분석의 분포 위험을 확인하세요.")
        self.portfolio = PortfolioPane()
        self.portfolio.requested.connect(self.run_portfolio)
        self.signals=SignalsPane();self.signals.requested.connect(lambda q:self.run_tool('signals',q))
        self.risk_tabs=CurrentPageTabs();self.risk_tabs.addTab(self.portfolio,'Portfolio');self.risk_tabs.addTab(self.signals,'Signals')
        from .paper import PaperPane
        self.paper = PaperPane(self.paper_session)
        self.risk_tabs.addTab(self.paper, 'Paper Trading')
        layout.addWidget(self.risk_tabs)
        layout.addWidget(label("개별 가격 시뮬레이션 위험", "heading"))
        self.risk_table = table(["Symbol", "Model", "P(loss)", "VaR 95", "CVaR", "Source"])
        self.risk_table.setMinimumHeight(300)
        layout.addWidget(self.risk_table)
        layout.addWidget(label("각 행은 개별 가격 시뮬레이션입니다. 포트폴리오 전체 위험이나 전략 백테스트가 아닙니다.", "muted"))
        layout.addStretch()

    def make_library(self):
        layout = self.page("Research Library", "이번 앱 세션의 실행 근거 · 종료 전에 필요한 결과를 저장하세요.")
        self.run_table = table(["Symbol", "Model", "실행 상태", "검증 판정", "생성 시각 · UTC"])
        self.run_table.setMinimumHeight(280)
        layout.addWidget(self.run_table)
        buttons = QHBoxLayout()
        self.save_json = QPushButton("선택한 ResearchRun JSON 저장")
        self.save_bundle = QPushButton("선택한 보고서 + JSON ZIP 저장")
        self.save_json.clicked.connect(lambda:self.export_selected(False))
        self.save_bundle.clicked.connect(lambda:self.export_selected(True))
        buttons.addWidget(self.save_json); buttons.addWidget(self.save_bundle)
        layout.addLayout(buttons)
        self.export_status = label("현재 저장 대상은 Monte Carlo 실행입니다. 자동 저장되지 않으며 경로는 직접 선택합니다.", "muted")
        layout.addWidget(self.export_status)
        layout.addWidget(label("재현성 PARTIAL · 데이터 빈티지/라이선스 미검증 · 비용 NOT_APPLIED · 검증 NOT_RUN\n동결 연구·과거 원장·비밀 설정을 탐색하지 않습니다.", "caption"))
        from .commentary import CommentaryPane
        options = {'runner': self.commentary_runner} if self.commentary_runner else {}
        self.commentary = CommentaryPane(self.commentary_sources, **options)
        layout.addWidget(self.commentary)
        layout.addStretch()

    def commentary_sources(self):
        """Only explicit calculation results, never stores/settings/owner records."""
        result=[]
        for run in self.session.runs():
            if run['execution_status'] != 'COMPLETED': continue
            result.append(('Monte Carlo · '+str(run['parameters'].get('symbol','')), {
                'tool':'monte_carlo','execution_status':'COMPLETED','verdict':run['verdict'],
                'reproducibility':run['reproducibility'],'parameters':run['parameters'],
                'sections':[{'type':'metrics','data':run['metrics']},{'type':'data','data':run['data']}]}))
        for name in ('portfolio','bonds'):
            report=getattr(self,name).exports.report
            if report:result.append((name,report))
        for name in self.tool_names:
            if name in {'connections','macro_records'}: continue
            report=getattr(self,name).report
            if report and report.get('parameters',{}).get('tool')!='cards':result.append((name,report))
        return result

    def make_system(self):
        layout = self.page("System", "기록된 근거와 이번 실행 결과를 구분합니다.")
        from .localization import locale_picker
        box,inner=panel(self.ctx.t('language'))
        self.locale_picker=locale_picker(self.ctx)
        self.locale_picker.setAccessibleName(self.ctx.t('language'))
        self.locale_picker.currentIndexChanged.connect(self.change_language)
        inner.addWidget(self.locale_picker)
        self.locale_notice=label(self.ctx.t('language_fallback' if self.ctx.is_fallback else 'language_coverage'),'caption')
        inner.addWidget(self.locale_notice)
        layout.addWidget(box)
        from .connections import ConnectionsPane
        self.connections = ConnectionsPane()
        self.connections.requested.connect(lambda q: self.run_tool('connections', q))
        from .paper import RulesPane
        self.rules = RulesPane(self.paper_session)
        self.system_tabs = QTabWidget()
        self.system_tabs.addTab(self.connections, 'Connections')
        self.system_tabs.addTab(self.rules, 'Rules')
        from .data_rights import DataRightsPane
        self.data_rights=DataRightsPane(self.ctx)
        self.system_tabs.addTab(self.data_rights,self.ctx.t('data_rights'))
        layout.addWidget(self.system_tabs)
        box, inner = panel("프로젝트 상태")
        try:
            status = verify(application_root())
            counts = status["code_test"]["counts"]
            calendar = status["data_readiness"]["calendar"]
            text = (f"기록된 검사: {counts['PASS']} PASS / {counts['FAIL']} FAIL / {counts['NOT_RUN']} NOT_RUN\n"
                    f"달력: {calendar['files']}개 서명 메타데이터 · 세트 {calendar['version']}\n"
                    "위 수치는 이번에 실행한 검사 결과가 아닙니다. 파일별 서명 검증은 별도입니다.")
        except (OSError, ValueError, KeyError, TypeError):
            text = "기록된 상태를 검증할 수 없습니다. 출처 자료를 확인하세요."
        inner.addWidget(label(text))
        inner.addWidget(label("데이터 NOT_VERIFIED · 공식 게이트 NOT_FROZEN (문서 기록)\n동결 연구 NOT_INSPECTED · 공개 배포 NOT_APPROVED", "muted"))
        layout.addWidget(box)
        box, inner = panel("데스크톱 이전 상태")
        inner.addWidget(label("PyQt6 네이티브: Home, Markets(관심종목 차트·종목 한 화면), 분석 도구(Bonds, Rates, FX, Structuring, Macro sheet, Macro v2, Derivatives, ETF, Crypto, KRX), 기술지표 가이드, Monte Carlo, Strategy Lab, 포트폴리오, Signals, Library·저장, 연결 설정, System\n모의매매·규칙·선택 AI 해설 연결 완료 / 남은 검증: 실제 Windows 표시·DPI·설치\n브라우저: 기존 Flet 앱을 유지합니다."))
        inner.addWidget(label("이번 데스크톱은 선택 실행하는 미리보기입니다. 전체 기능 이전 완료본이 아닙니다.", "muted"))
        layout.addWidget(box)
        layout.addStretch()

    def navigate(self, route):
        if route != 'home' and hasattr(self, 'home_feed') and self.home_feed.active:
            self.home_feed.stop()
        self.stack.setCurrentIndex(self.route_indices[route])
        for name, button in self.nav.items(): button.setChecked(name == route)

    def setup_live_watchlist(self):
        from .watchlist_live import WatchlistLiveController
        from .qscore import QScoreController
        self._live_quotes = {}
        self._dirty_quotes = set()
        self._failed_scores = {}
        self.quote_paint_timer = QTimer(self)
        self.quote_paint_timer.setInterval(200)
        self.quote_paint_timer.timeout.connect(self.flush_market_quotes)
        self.quote_paint_timer.start()
        self.home_feed = WatchlistLiveController(self)
        self.q_scores = QScoreController(self)
        self.chart_scores = QScoreController(self)
        self.watchlist.live_requested.connect(self.start_watchlist_live)
        self.watchlist.stop_requested.connect(self.home_feed.stop)
        self.home_feed.history_ready.connect(self.q_scores.set_history)
        self.home_feed.history_failed.connect(self.home_history_failed)
        self.home_feed.tick_received.connect(self.accept_market_tick)
        self.home_feed.state_changed.connect(self.home_feed_changed)
        self.q_scores.score_changed.connect(self.show_q_score)
        self.chart_scores.score_changed.connect(self.show_q_score)
        self.market_chart.snapshot_loaded.connect(self.chart_history_loaded)
        self.market_chart.trade_received.connect(self.accept_chart_tick)
        self.market_chart.feed_state_changed.connect(self.chart_feed_changed)

    def start_watchlist_live(self):
        self.market_chart.stop()
        self.q_scores.stop()
        self.home_feed.start()

    def home_feed_changed(self, state):
        self.watchlist.set_live_state(state)
        self.q_scores.set_feed_state(state)
        if state in ('stopped', 'stale', 'error'):
            for quote in self._live_quotes.values():
                quote['status'] = 'STALE'

    def chart_feed_changed(self, state):
        self.chart_scores.set_feed_state(state)
        if state in ('stopped', 'stale', 'error'):
            for quote in self._live_quotes.values():
                quote['status'] = 'STALE'
            for symbol, quote in self._live_quotes.items():
                self.watchlist.update_quote(symbol, **quote)

    def chart_history_loaded(self, snapshot):
        if snapshot.request.instrument.asset == 'domestic_stock':
            self.chart_scores.request_history(snapshot.request.instrument)
            score = self.all_q_scores().get(snapshot.request.instrument.code)
            if score:
                self.market_chart.set_q_score(snapshot.request.instrument.code, score)

    def home_history_failed(self, symbol, code):
        from core.research.qscore import compute_q_score
        score = compute_q_score(None, symbol=symbol)
        score['reason'] = 'history_unavailable'
        self._failed_scores[symbol] = score
        self.show_q_score(symbol, score)

    def all_q_scores(self):
        scores = self.q_scores.scores()
        for symbol, score in self.chart_scores.scores().items():
            if score.get('computed_at', '') >= scores.get(symbol, {}).get('computed_at', ''):
                scores[symbol] = score
        for symbol, score in self._failed_scores.items():
            if score.get('computed_at', '') >= scores.get(symbol, {}).get('computed_at', ''):
                scores[symbol] = score
        return scores

    def accept_market_tick(self, tick):
        self.show_market_tick(tick)
        self.q_scores.accept_tick(tick)

    def accept_chart_tick(self, tick):
        self.show_market_tick(tick)
        self.chart_scores.accept_tick(tick)

    def show_market_tick(self, tick):
        if tick.instrument.asset != 'domestic_stock':
            return
        try:
            observed = datetime.fromisoformat(tick.timestamp.replace('Z', '+00:00'))
            received = datetime.fromisoformat(tick.received_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            fresh = all(stamp.tzinfo is not None and -5 <= (now-stamp).total_seconds() <= 60
                        for stamp in (observed, received))
        except (TypeError, ValueError):
            fresh = False
        quote = dict(price=tick.price, change_pct=tick.change_pct,
                     received_at=tick.received_at, market_time=tick.timestamp,
                     status='STREAMING' if fresh else 'STALE', source=tick.source,
                     volume=tick.cumulative_volume, absolute_change=tick.change)
        self._live_quotes[tick.instrument.code] = quote
        self._dirty_quotes.add(tick.instrument.code)

    def flush_market_quotes(self):
        now = datetime.now(timezone.utc)
        for symbol, quote in self._live_quotes.items():
            if quote['status'] == 'STREAMING':
                try:
                    age = (now - datetime.fromisoformat(quote['received_at'])).total_seconds()
                except (TypeError, ValueError):
                    age = 61
                if age > 15:
                    quote['status'] = 'STALE'
                    self._dirty_quotes.add(symbol)
        for symbol in tuple(self._dirty_quotes):
            self.watchlist.update_quote(symbol, **self._live_quotes[symbol])
        self._dirty_quotes.clear()

    def show_q_score(self, symbol, score):
        if score.get('status') == 'ready':
            self._failed_scores.pop(symbol, None)
        self.watchlist.update_score(symbol, score)
        self.market_chart.set_q_score(symbol, score)

    def open_data_rights(self):
        self.navigate('system')
        self.system_tabs.setCurrentWidget(self.data_rights)

    def open_live_chart(self):
        self.navigate('markets')
        scroll = self.stack.widget(self.route_indices['markets'])
        if self.markets_view.showing_stock():
            def reveal():
                if self.stack.currentWidget() is scroll:
                    top = self.market_chart.mapTo(scroll.widget(), self.market_chart.rect().topLeft()).y()
                    scroll.verticalScrollBar().setValue(max(0, top - 120))
            QTimer.singleShot(0, reveal)
        else:
            self.markets_view.search.setFocus(Qt.FocusReason.OtherFocusReason)

    def open_stock_chart(self, symbol):
        """A Home row opens that stock's screen on Markets (it loads when automatic refresh is on)."""
        from core.market.models import Instrument
        self.navigate('markets')
        self.markets_view.open_instrument(Instrument('domestic_stock', symbol))
        scroll = self.stack.widget(self.route_indices['markets'])
        QTimer.singleShot(0, lambda: scroll.verticalScrollBar().setValue(0))

    def change_language(self,index):
        value=self.locale_picker.itemData(index)
        if not value:return
        self.ctx=LocaleContext(value)
        self.ui_language=self.ctx.language
        self.language.blockSignals(True)
        self.language.setCurrentIndex(self.language.findData(self.ui_language))
        self.language.blockSignals(False)
        self.data_rights.set_locale(self.ctx)
        self.indicator_guide.set_locale(self.ctx)
        self.guide_subtitle.setText(self.ctx.t('search_intro'))
        self.watchlist.set_locale(self.ctx)
        self.market_chart.set_locale(self.ctx)
        self.markets_view.set_locale(self.ctx)
        for completer in self.symbol_completers:
            completer.set_locale(self.ctx)
        self.locale_notice.setText(self.ctx.t('language_fallback' if self.ctx.is_fallback else 'language_coverage'))
        from .indicator_guide import IndicatorGuide
        for pane in self.findChildren(IndicatorGuide):
            if pane is not self.indicator_guide:pane.set_locale(self.ctx)
        self.refresh_views()
        if self.language_store is not None:
            self.language_store.setValue("ui/language", self.ui_language)
            self.language_store.setValue("ui/locale", str(self.ctx.locale))
        self.localizer.apply()
        self.fit_sidebar()

    @pyqtSlot()
    def refresh_markets(self):
        if self.jobs.busy or not self.session.start_market_refresh():
            return
        self.pending = "markets"
        self.jobs.start(self.market_loader)

    @pyqtSlot()
    def run_analysis(self):
        if self.jobs.busy or self.paper_session.jobs.busy:
            return
        try:
            request = AnalysisRequest(symbol=self.symbol.text(), source_requested=self.source.currentData(),
                model=self.model.currentData(), drift=self.drift.currentData(), horizon_days=self.horizon.value(),
                n_paths=self.paths.value(), seed=self.seed.value(), erp=self.erp.value()/100,
                target=float(self.target.text()) if self.target.text().strip() else None)
            parameters = request.parameters()
        except (ValueError, TypeError):
            self.analysis_status.setText("입력을 확인하세요. Symbol과 유한한 양수 Target이 필요합니다.")
            return
        self.active_run = new_run(parameters, code=code_evidence(), environment=runtime_evidence())
        run = self.active_run
        self.session.put(run)
        self.pending = "analysis"
        self.analysis_status.setText("분석 중… 화면을 이동해도 계산은 계속됩니다.")
        self.refresh_views()
        self.jobs.start(lambda:self.analysis_runner(request, run))

    @pyqtSlot(object)
    def job_succeeded(self, value):
        if self.pending == "markets":
            self.session.finish_market_refresh(value)
        elif self.pending == "portfolio":
            self.portfolio.show_result(value)
        elif self.pending == "bonds":
            self.bonds.show_result(value)
        elif self.pending in self.tool_names:
            pane = getattr(self,self.pending)
            try:
                pane.show_result(value)
                pane.bind_output(self.pending, value)
            except Exception as exc:
                pane.clear_result()
                pane.status.setText(f'FAILED · 표시 자료 검증 오류 · {type(exc).__name__}')
        else:
            self.session.put(value.run)
            self.outputs[value.run["run_id"]] = value
            self.quant_chart.set_result(value.result)
            r, h = value.result, value.history
            vol_info = volatility_disclosure(r)
            table_rows(self.quant_metrics, [("Spot", f"{r.spot:,.2f}"), ("P5 / P50 / P95", f"{r.p05:,.2f} / {r.median_terminal:,.2f} / {r.p95:,.2f}"),
                (vol_info["label"], f"{vol_info['value']:.1%}"),
                ("P(loss)", f"{r.prob_loss:.1%}"), ("VaR 95 / CVaR", f"{r.var_pct:.1%} / {r.cvar_pct:.1%}"),
                ("Paths / horizon / seed", f"{r.n_paths:,} / {r.horizon_days} / {value.run['parameters']['seed']}"),
                ("P(terminal ≥ target)", "—" if r.prob_target is None else f"{r.prob_target:.1%}")] +
                ([("Horizon-average vol (ann.)", f"{r.garch_horizon_vol:.1%}")] if r.garch is not None else []))
            notes = [f"{'합성 데이터 · ' if h.source=='SYNTHETIC' else ''}{h.source} · {h.first_date} → {h.last_date}",
                     h.note, value.funding_note, r.drift_note, r.bound_note, r.jump_note]
            resampling = bootstrap_disclosure(r.model)   # None for every model but bootstrap
            if resampling is not None:
                notes.append(resampling["description"])
            notes.append(vol_info["description"])
            if vol_info["horizon_basis"]:
                notes.append("Horizon-average volatility: " + vol_info["horizon_basis"])
            if r.prob_target is not None:
                notes.append(f"Target probability: final price >= {r.target:,.2f} after {r.horizon_days} sessions. Only the final session is used.")
            if r.garch is not None:
                fit = r.garch
                notes.append(f"GARCH fit: alpha={fit.alpha:.4f}, beta={fit.beta:.4f}, nu={fit.nu:.3f}")
                notes.append(f"converged={fit.converged} · persistence={fit.persistence:.4f} · half-life={fit.half_life:.2f} sessions")
                for field in ("at_bound", "note", "se_note", "interval_at_bound"):
                    info = getattr(fit, field)
                    if info: notes.append(f"{field}: {info}")
                for field in ("alpha", "beta", "persistence"):
                    interval = fit.interval(field)
                    if interval: notes.append(f"{field} 95% Wald interval: {interval}")
                if fit.eta_interval: notes.append(f"eta 95% profile interval: {fit.eta_interval}")
            self.quant_notes.setText("\n".join(str(n) for n in notes if n))
            self.analysis_status.setText("COMPLETED · 검증 NOT_RUN · 재현성 PARTIAL")
        self.refresh_views()

    @pyqtSlot(str)
    def job_failed(self, code):
        if self.pending == "markets":
            self.session.finish_market_refresh([])
            self.statusBar().showMessage(f"시장 조회 실패: {code}")
        elif self.pending == "portfolio":
            self.portfolio.status.setText(f"FAILED · {code} · 입력/데이터를 확인하세요.")
        elif self.pending == "bonds":
            self.bonds.status.setText(f"FAILED · {code} · Price/Yield와 곡선 출처를 확인하세요.")
        elif self.pending in self.tool_names:
            getattr(self,self.pending).status.setText(f"FAILED · {code} · 입력·곡선 범위·데이터 출처를 확인하세요.")
        else:
            self.session.put(failed(self.active_run, code))
            self.analysis_status.setText(f"FAILED · {code} · 입력 또는 데이터 연결을 확인하세요.")
        self.refresh_views()

    @pyqtSlot(bool)
    def busy_changed(self, busy):
        self.run_button.setEnabled(not busy)
        self.watchlist.set_busy(busy)
        self.portfolio.run.setEnabled(not busy)
        self.bonds.run.setEnabled(not busy)
        for name in self.tool_names:getattr(self,name).input_box.setEnabled(not busy)
        if not busy:
            self.pending = None
            self.active_run = None

    @pyqtSlot(object)
    def run_portfolio(self, request):
        if self.jobs.busy: return
        self.portfolio.clear_result()
        self.pending = "portfolio"
        self.portfolio.status.setText("최적화 중… 화면을 이동해도 계속됩니다.")
        self.jobs.start(lambda:self.portfolio_runner(request))

    @pyqtSlot(object)
    def run_bond(self, request):
        if self.jobs.busy:return
        self.bonds.clear_result()
        self.pending='bonds'
        self.bonds.status.setText('채권 계산 중…')
        self.jobs.start(lambda:self.bond_runner(request))

    def run_tool(self, tool, request):
        if self.jobs.busy:return
        self.pending=tool
        pane=getattr(self,tool)
        pane.clear_result()
        pane.status.setText('계산 중… 화면을 이동해도 계속됩니다.')
        runner=getattr(self,tool+'_runner')
        self.jobs.start(lambda:runner(request))

    def refresh_views(self):
        runs = self.session.runs()
        for w, state in zip(self.count_labels, ("COMPLETED", "RUNNING", "FAILED")):
            w.setText(str(sum(r["execution_status"] == state for r in runs)))
        markets = self.session.markets()
        if not markets:
            markets=default_home_rows(status='UNAVAILABLE' if self.session.market_attempted and not self.session.market_loading else 'NOT_LOADED')
        self.watchlist.set_rows(markets)
        for symbol, quote in self._live_quotes.items():
            self.watchlist.update_quote(symbol, **quote)
        for symbol, score in self.all_q_scores().items():
            self.watchlist.update_score(symbol, score)
        table_rows(self.run_table, [[r["parameters"].get("symbol", "—"), r["parameters"].get("model", "—"),
            r["execution_status"], r["verdict"], self.ctx.timestamp(r["created_at"])] for r in runs], [r["run_id"] for r in runs])
        complete = [r for r in runs if r["execution_status"] == "COMPLETED"]
        table_rows(self.risk_table, [[r["parameters"]["symbol"], r["parameters"]["model"],
            f"{r['metrics']['prob_loss']:.1%}", f"{r['metrics']['var_pct']:.1%}", f"{r['metrics']['cvar_pct']:.1%}",
            r["data"]["source"]] for r in complete])
        if complete:
            r = complete[0]
            if r["run_id"] in self.outputs: self.home_chart.set_result(self.outputs[r["run_id"]].result)
            self.home_summary.setText(f"{r['parameters']['symbol']} · {r['parameters']['model']} · {r['data']['source']}\n"
                f"P5 {r['metrics']['p05']:,.2f} / P50 {r['metrics']['p50']:,.2f} / P95 {r['metrics']['p95']:,.2f}\n"
                f"관측 {r['data']['last_observation']} · 판정 {r['verdict']} · 재현성 {r['reproducibility']}")
        self.localizer.apply()

    def export_selected(self, bundle):
        row = self.run_table.currentRow()
        if row < 0:
            self.export_status.setText("먼저 저장할 실행을 선택하세요.")
            return
        run_id = self.run_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        run = next(r for r in self.session.runs() if r["run_id"] == run_id)
        if run["execution_status"] == "RUNNING":
            self.export_status.setText("실행이 끝난 뒤 저장하세요.")
            return
        extension = "zip" if bundle else "json"
        filename, _ = QFileDialog.getSaveFileName(self, display(self, "ResearchRun 저장"), f"quantgen-{run_id}.{extension}",
                                                 f"Research report (*.{extension})")
        if not filename:
            return
        try:
            data = bundle_bytes(run,locale=self.ctx) if bundle else export_bytes(run)
            save_desktop_export(filename, data, extension=extension)
        except (OSError, ValueError, TypeError) as exc:
            self.export_status.setText(f"저장 실패: {type(exc).__name__} · 경로와 확장자를 확인하세요.")
            return
        self.export_status.setText("저장 완료 · " + Path(filename).name)

    def change_theme(self, index):
        # Preserve the F1 geometry; use a legible foreground on dark surfaces.
        symbol = self.brand_symbol_svg
        if index:
            symbol = symbol.replace(b'#194C40', b'#E5EEE8').replace(b'fill="#E5EEE8"', b'fill="#A9C6BD"')
        self.brand_symbol.load(QByteArray(symbol))
        p = self.colors = DARK if index else LIGHT
        self.watchlist.set_theme(p)
        self.markets_view.set_theme(bool(index))
        for completer in getattr(self, 'symbol_completers', ()):
            completer.set_theme(p, bool(index))
        if self.language_store is not None:
            self.language_store.setValue("ui/theme", "dark" if index else "light")
        self.setStyleSheet(typography.window_stylesheet(p, bool(index)))
        for chart in [*self.findChildren(FanChart), *self.findChildren(FrontierChart), *self.findChildren(LineChart), *self.findChildren(SignedBars)]:
            chart.colors = p
            chart.update()
        from .indicator_guide import TechnicalChart
        for chart in self.findChildren(TechnicalChart):chart.redraw()
        self.market_chart.render()

    def closeEvent(self, event):
        closed = (self.home_feed.close(), self.q_scores.close(), self.chart_scores.close())
        if not all(closed):
            event.ignore()
            self.statusBar().showMessage(display(self, "진행 중인 분석 또는 조회가 끝난 뒤 종료할 수 있습니다."))
            return
        # The watchlist cards and the stock details poll on their own and do not block closing: stop()
        # cancels the cards still queued and drops late answers, so exit waits for one request at most.
        if self.jobs.busy or self.paper_session.jobs.busy or self.commentary.jobs.busy or self.market_chart.jobs.busy:
            event.ignore()
            self.statusBar().showMessage(display(self, "진행 중인 분석 또는 조회가 끝난 뒤 종료할 수 있습니다."))
            return
        if self.session.runs() or self.portfolio.chart.output is not None or self.bonds.chart.series or any(getattr(self,n).has_result for n in self.tool_names):
            answer = QMessageBox.question(self, display(self, "세션 종료"), display(self, "저장하지 않은 세션 기록은 사라집니다. 종료할까요?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        if not self.paper_session.stop():
            event.ignore()
            self.statusBar().showMessage(display(self, '모의 엔진의 진행 중인 조회가 끝나면 다시 종료해 주세요.'))
            return
        self.market_chart.stop()
        self.markets_view.stop()
        self.quote_paint_timer.stop()
        event.accept()


def main():
    if sys.platform == "win32":
        import ctypes
        set_app_id = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
        set_app_id.argtypes = [ctypes.c_wchar_p]
        set_app_id.restype = ctypes.c_long
        if set_app_id("QUANTGEN.Desktop") != 0:  # S_OK; otherwise Windows groups the window under python.exe
            print("QUANTGEN: Windows did not accept the application ID; the taskbar may show the Python icon.",
                  file=sys.stderr)
    app = QApplication(sys.argv)
    app.setWindowIcon(app_icon())
    app.setApplicationName("QUANTGEN")
    app.setOrganizationName("QUANTGEN")
    load_interface_fonts(app)
    settings = QSettings("QUANTGEN", "QUANTGEN")
    window = ResearchWindow(language=settings.value("ui/language", "en"),
                            locale=settings.value("ui/locale", None), language_store=settings,
                            theme_mode=settings.value("ui/theme", "light"))
    window.show()
    return app.exec()
