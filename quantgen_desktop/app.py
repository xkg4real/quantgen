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
from yaml import YAMLError

from PyQt6.QtCore import Qt, QEvent, QTimer, pyqtSlot, QByteArray, QSettings, QSize
from PyQt6.QtGui import QFont, QFontDatabase, QFontMetrics, QIcon, QKeySequence, QShortcut
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QFileDialog,
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSpinBox, QStackedWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QTabWidget, QButtonGroup, QSizePolicy)

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
from core.recorded_status_display import recorded_status_display
from tools.status.snapshot import verify
from .charts import FanChart, FrontierChart, LineChart, SignedBars
from .jobs import Jobs
from .localization import UiLabel, LanguageController, CAPTION_ROLE
from .translations import display
from .chart_study import CurrentPageTabs
from .macro_records import execute_macro_records
from . import rail_menu, shell_rail, typography

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
    """Register the complete hinted font bundle; preserve platform fallback on failure."""
    from .font_policy import configure_interface_font
    return configure_interface_font(app, application_root() / "assets/fonts", logger=log)


def panel(title):
    box = QFrame()
    box.setObjectName("panel")
    layout = QVBoxLayout(box)
    layout.setContentsMargins(22, 20, 22, 22)  # owner 2026-11-11: roomier panels, lighter lines
    layout.setSpacing(14)
    if title:
        layout.addWidget(label(title, "heading"))
    return box, layout


def table(headers):
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().hide()
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    t.setAlternatingRowColors(True)
    from .table_layout import configure_compact_table
    return configure_compact_table(t)


