"""Pieces of the Portfolio & Risk page in the approved page draft (owner 2026-11-17, "시안 7개 전부 승인, 앱에 적용
진행하세요"; docs/product/ui_drafts_2026-11-17/draft_05_risk.png). Display only: the tables keep their cells, the
language controller keeps translating them, and nothing here computes or sends anything."""
from PyQt6.QtCore import QEvent, QObject, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QFontMetricsF, QPainter
from PyQt6.QtWidgets import (QAbstractItemView, QFrame, QHeaderView, QStyle, QStyledItemDelegate, QStyleOptionViewItem,
                             QTableWidget)
from .qt_compat import call_later

from core.theme import LIGHT


def _language(widget):
    return "ko" if str(getattr(widget.window(), "ui_language", "ko") or "ko").startswith("ko") else "en"


RUN_RISK_ROLE = Qt.ItemDataRole.UserRole + 9182


def set_run_help(table, runs, outputs=None):
    """Associate view metadata with rows without changing the saved run or its cells."""
    from .metric_help import mc_metadata, risk_pair
    from .page_kit import set_cell_help
    outputs = outputs or {}
    for row, record in enumerate(runs):
        current = outputs.get(record.get('run_id'))
        metadata = mc_metadata(record, getattr(current, 'result', None))
        item = table.item(row, 0)
        if item is not None:
            item.setData(RUN_RISK_ROLE, metadata)
        var_hover = risk_pair('var', 'mc_terminal_loss', **metadata)[1]
        cvar_hover = risk_pair('cvar', 'mc_terminal_loss', **metadata)[1]
        set_cell_help(table, row, (0,), tuple(a + "\n\n" + b for a, b in zip(var_hover, cvar_hover)))
        set_cell_help(table, row, (3,), var_hover)
        set_cell_help(table, row, (4,), cvar_hover)


class RunRowsDelegate(QStyledItemDelegate):
    """One completed Monte Carlo run per row, as the draft's list: the symbol, then the model and the data source,
    then the loss probability and CVaR on the left; the 95% VaR with its caption on the right. It paints the row's six
    cells (Symbol, Model, P(loss), VaR 95, CVaR, Source) as the table holds them."""

    def paint(self, painter, option, index):
        from .typography import TONE_COLORS
        table = option.widget
        colors = getattr(table.window(), "colors", None) or LIGHT
        dark = QColor(colors.bg).lightnessF() < .5
        view = QStyleOptionViewItem(option)
        self.initStyleOption(view, index)
        view.text = ""
        table.style().drawControl(QStyle.ControlElement.CE_ItemViewItem, view, painter, table)
        cell = lambda column: str(index.sibling(index.row(), column).data() or "")
        ko = _language(table) == "ko"
        painter.save()
        rect = QRectF(option.rect).adjusted(4, 8, -4, -8)
        name = QFont(option.font); name.setPixelSize(13); name.setWeight(QFont.Weight.DemiBold)
        small = QFont(option.font); small.setPixelSize(12)
        from .font_policy import number_font
        figure = number_font(QFont(option.font)); figure.setPixelSize(13); figure.setWeight(QFont.Weight.Medium)
        name_m, small_m, figure_m = QFontMetricsF(name), QFontMetricsF(small), QFontMetricsF(figure)
        var = cell(3).replace("-", "−")
        from .metric_help import risk_help
        metadata = index.data(RUN_RISK_ROLE) or {}
        caption = risk_help('var', 'mc_terminal_loss', 'ko' if ko else 'en', **metadata).label
        right = max(figure_m.horizontalAdvance(var), small_m.horizontalAdvance(caption)) + 2
        left = QRectF(rect.left(), rect.top(), max(1., rect.width() - right - 12), rect.height())
        line1 = name_m.height()
        painter.setFont(name); painter.setPen(QColor(colors.text))
        painter.drawText(QRectF(left.left(), left.top(), left.width(), line1),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         name_m.elidedText(cell(0), Qt.TextElideMode.ElideRight, left.width()))
        painter.setFont(small); painter.setPen(QColor(colors.muted))
        second = " · ".join(t for t in (cell(1), cell(5)) if t)
        third = (f"손실 확률 {cell(2)} · 큰 손실 평균(CVaR) {cell(4)}" if ko else f"Loss probability {cell(2)} · tail mean(CVaR) {cell(4)}")
        y = left.top() + line1 + 2
        for text in (second, third):
            painter.drawText(QRectF(left.left(), y, left.width(), small_m.height()),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             small_m.elidedText(text, Qt.TextElideMode.ElideRight, left.width()))
            y += small_m.height() + 1
        painter.setFont(figure); painter.setPen(QColor(TONE_COLORS[dark]["down"]))
        painter.drawText(QRectF(rect.right() - right, rect.top(), right, line1),
                         Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, var)
        painter.setFont(small); painter.setPen(QColor(colors.muted))
        painter.drawText(QRectF(rect.right() - right, rect.top() + line1 + 2, right, small_m.height()),
                         Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, caption)
        painter.restore()

    def sizeHint(self, option, index):
        name = QFont(option.font); name.setPixelSize(13)
        small = QFont(option.font); small.setPixelSize(12)
        height = QFontMetricsF(name).height() + 2 + 2 * (QFontMetricsF(small).height() + 1) + 16
        return QSize(240, int(height + .999))


