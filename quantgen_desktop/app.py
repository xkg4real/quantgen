"""Native desktop research workspace. Run with python -m quantgen_desktop.

This first migration slice is deliberately opt-in. Existing Flet routes remain
available unchanged while their native equivalents are ported and verified.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QFontDatabase, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QFileDialog,
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSpinBox, QStackedWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QTabWidget)

from core.app_paths import application_root
from core.research.analysis import AnalysisRequest, execute_analysis
from core.research.export import bundle_bytes, save_desktop_export
from core.research.markets import load_markets, SPECS
from core.research.provenance import code_evidence, runtime_evidence
from core.research.portfolio_analysis import execute_portfolio
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
from tools.status.snapshot import verify
from .charts import FanChart, FrontierChart, LineChart, SignedBars
from .jobs import Jobs
from .macro_records import execute_macro_records


def label(text, role="", *, wrap=True):
    w = QLabel(text)
    w.setTextFormat(Qt.TextFormat.PlainText)
    w.setWordWrap(wrap)
    w.setProperty("role", role)
    w.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return w


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
            if ids:
                item.setData(Qt.ItemDataRole.UserRole, ids[i])
            t.setItem(i, j, item)
    t.resizeRowsToContents()


class ResearchWindow(QMainWindow):
    def __init__(self, *, session=None, market_loader=load_markets,
                 analysis_runner=execute_analysis, portfolio_runner=execute_portfolio, bond_runner=execute_bond,
                 rates_runner=execute_rates, fx_runner=execute_fx, structuring_runner=execute_structuring,
                 signals_runner=execute_signals, macro_runner=execute_macro,
                 derivatives_runner=execute_derivatives, etf_runner=execute_etf,
                 crypto_runner=execute_crypto, krx_runner=execute_krx,
                 connections_runner=execute_connections, strategy_runner=execute_strategy,
                 macro_records_runner=execute_macro_records, paper_factory=None, auto_refresh=True):
        super().__init__()
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
        self.setWindowIcon(QIcon(str(application_root()/"assets/icon.png")))
        self.resize(1360, 940)
        self.setMinimumSize(1000, 700)
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(222)
        rail = QVBoxLayout(sidebar)
        rail.setContentsMargins(18, 28, 18, 22)
        rail.setSpacing(9)
        brand = QHBoxLayout()
        icon = QSvgWidget(str(application_root()/"assets/branding/f1-symbol.svg"))
        icon.setFixedSize(38, 38)
        brand.addWidget(icon)
        brand.addWidget(label("QUANTGEN", "brand", wrap=False))
        rail.addLayout(brand)
        rail.addSpacing(34)
        self.stack = QStackedWidget()
        self.nav = {}
        routes = (("home", "Research Home"), ("markets", "Markets"),
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
        rail.addWidget(label("PERSONAL RESEARCH", "caption"))
        rail.addWidget(label("Native desktop preview\nFlet browser is retained", "muted"))
        self.paper_halt = QPushButton('모의 엔진 긴급 정지')
        self.paper_halt.setEnabled(False)
        self.paper_halt.clicked.connect(lambda: self.paper_session.runtime.halt() if self.paper_session.runtime else None)
        self.paper_session.changed.connect(lambda: self.paper_halt.setEnabled(self.paper_session.runtime is not None))
        rail.addWidget(self.paper_halt)
        self.theme = QComboBox()
        self.theme.addItems(["Light · A", "Dark"])
        self.theme.currentIndexChanged.connect(self.change_theme)
        rail.addWidget(self.theme)
        outer.addWidget(sidebar)
        outer.addWidget(self.stack, 1)
        self.make_home()
        self.make_markets()
        self.make_quant()
        self.make_risk()
        self.make_library()
        self.make_system()
        self.change_theme(0)
        self.navigate("home")
        self.refresh_views()
        if auto_refresh:
            QTimer.singleShot(0, self.refresh_markets)

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
        box, inner = panel("주요 시장지표")
        self.home_markets = table(["지표", "관측값", "변화", "상태 · 관측일"])
        self.home_markets.setMinimumHeight(100)
        inner.addWidget(self.home_markets)
        inner.addWidget(label("일별 관측 · 실시간 아님 · 조회 실패와 오래된 관측은 구분합니다.", "caption"))
        layout.addWidget(box)
        box, inner = panel("가능성을 하나의 숫자로 좁히지 마세요")
        self.home_chart = FanChart()
        inner.addWidget(self.home_chart)
        self.home_summary = label("분석을 실행하면 최신 결과와 데이터 근거가 연결됩니다.")
        inner.addWidget(self.home_summary)
        b = QPushButton("Quant Lab에서 연구 시작 →")
        b.clicked.connect(lambda:self.navigate("quant"))
        inner.addWidget(b)
        inner.addWidget(label("P5–P95는 시뮬레이션 분포의 중앙 90% 구간입니다. 수익 보장이나 95% 신뢰구간이 아닙니다.", "caption"))
        layout.addWidget(box)
        layout.addStretch()

    def make_markets(self):
        from .bonds import BondsPane
        from .rates import RatesPane
        from .fx import FXPane
        from .structuring import StructuringPane
        from .macro import MacroPane
        from .market_tools import DerivativesPane, ETFPane, CryptoPane, KRXPane
        layout = self.page("Markets", "공급자와 관측일을 함께 확인하는 일별 시장 데이터")
        self.market_refresh = QPushButton("시장지표 새로고침")
        self.market_refresh.clicked.connect(self.refresh_markets)
        layout.addWidget(self.market_refresh)
        self.market_table = table(["지표", "값", "단위", "직전 대비", "공급자", "관측일", "상태"])
        self.market_table.setMinimumHeight(100)
        layout.addWidget(self.market_table)
        layout.addWidget(label("USD 금리는 변화량을 bp로 표시합니다. 나머지는 직전 관측 대비 %입니다. 데이터 권리와 빈티지는 미검증입니다.", "muted"))
        self.bonds=BondsPane();self.bonds.requested.connect(self.run_bond)
        self.rates=RatesPane(); self.rates.requested.connect(lambda q:self.run_tool('rates',q))
        self.fx=FXPane(); self.fx.requested.connect(lambda q:self.run_tool('fx',q))
        self.structuring=StructuringPane(); self.structuring.requested.connect(lambda q:self.run_tool('structuring',q))
        self.macro=MacroPane(); self.macro.requested.connect(lambda q:self.run_tool('macro',q))
        from .macro_records import MacroRecordsPane
        self.macro_records = MacroRecordsPane()
        self.macro_records.requested.connect(lambda q:self.run_tool('macro_records',q))
        for name, pane_type in (('derivatives', DerivativesPane), ('etf', ETFPane), ('crypto', CryptoPane), ('krx', KRXPane)):
            pane = pane_type()
            pane.requested.connect(lambda q, n=name:self.run_tool(n,q))
            setattr(self, name, pane)
        self.market_tabs=QTabWidget()
        for pane,name in ((self.bonds,'Bonds'),(self.rates,'Rates'),(self.fx,'FX'),(self.structuring,'Structuring'),
                          (self.derivatives,'Derivatives'),(self.etf,'ETF'),(self.crypto,'Crypto'),(self.krx,'KRX'),
                          (self.macro,'Macro sheet'),(self.macro_records,'Macro v2')):self.market_tabs.addTab(pane,name)
        self.market_tabs.setUsesScrollButtons(True)
        layout.addWidget(self.market_tabs)
        layout.addStretch()

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
        inner.addWidget(self.quant_chart)
        self.quant_metrics = table(["지표", "값"])
        self.quant_metrics.setMinimumHeight(280)
        inner.addWidget(self.quant_metrics)
        self.quant_notes = label("아직 실행한 분석이 없습니다.", "muted")
        inner.addWidget(self.quant_notes)
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
        self.risk_tabs=QTabWidget();self.risk_tabs.addTab(self.portfolio,'Portfolio');self.risk_tabs.addTab(self.signals,'Signals')
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
        layout.addStretch()

    def make_system(self):
        layout = self.page("System", "기록된 근거와 이번 실행 결과를 구분합니다.")
        from .connections import ConnectionsPane
        self.connections = ConnectionsPane()
        self.connections.requested.connect(lambda q: self.run_tool('connections', q))
        from .paper import RulesPane
        self.rules = RulesPane(self.paper_session)
        self.system_tabs = QTabWidget()
        self.system_tabs.addTab(self.connections, 'Connections')
        self.system_tabs.addTab(self.rules, 'Rules')
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
        inner.addWidget(label("PyQt6 네이티브: Home, 일별 Markets, Bonds, Rates, FX, Structuring, Macro sheet, Derivatives, ETF, Crypto, KRX, Monte Carlo, Strategy Lab, 포트폴리오, Signals, Library·저장, 연결 설정, System\nMacro v2·모의매매·규칙 연결 완료 / 남은 이전: AI 분석 패널\n브라우저: 기존 Flet 앱을 유지합니다."))
        inner.addWidget(label("이번 데스크톱은 선택 실행하는 미리보기입니다. 전체 기능 이전 완료본이 아닙니다.", "muted"))
        layout.addWidget(box)
        layout.addStretch()

    def navigate(self, route):
        self.stack.setCurrentIndex(self.route_indices[route])
        for name, button in self.nav.items(): button.setChecked(name == route)

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
            table_rows(self.quant_metrics, [("Spot", f"{r.spot:,.2f}"), ("P5 / P50 / P95", f"{r.p05:,.2f} / {r.median_terminal:,.2f} / {r.p95:,.2f}"),
                ("P(loss)", f"{r.prob_loss:.1%}"), ("VaR 95 / CVaR", f"{r.var_pct:.1%} / {r.cvar_pct:.1%}"),
                ("Paths / horizon / seed", f"{r.n_paths:,} / {r.horizon_days} / {value.run['parameters']['seed']}"),
                ("P(target)", "—" if r.prob_target is None else f"{r.prob_target:.1%}")])
            notes = [f"{'합성 데이터 · ' if h.source=='SYNTHETIC' else ''}{h.source} · {h.first_date} → {h.last_date}",
                     h.note, value.funding_note, r.drift_note, r.bound_note, r.jump_note]
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
        self.market_refresh.setEnabled(not busy)
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
            markets=[dict(label=name,symbol=symbol,provider=provider.upper(),unit=unit,
                value=None,change=None,observation_date=None,
                status='UNAVAILABLE' if self.session.market_attempted and not self.session.market_loading else 'NOT_LOADED')
                for name,symbol,provider,unit,_ in SPECS]
        home, details = [], []
        for r in markets:
            v = "—" if r["value"] is None else f"{r['value']:,.2f}"
            change = "—" if r["change"] is None else f"{r['change']:+.2f} {'bp' if r['unit']=='%' else '%'}"
            observed = r["observation_date"] or "—"
            home.append([r["label"], v, change, f"{r['status']} · {observed}"])
            details.append([r["label"], v, r["unit"], change, r["provider"], observed, r["status"]])
        if not home:
            home = [["시장 데이터", "—", "—", "미연결 · 새로고침 필요"]]
        table_rows(self.home_markets, home)
        table_rows(self.market_table, details)
        for widget in (self.home_markets,self.market_table):
            widget.setFixedHeight(min(350,max(100,widget.horizontalHeader().height()+sum(widget.rowHeight(i) for i in range(widget.rowCount()))+12)))
        table_rows(self.run_table, [[r["parameters"].get("symbol", "—"), r["parameters"].get("model", "—"),
            r["execution_status"], r["verdict"], r["created_at"][:19]] for r in runs], [r["run_id"] for r in runs])
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
        filename, _ = QFileDialog.getSaveFileName(self, "ResearchRun 저장", f"quantgen-{run_id}.{extension}",
                                                 f"Research report (*.{extension})")
        if not filename:
            return
        try:
            data = bundle_bytes(run) if bundle else export_bytes(run)
            save_desktop_export(filename, data, extension=extension)
        except (OSError, ValueError, TypeError) as exc:
            self.export_status.setText(f"저장 실패: {type(exc).__name__} · 경로와 확장자를 확인하세요.")
            return
        self.export_status.setText("저장 완료 · " + Path(filename).name)

    def change_theme(self, index):
        p = self.colors = DARK if index else LIGHT
        self.setStyleSheet(f"""
          QWidget {{ background: {p.bg}; color: {p.text}; font-size: 13px; }}
          QFrame#sidebar {{ background: {p.surface}; border-right: 1px solid {p.border}; }}
          QFrame#panel {{ background: {p.surface}; border: 1px solid {p.border}; border-radius: 14px; }}
          QFrame#panel QLabel {{ background: transparent; }}
          QLabel {{ background: transparent; }}
          QLabel[role='title'] {{ font-size: 30px; font-weight: 700; }}
          QLabel[role='heading'] {{ font-size: 17px; font-weight: 600; }}
          QLabel[role='brand'] {{ font-size: 16px; font-weight: 700; color: {p.accent}; }}
          QLabel[role='number'] {{ font-size: 30px; font-weight: 700; }}
          QLabel[role='muted'], QLabel[role='caption'] {{ color: {p.muted}; }}
          QLabel[role='caption'] {{ font-size: 11px; }}
          QPushButton {{ padding: 10px 14px; border: 1px solid {p.border}; border-radius: 8px; background: {p.surface}; }}
          QPushButton:hover {{ background: {p.accent_soft}; }}
          QPushButton:focus, QLineEdit:focus, QComboBox:focus {{ border: 2px solid {p.accent}; }}
          QPushButton[primary='true'], QPushButton:checked {{ background: {p.accent}; color: {p.on_accent}; }}
          QPushButton[nav='true'] {{ text-align: left; border: 0; min-height: 24px; }}
          QPushButton:disabled {{ color: {p.muted}; background: {p.surface_2}; }}
          QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{ min-height: 28px; padding: 5px; border: 1px solid {p.border}; border-radius: 6px; background: {p.surface}; }}
          QTableWidget {{ background: {p.surface}; alternate-background-color: {p.surface_2}; gridline-color: {p.border}; border: 0; selection-background-color: {p.accent_soft}; selection-color: {p.text}; }}
          QHeaderView::section {{ padding: 8px; border: 0; background: {p.surface_2}; color: {p.muted}; }}
          QScrollArea {{ border: 0; }}
          QTabWidget::pane {{ border: 0; }}
          QTabBar::tab {{ background: {p.surface_2}; color: {p.muted}; padding: 10px 18px; margin-right: 4px; border-top-left-radius: 7px; border-top-right-radius: 7px; }}
          QTabBar::tab:selected {{ background: {p.accent}; color: {p.on_accent}; }}
        """)
        for chart in [*self.findChildren(FanChart), *self.findChildren(FrontierChart), *self.findChildren(LineChart), *self.findChildren(SignedBars)]:
            chart.colors = p
            chart.update()

    def closeEvent(self, event):
        if self.jobs.busy or self.paper_session.jobs.busy:
            event.ignore()
            self.statusBar().showMessage("진행 중인 분석 또는 조회가 끝난 뒤 종료할 수 있습니다.")
            return
        if self.session.runs() or self.portfolio.chart.output is not None or self.bonds.chart.series or any(getattr(self,n).has_result for n in self.tool_names):
            answer = QMessageBox.question(self, "세션 종료", "저장하지 않은 세션 기록은 사라집니다. 종료할까요?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        if not self.paper_session.stop():
            event.ignore()
            self.statusBar().showMessage('모의 엔진의 진행 중인 조회가 끝나면 다시 종료해 주세요.')
            return
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("QUANTGEN")
    app.setOrganizationName("QUANTGEN")
    font_id = QFontDatabase.addApplicationFont(str(application_root()/"assets/fonts/qg-interface.otf"))
    families = QFontDatabase.applicationFontFamilies(font_id)
    if families: app.setFont(QFont(families[0], 10))
    window = ResearchWindow()
    window.show()
    return app.exec()