def table_rows(t, rows, ids=None):
    from .status_language import STATUS_ROLE, status_text
    t.setRowCount(len(rows))
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            item = QTableWidgetItem(str(value))
            if j in (t.property('localized_columns') or ()):
                item.setData(CAPTION_ROLE, str(value))
            context = getattr(t, '_qg_status_columns', {}).get(j)
            if context:
                item.setData(STATUS_ROLE, str(value))
                item.setToolTip(str(value))
                item.setText(status_text(t, value, context))
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
        from . import use_fusion_style, use_interface_fonts
        use_fusion_style()  # the look the style sheets and captures were made for, on Windows too
        use_interface_fonts()  # main() loads them first; a window built elsewhere gets the same face
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
        # Owner 2026-11-13: initially hidden market rows expand downward inside the rail.
        from .market_menu import InlineMarketMenu
        self.rail_flyouts = InlineMarketMenu(root, self)
        self.rail_flyouts.activated.connect(self.open_market_leaf)
        self.rail_flyouts.current = self.market_marks
        self._market_choice = None     # the 시장 row of the market page shown last on Markets
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        self.sidebar = sidebar
        self.sidebar_collapsed = False
        # Owner 2026-11-04: a thinner rail, sized from its widest label (fit_sidebar).
        sidebar.setFixedWidth(typography.SIDEBAR_WIDTH_RANGE[1])
        shell = QVBoxLayout(sidebar)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        # Owner 2026-11-11 (UI-D7 point 3): the rail hides to a thin strip (toggle, Ctrl+B) and the
        # choice is remembered. railPanel is the full rail, railStrip the hidden state.
        self.rail_panel = QWidget()
        self.rail_panel.setObjectName("railPanel")
        rail = QVBoxLayout(self.rail_panel)
        rail.setContentsMargins(*typography.RAIL_MARGINS)
        rail.setSpacing(typography.RAIL_SPACING)
        brand = QHBoxLayout()
        brand.setSpacing(typography.BRAND_SPACING)
        icon = QSvgWidget(str(application_root()/"assets/branding/f1-symbol.svg"))
        self.brand_symbol = icon
        self.brand_symbol_svg = (application_root()/"assets/branding/f1-symbol.svg").read_bytes()
        icon.setFixedSize(typography.BRAND_SYMBOL_SIZE, typography.BRAND_SYMBOL_SIZE)
        brand.addWidget(icon)
        self.brand_label = label("QUANTGEN", "brand", wrap=False)
        brand.addWidget(self.brand_label)
        brand.addStretch(1)
        self.sidebar_hide = shell_rail.icon_button("Hide menu", "Hide menu (Ctrl+B)", typography.RAIL_TOGGLE_SIZE)
        self.sidebar_hide.clicked.connect(lambda: self.set_sidebar_collapsed(True))
        brand.addWidget(self.sidebar_hide)
        rail.addLayout(brand)
        rail.addSpacing(10)
        # Nav and the Markets sub-menu scroll inside the rail when the window is short; the paper
        # stop, theme and language stay pinned at the bottom.
        self.rail_scroll = QScrollArea()
        self.rail_scroll.setObjectName("railScroll")
        self.rail_scroll.setWidgetResizable(True)
        self.rail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.rail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_host = QWidget()
        nav_host.setObjectName("railNav")
        nav_column = QVBoxLayout(nav_host)
        nav_column.setContentsMargins(0, 0, 0, 0)
        nav_column.setSpacing(typography.RAIL_SPACING)
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
            nav_column.addWidget(b)
            self.nav[route] = b
            if route == "markets":
                nav_column.addWidget(self.make_market_submenu())
        nav_column.addStretch(1)
        self.rail_scroll.setWidget(nav_host)
        self.rail_scroll.viewport().installEventFilter(self)  # its height sets the 시장 rows' (`fit_market_rows`)
        rail.addWidget(self.rail_scroll, 1)
        rail.addSpacing(6)
        self.paper_halt = QPushButton('모의 엔진 긴급 정지')
        self.paper_halt.setEnabled(False)
        self.paper_halt.clicked.connect(self.halt_paper_engine)
        self.paper_session.changed.connect(self.paper_engine_changed)
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
        shell.addWidget(self.rail_panel)
        self.rail_strip = QWidget()
        self.rail_strip.setObjectName("railStrip")
        strip = QVBoxLayout(self.rail_strip)
        _, top, _, bottom = typography.RAIL_MARGINS
        # The show toggle sits where the hide toggle was: centred on the brand row's height.
        strip.setContentsMargins(0, top + (typography.BRAND_SYMBOL_SIZE - typography.RAIL_TOGGLE_SIZE) // 2, 1, bottom)
        strip.setSpacing(typography.RAIL_SPACING + 4)
        self.sidebar_show = shell_rail.icon_button("Show menu", "Show menu (Ctrl+B)", typography.RAIL_TOGGLE_SIZE)
        self.sidebar_show.clicked.connect(lambda: self.set_sidebar_collapsed(False))
        strip.addWidget(self.sidebar_show, 0, Qt.AlignmentFlag.AlignHCenter)
        # The 시장 menu stays one move away while the rail is hidden: this button opens the same flyouts.
        self.market_strip = rail_menu.StripMenuButton("Markets", typography.RAIL_TOGGLE_SIZE)
        self.market_strip.clicked.connect(
            lambda: self.rail_flyouts.root_clicked(self.market_strip,
                                                   keyboard=bool(self.market_strip.property("focusRing"))))
        self.rail_flyouts.configure(self.nav['markets'], self.market_submenu, self.market_strip)
        # Owner 2026-11-17: 시장 itself opens the 시장 main screen (`market_hub.MarketHub`), then shows the categories
        # (navigating closes the disclosure, so the screen opens first).
        self.nav['markets'].clicked.connect(lambda: (self.open_market_hub(), self.rail_flyouts.open_root()))
        strip.addWidget(self.market_strip, 0, Qt.AlignmentFlag.AlignHCenter)
        # The paper engine's emergency stop stays one click away while the engine runs.
        self.paper_halt_strip = shell_rail.icon_button("Stop paper engine", "Stop paper engine",
                                                       typography.RAIL_TOGGLE_SIZE)
        self.paper_halt_strip.clicked.connect(self.halt_paper_engine)
        self.paper_halt_strip.hide()
        strip.addWidget(self.paper_halt_strip, 0, Qt.AlignmentFlag.AlignHCenter)
        strip.addStretch(1)
        shell.addWidget(self.rail_strip)
        self.rail_strip.hide()
        self.rail_keys = shell_rail.RailKeys(self.rail_buttons, self, expand=self.expand_rail_button,
                                             collapse=self.collapse_rail_flyout)
        for button in self.rail_buttons():
            self.rail_keys.watch(button)
        self.sidebar_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        self.sidebar_shortcut.activated.connect(self.toggle_sidebar)
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
        self.connect_market_sections(self.markets_view)
        self.setup_live_watchlist()
        self.change_theme(self.theme.currentIndex())
        self.navigate("home")
        self.localizer = LanguageController(self)
        self.refresh_views()
        self.fit_sidebar()
        if shell_rail.stored_flag(self.language_store):
            self.set_sidebar_collapsed(True, remember=False)
        from .reading_panel import install_reading_help
        self.reading_help = install_reading_help(self)
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
        theme/language selectors, the brand row (with its hide toggle) or the widest
        Markets sub-item need, and clamped to SIDEBAR_WIDTH_RANGE. A hidden rail keeps
        that width for later and shows the RAIL_COLLAPSED_WIDTH strip.
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
        self.brand_label.ensurePolished()
        needed = max(needed, typography.BRAND_SYMBOL_SIZE + 2 * typography.BRAND_SPACING
                     + self.brand_label.sizeHint().width() + typography.RAIL_TOGGLE_SIZE)
        sub_metrics = QFontMetrics(typography.scaled_font(font, 14, 600))
        sub_widest = max(sub_metrics.horizontalAdvance(b.text()) for b in self.market_sections.values())
        row_left, row_right = typography.MARKET_ROW_PADDING
        needed = max(needed, sub_widest + typography.SUBNAV_INDENT + 2 + row_left + row_right + 6)
        width = max(low, min(high, needed + left + right + frame))
        self.sidebar_expanded_width = width
        shown = typography.RAIL_COLLAPSED_WIDTH if self.sidebar_collapsed else width
        if self.sidebar.width() != shown or self.sidebar.minimumWidth() != shown:
            self.sidebar.setFixedWidth(shown)
        return shown

    def make_market_submenu(self):
        """Nine market categories, revealed on hover/click below 시장. Owner 2026-11-17: only the categories; their
        destinations (코스피, 국내 주식, ...) are on each category's main screen, not in the rail."""
        self.market_submenu = QWidget()
        self.market_submenu.setObjectName("marketSubmenu")
        self.market_submenu.setAccessibleName("Markets sections")
        column = QVBoxLayout(self.market_submenu)
        column.setContentsMargins(typography.SUBNAV_INDENT, 0, 0, 2)
        column.setSpacing(0)
        self.market_sections = {}
        self.market_section = None
        for key, _title in shell_rail.market_sections():
            row = rail_menu.MarketRailRow(key)
            row.clicked.connect(lambda checked=False, k=key: self.open_market_category(k))
            self.rail_flyouts.watch_root(row, lambda k=key: self._market_flyout(k))
            column.addWidget(row)
            self.market_sections[key] = row
        self.retitle_market_sections()
        return self.market_submenu

    def retitle_market_sections(self):
        """The 시장 rows (and the hidden rail's 시장 button) in the window language; an open flyout closes, so the
        next one opens in the new language."""
        self.rail_flyouts.close_all()
        for key, button in self.market_sections.items():
            title = shell_rail.market_section_text(key, self.ui_language)
            button.setText(title)
            button.setAccessibleName(title)
            button.chevron = False   # owner 2026-11-17: no sub-rows in the rail

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Resize and watched is self.rail_scroll.viewport():
            self.fit_market_rows()
        return super().eventFilter(watched, event)

    def fit_market_rows(self):
        """The 시장 rows at MARKET_ROW_HEIGHT while the rail has the room; a shorter window tightens them, down to
        MARKET_ROW_MIN_HEIGHT (close to the flyouts' rows, UI-D11 review), before the rail has to scroll."""
        rows = list(self.market_sections.values())
        full, low = typography.MARKET_ROW_HEIGHT, typography.MARKET_ROW_MIN_HEIGHT
        content = self.rail_scroll.widget().layout().sizeHint().height()
        others = content - sum(row.row_height for row in rows)
        room = self.rail_scroll.viewport().height() - others
        height = max(low, min(full, room // len(rows)))
        for row in rows:
            row.set_row_height(height)
        return height

    def _market_node(self, key):
        """A 시장 row's `shell_rail.MenuNode`, in the window language."""
        return next(node for node in shell_rail.market_menu(self.ui_language) if node.key == key)

    def _market_flyout(self, key):
        """The rows under a 시장 row in the rail: none since the owner's 2026-11-17 request ("이 범주까지만 살려두고,
        그다음 하위범주 ... 좌측 바로가기 ui 삭제"); a category's destinations are on its main screen."""
        return ()

    def open_market_category(self, key, *, keyboard=None):
        """A 시장 row clicked (or Enter / Space on it): a row with one page of its own (크립토, 선물, 회사채) opens it,
        the others open their category's main screen (owner 2026-11-17: "정작 '주식' 바로가기는 눌리지 않습니다")."""
        node = self._market_node(key)
        if not node.children and node.leaf:
            self.rail_flyouts.close_all()
            self.open_market_leaf(node.leaf)
            return None
        self.rail_flyouts.close_all()   # as a leaf does: the choice is made, the rail's list folds away
        self.open_market_hub(key)
        return None

    def _open_hub_stock(self, instrument):
        """A name in a 시장 screen's preview list: its stock screen, over that market's page."""
        from core.market import rankings as R
        member = R.member_for(instrument)
        page = member.group if member is not None else None
        self.open_market_section(page if page in ("kr", "us", "etf_kr", "etf_us") else
                                 ("kr" if instrument.asset == "domestic_stock" else "us"))
        self.markets_view.open_instrument(instrument)

    def open_market_hub(self, category=None):
        """The 시장 main screen (category None) or one category's main screen, inside Markets."""
        self.navigate("markets")
        hub = self.market_hub
        if category is None:
            hub.show_root()
        else:
            hub.show_category(category)
        self.markets_content.setCurrentWidget(hub)
        self.market_asset_category = category
        self.sync_market_section()
        return hub

    def expand_rail_button(self, button):
        """→ on a rail button with a flyout (a 시장 row, or the hidden rail's 시장 button)."""
        self.rail_flyouts.root_clicked(button, keyboard=True)

    def collapse_rail_flyout(self, button):
        """← / Esc on a 시장 row closes its flyout (True: the key was used); None: another rail button took the
        focus, so an open flyout closes."""
        if not self.rail_flyouts.is_open():
            return False
        if button is None:
            self.rail_flyouts._close_from(0)
            self.rail_flyouts.keyboard=True
            return False
        self.rail_flyouts.close_all()
        return True

    def open_market_leaf(self, leaf):
        """Open a ranking, observed series or independent asset workspace within Markets."""
        self.rail_flyouts.close_all()
        kind = leaf[0]
        if kind == "market":
            _kind, page, category = leaf
            self.open_market_section(page)
            view = self.markets_view
            if category and hasattr(view, "show_category"):
                view.show_category(category)
        elif kind in ('series', 'workspace'):
            from .market_destinations import MarketSeriesPage, MarketToolPage
            self.navigate('markets')
            category=leaf[1]
            cache_key=('series',) if kind=='series' else ('workspace',category,leaf[2])
            page=self.market_destinations.get(cache_key)
            if page is None:
                page=(MarketSeriesPage(ctx=self.ctx,auto_load=self.auto_refresh,
                      loader=getattr(self,'summary_loader',None)) if kind=='series'
                      else MarketToolPage(self,leaf[2],category))
                self.market_destinations[cache_key]=page
                self.markets_content.addWidget(page)
            self.market_asset_category=category
            self.markets_content.setCurrentWidget(page)
            if kind=='series':page.select(category,leaf[2]);page.set_theme(self.colors)
            else:page.select(leaf[3])
        else:
            raise ValueError(f"Unknown 시장 menu leaf: {leaf!r}")
        self.sync_market_section()
        return True

    def rail_buttons(self):
        """The rail's buttons in visual order (the arrow keys walk them)."""
        buttons = [self.sidebar_hide]
        for route, button in self.nav.items():
            buttons.append(button)
            if route == "markets":
                buttons.extend(self.market_sections.values())
        return buttons + [self.sidebar_show, self.market_strip, self.paper_halt_strip]

    def open_market_section(self, key):
        """Open Markets on one market's page (a `markets_view.MARKET_PAGES` key: kr, us, crypto, etf_kr, etf_us);
        its 시장 row (주식, 크립토 or ETF) is highlighted."""
        from core.market.screen import PAGE_KEYS
        if key not in PAGE_KEYS:
            raise ValueError(f"Unknown market page: {key!r}")
        self.navigate("markets")
        self.markets_content.setCurrentWidget(self.markets_view)
        self.market_asset_category=None
        view = self.markets_view
        if hasattr(view, "show_market"):
            view.show_market(key)
        self.sync_market_section(key)

    def _route(self):
        index = self.stack.currentIndex()
        return next((route for route, i in self.route_indices.items() if i == index), None)

    def market_marks(self):
        """The `shell_rail.MenuNode.mark`s of what Markets shows (the market page and its ranking): its 시장 row and
        flyout rows are marked. Another page marks nothing: its own rail item says where the window is (UI-D11
        review, a 시장 row lit under another selected page was a second 'you are here')."""
        marks = set()
        if self._route() == "markets":
            hub = getattr(self, "market_hub", None)
            if hub is not None and self.markets_content.currentWidget() is hub:
                return frozenset({('category', hub.category)}) if hub.category else frozenset()
            if getattr(self,'market_asset_category',None):
                return frozenset({('category',self.market_asset_category)})
            view = self.markets_view
            current = getattr(view, "current_market", None)
            page = current() if callable(current) else None
            if page:
                marks |= {("page", page), ("category", shell_rail.PAGE_CATEGORY.get(page, ""))}
                showing = getattr(view, "showing_stock", None)
                category = getattr(view, "current_category", None)
                if callable(category) and not (callable(showing) and showing()):
                    marks.add(("market", page, category()))
        return frozenset(marks)

    def sync_market_section(self, key=None):
        """Highlight the 시장 row of the market page Markets shows (`key`, a market page key, else the page's own
        market, also while a stock's screen is open over it, else the last choice); on any other page none."""
        category = None
        hub = getattr(self, "market_hub", None)
        if self._route() == "markets" and hub is not None and self.markets_content.currentWidget() is hub:
            self.market_section = hub.category if hub.category in self.market_sections else None
            for name, button in self.market_sections.items():
                button.setChecked(name == self.market_section)
            return
        if self._route() == "markets":
            view = getattr(self, "markets_view", None)
            if key is None and view is not None:
                current = getattr(view, "current_market", None)
                key = current() if callable(current) else None
            category = getattr(self,'market_asset_category',None) or (shell_rail.PAGE_CATEGORY.get(key) if key else self._market_choice)
            self._market_choice = category
        self.market_section = category if category in self.market_sections else None
        for name, button in self.market_sections.items():
            button.setChecked(name == self.market_section)

    def connect_market_sections(self, view):
        """Follow the Markets page's own market changes when it announces them (an optional
        `market_changed(str)` signal); otherwise the highlight follows the rail and navigate()."""
        signal = getattr(view, "market_changed", None)
        if signal is not None and hasattr(signal, "connect"):
            signal.connect(lambda key: self.sync_market_section(key or None))

    def set_sidebar_collapsed(self, collapsed, *, remember=True):
        """Hide the rail to a thin strip, or show it again, keeping the page and its scroll position."""
        collapsed = bool(collapsed)
        self.rail_flyouts.close_all()
        page = self.stack.currentWidget()
        bar = page.verticalScrollBar() if isinstance(page, QScrollArea) else None
        position = bar.value() if bar is not None else None
        focus = QApplication.focusWidget()
        keep_focus = focus is not None and (focus is self.sidebar or self.sidebar.isAncestorOf(focus))
        ring = keep_focus and bool(focus.property("focusRing"))  # read before hiding clears it
        self.sidebar_collapsed = collapsed
        self.rail_panel.setVisible(not collapsed)
        self.rail_strip.setVisible(collapsed)
        self.fit_sidebar()
        if remember and self.language_store is not None:
            self.language_store.setValue(shell_rail.SETTINGS_KEY, collapsed)
        if keep_focus:  # a keyboard user stays on the toggle, with its ring if it had one
            reason = Qt.FocusReason.TabFocusReason if ring else Qt.FocusReason.OtherFocusReason
            (self.sidebar_show if collapsed else self.sidebar_hide).setFocus(reason)
        if bar is not None:
            # The page reflows to its new width now and once more after queued layout requests.
            self._page_position = (bar, position)
            self.centralWidget().layout().activate()
            self.restore_page_position(final=False)
            QTimer.singleShot(0, self.restore_page_position)
        return collapsed

    def restore_page_position(self, final=True):
        pending = getattr(self, "_page_position", None)
        if not pending:
            return
        if final:
            self._page_position = None
        bar, position = pending
        try:
            bar.setValue(min(position, bar.maximum()))
        except RuntimeError:  # the window closed before the deferred pass
            pass

    def toggle_sidebar(self):
        return self.set_sidebar_collapsed(not self.sidebar_collapsed)

    def halt_paper_engine(self):
        if self.paper_session.runtime:
            self.paper_session.runtime.halt()

    def paper_engine_changed(self):
        running = self.paper_session.runtime is not None
        self.paper_halt.setEnabled(running)
        self.paper_halt_strip.setVisible(running)

    def apply_rail_theme(self, palette, dark):
        """The rail's own sheet (typography.rail_stylesheet), its painted icons and the 시장 flyouts for a theme."""
        self.sidebar.setStyleSheet(typography.rail_stylesheet(palette, dark))
        size = QSize(18, 18)
        for button, rail_open in ((self.sidebar_hide, True), (self.sidebar_show, False)):
            button.setIcon(shell_rail.toggle_icon(palette.muted, rail_open=rail_open))
            button.setIconSize(size)
        self.market_strip.setIcon(shell_rail.markets_icon(palette.muted))
        self.market_strip.setIconSize(size)
        self.rail_flyouts.set_theme(palette, dark)  # also the rows' chevrons and the tint of an open row
        self.paper_halt_strip.setIcon(shell_rail.stop_icon(typography.tone_colors(palette)["up"]))
        self.paper_halt_strip.setIconSize(QSize(16, 16))

    def page(self, title, subtitle):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        # Owner 2026-11-11: light section lines need roomy blocks ("한칸한칸 공간을 넓게").
        layout.setContentsMargins(32, 28, 32, 36)
        layout.setSpacing(24)
        if title is not None:
            layout.addWidget(label(title, "title"))
            layout.addWidget(label(subtitle, "muted"))
        scroll.setWidget(content)
        self.stack.addWidget(scroll)
        return layout

    def make_home(self):
        """Research Home (owner, 2026-11-11, UI-D7 point 4: no big table; owner-approved draft 2026-11-17,
        docs/product/ui_drafts_2026-11-17/draft_01_home.png): the stock detail's frame. Toolbar: title, today's date,
        a '지연 · 일별 종가' badge, '전체 시세 표' (opens the quotes table below the chart) and 새로고침. Canvas: the
        market tiles that page with arrows (TradingView style), the selected market's key figures and its large
        chart. Right column, 내 목록: the watchlist rows, the latest research runs with the three counts and the
        small fan card; 읽는 법: how to read the page and the data-use terms. '설계/검증에서 연구 시작' is pinned at the
        bottom. Every attribute, signal and request is as before. See home_view."""
        from .home_view import (HomeSide, HomeView, MiniFan, QuotesFold, RecentRuns, TodayText, directory_name,
                                style_link)
        from .page_kit import Button, Fold, Soft, Text, Workspace, rule
        from .stock_detail_style import numbers
        outer = self.page(None, None)
        scroll = self.stack.widget(self.stack.count() - 1)
        self.home_workspace = ws = Workspace(("Research Home", "연구 홈"))
        outer.addWidget(ws)
        ws.fit_to(scroll)
        from .markets_view import WatchlistStore
        from .watchlist import WatchlistPanel
        # The live-quote table stays the window's (live feed, Q-SCORE, details); it is no longer the main surface.
        self.watchlist = WatchlistPanel(locale=self.ctx)
        self.watchlist.setProperty("reading_help_keep_visible", True)
        self.watchlist.refresh_requested.connect(self.refresh_markets)
        self.watchlist.chart_requested.connect(self.open_stock_chart)
        self.home_markets = self.watchlist.table
        # Home and Markets share one watchlist store and one symbol directory, whichever page is built first.
        if self.watchlist_store is None:
            self.watchlist_store = WatchlistStore(self.language_store)
        if self.symbol_directory is None:
            from core.market.directory import default_directory
            self.symbol_directory = default_directory()

        def open_watch(instrument):
            # A watchlist card opens that stock's screen on Markets (as open_stock_chart, any stock kind).
            self.navigate('markets')
            self.markets_content.setCurrentWidget(self.markets_view)
            self.market_asset_category=None
            self.markets_view.open_instrument(instrument)
            scroll = self.stack.widget(self.route_indices['markets'])
            QTimer.singleShot(0, lambda: scroll.verticalScrollBar().setValue(0))

        def add_watch():
            self.navigate('markets')
            self.markets_content.setCurrentWidget(self.markets_view)
            self.market_asset_category=None
            if hasattr(self.markets_view, 'show_category'):
                self.markets_view.show_category('search')
            else:
                self.markets_view.show_watchlist()
                self.markets_view.search.setFocus(Qt.FocusReason.OtherFocusReason)

        self.home_view = HomeView(
            store=self.watchlist_store, card_router_factory=self.card_router_factory or _production_card_router,
            name_fn=lambda instrument, language: directory_name(self.symbol_directory, instrument, language),
            rows_source=lambda: self.watchlist.rows, locale=self.ctx, auto_load=self.auto_refresh, docked=True)
        self.home_view.refresh_requested.connect(self.refresh_markets)
        self.home_view.stock_requested.connect(open_watch)
        self.home_view.add_requested.connect(add_watch)
        self.jobs.busy_changed.connect(self.home_view.set_busy)
        hv = self.home_view

        # Toolbar: date, the data badge, then the quotes table and the page's refresh on the right.
        self.home_date = ws.add_toolbar(TodayText())
        self.home_badge = ws.add_badge(("Delayed · daily closes", "지연 · 일별 종가"))
        # The full quotes table, folded (owner: "표에 종목 너무많이 때려박는거 자체의 구조적 문제"); its toggle is the
        # toolbar's '전체 시세 표' and the table opens below the chart.
        self.quotes_fold = QuotesFold("All quotes table", self.watchlist,
                                      "Markets and Korean stocks, live connection and Q-SCORE")
        ws.add_toolbar(self.quotes_fold.dock_toggle(), right=True)
        hv.refresh_button.setProperty("kit", "secondary")
        hv.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        ws.add_toolbar(hv.refresh_button, right=True)
        self.quotes_fold.toggle.toggled.connect(self.home_reveal_quotes)

        # Canvas: tiles, key figures and the chart (HomeView), then the folded quotes table.
        ws.canvas.addWidget(hv, 1)
        ws.canvas.addWidget(self.quotes_fold)

        # Right column, 내 목록: watchlist rows, recent research, the latest fan.
        side = HomeSide()
        mine = ws.side.add_page(("My list", "내 목록"))
        mine.addWidget(side)
        self.home_watch_fold = Fold(("Watchlist", "관심종목"))
        self.home_watch_fold.head.layout().addWidget(style_link(hv.add_button), 0, Qt.AlignmentFlag.AlignVCenter)
        self.home_watch_fold.body.setContentsMargins(0, 0, 0, 2)
        self.home_watch_fold.body.addWidget(hv.grid)
        side.column.addWidget(self.home_watch_fold)
        self.watchlist_store.changed.connect(self.home_watch_count)
        self.home_watch_count()
        side.column.addWidget(rule())
        self.home_research_fold = Fold(("Recent research", "최근 연구"), count="0")
        library = Button(("Library ›", "연구 보관함 ›"), "")
        library.setProperty("kit", None)
        style_link(library, quiet=True)
        library.clicked.connect(lambda: self.navigate('library'))
        self.home_research_fold.head.layout().addWidget(library, 0, Qt.AlignmentFlag.AlignVCenter)
        counts = QWidget()
        line = QHBoxLayout(counts)
        line.setContentsMargins(2, 0, 0, 0)
        line.setSpacing(5)
        self.count_labels = []
        for pair in (("Completed", "완료한 분석"), ("In progress", "진행 중"), ("To review", "확인할 실행")):
            key = Text(pair)
            key.setProperty("homeRole", "countKey")
            number = numbers(QLabel("0"))
            number.setProperty("homeRole", "countValue")
            number.setProperty("qg_literal", True)
            line.addWidget(key)
            line.addWidget(number)
            line.addSpacing(10)
            self.count_labels.append(number)
        line.addStretch(1)
        self.home_research_fold.body.addWidget(counts)
        self.home_runs = RecentRuns(lambda: self.session.runs())
        self.home_runs.changed.connect(self.home_runs_changed)
        self.home_research_fold.body.addWidget(self.home_runs)
        side.column.addWidget(self.home_research_fold)
        fan = QFrame()
        fan.setProperty("kit", "soft")
        fan.setProperty("reading_help_keep_visible", True)
        box = QVBoxLayout(fan)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(7)
        head = QHBoxLayout()
        head.setSpacing(8)
        head.addWidget(Text(("Do not narrow the possibilities to one number", "가능성을 하나의 숫자로 좁히지 마세요"),
                            "softTitle", wrap=True), 1)
        self.home_fan_note = numbers(Text("", "fine"))
        head.addWidget(self.home_fan_note, 0, Qt.AlignmentFlag.AlignTop)
        box.addLayout(head)
        self.home_chart = MiniFan()
        box.addWidget(self.home_chart)
        box.addWidget(Text(("P5–P95 is the central 90% of the simulated distribution · not a return guarantee",
                            "P5–P95는 시뮬레이션 분포의 중앙 90% 구간이에요 · 수익 보장 아님"), "fine", wrap=True))
        self.home_summary = label("분석을 실행하면 최신 결과와 데이터 근거가 연결됩니다.")
        self.home_summary.localized_text = {'ko': '분석을 실행하면 최신 결과와 데이터 근거가 여기에 연결돼요.',
                                            'en': 'Run an analysis to connect its results and data evidence here.'}
        self.home_summary.retranslate()
        self.home_summary.setProperty("kit", "hint")
        self.home_summary.setProperty("reading_help_keep_visible", True)
        box.addWidget(self.home_summary)
        side.column.addWidget(fan)

        # Right column, 읽는 법: how to read the page, the data-use terms.
        guide = ws.side.add_page(("How to read", "읽는 법"))
        for title, body in (
                (("Major markets", "주요 시장"),
                 ("Each tile is its provider's latest daily observation (delayed). Prices change against the previous "
                  "close; yields move in basis points (bp). A tile's line is drawn from closes already loaded.",
                  "타일마다 공급자의 최근 일별 관측값이에요(지연). 가격은 전일 대비, 금리는 bp로 변해요. 타일의 선은 이미 불러온 "
                  "종가로만 그려요.")),
                (("The chart", "차트"),
                 ("The line is the daily close; the dashed line is the range's first close, the line its change is read "
                  "against. Point at the chart for a date and its close.",
                  "선은 일별 종가, 점선은 기간 첫 종가예요. 기간 변동은 이 점선과 견줘 읽어요. 차트 위에 마우스를 올리면 날짜와 "
                  "종가가 보여요.")),
                (("Watchlist", "관심종목"),
                 ("Open a stock on Markets and press ☆ to add it. Click a row to open its screen; Delete removes it.",
                  "시장에서 종목을 열고 ☆를 누르면 추가돼요. 행을 누르면 그 종목 화면이 열리고, Delete 키로 뺄 수 있어요.")),
                (("Monte Carlo", "몬테카를로"),
                 ("This session's runs only. P5–P95 is the central 90% of the simulated distribution, not a return "
                  "guarantee or a 95% confidence interval. Results stay NOT_RUN, separate from investment validation.",
                  "이번 세션의 실행만 보여요. P5–P95는 시뮬레이션 분포의 중앙 90% 구간이에요. 수익 보장이나 95% 신뢰구간이 "
                  "아니에요. 결과는 투자 판정과 별개로 NOT_RUN을 유지해요."))):
            note = Soft(title, body)
            note.setProperty("reading_help_keep_visible", True)
            guide.addWidget(note)
        rights = Button(("Market data usage review", "시장 데이터 이용 조건"), "secondary")
        rights.clicked.connect(self.open_data_rights)
        guide.addWidget(rights, 0, Qt.AlignmentFlag.AlignLeft)

        # Pinned: the way into Build & Test, and the quiet no-guarantee line.
        start = Button(("Start research in Build & Test", "설계/검증에서 연구 시작"), "primary")
        start.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        start.clicked.connect(lambda: self.navigate("quant"))
        self.home_start = start
        ws.side.foot.addWidget(start)
        caption = Text(("Monte Carlo results are separate from investment validation · no future guarantee · "
                        "not investment advice",
                        "몬테카를로 결과는 투자 판정과 별개예요 · 미래 보장 아님 · 투자 권유 아님"), "fine", wrap=True)
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        caption.setProperty("reading_help_keep_visible", True)
        ws.side.foot.addWidget(caption)
        ws.finish()
        self.home_library_link = library
        self.home_focus_chain()
        ws.set_language(self.ui_language)

    def home_focus_chain(self):
        """Tab order: the toolbar, the canvas (arrows, tiles, periods), the right column (watchlist rows included,
        as they come and go), then the pinned action."""
        hv = self.home_view
        chain = [self.quotes_fold.toggle, hv.refresh_button, hv.previous_button, hv.next_button,
                 *hv.cards.values(), *hv.range_buttons.values(), *self.home_workspace.side.segment.buttons,
                 self.home_watch_fold.head, hv.add_button, *hv.grid.cards.values(), self.home_research_fold.head,
                 self.home_library_link, self.home_start]
        for first, second in zip(chain, chain[1:]):
            QWidget.setTabOrder(first, second)

    def home_watch_count(self):
        """The 관심종목 fold's count ('6/20'), after every change to the shared watchlist."""
        store = self.watchlist_store
        self.home_watch_fold.set_count(f"{len(store.items())}/{store.limit}")
        if hasattr(self, 'home_library_link'):
            self.home_focus_chain()

    def home_runs_changed(self, count, latest):
        """The 최근 연구 fold's count and the fan card's note ('AAPL · 126거래일') from the latest completed run."""
        self.home_research_fold.set_count(str(count))
        if latest:
            params = latest.get("parameters") or {}
            days = params.get("horizon_days")
            symbol = str(params.get("symbol") or "")
            self.home_fan_note.set_pair((f"{symbol} · {days} sessions" if days else symbol,
                                         f"{symbol} · {days}거래일" if days else symbol))
        else:
            self.home_fan_note.set_pair("")
        self.home_fan_note.set_language(getattr(self, "ui_language", "ko"))

    def home_reveal_quotes(self, expanded):
        """'전체 시세 표' opens the table below the chart and scrolls the canvas to it."""
        if not expanded:
            return
        canvas = self.home_workspace.canvas_scroll

        def reveal():
            if self.quotes_fold.expanded():
                canvas.verticalScrollBar().setValue(max(0, self.quotes_fold.y() - 8))
        QTimer.singleShot(30, reveal)

    def make_indicator_guide(self):
        """기술지표 가이드 (owner-approved draft 2026-11-17, docs/product/ui_drafts_2026-11-17/draft_03_guide.png): the
        stock detail's frame. Toolbar: title, 기술지표 27 | 투자 용어, the education badge, 모두 해제 and 보고서 저장.
        Canvas: the example's name line and price figures, the chart card (indicator tags with their values, the
        chart with the reading date, the date slider, the signals that missed) and the provenance in small print.
        Right column: 지표 | 해석 with the combined reading and the education note pinned at the foot. The guide
        keeps its widgets, signals, calculations and export (IndicatorGuide.dock_into)."""
        from .indicator_guide import IndicatorGuide
        from .page_kit import Workspace
        outer = self.page(None, None)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = self.stack.widget(self.stack.count() - 1)
        self.indicator_guide = IndicatorGuide(locale=self.ctx)
        self.guide_workspace = ws = Workspace(("Technical indicator guide", "기술지표 가이드"))
        self.indicator_guide.dock_into(ws)
        outer.addWidget(self.indicator_guide)
        ws.fit_to(scroll)
        # The empty chart's hint ('오른쪽 지표 목록에서 고르면 …'); the language change sets its text.
        self.guide_subtitle = self.indicator_guide.hint
        self.guide_subtitle.setText(self.indicator_guide.intro_text())
        self.indicator_guide.intro.hide()
        self.kit_language()

    def make_markets(self):
        """Markets: one page per market (owner ruling UI-D10, 2026-11-11; since UI-D11, 2026-11-12: 국내 주식, 미국 주식,
        크립토, 국내 ETF, 미국 ETF, reached from the rail's 시장 flyouts), each a compact header with its own search, an
        index strip, the ranking categories as criteria and the list; one screen per stock. No page title or
        description paragraph: the market page's header names it. The watchlist chart cards moved to Research Home
        (make_home)."""
        from .market_chart import MarketChartPane
        from .market_rankings import ProductionRankingLoader
        from .market_summary import production_series
        from .markets_view import DirectoryLoader, MarketsWorkspace, WatchlistStore
        from core.market.directory import default_directory
        layout = self.page(None, None)
        layout.setContentsMargins(32, 24, 32, 36)
        # Owner, 2026-11-04: no indicator board (UI-7) and no asset-class tab strip (UI-8) here.
        self.market_chart = MarketChartPane(locale=self.ctx)
        self.market_chart.setProperty("reading_help_keep_visible", True)
        self.market_chart.setObjectName('marketChart')
        if self.symbol_directory is None:
            self.symbol_directory = default_directory()
        self.directory_loader = DirectoryLoader(self.symbol_directory, enabled=self.auto_refresh)
        if self.watchlist_store is None:
            self.watchlist_store = WatchlistStore(self.language_store)
        # Ranked quotes: an injected loader (tests: window.ranking_loader before make_markets, or
        # markets_view.rankings.loader after) or KIS/Yahoo constructed on first use. The index strip reads Home's
        # Yahoo daily path unless window.summary_loader (a core.ficc.data.load_series-like callable) is injected.
        self.markets_view = MarketsWorkspace(
            self.market_chart, store=self.watchlist_store, directory=self.symbol_directory,
            directory_loader=self.directory_loader,
            ranking_loader=getattr(self, "ranking_loader", None) or ProductionRankingLoader(),
            profile_loader=self.profile_loader or _ProductionProfileLoader(),
            summary_loader=getattr(self, "summary_loader", None) or production_series,
            locale=self.ctx, auto_load=self.auto_refresh)
        self.markets_view.setProperty("reading_help_keep_visible", True)
        from .tools import CurrentPageStack
        self.markets_content=CurrentPageStack()
        self.markets_content.addWidget(self.markets_view)
        self.market_destinations={}
        # Owner 2026-11-17: the 시장 main screen and the categories' main screens (opened from the rail's 시장 and
        # category rows). Kept with the other destinations, so language, theme and closing reach it.
        from .market_hub import MarketHub
        self.market_hub = MarketHub(ctx=self.ctx, summary_loader=getattr(self, "summary_loader", None) or production_series,
                                    auto_load=self.auto_refresh)
        self.market_hub.setProperty("reading_help_keep_visible", True)
        self.market_hub.open_leaf.connect(self.open_market_leaf)
        self.market_hub.attach_board(self.markets_view.rankings)
        self.market_hub.open_stock.connect(self._open_hub_stock)
        self.market_hub.open_category.connect(self.open_market_hub)
        self.market_hub.back.connect(lambda: self.open_market_hub())
        self.markets_content.addWidget(self.market_hub)
        self.market_destinations[('hub',)] = self.market_hub
        self.market_asset_category=None
        layout.addWidget(self.markets_content)
        layout.addStretch()

    def make_tools(self):
        """Analysis tools (owner-approved draft 2026-11-17, docs/product/ui_drafts_2026-11-17/draft_02_tools.png): the
        stock detail's frame. Toolbar: the title, the ten tools as pill tabs (`tool_buttons`, which drive `tool_host`)
        and a status badge. Canvas: the selected tool's result (Bonds: the lead line, key figures, the price–yield chart
        card, the scenario and hedge cards, every metric; the other tools: the status line with their exports, then the
        result in one card). Right column, one per tool: 설정 (the docked form, its run button pinned at the bottom) and
        읽는 법 (`tools_guide`, which follows the selected tool). Every pane, signal, request and export is as before."""
        from .bonds import BondsPane
        from .rates import RatesPane
        from .fx import FXPane
        from .structuring import StructuringPane
        from .macro import MacroPane
        from .macro_records import MacroRecordsPane
        from .market_tools import DerivativesPane, ETFPane, CryptoPane, KRXPane
        from .tools import CurrentPageStack
        from .page_kit import Text, Workspace
        titles = {'bonds': ('Bonds', '채권'), 'rates': ('Rates', '금리'), 'structuring': ('Structuring', '구조화 상품'),
                  'fx': ('FX', '외환'), 'derivatives': ('Derivatives', '파생상품'), 'etf': ('ETF', 'ETF'),
                  'krx': ('KRX', 'KRX'), 'crypto': ('Crypto', '가상자산'), 'macro': ('Macro', '매크로 지표'),
                  'macro_records': ('Macro v2', '매크로 v2')}
        outer = self.page(None, None)
        from .research_style import prepare_page
        self.tools_page = prepare_page(outer)
        self.tools_page.setMaximumWidth(16777215)
        scroll = self.stack.widget(self.stack.count() - 1)
        self.tools_workspace = ws = Workspace(("Analysis tools", "분석 도구"))
        outer.addWidget(ws)
        ws.fit_to(scroll)
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
        self.tool_host = CurrentPageStack()
        self.tool_host.setObjectName('toolHost')
        from .workspace_guide import WorkspaceGuide
        self.tools_guide = WorkspaceGuide('bonds')
        sides, self.tools_guide_pages = [], []
        for index, (name, _title) in enumerate(TOOL_PANES):
            pane = getattr(self, name)
            self.tool_host.addWidget(pane)
            side = ws.side if index == 0 else ws.add_side()
            pane.result_changed.connect(self.tools_show_badge)
            if pane is self.bonds:
                pane.dock_into(side, title=("Settings", "설정"))
                ws.follow(pane)          # its key figures carry units in the window language
            else:
                pane.dock_tool(side, title=("Settings", "설정"))
            self.tools_guide_pages.append(side.add_page(("How to read", "읽는 법")))
            side.foot.addWidget(Text(("Research calculation · not investment advice", "연구용 계산 · 투자 권유 아님"),
                                     "fine"))
            sides.append(side)
        self.tools_guide_pages[0].addWidget(self.tools_guide)
        ws.finish()
        ws.canvas.addWidget(self.tool_host)
        ws.canvas.addStretch(1)
        # The pill tabs drive the existing stack (kept for show_tool, current_market_pane and tests).
        self.tool_switch = ws.bind_tabs(self.tool_host, [titles[name] for name, _ in TOOL_PANES], sides=sides,
                                        kind="pills", on_change=self.tools_follow)
        self.tool_group = self.tool_switch.group
        self.tool_buttons = {}
        for (name, _title), button in zip(TOOL_PANES, self.tool_switch.buttons):
            button.setProperty('tool', True)
            self.tool_buttons[name] = button
        from .page_kit import Badge
        self.tools_badge = ws.add_toolbar(Badge(), right=True)
        self.tools_follow(self.tool_host.currentIndex())
        self.kit_language()

    def tools_follow(self, index):
        """The selected tool's right column opens on the same tab (설정 or 읽는 법) as the one it replaces, the workflow
        guide moves into it, and the badge says whether this tool has a result."""
        if not hasattr(self, 'tools_badge') or not 0 <= index < len(TOOL_PANES):
            return
        side = self.tools_workspace.side
        previous = getattr(self, '_tools_side', None)
        if previous is not None and previous is not side:
            side.show_page(previous.pages.currentIndex())
        self._tools_side = side
        self.tools_guide.set_key(TOOL_PANES[index][0])
        self.tools_guide_pages[index].insertWidget(0, self.tools_guide)
        self.tools_show_badge()

    def tools_show_badge(self, *args):
        """'● 계산 완료' once the selected tool has a result, '● 실행 전' before."""
        badge = getattr(self, 'tools_badge', None)
        if badge is None:
            return
        if getattr(self.tool_host.currentWidget(), 'has_result', False):
            badge.set_pair(("Run complete", "계산 완료")); badge.set_tone("ok")
        else:
            badge.set_pair(("Not run yet", "실행 전")); badge.set_tone("")

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
                    if getattr(self, name) is pane and hasattr(self, 'tools_guide'):
                        self.tools_guide.set_key(name)
                return pane
        raise ValueError('Pane is not one of the analysis tools')

    def show_market_pane(self, pane):
        """Kept for callers of the former Markets tabs: the chart opens Markets, a tool opens its page."""
        if pane is self.market_chart:
            self.navigate('markets')
            self.markets_content.setCurrentWidget(self.markets_view)
            self.market_asset_category=None
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
        return self.market_chart if self.markets_view.showing_stock() else self.markets_view.rankings

    def make_quant(self):
        """Build & Test (owner-approved draft 2026-11-17, docs/product/ui_drafts_2026-11-17/draft_04_quant.png): the
        stock detail's frame. Toolbar: title, 몬테카를로 | 전략 실험실, a status badge. Canvas: the run's lead line, its key
        figures, the fan chart with its reading, then the metrics table. Right column: the settings in two folds
        (종목·기간, 모형 가정) and a reading note, with the run button pinned at the bottom; the 읽는 법 tab holds the
        workflow guide. Strategy Lab keeps its pane; its form docks into its own right column (ToolPane.dock_into).
        Every attribute, signal and calculation is as before."""
        from .page_kit import Badge, Card, Fold, KeyFigures, Soft, Text, Workspace
        outer = self.page(None, None)
        from .research_style import prepare_page
        self.quant_page = prepare_page(outer)
        self.quant_page.setMaximumWidth(16777215)
        scroll = self.stack.widget(self.stack.count() - 1)
        self.quant_workspace = ws = Workspace(("Build & Test", "설계/검증"))
        outer.addWidget(ws)
        ws.fit_to(scroll)
        from .workspace_guide import WorkspaceGuide
        self.quant_guide = WorkspaceGuide('monte_carlo')
        # Only the selected page sets the scroll width. The inactive Strategy
        # form has platform-dependent font/combobox hints of its own.
        self.quant_tabs = CurrentPageTabs()
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.quant_tabs.addTab(host, 'Monte Carlo')
        from .strategy import StrategyPane
        self.strategy = StrategyPane()
        self.strategy.requested.connect(lambda q: self.run_tool('strategy', q))
        self.quant_tabs.addTab(self.strategy, 'Strategy Lab')
        ws.canvas.addWidget(self.quant_tabs, 1)
        mc_side, strategy_side = ws.side, ws.add_side()
        ws.bind_tabs(self.quant_tabs, (("Monte Carlo", "몬테카를로"), ("Strategy Lab", "전략 실험실")),
                     sides=(mc_side, strategy_side),
                     on_change=lambda i: (self.quant_guide.set_key(('monte_carlo', 'strategy')[i]),
                                          getattr(self, 'quant_badge', None) is not None and
                                          self.quant_badge.setVisible(i == 0 and bool(self.quant_badge.text()))))
        self.quant_badge = ws.add_badge(("Simulation · not a guarantee", "시뮬레이션 · 미래 보장 아님"))
        self.symbol = QLineEdit("AAPL")
        self.symbol.setMaxLength(120)
        # Owner issues 04/12: no data-source selector; the app fetches by itself ("best": keyless Yahoo
        # before a labelled synthetic fallback). The combo stays, hidden, for tests and scripts.
        self.source = QComboBox()
        for text, value in [("Auto", "best"), ("Auto · KIS / FMP", "auto"), ("FMP", "fmp"), ("KIS · KRX", "kis"),
                            ("Synthetic demo", "synthetic")]:
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
        fields = (("Symbol", self.symbol), ("Model", self.model),
                  ("Drift", self.drift), ("Horizon · sessions", self.horizon), ("Paths", self.paths),
                  ("Seed", self.seed), ("ERP · %", self.erp), ("Target price", self.target))
        for name, widget in (*fields, ("Data source", self.source)):
            widget.setAccessibleName(name)
            if isinstance(widget, QComboBox):
                # Full option labels stay in the popup and selected tooltip; the column is narrow.
                widget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
                widget.setMinimumContentsLength(8)
                widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                widget.setToolTip(widget.currentText())
                widget.currentTextChanged.connect(widget.setToolTip)
                widget.model().dataChanged.connect(lambda *args, combo=widget: combo.setToolTip(combo.currentText()))
        from .form_layout import CompactFieldGrid, bound_input_panel
        box, inner = panel("분석 설정")
        bound_input_panel(box)
        self.quant_form = CompactFieldGrid([(label(name, "caption"), widget) for name, widget in fields])
        inner.addWidget(self.quant_form)
        inner.addWidget(self.source)
        self.source.hide()
        self.run_button = QPushButton("분포 분석 실행")
        self.run_button.setProperty("primary", True)
        self.run_button.clicked.connect(self.run_analysis)
        inner.addWidget(self.run_button)
        from .tools import dock_form
        settings = mc_side.add_page(("Settings", "설정"))
        dock_form(box, self.run_button, mc_side, page=settings)
        reading = Soft(("Reading the result", "결과를 읽는 법"),
                       ("Half of the paths stay inside the dark band and 90% inside the light one. A wider band means "
                        "the assumed volatility is larger.",
                        "진한 띠 안에 경로의 절반이, 옅은 띠 안에 90%가 들어와요. 띠가 넓을수록 가정한 변동성이 커요."))
        settings.addWidget(reading)
        guide_page = mc_side.add_page(("How to read", "읽는 법"))
        guide_page.addWidget(self.quant_guide)
        self.analysis_status = label("데이터 출처·시드·모델 가정을 기록합니다.", "caption")
        self.analysis_status.setProperty("reading_help_keep_visible", True)
        mc_side.foot.addWidget(self.analysis_status)
        self.strategy.dock_into(strategy_side, title=("Settings", "설정"))
        strategy_guide = strategy_side.add_page(("How to read", "읽는 법"))
        strategy_guide.addWidget(Soft(("Strategy Lab", "전략 실험실"),
                                      ("A backtest of the chosen rule on past prices, with costs. Past results are not a "
                                       "promise of future ones.",
                                       "고른 규칙을 과거 가격에 비용과 함께 시험해요. 과거 성과가 미래를 약속하지 않아요.")))
        ws.finish()
        # Canvas (Monte Carlo): lead line and key figures, the fan chart card, the metrics.
        self.quant_lead = Text("", "lead")
        self.quant_lead_note = Text("", "leadNote")
        self.quant_lead_row = QWidget()
        lead = QHBoxLayout(self.quant_lead_row); lead.setContentsMargins(0, 0, 0, 0); lead.setSpacing(8)
        lead.addWidget(self.quant_lead); lead.addWidget(self.quant_lead_note); lead.addStretch(1)
        self.quant_lead_row.hide()
        layout.addWidget(self.quant_lead_row)
        self.quant_figures = KeyFigures()
        self.quant_figures.hide()
        layout.addWidget(self.quant_figures)
        chart_card = Card()
        result_heading = label("분포와 근거", "heading")   # the result block's title (A3 contract)
        result_heading.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        chart_card.body.addWidget(result_heading, 0, Qt.AlignmentFlag.AlignTop)   # the accent bar stays at text height
        self.quant_chart = FanChart()
        self.quant_notes = label("아직 실행한 분석이 없습니다.", "muted")
        self.quant_notes.setProperty('reading_help_keep_visible', True)
        from .chart_study import ChartStudy, LocalLabel
        self.quant_study = ChartStudy(self.quant_chart, self.quant_notes)
        self.quant_empty = LocalLabel({'ko':'분석을 실행하면 가격 분포와 위험 지표가 여기에 나타나요.',
                                      'en':'Run the analysis to see the price distribution and risk metrics here.'}, 'muted')
        self.quant_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quant_empty.setMinimumHeight(280)
        chart_card.body.addWidget(self.quant_empty)
        chart_card.body.addWidget(self.quant_study)
        self.quant_metrics = table(["지표", "값"])
        self.quant_metrics.horizontalHeaderItem(0).setData(CAPTION_ROLE, 'Metric')
        self.quant_metrics.setProperty("localized_columns", [0])
        from .result_layout import fit_result_table
        fit_result_table(self.quant_metrics)
        chart_card.body.addWidget(self.quant_metrics)
        self.quant_study.hide();self.quant_metrics.hide()
        notice = label("계산 완료 ≠ 투자 검증. 이 화면은 NOT_RUN 판정을 유지하며 주문이나 전략 원장을 생성하지 않습니다.", "caption")
        notice.setProperty('reading_help_keep_visible', True)
        chart_card.body.addWidget(notice)
        layout.addWidget(chart_card, 1)
        self.quant_kit_language()

    def quant_kit_language(self):
        self.kit_language()

    def kit_language(self):
        """The page kit's pieces (page_kit.Workspace) follow the window language; the rest of each page is translated by
        the LanguageController as before."""
        from .page_kit import Workspace
        for workspace in self.findChildren(Workspace):
            workspace.set_language(getattr(self, "ui_language", "ko"))

    def quant_show_figures(self, value):
        """The run's lead line and key figures over the fan chart (draft: 'AAPL · GARCH(1,1)-t · 126거래일 · 경로 5,000개',
        then 시작 · 중앙값 · 하위 5% · 상위 5% · 손실 확률 · 95% VaR)."""
        r = value.result
        params = value.run.get("parameters", {})
        model = self.model.itemText(max(0, self.model.findData(params.get("model", self.model.currentData()))))
        self.quant_lead.set_pair(str(params.get("symbol", "")))
        self.quant_lead_note.set_pair((f"· {model} · {r.horizon_days} sessions · {r.n_paths:,} paths",
                                       f"· {model} · {r.horizon_days}거래일 · 경로 {r.n_paths:,}개"))
        self.quant_figures.set_items((
            (("Start", "시작"), f"{r.spot:,.2f}", ""),
            (("Median", "중앙값"), f"{r.median_terminal:,.2f}", ""),
            (("Lower 5%", "하위 5%"), f"{r.p05:,.2f}", "down"),
            (("Upper 5%", "상위 5%"), f"{r.p95:,.2f}", "up"),
            (("P(loss)", "손실 확률"), f"{r.prob_loss:.1%}", ""),
            (("95% VaR", "95% VaR"), f"{r.var_pct:.1%}".replace("-", "−"), "")))
        self.quant_figures.show()
        self.quant_lead_row.show()
        self.quant_badge.set_pair(("Run complete · NOT_RUN", "계산 완료 · 검증 NOT_RUN"))
        self.quant_badge.set_tone("ok")
        self.quant_kit_language()

    def make_risk(self):
        """Portfolio & Risk (owner-approved draft 2026-11-17, docs/product/ui_drafts_2026-11-17/draft_05_risk.png): the
        stock detail's frame, as Build & Test. Toolbar: title, 포트폴리오 | 기술적 분석 | 모의투자 driving risk_tabs (kept
        for callers and tests), the tab's scope badge, then the portfolio run's status badge and its exports (결과 저장 ·
        보고서 ZIP). 포트폴리오: the canvas reads the result (PortfolioPane: lead line, key figures, frontier, weights and
        comparison cards, the reading); the right column holds the settings in two folds and the per-symbol Monte Carlo
        rows (risk_table / risk_empty) in a third, the run button pinned with the scope line; 읽는 법 holds the workspace
        guide, which follows the tab. 기술적 분석: SignalsPane docked (ToolPane.dock_into). 모의투자: PaperPane, its engine
        controls in the right column (PaperPane.dock_into); the rail's emergency stop stays. Every attribute, signal,
        request, calculation and export is as before."""
        from .page_kit import Badge, Button, Card, EmptyState, Fold, Soft, Workspace, rule
        from .portfolio import PortfolioPane
        from .signals import SignalsPane
        from .paper import PaperPane
        from .research_style import prepare_page
        from .workspace_guide import WorkspaceGuide
        from .risk_page import READINGS, EnabledMirror, ResultEmptyState, ToolbarFit, run_rows_table
        outer = self.page(None, None)
        self.risk_page = prepare_page(outer)
        self.risk_page.setMaximumWidth(16777215)
        scroll = self.stack.widget(self.stack.count() - 1)
        self.risk_workspace = ws = Workspace(("Portfolio & Risk", "분석"))
        outer.addWidget(ws)
        ws.fit_to(scroll)
        self.portfolio = PortfolioPane()
        self.portfolio.requested.connect(self.run_portfolio)
        self.signals=SignalsPane();self.signals.requested.connect(lambda q:self.run_tool('signals',q))
        self.paper = PaperPane(self.paper_session)
        self.paper.setProperty("reading_help_keep_visible", True)
        self.risk_tabs=CurrentPageTabs();self.risk_tabs.addTab(self.portfolio,'Portfolio');self.risk_tabs.addTab(self.signals,'Signals')
        self.risk_tabs.addTab(self.paper, 'Paper Trading')
        # As tall as the selected page: the canvas scrolls by itself when a result is longer than the window.
        self.risk_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        ws.canvas.addWidget(self.risk_tabs, 1)
        portfolio_side, signals_side, paper_side = ws.side, ws.add_side(), ws.add_side()
        self.risk_guide = WorkspaceGuide('portfolio')
        # 포트폴리오, right column: 자산 구성 · 목적함수·제약 (PortfolioPane) and the Monte Carlo rows; 읽는 법.
        settings = portfolio_side.add_page(("Settings", "설정"))
        self.portfolio.dock_into(portfolio_side, page=settings)
        settings.addWidget(rule())
        self.risk_fold = Fold(("Individual price simulation risk", "개별 가격 시뮬레이션 위험"))
        self.risk_table = run_rows_table(["Symbol", "Model", "P(loss)", "VaR 95", "CVaR", "Source"])
        self.risk_table.setProperty('localized_columns', [1])
        self.risk_table._qg_status_columns = {5: 'official'}   # SYNTHETIC -> 합성 데이터(SYNTHETIC)
        self.risk_fold.body.addWidget(self.risk_table)
        # Until a Monte Carlo run completes, say where the rows come from instead of an empty table.
        self.risk_empty = label("No Monte Carlo run in this session yet. Run one under Build & Test → Monte Carlo; "
                                "each completed run adds a row here.", "caption")
        self.risk_empty.localized_text = {
            "ko": "이번 세션에 실행한 몬테카를로 분석이 아직 없어요. 설계/검증 → 몬테카를로에서 분석을 실행하면 완료된 "
                  "실행마다 여기에 한 줄씩 추가돼요.",
            "en": self.risk_empty.source_text}
        self.risk_empty.retranslate()
        self.risk_empty.setProperty("reading_help_keep_visible", True)
        self.risk_fold.body.addWidget(self.risk_empty)
        notice = label("각 행은 개별 가격 시뮬레이션입니다. 포트폴리오 전체 위험이나 전략 백테스트가 아닙니다.", "caption")
        notice.localized_text = {"ko": "설계/검증에서 실행한 개별 가격 시뮬레이션이에요. 포트폴리오 전체 위험이나 "
                                       "전략 백테스트가 아니에요.",
                                 "en": "Individual price simulations run under Build & Test; not portfolio-wide risk "
                                       "or a strategy backtest."}
        notice.retranslate()
        notice.setProperty("reading_help_keep_visible", True)
        self.risk_fold.body.addWidget(notice)
        holder = QFrame(); holder.setObjectName("dockedForm")      # the column's transparent form surface
        box = QVBoxLayout(holder); box.setContentsMargins(2, 0, 2, 0); box.addWidget(self.risk_fold)
        settings.addWidget(holder)
        model = self.risk_table.model()
        for signal in (model.rowsInserted, model.rowsRemoved, model.modelReset):
            signal.connect(self.risk_count_runs)
        self.risk_guide_pages = [portfolio_side.add_page(("How to read", "읽는 법"))]
        # 기술적 분석: the form in the right column, the run button pinned; the result and its exports in the canvas.
        self.signals.dock_into(signals_side, title=("Settings", "설정"))
        self.signals_empty = Card()
        self.signals_empty.setMinimumHeight(320)
        self.signals_empty.body.addWidget(EmptyState(
            ("Press [Run analysis] to see the composite score, each indicator's score and a costed backtest here.",
             "[분석 실행]을 누르면 종합 점수, 지표별 점수, 비용을 뺀 백테스트가 여기에 나타나요.")))
        self.signals.layout().insertWidget(1, self.signals_empty)
        ResultEmptyState(self.signals, self.signals_empty)
        self.risk_guide_pages.append(signals_side.add_page(("How to read", "읽는 법")))
        # 모의투자: engine controls in the right column, 모의 세션 읽기 pinned; the tables in the canvas.
        self.paper.dock_into(paper_side, title=("Controls", "제어"))
        self.risk_guide_pages.append(paper_side.add_page(("How to read", "읽는 법")))
        self.risk_guide_pages[0].addWidget(self.risk_guide)
        for page, (title, text) in zip(self.risk_guide_pages, READINGS):
            page.addWidget(Soft(title, text))
        ws.finish()
        ws.bind_tabs(self.risk_tabs, (("Portfolio", "포트폴리오"), ("Technical analysis", "기술적 분석"),
                                      ("Paper trading", "모의투자")),
                     sides=(portfolio_side, signals_side, paper_side), on_change=self.risk_tab_changed)
        scope = QWidget()                      # the tab's scope badge; steps aside when the toolbar is narrow
        scope_row = QHBoxLayout(scope); scope_row.setContentsMargins(0, 0, 0, 0)
        self.risk_scope_badge = Badge()
        scope_row.addWidget(self.risk_scope_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        ws.add_toolbar(scope)
        # The portfolio run's status and its exports (the pane's own buttons stay, hidden, for the same report).
        actions = QWidget()
        row = QHBoxLayout(actions); row.setContentsMargins(0, 0, 0, 0); row.setSpacing(8)
        row.addWidget(self.portfolio.badge, 0, Qt.AlignmentFlag.AlignVCenter)
        self.risk_save = Button(("Save result", "결과 저장"), "ghost")
        self.risk_zip = Button(("Report ZIP", "보고서 ZIP"), "secondary")
        exports = self.portfolio.exports
        for button, source, bundle in ((self.risk_save, exports.json_button, False), (self.risk_zip, exports.zip_button, True)):
            button.clicked.connect(lambda checked=False, b=bundle: self.portfolio.exports.save(b))
            EnabledMirror(source, button)
            row.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
        exports.hide()
        self.risk_portfolio_actions = ws.add_toolbar(actions, right=True)
        self.risk_toolbar_fit = ToolbarFit(ws, scope, actions, ws.toolbar_right, self.portfolio.lead_actions)
        self.risk_tab_changed(self.risk_tabs.currentIndex())
        self.kit_language()

    def risk_count_runs(self, *args):
        """'개별 가격 시뮬레이션 위험 2건': the fold's count follows the rows refresh_views writes."""
        try:
            rows = self.risk_table.rowCount()
            self.risk_fold.set_count((f"{rows}", f"{rows}건") if rows else "")
        except RuntimeError:   # the window is being destroyed
            pass

    def risk_tab_changed(self, index):
        """The guide follows the tab (its key and its place in that tab's 읽는 법); the toolbar shows the tab's scope
        badge, and the portfolio's status and exports only on 포트폴리오."""
        from .risk_page import SCOPE_BADGES, TAB_KEYS
        if not 0 <= index < len(TAB_KEYS):
            return
        self.risk_guide.set_key(TAB_KEYS[index])
        pages = getattr(self, 'risk_guide_pages', ())
        if index < len(pages) and pages[index].indexOf(self.risk_guide) < 0:
            for page in pages:
                page.removeWidget(self.risk_guide)
            pages[index].insertWidget(0, self.risk_guide)
        if hasattr(self, 'risk_scope_badge'):
            self.risk_scope_badge.set_pair(SCOPE_BADGES[index])
        if hasattr(self, 'risk_portfolio_actions'):
            self.risk_portfolio_actions.setVisible(index == 0)

    def make_library(self):
        """Research Library (owner-approved draft 2026-11-17, docs/product/ui_drafts_2026-11-17/draft_06_library.png).
        Toolbar: title, '이번 앱 세션의 실행 근거', the no-autosave badge and a search over the runs. Canvas: the session's
        lead line and counts, the runs card (filter pills 전체 · 몬테카를로 · 포트폴리오 · 전략 and the run rows), then a
        preview of the selected run. Right column: 실행 상세 (run information, the reproducibility checklist read from
        the record, the AI 해설 fold) | 읽는 법, with the two exports pinned at the bottom. `run_table` keeps the
        ResearchRun rows, their status roles and the selection the exports save; it is hidden behind the row list, which
        drives it. Nothing is saved automatically and nothing is sent without the user's action."""
        from .commentary import CommentaryPane
        from .library_view import (KINDS, CheckList, ExportRow, InfoGrid, LibraryWorkspace, RunList, SearchField,
                                   preview_chart)
        from .page_kit import Button, Card, EmptyState, Fold, KeyFigures, Pill, PillTabs, Soft, Text, rule
        outer = self.page(None, None)
        scroll = self.stack.widget(self.stack.count() - 1)
        self.library_workspace = ws = LibraryWorkspace(("Research Library", "연구 보관함"))
        outer.addWidget(ws)
        ws.fit_to(scroll)
        self.library_saved = set()               # ResearchRun ids saved from this page in this session
        self.library_started = datetime.now(timezone.utc)
        self.library_selected = ""
        self.library_chosen = False              # True once the user picked a row; until then the newest result shows
        self.library_rows = []
        self._library_syncing = False
        # Toolbar
        self.library_caption = ws.add_toolbar(Text(("Run evidence of this app session", "이번 앱 세션의 실행 근거"), "sub"))
        self.library_badge = ws.add_badge(("No autosave · save before closing", "자동 저장 안 함 · 종료 전에 저장하세요"),
                                          "warn")
        ws.optional_toolbar.append(self.library_caption)
        self.library_search = SearchField()
        ws.add_toolbar(self.library_search, right=True)
        ws.on_theme(self.library_search)
        # Canvas: lead line, counts, the runs card, the preview card.
        lead_row = QWidget()
        lead = QHBoxLayout(lead_row)
        lead.setContentsMargins(2, 0, 0, 0)
        lead.setSpacing(8)
        self.library_lead = Text("", "lead")
        self.library_lead_note = Text("", "leadNote", wrap=True)
        lead.addWidget(self.library_lead, 0, Qt.AlignmentFlag.AlignTop)
        lead.addWidget(self.library_lead_note, 1)
        ws.canvas.addWidget(lead_row)
        self.library_counts = KeyFigures()
        ws.canvas.addWidget(self.library_counts)
        runs_card = Card(margins=(10, 10, 10, 8), spacing=4)
        head = QHBoxLayout()
        head.setContentsMargins(2, 0, 6, 0)
        head.setSpacing(8)
        self.library_filter = PillTabs([("All", "전체")] + [("", "") for _ in KINDS])
        head.addWidget(self.library_filter, 1)
        sort = Text(("Newest first", "최신순"), "")
        sort.setProperty("lib", "sort")
        head.addWidget(sort, 0, Qt.AlignmentFlag.AlignVCenter)
        runs_card.body.addLayout(head)
        self.library_list = RunList()
        ws.follow(self.library_list)
        ws.on_theme(self.library_list)
        self.library_list.selected.connect(self.library_select)
        self.library_filter.changed.connect(lambda index: (self.library_list.set_kind((("all",) + KINDS)[index]),
                                                           self.library_empty_text()))
        self.library_search.textChanged.connect(lambda text: (self.library_list.set_query(text), self.library_empty_text()))
        runs_card.body.addWidget(self.library_list)
        runs_card.body.addWidget(rule())
        list_note = Text(("Only results calculated in this session · verdict NOT_RUN · frozen studies, past ledgers and "
                          "secret settings are not inspected",
                          "이번 세션에서 계산한 결과만 보여요 · 검증 NOT_RUN · 동결 연구·과거 원장·비밀 설정은 탐색하지 않아요"),
                         "", wrap=True)
        list_note.setProperty("lib", "foot")
        list_note.setContentsMargins(6, 0, 6, 0)
        list_note.setProperty("reading_help_keep_visible", True)
        runs_card.body.addWidget(list_note)
        ws.canvas.addWidget(runs_card)
        # The ResearchRun table keeps its columns, status roles and selection for callers, tests and the two exports.
        # Owner-approved draft 2026-11-17: the row list above shows the same runs in the approved look and selects here.
        self.run_table = table(["Symbol", "Model", "실행 상태", "검증 판정", "생성 시각 · UTC"])
        self.run_table._qg_status_columns = {2: 'execution', 3: 'official'}
        self.run_table.setProperty('localized_columns', [1])
        self.run_table.setMinimumHeight(280)
        self.run_table.itemSelectionChanged.connect(self.library_table_selected)
        self.run_table.hide()
        ws.canvas.addWidget(self.run_table)
        self.library_preview = Card(("", ""), ("", ""), margins=(18, 12, 16, 10), spacing=6)
        self.library_preview.note.setWordWrap(True)     # a narrow canvas wraps the run's settings, never widens it
        head = self.library_preview.head
        head.takeAt(head.count() - 1)                   # the note, not a spacer, takes the head's spare width
        head.setStretchFactor(self.library_preview.note, 1)
        self.library_open = Button(("Go to Build & Test ›", "설계/검증으로 이동 ›"), "")
        self.library_open.setProperty("lib", "link")
        self.library_open.clicked.connect(self.library_open_source)
        self.library_preview.add_head_widget(self.library_open)
        self.library_preview_figures = KeyFigures()
        self.library_preview.body.addWidget(self.library_preview_figures)
        self.library_chart = preview_chart()
        self.library_preview.body.addWidget(self.library_chart, 1)
        self.library_preview_text = Text("", "hint", wrap=True)
        self.library_preview.body.addWidget(self.library_preview_text)
        self.library_preview_empty = EmptyState("")
        self.library_preview_empty.setMinimumHeight(170)
        self.library_preview.body.addWidget(self.library_preview_empty, 1)
        self.library_preview_note = Text("", "fine", wrap=True)
        self.library_preview_note.setProperty("reading_help_keep_visible", True)
        self.library_preview.body.addWidget(self.library_preview_note)
        self.library_preview.body.addStretch(0)       # without a chart the preview's lines sit at the top
        ws.canvas.addWidget(self.library_preview, 1)
        # Right column: 실행 상세 | 읽는 법, the exports pinned at the bottom.
        details = ws.side.add_page(("Run details", "실행 상세"))
        self.library_side_empty = Soft(("Run details", "실행 상세"),
                                       ("Choose a run in the list: its information and reproducibility records show here.",
                                        "목록에서 실행을 고르면 그 실행의 정보와 재현성 기록이 여기에 보여요."))
        details.addWidget(self.library_side_empty)
        self.library_info_fold = Fold(("Run information", "실행 정보"))
        self.library_info_pill = Pill("", "ok")
        self.library_info_fold.head.layout().addWidget(self.library_info_pill, 0, Qt.AlignmentFlag.AlignVCenter)
        self.library_info = InfoGrid()
        self.library_info_fold.body.addWidget(self.library_info)
        self.library_rules = (rule(), rule())
        self.library_repro_fold = Fold(("Reproducibility", "재현성"))
        self.library_repro_pill = Pill("", "warn")
        self.library_repro_fold.head.layout().addWidget(self.library_repro_pill, 0, Qt.AlignmentFlag.AlignVCenter)
        self.library_repro_fold.head.digest.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.library_checks = CheckList()
        self.library_repro_fold.body.addWidget(self.library_checks)
        self.library_ai_fold = Fold(("AI commentary", "AI 해설"), count=("optional", "선택 기능"))
        options = {'runner': self.commentary_runner} if self.commentary_runner else {}
        self.commentary = CommentaryPane(self.commentary_sources, **options)
        self.commentary.setProperty("reading_help_keep_visible", True)
        self.library_ai_fold.body.addWidget(self.commentary)
        self.commentary.dock(self.library_ai_fold)
        ws.follow(self.commentary)
        for widget in (self.library_info_fold, self.library_rules[0], self.library_repro_fold, self.library_rules[1],
                       self.library_ai_fold):
            details.addWidget(widget)
        for fold in (self.library_info_fold, self.library_repro_fold, self.library_ai_fold):
            fold.body_host.setProperty("lib", "plain")
        reading = ws.side.add_page(("How to read", "읽는 법"))
        for title, text in (
                (("What the list holds", "이 목록에 있는 것"),
                 ("Only calculations run in this app session: one row per Monte Carlo run, and the latest portfolio and "
                  "strategy result of their pages. The list empties when the app closes.",
                  "이번 앱 세션에서 실행한 계산만 보여요. 몬테카를로는 실행마다 한 줄, 포트폴리오와 전략은 각 화면의 마지막 결과가 "
                  "한 줄이에요. 앱을 닫으면 목록이 비워져요.")),
                (("Status and verdict", "상태와 판정"),
                 ("Completed means the calculation finished. Verdict NOT_RUN means no official validation ran; a result "
                  "is neither an investment validation nor advice.",
                  "완료는 계산이 끝났다는 뜻이에요. 검증 판정 NOT_RUN은 공식 검증을 하지 않았다는 뜻이고, 결과는 투자 검증이나 "
                  "권유가 아니에요.")),
                (("Reproducibility", "재현성"),
                 ("Each run records its seed, a hash of the calculation code, a fingerprint of the prices and the runtime. "
                  "Data vintage and licence are not verified, so reproducibility stays PARTIAL.",
                  "실행마다 난수 시드, 계산 코드 해시, 가격 자료 지문, 실행 환경을 기록해요. 데이터 빈티지와 라이선스는 확인하지 "
                  "않아 재현성은 PARTIAL로 남아요.")),
                (("Saving", "저장"),
                 ("Nothing is saved automatically. Save the selected run as ResearchRun JSON or as a report ZIP; you "
                  "choose the path.",
                  "자동으로 저장하지 않아요. 고른 실행을 ResearchRun JSON이나 보고서 ZIP으로 저장하세요. 경로는 직접 골라요."))):
            reading.addWidget(Soft(title, text))
        codes = Text(("Reproducibility PARTIAL · data vintage/licence unverified · costs NOT_APPLIED · verdict NOT_RUN",
                      "재현성 PARTIAL · 데이터 빈티지/라이선스 미검증 · 비용 NOT_APPLIED · 검증 NOT_RUN"), "fine", wrap=True)
        codes.setProperty("reading_help_keep_visible", True)
        reading.addWidget(codes)
        self.save_json = Button(("Save ResearchRun JSON", "ResearchRun JSON 저장"), "secondary")
        self.save_bundle = Button(("Save report + JSON ZIP", "보고서 + JSON ZIP 저장"), "primary")
        self.save_json.clicked.connect(lambda:self.export_selected(False))
        self.save_bundle.clicked.connect(lambda:self.export_selected(True))
        self.library_exports = ExportRow((self.save_json, self.save_bundle))
        ws.side.foot.addWidget(self.library_exports)
        ws.follow(self.library_exports)
        self.library_export_hint = Text(("Save this result with the export on its own page.",
                                         "이 결과는 해당 화면의 저장 버튼으로 저장해요."), "fine", wrap=True)
        self.library_export_hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.library_export_hint.hide()
        ws.side.foot.addWidget(self.library_export_hint)
        self.export_status = label("선택한 실행만 저장해요 · 자동 저장되지 않으며 경로는 직접 골라요", "caption")
        self.export_status.localized_text = {"ko": "선택한 실행만 저장해요 · 자동 저장되지 않으며 경로는 직접 골라요",
                                             "en": "Only the selected run is saved · nothing is saved automatically and you "
                                                   "choose the path"}
        self.export_status.retranslate()
        self.export_status.setProperty("kit", "fine")
        self.export_status.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.export_status.setProperty("reading_help_keep_visible", True)
        ws.side.foot.addWidget(self.export_status)
        ws.finish()
        self.setTabOrder(self.library_search, self.library_filter.buttons[0])
        self.setTabOrder(self.library_filter.buttons[-1], self.library_list)
        self.setTabOrder(self.library_list, self.library_open)
        self.library_workspace.set_language(self.ui_language)

    def library_refresh(self):
        """Fill the Research Library from the session (display only; nothing is fetched): the lead line, the counts, the
        filter counts, the rows, then the selected run, which the run table follows."""
        from .library_view import KIND_NAMES, KINDS, counts, entries
        rows = entries(self.session.runs(), saved=self.library_saved, portfolio=self.portfolio.exports.report,
                       strategy=self.strategy.report)
        self.library_rows = rows
        self.library_list.set_entries(rows)
        language = self.library_workspace.language
        n = len(rows)
        self.library_lead.set_pair((f"{n} run{'s' if n != 1 else ''} this session", f"이번 세션 실행 {n}건"))
        started = self.library_started.strftime("%Y-%m-%d %H:%M")
        self.library_lead_note.set_pair((f"· started {started} UTC · the list empties when the app closes",
                                         f"· {started} UTC 시작 · 앱을 닫으면 목록이 비워져요"))
        c = counts(rows, self.library_saved)
        items = [(("Completed", "완료"), str(c["completed"]), ""), (("Running", "실행 중"), str(c["running"]), ""),
                 (("Failed", "실패"), str(c["failed"]), "err" if c["failed"] else ""),
                 (("Saved", "저장함"), str(c["saved"]), ""), (("Not saved", "저장 전"), str(c["unsaved"]), "")]
        if c["reproducibility"]:
            items.append((("Reproducibility", "재현성"), c["reproducibility"], ""))
        if c["verdict"]:
            items.append((("Verdict", "검증 판정"), c["verdict"], ""))
        self.library_counts.set_items(items)
        per = {kind: sum(row.kind == kind for row in rows) for kind in KINDS}
        pairs = [(f"All  {n}", f"전체  {n}")] + [(f"{KIND_NAMES[k][0]}  {per[k]}", f"{KIND_NAMES[k][1]}  {per[k]}")
                                                for k in KINDS]
        for button, pair in zip(self.library_filter.buttons, pairs):
            button.set_pair(pair)
        self.library_filter.set_language(language)
        self.library_empty_text()
        keys = [row.key for row in rows]
        if self.library_selected not in keys or not self.library_chosen:
            self.library_selected = next((row.key for row in rows if row.status == "COMPLETED"), keys[0] if keys else "")
        self.library_list.select(self.library_selected)
        self._library_sync_table()
        self.library_show()

    def library_empty_text(self):
        searching = bool(self.library_search.text().strip()) or self.library_filter.current() > 0
        self.library_list.set_empty(("No run matches the filter.", "조건에 맞는 실행이 없어요.")
                                    if searching and self.library_rows else
                                    ("No calculation has run in this session yet.", "아직 이번 세션에 실행한 계산이 없어요."))

    def library_select(self, key):
        """A row chosen in the list: the run table follows (its selection is what the two exports save)."""
        self.library_selected, self.library_chosen = key, True
        self.library_list.select(key)
        self._library_sync_table()
        self.library_show()

    def _library_sync_table(self):
        self._library_syncing = True
        try:
            for row in range(self.run_table.rowCount()):
                item = self.run_table.item(row, 0)
                if item is not None and item.data(Qt.ItemDataRole.UserRole) == self.library_selected:
                    self.run_table.selectRow(row)
                    break
            else:
                self.run_table.clearSelection()
                self.run_table.setCurrentItem(None)
        finally:
            self._library_syncing = False

    def library_table_selected(self):
        """A run selected in the run table (by a caller or a test): the list and the preview follow."""
        if self._library_syncing:
            return
        row = self.run_table.currentRow()
        item = self.run_table.item(row, 0) if row >= 0 else None
        key = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if key and key != self.library_selected:
            self.library_selected, self.library_chosen = key, True
            self.library_list.select(key)
            self.library_show()

    def library_show(self):
        """The selected row's preview card and its evidence in the right column, read from its record."""
        from .library_view import preview_content, side_content
        from .page_kit import pick
        entry = self.library_list.entry(self.library_selected)
        language = self.library_workspace.language
        chosen = entry is not None
        self.library_side_empty.setVisible(not chosen)
        for widget in (self.library_info_fold, self.library_repro_fold, *self.library_rules):
            widget.setVisible(chosen)
        report_row = chosen and entry.kind != "monte_carlo"
        for button in (self.save_json, self.save_bundle):
            button.setEnabled(not report_row)
        self.library_export_hint.setVisible(report_row)
        content = preview_content(entry, bool(self.library_rows))
        preview = self.library_preview
        preview.title.set_pair(content["title"])
        preview.note.set_pair(content["note"])
        preview.note.setVisible(chosen)
        self.library_open.set_pair(content["open"])
        self.library_open.setVisible(chosen)
        self.library_preview_empty.text.set_pair(content["empty"])
        self.library_preview_empty.setVisible(not chosen)
        self.library_preview_figures.set_items(content["figures"])
        output = self.outputs.get(entry.record.get("run_id")) if content["chart"] else None
        result = getattr(output, "result", None)
        self.library_chart.set_result(result)
        self.library_chart.setVisible(result is not None)
        self.library_preview_text.set_pair(content["text"])
        self.library_preview_text.setVisible(bool(content["text"][0]))
        self.library_preview_note.set_pair(content["foot"])
        self.library_preview_note.setVisible(bool(content["foot"][0]))
        if chosen:
            side = side_content(entry)
            self.library_info_pill.set_pair(side["status"])
            self.library_info_pill.set_tone(side["status_tone"])
            from .stock_detail_style import set_prop
            set_prop(self.library_info_pill, "pill", "live" if entry.status == "RUNNING" else "")
            self.library_info.set_rows(side["info"], language)
            self.library_checks.set_checks(side["checks"], language)
            # In the head's digest, which shortens before it would push the pill out of a narrow column.
            self.library_repro_fold.head.digest.set_choices([pick(language, pair) for pair in side["count"]])
            self.library_repro_pill.set_pair(side["reproducibility"])
            self.library_repro_pill.set_tone(side["reproducibility_tone"])
        for widget in (preview, self.library_open, self.library_info_pill, self.library_repro_pill,
                       self.library_repro_fold, self.library_preview_empty, self.library_preview_text,
                       self.library_preview_note):
            widget.set_language(language)

    def library_open_source(self):
        """'…으로 이동 ›': the page the selected result came from (navigation only; nothing is re-run)."""
        entry = self.library_list.entry(self.library_selected)
        if entry is None:
            return
        if entry.kind == "portfolio":
            self.navigate("risk")
            self.risk_tabs.setCurrentIndex(0)
        else:
            self.navigate("quant")
            self.quant_tabs.setCurrentIndex(1 if entry.kind == "strategy" else 0)

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
        self.locale_notice.setProperty("reading_help_keep_visible", True)
        inner.addWidget(self.locale_notice)
        layout.addWidget(box)
        from .connections import ConnectionsPane
        self.connections = ConnectionsPane()
        self.connections.setProperty("reading_help_keep_visible", True)
        self.connections.requested.connect(lambda q: self.run_tool('connections', q))
        from .paper import RulesPane
        self.rules = RulesPane(self.paper_session)
        self.rules.setProperty("reading_help_keep_visible", True)
        self.system_tabs = QTabWidget()
        self.system_tabs.addTab(self.connections, 'Connections')
        self.system_tabs.addTab(self.rules, 'Rules')
        from .data_rights import DataRightsPane
        self.data_rights=DataRightsPane(self.ctx)
        self.data_rights.setProperty("reading_help_keep_visible", True)
        self.system_tabs.addTab(self.data_rights,self.ctx.t('data_rights'))
        layout.addWidget(self.system_tabs)
        box, inner = panel("프로젝트 상태")
        box.setProperty("reading_help_keep_visible", True)
        box.setProperty("recorded_project_status", True)
        try:
            status = verify(application_root())
        except (OSError, ValueError, KeyError, TypeError, YAMLError):
            status = None
        for line in recorded_status_display(status):
            item = label(line.en, 'muted' if line.muted else '')
            item.localized_text = {'en': line.en, 'ko': line.ko}
            inner.addWidget(item)
            item.retranslate()
        layout.addWidget(box)
        box, inner = panel("데스크톱 이전 상태")
        box.setProperty("reading_help_keep_visible", True)
        inner.addWidget(label("PyQt6 네이티브: Home, Markets(관심종목 차트·종목 한 화면), 분석 도구(Bonds, Rates, FX, Structuring, Macro sheet, Macro v2, Derivatives, ETF, Crypto, KRX), 기술지표 가이드, Monte Carlo, Strategy Lab, 포트폴리오, Signals, Library·저장, 연결 설정, System\n모의매매·규칙·선택 AI 해설 연결 완료 / 남은 검증: 실제 Windows 표시·DPI·설치\n브라우저: 기존 Flet 앱을 유지합니다."))
        inner.addWidget(label("이번 데스크톱은 선택 실행하는 미리보기입니다. 전체 기능 이전 완료본이 아닙니다.", "muted"))
        layout.addWidget(box)
        layout.addStretch()

    def navigate(self, route):
        """Show a page and close the market disclosure; keep each page's reading position."""
        if route != 'home' and hasattr(self, 'home_feed') and self.home_feed.active:
            self.home_feed.stop()
        self.rail_flyouts.close_all()
        self.stack.setCurrentIndex(self.route_indices[route])
        for name, button in self.nav.items(): button.setChecked(name == route)
        self.sync_market_section()
        visited = getattr(self, '_visited_routes', set())
        if route not in visited:
            visited.add(route)
            self._visited_routes = visited
            scroll = self.stack.currentWidget()
            focused=QApplication.focusWidget()
            if focused is not None and scroll.isAncestorOf(focused):
                scroll.setFocus(Qt.FocusReason.OtherFocusReason)
            # Qt may scroll to the first input as a page is first shown. Start
            # at its purpose/header; subsequent visits retain the reading place.
            self._first_visit_scroll = scroll
            if not hasattr(self, '_navigation_scroll_timer'):
                # An owned timer is cancelled when the window is destroyed.
                # A free singleShot closure can outlive the underlying Qt stack.
                self._navigation_scroll_timer = QTimer(self)
                self._navigation_scroll_timer.setSingleShot(True)
                self._navigation_scroll_timer.timeout.connect(self._show_first_page_top)
            self._navigation_scroll_timer.start(0)

    def _show_first_page_top(self):
        scroll = self._first_visit_scroll
        if self.stack.currentWidget() is scroll:
            scroll.verticalScrollBar().setValue(0)
        self._first_visit_scroll = None

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
        self.indicator_guide.set_market_snapshot(snapshot,self.market_chart.supply)
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
        self.markets_content.setCurrentWidget(self.markets_view)
        self.market_asset_category=None
        self.sync_market_section()
        scroll = self.stack.widget(self.route_indices['markets'])
        if self.markets_view.showing_stock():
            def reveal():
                if self.stack.currentWidget() is scroll:
                    top = self.market_chart.mapTo(scroll.widget(), self.market_chart.rect().topLeft()).y()
                    scroll.verticalScrollBar().setValue(max(0, top - 120))
            QTimer.singleShot(0, reveal)
        elif hasattr(self.markets_view, 'focus_search'):
            self.markets_view.focus_search()  # a coin page gives way to a stock market's search (UI-D10 review)
        else:
            self.markets_view.search.setFocus(Qt.FocusReason.OtherFocusReason)

    def open_stock_chart(self, symbol):
        """A Home row opens that stock's screen on Markets (it loads when automatic refresh is on)."""
        from core.market.models import Instrument
        self.navigate('markets')
        self.markets_content.setCurrentWidget(self.markets_view)
        self.market_asset_category=None
        self.markets_view.open_instrument(Instrument('domestic_stock', symbol))
        self.sync_market_section()
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
        self.guide_subtitle.setText(self.indicator_guide.intro_text())
        self.watchlist.set_locale(self.ctx)
        self.market_chart.set_locale(self.ctx)
        self.markets_view.set_locale(self.ctx)
        for destination in self.market_destinations.values():destination.set_locale(self.ctx)
        self.kit_language()
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
        self.retitle_market_sections()
        self.fit_sidebar()

        if hasattr(self, 'reading_help'):
            self.reading_help.set_locale(self.ctx)

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
            self.quant_empty.hide();self.quant_study.show();self.quant_metrics.show()
            self.quant_show_figures(value)
            r, h = value.result, value.history
            vol_info = volatility_disclosure(r)
            table_rows(self.quant_metrics, [("Spot", f"{r.spot:,.2f}"), ("P5 / P50 / P95", f"{r.p05:,.2f} / {r.median_terminal:,.2f} / {r.p95:,.2f}"),
                (vol_info["label"], f"{vol_info['value']:.1%}"),
                ("P(loss)", f"{r.prob_loss:.1%}"), ("VaR 95 / CVaR", f"{r.var_pct:.1%} / {r.cvar_pct:.1%}"),
                ("Paths / horizon / seed", f"{r.n_paths:,} / {r.horizon_days} / {value.run['parameters']['seed']}"),
                ("P(terminal ≥ target)", "—" if r.prob_target is None else f"{r.prob_target:.1%}")] +
                ([("Horizon-average vol (ann.)", f"{r.garch_horizon_vol:.1%}")] if r.garch is not None else []))
            # (group, line): the plain lines are the source text; the display groups them under short
            # headings with a Korean reading per line (owner issues 11 and 14). Display only.
            entries = [("data", f"{'합성 데이터 · ' if h.source=='SYNTHETIC' else ''}{h.source} · {h.first_date} → {h.last_date}"),
                       ("data", h.note), ("assumptions", value.funding_note), ("assumptions", r.drift_note),
                       ("assumptions", r.bound_note), ("assumptions", r.jump_note)]
            resampling = bootstrap_disclosure(r.model)   # None for every model but bootstrap
            if resampling is not None:
                entries.append(("assumptions", resampling["description"]))
            entries.append(("volatility", vol_info["description"]))
            if vol_info["horizon_basis"]:
                entries.append(("volatility", "Horizon-average volatility: " + vol_info["horizon_basis"]))
            if r.prob_target is not None:
                entries.append(("volatility", f"Target probability: final price >= {r.target:,.2f} after {r.horizon_days} sessions. Only the final session is used."))
            if r.garch is not None:
                fit = r.garch
                entries.append(("garch", f"GARCH fit: alpha={fit.alpha:.4f}, beta={fit.beta:.4f}, nu={fit.nu:.3f}"))
                entries.append(("garch", f"converged={fit.converged} · persistence={fit.persistence:.4f} · half-life={fit.half_life:.2f} sessions"))
                for field in ("at_bound", "note", "se_note", "interval_at_bound"):
                    info = getattr(fit, field)
                    if info: entries.append(("garch", f"{field}: {info}"))
                for field in ("alpha", "beta", "persistence"):
                    interval = fit.interval(field)
                    if interval: entries.append(("garch", f"{field} 95% Wald interval: {interval}"))
                if fit.eta_interval: entries.append(("garch", f"eta 95% profile interval: {fit.eta_interval}"))
            self.quant_notes.setText("\n".join(str(n) for _, n in entries if n))
            from .risk_display import grouped_notes
            self.quant_notes.localized_text = {language: grouped_notes(entries, language, result=r, history=h)
                                               for language in ("en", "ko")}
            self.quant_notes.retranslate()
            self.analysis_status.setText("COMPLETED · 검증 NOT_RUN · 재현성 PARTIAL")
            # Owner issue 14: status codes stay visible with their Korean meaning beside them.
            self.analysis_status.localized_text = {"ko": "완료 · 검증 미실행(NOT_RUN) · 재현성 부분(PARTIAL)"}
            self.analysis_status.retranslate()
        self.refresh_views()

    @pyqtSlot(str)
    def job_failed(self, code):
        if self.pending == "markets":
            self.session.finish_market_refresh([])
            self.statusBar().showMessage(f"시장 조회 실패: {code}")
        elif self.pending == "portfolio":
            self.portfolio.status.setText(f"FAILED · {code} · 입력/데이터를 확인하세요.")
            self.portfolio.set_state("failed")
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
        self.portfolio.set_state("running")
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
        self.library_refresh()   # the Research Library's rows, counts and preview (display only)
        complete = [r for r in runs if r["execution_status"] == "COMPLETED"]
        from .risk_display import MC_MODEL_LABELS, ko, source_name, status_ko
        table_rows(self.risk_table, [[r["parameters"]["symbol"],
            MC_MODEL_LABELS.get(r["parameters"]["model"], r["parameters"]["model"]),
            f"{r['metrics']['prob_loss']:.1%}", f"{r['metrics']['var_pct']:.1%}", f"{r['metrics']['cvar_pct']:.1%}",
            r["data"]["source"]] for r in complete])
        self.risk_table.setVisible(bool(complete))
        self.risk_empty.setVisible(not complete)
        if complete:
            r = complete[0]
            if r["run_id"] in self.outputs: self.home_chart.set_result(self.outputs[r["run_id"]].result)
            self.home_summary.setText(f"{r['parameters']['symbol']} · {r['parameters']['model']} · {r['data']['source']}\n"
                f"P5 {r['metrics']['p05']:,.2f} / P50 {r['metrics']['p50']:,.2f} / P95 {r['metrics']['p95']:,.2f}\n"
                f"관측 {r['data']['last_observation']} · 판정 {r['verdict']} · 재현성 {r['reproducibility']}")
            # Owner issue 14: model and source as words, status codes with their Korean meaning.
            model = MC_MODEL_LABELS.get(r['parameters']['model'], r['parameters']['model'])
            band = f"P5 {r['metrics']['p05']:,.2f} / P50 {r['metrics']['p50']:,.2f} / P95 {r['metrics']['p95']:,.2f}"
            source = r['data']['source']
            self.home_summary.localized_text = {
                'en': (f"{r['parameters']['symbol']} · {model} · {source}\n{band}\n"
                       f"Observed {r['data']['last_observation']} · verdict {r['verdict']} · "
                       f"reproducibility {r['reproducibility']}"),
                'ko': (f"{r['parameters']['symbol']} · {ko(model)} · "
                       f"{'합성 데이터' if source == 'SYNTHETIC' else source_name(source, 'ko')}\n{band}\n"
                       f"관측 {r['data']['last_observation']} · 판정 {status_ko(r['verdict'])} · "
                       f"재현성 {status_ko(r['reproducibility'])}")}
            self.home_summary.retranslate()
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
        # The library counts this run as saved (its row and the 저장함 / 저장 전 counts); nothing else changes.
        self.library_saved.add(run_id)
        self.library_refresh()

    def change_theme(self, index):
        # Preserve the F1 geometry; use a legible foreground on dark surfaces.
        symbol = self.brand_symbol_svg
        if index:
            symbol = symbol.replace(b'#194C40', b'#E5EEE8').replace(b'fill="#E5EEE8"', b'fill="#A9C6BD"')
        self.brand_symbol.load(QByteArray(symbol))
        p = self.colors = DARK if index else LIGHT
        self.apply_rail_theme(p, bool(index))
        self.watchlist.set_theme(p)
        self.markets_view.set_theme(bool(index))
        from .research_style import apply
        for workspace in (self.tools_page, self.quant_page, self.risk_page):
            apply(workspace,p,bool(index))
        from .page_kit import Workspace
        for workspace in self.findChildren(Workspace):
            workspace.set_theme(p, bool(index))
        self.indicator_guide.set_theme(p)
        for destination in self.market_destinations.values():
            if hasattr(destination,'set_theme'):destination.set_theme(p)
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
        if (self.jobs.busy or self.paper_session.jobs.busy or self.commentary.jobs.busy or self.market_chart.jobs.busy
                or any(page.jobs.busy for page in self.market_destinations.values())):
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
        self.home_view.stop()
        for destination in self.market_destinations.values():
            if hasattr(destination,'stop'):destination.stop()
        self.quote_paint_timer.stop()
        event.accept()


def main():
    from .windows_branding import set_app_identity, bind_window_icons
    if not set_app_identity():
        print("QUANTGEN: Windows did not accept the application ID; the taskbar may show the Python icon.",
              file=sys.stderr)
    app = QApplication(sys.argv)
    from . import use_fusion_style
    use_fusion_style()
    app.setWindowIcon(app_icon())
    app.setApplicationName("QUANTGEN")
    app.setOrganizationName("QUANTGEN")
    load_interface_fonts(app)
    settings = QSettings("QUANTGEN", "QUANTGEN")
    window = ResearchWindow(language=settings.value("ui/language", "en"),
                            locale=settings.value("ui/locale", None), language_store=settings,
                            theme_mode=settings.value("ui/theme", "light"))
    window.show()
    window._native_icon_binding = bind_window_icons(window, application_root() / 'assets' / 'icon.ico')
    return app.exec()