def run_rows_table(headers):
    """The per-symbol Monte Carlo risk table as the draft's rows: the six columns stay (the language controller and
    the callers read them), only the first is shown and painted as a two-line row."""
    from .result_layout import fit_result_table
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().hide()
    t.horizontalHeader().hide()
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    t.setShowGrid(False)
    t.setFrameShape(QFrame.Shape.NoFrame)
    t.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    t.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    for column in range(1, len(headers)):
        t.setColumnHidden(column, True)
    t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    t.rows_delegate = RunRowsDelegate(t)   # kept with the table: Qt does not own a delegate (PySide6 checklist 9)
    t.setItemDelegateForColumn(0, t.rows_delegate)
    t.setAccessibleName("Individual price simulation risk")
    fit_result_table(t)
    return t


class EnabledMirror(QObject):
    """Shows a toolbar action, enabled, exactly when the pane's own export button is enabled (결과 저장 · 보고서 ZIP
    appear once there is a report to save, as in the draft)."""

    def __init__(self, source, target):
        super().__init__(target)
        self.source, self.target = source, target
        source.installEventFilter(self)
        self.sync()

    def sync(self):
        enabled = self.source.isEnabled()
        self.target.setEnabled(enabled)
        self.target.setVisible(enabled)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.EnabledChange:
            self.sync()
        return False


TAB_KEYS = ("portfolio", "signals", "paper")
SCOPE_BADGES = (("Historical-sample optimization · no guarantee", "과거 표본 최적화 · 미래 보장 아님"),
                ("Context only · not a trading instruction", "참고용 분석 · 매매 지시 아님"),
                ("Simulated orders only · no real orders", "모의 주문만 · 실제 주문 없음"))
READINGS = (
    (("Reading the frontier", "프런티어 읽는 법"),
     ("Each grey dot is a random mix of the same assets; the line is the lowest volatility for each expected return. "
      "The four rings are the objectives; the filled one is the one you chose. Expected returns come from the sample "
      "window and move the most when it changes.",
      "회색 점은 같은 종목을 무작위로 섞은 조합이고, 선은 기대수익률마다 변동성이 가장 낮은 조합이에요. 네 개의 원이 "
      "목적함수이고 채워진 원이 고른 목적이에요. 기대수익률은 표본 기간에서 나온 추정치라 기간이 바뀌면 가장 크게 "
      "달라져요.")),
    (("Reading the signals", "신호 읽는 법"),
     ("The composite combines trend, momentum and volatility readings on one history. The backtest charges the "
      "cost per side you enter and compares the rule with buy-and-hold over the same period.",
      "종합 점수는 한 가격 이력에서 추세·모멘텀·변동성 신호를 합친 값이에요. 백테스트는 입력한 편도 비용을 빼고, "
      "같은 기간의 매수 후 보유와 비교해요.")),
    (("Paper trading", "모의투자"),
     ("There is no real order path. Rules are written under System; here you open the session, arm or disarm the "
      "engine and review simulated orders and the decision log. The emergency stop also stays in the left rail.",
      "실제 주문 경로가 없어요. 규칙은 시스템에서 작성하고, 여기서는 세션을 열고 엔진을 켜고 끄며 모의 주문과 판단 기록을 "
      "확인해요. 긴급 정지 버튼은 왼쪽 메뉴에도 늘 있어요.")),
)


class ResultEmptyState(QObject):
    """An empty-state card in a docked ToolPane's canvas, shown until the pane holds a result (기술적 분석): it follows
    the pane's own `has_result`, re-checked whenever the pane's result area gains or loses widgets."""

    def __init__(self, pane, card):
        super().__init__(card)
        self.pane, self.card = pane, card
        pane.result.installEventFilter(self)
        self.sync()

    def sync(self):
        try:
            self.card.setVisible(not self.pane.has_result)
        except RuntimeError:     # the window is being destroyed
            pass

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.ChildAdded, QEvent.Type.ChildRemoved, QEvent.Type.LayoutRequest):
            from PyQt6.QtCore import QTimer
            call_later(self, 0, self.sync)
        return False


class ToolbarFit(QObject):
    """The toolbar never widens the page (A3): when the window is too narrow for everything on one row, the scope badge
    steps aside and the portfolio's status and exports move from the toolbar to the canvas's lead row; they come back
    when there is room. The decision reads size hints only, so it does not depend on where the actions sit."""

    def __init__(self, workspace, scope, actions, inside, outside):
        super().__init__(workspace)
        self.ws, self.scope, self.actions, self.inside, self.outside = workspace, scope, actions, inside, outside
        self.pending = False
        workspace.toolbar_host.installEventFilter(self)
        fitter = getattr(workspace, "_fitter", None)
        self.viewport = fitter.viewport if fitter is not None else None
        if self.viewport is not None:
            self.viewport.installEventFilter(self)
        self.schedule()

    def schedule(self):
        if not self.pending:
            self.pending = True
            from PyQt6.QtCore import QTimer
            call_later(self, 0, self.fit)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.LayoutRequest, QEvent.Type.Show):
            self.schedule()
        return False

    def available(self):
        if self.viewport is None:
            return self.ws.width()
        margins = self.ws.parentWidget().layout().contentsMargins() if self.ws.parentWidget() is not None else None
        return self.viewport.width() - ((margins.left() + margins.right()) if margins is not None else 0)

    def fit(self):
        self.pending = False
        try:
            gap = self.ws.toolbar.spacing()
            base = self.ws.title.sizeHint().width() + gap + 24
            for index in range(self.ws.toolbar_left.count()):
                widget = self.ws.toolbar_left.itemAt(index).widget()
                if widget is not None and widget is not self.scope and not widget.isHidden():
                    base += widget.sizeHint().width() + gap
            actions = 0 if self.actions.isHidden() else self.actions.sizeHint().width() + gap
            room = self.available()
            inside = base + actions <= room
            target = self.inside if inside else self.outside
            if target.indexOf(self.actions) < 0:
                (self.outside if inside else self.inside).removeWidget(self.actions)
                target.addWidget(self.actions)
            host = self.outside.parentWidget()
            if host is not None and host.isHidden() != inside:
                host.setVisible(not inside)
            self.scope.setVisible(base + self.scope.sizeHint().width() + gap + (actions if inside else 0) <= room)
        except RuntimeError:     # the window is being destroyed
            pass
