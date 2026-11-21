"""Native portfolio editor and result tables, backed by existing core solvers.

Owner UI review (2026-11-10; issues 13, 04/12, 14, 11), ported from Claude's Flet fix (PR #98,
ui/portfolio_page.py) into GPT's compact native layout:
  * the app chooses the data source (`source="best"`); the selector stays in the tree, hidden, so tests
    and scripts can still pick a provider, and the result names the provider that answered;
  * the result opens with the selected objective's read (verdict first), objective names and yes/no are
    display words, tables are as tall as their rows, and the notes are headed bullets with the full
    paragraph folded underneath;
  * before the first run the page says what to do instead of showing empty tables.

Approved page draft (owner 2026-11-17, "시안 7개 전부 승인, 앱에 적용 진행하세요";
docs/product/ui_drafts_2026-11-17/draft_05_risk.png): the settings are two folds (자산 구성, 목적함수·제약) that
`dock_into` moves into the page's right column with the run button pinned at its foot. The canvas reads the
result as a lead line (objective · weights · data window) and a quiet key-figure line, the efficient-frontier card
with the four objectives marked, then a weights-and-risk-contribution card beside the four-objective comparison,
and the reading (summary, headed bullets, folded paragraph, scope and notices) below.
Display only: the request, every number and the export payload are unchanged.
"""
from PyQt6.QtCore import QEvent, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (QAbstractItemView, QBoxLayout, QButtonGroup, QComboBox, QDoubleSpinBox, QFrame,
                             QGridLayout, QHBoxLayout, QHeaderView, QLineEdit, QPushButton, QSizePolicy, QStyle,
                             QStyledItemDelegate, QStyleOptionViewItem, QTableWidget, QVBoxLayout, QWidget)

from core.research.portfolio_analysis import PortfolioRequest
from core.research.portfolio_disclosure import cap_label, portfolio_disclosure
from core.theme import LIGHT
from .charts import FrontierChart
from .bonds_portfolio_narrative import (portfolio_notes, portfolio_scope_korean,
                                       model_note_korean, display_variants)
from .page_kit import Badge, Button, Card, Fold, KeyFigures, PillTabs, Text, field, pick, rule
from .risk_display import (OBJECTIVE_LABELS, ko, portfolio_sections, portfolio_summary, provenance_line,
                           source_name, synthetic_line)

# "best" first: the app's own routing (keyless Yahoo before a labelled synthetic fallback).
SOURCES = (("best", "Auto"), ("auto", "Auto (keyed providers only)"), ("fmp", "FMP"), ("kis", "KIS · KRX"),
           ("yfinance", "Yahoo (total return)"), ("synthetic", "Synthetic demo"))
SCOPE_HINT = "선택한 목적에만 입력 상한이 적용됩니다. 나머지 목적·Frontier·무작위 구름의 종목당 상한은 100%입니다."
EMPTY_STATE = ("Enter symbols separated by commas, pick an objective and press [Run portfolio analysis]. "
               "All four objectives are computed and marked on the frontier, so their trade-offs are "
               "visible side by side.")
OBJECTIVES = ("max_sharpe", "min_vol", "risk_parity", "equal_weight")
VALUE_ROLE = Qt.ItemDataRole.UserRole + 903       # a cell's number (weights, risk contributions)
SERIES_ROLE = Qt.ItemDataRole.UserRole + 904      # an objective's weights, for its composition bar
OBJECTIVE_ROLE = Qt.ItemDataRole.UserRole + 905   # an objective row's id
# One colour per symbol, the draft's greens and gold first (light, dark); repeats after eight symbols.
SERIES = (("#194C40", "#91C5AC"), ("#4E8571", "#5E9C84"), ("#93BCA9", "#3E6E5C"), ("#C7A867", "#C7A867"),
          ("#6E7F75", "#A7B8AC"), ("#2F6DB5", "#7FB0E8"), ("#A85F7A", "#D893AC"), ("#8A6A2A", "#E5BE74"))


def _colors(widget):
    return getattr(widget.window(), "colors", None) or LIGHT


def _dark(colors):
    return QColor(colors.bg).lightnessF() < .5


def series_color(index, colors):
    return QColor(SERIES[index % len(SERIES)][1 if _dark(colors) else 0])


def _percent(value, digits=1, sign=False):
    text = f"{value * 100:+.{digits}f}%" if sign else f"{value * 100:.{digits}f}%"
    return text.replace("-", "−")


def card_table(headers):
    """A table that fills its card (the draft's compact tables): no grid, no frame, the header quiet. Unlike
    `app.table` its columns share the card's width; every row stays visible (`fit_result_table`)."""
    from .result_layout import fit_result_table
    t = QTableWidget(0, len(headers))
    t.setHorizontalHeaderLabels(headers)
    t.verticalHeader().hide()
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    t.setShowGrid(False)
    t.setWordWrap(True)
    t.setFrameShape(QFrame.Shape.NoFrame)
    t.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    t.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    header = t.horizontalHeader()
    header.setHighlightSections(False)
    header.setMinimumSectionSize(36)
    header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    t.verticalHeader().setMinimumSectionSize(34)
    fit_result_table(t)
    return t


def _figure_cells(table, columns):
    """Figures in the number face, right-aligned (owner UI-D5), as the compact tables do."""
    from .font_policy import number_font
    face = number_font(table.font())
    for row in range(table.rowCount()):
        for column in columns:
            item = table.item(row, column)
            if item is not None:
                item.setFont(face)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)


def _panel(delegate, painter, option, index, *, tint=False):
    """The cell's own background, selection and row line (the table's style sheet), without its text; `tint` marks
    the selected objective's row as the draft does."""
    view = QStyleOptionViewItem(option)
    delegate.initStyleOption(view, index)
    view.text = ""
    view.icon = view.icon.__class__()
    widget = option.widget
    style = widget.style() if widget is not None else None
    if tint and not option.state & QStyle.StateFlag.State_Selected:
        from .typography import mix
        colors = _colors(widget)
        painter.fillRect(option.rect, QColor(mix(colors.accent_soft, colors.surface, .35)))
    if style is not None:
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, view, painter, widget)


class SymbolDelegate(QStyledItemDelegate):
    """A symbol with its series colour swatch (the weights card's first column)."""

    def paint(self, painter, option, index):
        colors = _colors(option.widget)
        _panel(self, painter, option, index)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(option.rect).adjusted(8, 0, -4, 0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(series_color(index.row(), colors))
        painter.drawRoundedRect(QRectF(rect.left(), rect.center().y() - 4, 8, 8), 2, 2)
        font = QFont(option.font)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor(colors.text))
        text = str(index.data() or "")
        metrics = painter.fontMetrics()
        painter.drawText(rect.adjusted(16, 0, 0, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         metrics.elidedText(text, Qt.TextElideMode.ElideRight, int(rect.width() - 16)))
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return QSize(size.width() + 30, max(size.height(), 36))


class BarDelegate(QStyledItemDelegate):
    """A share as a bar with its figure on the right (비중 34.6%, 위험 기여 28.2%); a negative share draws no bar
    and its figure in the falling colour. The cell text is the table's own text."""

    def paint(self, painter, option, index):
        value = index.data(VALUE_ROLE)
        if value is None:
            return super().paint(painter, option, index)
        from .typography import TONE_COLORS, mix
        colors = _colors(option.widget)
        _panel(self, painter, option, index)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(option.rect).adjusted(8, 0, -8, 0)
        font = index.data(Qt.ItemDataRole.FontRole) or option.font
        painter.setFont(font)
        text = str(index.data() or "")
        width = painter.fontMetrics().horizontalAdvance(text) + 2
        text_width = max(width, 52)
        bar = QRectF(rect.left(), rect.center().y() - 3, max(0., rect.width() - text_width - 10), 6)
        if bar.width() >= 24:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(mix(colors.surface_2, colors.border, .25)))
            painter.drawRoundedRect(bar, 3, 3)
            share = max(0., min(1., float(value)))
            if share > 0:
                painter.setBrush(series_color(index.row(), colors))
                painter.drawRoundedRect(QRectF(bar.left(), bar.top(), max(3., bar.width() * share), bar.height()), 3, 3)
        negative = float(value) <= -.0005        # a share that rounds to '−0.0%' is no hedge: drawn as 0.0%
        painter.setPen(QColor(TONE_COLORS[_dark(colors)]["down"] if negative else colors.text))
        painter.drawText(QRectF(rect.right() - text_width, rect.top(), text_width, rect.height()),
                         Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                         text.replace("-", "−") if negative else text.lstrip("-−"))
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return QSize(size.width() + 60, max(size.height(), 36))


class ObjectiveDelegate(QStyledItemDelegate):
    """The objective's name after its ring (the frontier's mark); the selected objective's ring is filled and its
    row tinted, as on the chart."""

    def __init__(self, pane):
        super().__init__(pane)
        self.pane = pane

    def paint(self, painter, option, index):
        colors = _colors(option.widget)
        selected = index.data(OBJECTIVE_ROLE) == self.pane.selected_objective
        _panel(self, painter, option, index, tint=selected)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = option.rect.left() + 14, option.rect.center().y()
        if selected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(colors.accent_soft if not option.state & QStyle.StateFlag.State_Selected
                                    else colors.surface))
            painter.drawEllipse(QRectF(cx - 8, cy - 8, 16, 16))
            painter.setBrush(QColor(colors.accent))
            painter.drawEllipse(QRectF(cx - 4.5, cy - 4.5, 9, 9))
        else:
            painter.setPen(QPen(QColor(colors.text), 1.4))
            painter.setBrush(QColor(colors.surface))
            painter.drawEllipse(QRectF(cx - 4.5, cy - 4.5, 9, 9))
        painter.setFont(self._font(option, selected))
        painter.setPen(QColor(colors.text))
        painter.drawText(QRectF(option.rect).adjusted(30, 0, -6, 0),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap,
                         str(index.data() or ""))
        painter.restore()

    @staticmethod
    def _font(option, selected):
        font = QFont(option.font)
        if selected:
            font.setWeight(QFont.Weight.DemiBold)
        return font

    def sizeHint(self, option, index):
        from PyQt6.QtCore import QRect
        from PyQt6.QtGui import QFontMetrics
        metrics = QFontMetrics(self._font(option, True))
        text = str(index.data() or "")
        available = option.rect.width() - 36 if option.rect.width() > 60 else 10000
        bounds = metrics.boundingRect(QRect(0, 0, max(40, available), 10000), Qt.TextFlag.TextWordWrap, text)
        return QSize(bounds.width() + 36, max(36, bounds.height() + 14))


class FigureDelegate(QStyledItemDelegate):
    """A figure right-aligned in the number face; `toned` paints a return in the rising or falling colour and the
    selected objective's row in the heavier weight (the draft's comparison table). The text is the cell's own."""

    def __init__(self, pane, *, toned=False, strong=False):
        super().__init__(pane)
        self.pane, self.toned, self.strong = pane, toned, strong

    def _font(self, option, index):
        from .font_policy import number_font
        font = number_font(QFont(option.font))
        if self.strong and index.sibling(index.row(), 0).data(OBJECTIVE_ROLE) == self.pane.selected_objective:
            font.setWeight(QFont.Weight.DemiBold)
        return font

    def paint(self, painter, option, index):
        from .typography import TONE_COLORS
        colors = _colors(option.widget)
        selected = index.sibling(index.row(), 0).data(OBJECTIVE_ROLE) == self.pane.selected_objective
        _panel(self, painter, option, index, tint=selected)
        value = index.data(VALUE_ROLE)
        color = colors.text
        if self.toned and value is not None and abs(float(value)) >= 5e-5:
            color = TONE_COLORS[_dark(colors)]["up" if float(value) > 0 else "down"]
        painter.save()
        painter.setFont(self._font(option, index))
        painter.setPen(QColor(color))
        painter.drawText(QRectF(option.rect).adjusted(6, 0, -8, 0),
                         Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(index.data() or ""))
        painter.restore()

    def sizeHint(self, option, index):
        from PyQt6.QtGui import QFontMetrics
        font = self._font(option, index)
        font.setWeight(QFont.Weight.DemiBold)
        return QSize(QFontMetrics(font).horizontalAdvance(str(index.data() or "")) + 22, 36)


class CompositionDelegate(QStyledItemDelegate):
    """An objective's weights as one stacked bar in the series colours (종목 구성)."""

    def paint(self, painter, option, index):
        weights = index.data(SERIES_ROLE) or ()
        colors = _colors(option.widget)
        selected = index.sibling(index.row(), 0).data(OBJECTIVE_ROLE) == getattr(self.parent(), "_pane_selected", None)
        _panel(self, painter, option, index, tint=selected)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(option.rect).adjusted(8, 0, -8, 0)
        bar = QRectF(rect.right() - min(rect.width(), 72), rect.center().y() - 3, min(rect.width(), 72), 6)
        x = bar.left()
        total = sum(max(0., float(w)) for w in weights) or 1.
        painter.setPen(Qt.PenStyle.NoPen)
        for i, weight in enumerate(weights):
            share = max(0., float(weight)) / total * bar.width()
            if share <= 0:
                continue
            painter.setBrush(series_color(i, colors))
            painter.drawRect(QRectF(x, bar.top(), max(.5, share - 1), bar.height()))
            x += share
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(88, 36)


class OptionButton(Button):
    """One choice of the objective (the draft's 2x2 option boxes): a bordered box, the chosen one tinted."""

    def __init__(self, pair):
        super().__init__(pair, "", checkable=True)
        self.setProperty("kit", None)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def sizeHint(self):
        metrics = self.fontMetrics()
        return QSize(metrics.horizontalAdvance(self.text()) + 24, 36)

    def minimumSizeHint(self):
        return QSize(60, 36)

    def paintEvent(self, event):
        from .typography import mix
        c = _colors(self)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        on = self.isChecked()
        if on:
            painter.setPen(QPen(QColor(c.accent), 2) if self.hasFocus() else Qt.PenStyle.NoPen)
            painter.setBrush(QColor(c.accent_soft))
        else:
            painter.setPen(QPen(QColor(c.accent), 2) if self.hasFocus() else QPen(QColor(mix(c.border, c.bg, .3)), 1))
            painter.setBrush(QColor(mix(c.accent_soft, c.surface, .5)) if self.underMouse() else QColor(c.surface))
        painter.drawRoundedRect(rect.adjusted(.5, .5, -.5, -.5), 9, 9)
        font = QFont(self.font())
        font.setPixelSize(13)
        font.setWeight(QFont.Weight.DemiBold if on else QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(QColor(c.accent if on else c.muted))
        painter.drawText(rect.adjusted(6, 0, -6, 0), Qt.AlignmentFlag.AlignCenter,
                         painter.fontMetrics().elidedText(self.text(), Qt.TextElideMode.ElideRight,
                                                          int(rect.width() - 12)))


class Figures(KeyFigures):
    """KeyFigures whose values may be (English, Korean) pairs (최적화 수렴 예 / Converged yes)."""

    def __init__(self):
        self.raw = ()
        super().__init__()

    def set_items(self, items):
        self.raw = tuple(items)
        super().set_items([(key, pick(self.language, value), *rest) for key, value, *rest in self.raw])

    def set_language(self, language):
        self.language = language
        self.set_items(self.raw)


class Lanes(QWidget):
    """Two cards side by side when there is room, stacked when narrow (the draft's lower row)."""

    def __init__(self, first, second, *, breakpoint=700, ratio=(100, 124)):
        super().__init__()
        self.breakpoint = breakpoint
        self.box = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.box.setContentsMargins(0, 0, 0, 0)
        self.box.setSpacing(12)
        for widget, stretch in zip((first, second), ratio):
            self.box.addWidget(widget, stretch)
        self.ratio = ratio

    def resizeEvent(self, event):
        super().resizeEvent(event)
        direction = (QBoxLayout.Direction.LeftToRight if self.width() >= self.breakpoint
                     else QBoxLayout.Direction.TopToBottom)
        if self.box.direction() != direction:
            self.box.setDirection(direction)


class PortfolioPane(QWidget):
    requested = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        # Imported here to avoid a module-level UI dependency cycle.
        from .app import label, table
        from .form_layout import CompactFieldGrid
        from .narrative_view import FullTextFold
        self.setObjectName("portfolio-pane")
        self.selected_objective = None
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(12)
        self.layout_ = layout

        # Settings: two folds, then the run button and the status (the page docks them in its right column).
        self.input_box = QFrame(); self.input_box.setObjectName("dockedForm")
        settings = QVBoxLayout(self.input_box); settings.setContentsMargins(2, 0, 2, 0); settings.setSpacing(8)
        self.symbols = QLineEdit("AAPL, MSFT, NVDA, TLT")
        self.symbols.setAccessibleName("Symbols · comma separated")
        self.symbols.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Owner issues 04/12: no data-source selector; the app fetches by itself.
        self.source = QComboBox()
        for v, text in SOURCES: self.source.addItem(text, v)
        self.source.setAccessibleName("Source")
        self.objective = QComboBox()
        for v in OBJECTIVES: self.objective.addItem(OBJECTIVE_LABELS[v], v)
        self.objective.setAccessibleName("Objective")
        self.cap = QDoubleSpinBox(); self.cap.setRange(.01, 1); self.cap.setSingleStep(.05); self.cap.setValue(1)
        self.cap.setAccessibleName("Max weight / asset")
        self.rf = QDoubleSpinBox(); self.rf.setRange(-100, 100); self.rf.setValue(3); self.rf.setSuffix(" %")
        self.rf.setAccessibleName("Risk-free")

        self.assets_fold = Fold(("Assets", "자산 구성"))
        self.assets_fold.body.addWidget(field(("Symbols · comma separated", "종목 코드 · 쉼표로 구분"), self.symbols,
                                              hint=("Enter 2–15 different symbols. Only the days on which all of "
                                                    "them traded are compared.",
                                                    "서로 다른 2–15개 종목을 넣어요. 모두 거래된 날만 맞춰 비교해요.")))
        self.symbols.textChanged.connect(self._count_symbols)
        self._count_symbols()
        settings.addWidget(self.assets_fold)
        settings.addWidget(rule())
        self.objective_fold = Fold(("Objective and limits", "목적함수·제약"))
        choices = QWidget(); grid = QGridLayout(choices); grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6); grid.setVerticalSpacing(6)
        self.objective_group = QButtonGroup(self); self.objective_group.setExclusive(True)
        self.objective_buttons = []
        # The draft's order: 최대 샤프 지수 · 최소 변동성 / 리스크 패리티 · 동일 비중 (the combo keeps the ids).
        for i, key in enumerate(OBJECTIVES):
            button = OptionButton((OBJECTIVE_LABELS[key], ko(key)))
            button.clicked.connect(lambda checked=False, index=i: self.objective.setCurrentIndex(index))
            self.objective_group.addButton(button)
            grid.addWidget(button, i // 2, i % 2)
            self.objective_buttons.append(button)
        self.objective.currentIndexChanged.connect(self._show_objective)
        self._show_objective(self.objective.currentIndex())
        choices.setAccessibleName("Objective")
        self.objective_fold.body.addWidget(field(("Objective", "목적함수"), choices))
        self.form = CompactFieldGrid([(label("Max weight / asset", "caption"), self.cap),
                                      (label("Risk-free", "caption"), self.rf)], max_columns=2)
        self.form.docked = True; self.form.columns = 0; self.form.refresh()
        self.objective_fold.body.addWidget(self.form)
        self.objective_fold.body.addWidget(Text(("The cap applies only to the selected objective; the other "
                                                 "objectives and the frontier are computed at 100%.",
                                                 "상한은 선택한 목적에만 적용돼요. 나머지 목적과 프런티어는 100%로 "
                                                 "계산해요."), "hint", wrap=True))
        settings.addWidget(self.objective_fold)
        for hidden in (self.source, self.objective):
            settings.addWidget(hidden); hidden.hide()
        self.run = QPushButton("포트폴리오 분석 실행"); self.run.setProperty("primary", True)
        self.run.clicked.connect(self.submit)
        settings.addWidget(self.run, 0, Qt.AlignmentFlag.AlignLeft)
        self.status = label("동일 관측일의 이력을 정렬한 후 네 가지 목적함수를 비교합니다.", "caption")
        self.status.setProperty("reading_help_keep_visible", True)
        settings.addWidget(self.status)
        self.fine = Text(("Historical returns · no promise of future results · not investment advice · "
                          "verdict stays NOT_RUN",
                          "과거 수익률 기반 · 미래 보장 아님 · 투자 권유 아님 · NOT_RUN 판정 유지"), "fine", wrap=True)
        self.fine.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings.addWidget(self.fine)
        layout.addWidget(self.input_box)
        self.badge = Badge()             # the page shows it in its toolbar: 계산 중 · 계산 완료 · 실패

        # Before a run: say what to press instead of showing empty tables.
        self.empty_card = Card()
        self.empty_card.setMinimumHeight(320)
        self.empty = label(EMPTY_STATE, "muted")
        self.empty.localized_text = {
            'ko': '종목과 목적함수를 정한 뒤 분석을 실행하세요. 결과에서 네 가지 배분 방식과 위험을 비교할 수 있어요.',
            'en': 'Choose assets and an objective, then run the analysis to compare four allocations and their risks.'}
        self.empty.retranslate()
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setProperty("reading_help_keep_visible", True)
        self.empty_card.body.addStretch(1)
        self.empty_card.body.addWidget(self.empty)
        self.empty_card.body.addStretch(1)
        layout.addWidget(self.empty_card, 1)

        # Everything below appears once a result exists.
        self.result = QWidget(); result = QVBoxLayout(self.result); result.setContentsMargins(0, 0, 0, 0)
        result.setSpacing(12)
        lead = QHBoxLayout(); lead.setContentsMargins(0, 0, 0, 0); lead.setSpacing(8)
        self.summary_title = label("", "")
        self.summary_title.setProperty("kit", "lead")
        self.summary_title.setWordWrap(False)
        self.lead_note = Text("", "leadNote", wrap=True)
        lead.addWidget(self.summary_title, 0, Qt.AlignmentFlag.AlignTop)
        lead.addWidget(self.lead_note, 1, Qt.AlignmentFlag.AlignTop)
        # The page's status and exports, on their own row when its toolbar is too narrow for them (hidden otherwise).
        self.lead_actions_host = QWidget()
        self.lead_actions = QHBoxLayout(self.lead_actions_host); self.lead_actions.setContentsMargins(0, 0, 0, 0)
        self.lead_actions.addStretch(1)
        self.lead_actions_host.hide()
        result.addWidget(self.lead_actions_host)
        result.addLayout(lead)
        self.figures = Figures()
        result.addWidget(self.figures)
        self.synthetic = label("", "")
        self.synthetic.setProperty("kit", "badge"); self.synthetic.setProperty("tone", "warn")
        result.addWidget(self.synthetic)

        self.frontier_card = Card(("Efficient frontier", "효율적 프런티어"),
                                  margins=(16, 14, 16, 10), spacing=6)
        self.frontier_read = Text(("The dashed line touches the curve at the maximum Sharpe ratio.",
                                   "점선이 곡선에 닿는 점이 최대 샤프 지수예요."), "cardNote", wrap=True)
        self.frontier_read.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.frontier_card.head.addWidget(self.frontier_read, 1, Qt.AlignmentFlag.AlignBottom)
        self.chart = FrontierChart()
        self.chart.setMaximumWidth(16777215)
        self.frontier_card.body.addWidget(self.chart)
        result.addWidget(self.frontier_card)

        self.weights_card = Card(("Weights and risk", "비중과 위험 기여"), margins=(16, 14, 16, 12), spacing=8)
        self.weights_view = PillTabs((("Weights", "비중·위험"), ("Correlation", "상관관계")))
        self.weights_view.changed.connect(self._show_weights_view)
        self.weights_card.add_head_widget(self.weights_view)
        self.weights = card_table(["Symbol", "Weight", "Risk contribution"])
        # Delegates are kept on the pane: Qt does not own a delegate it is given (PySide6 checklist item 9).
        self.weights_delegates = (SymbolDelegate(self.weights), BarDelegate(self.weights), BarDelegate(self.weights))
        for column, delegate in enumerate(self.weights_delegates):
            self.weights.setItemDelegateForColumn(column, delegate)
        header = self.weights.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for column in (1, 2):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        self.correlation = table([])
        from .result_layout import fit_result_table
        fit_result_table(self.correlation)
        self.correlation.hide()
        self.weights_note = Text("", "hint", wrap=True)
        for widget in (self.weights, self.correlation):
            self.weights_card.body.addWidget(widget)
        self.weights_card.body.addStretch(1)
        self.weights_card.body.addWidget(self.weights_note)

        self.comparison_card = Card(("All four objectives compared", "네 가지 목적함수 비교"),
                                    ("Long only · fully invested", "매수 전용 · 전액 투자"),
                                    margins=(16, 14, 16, 12), spacing=8)
        self.comparison_card.head.removeWidget(self.comparison_card.note)
        self.comparison_card.head.addWidget(self.comparison_card.note, 0, Qt.AlignmentFlag.AlignBottom)
        self.comparison = card_table(["Objective", "Return", "Volatility", "Sharpe", "수렴",
                                      "종목당 상한 / 범위", "Asset mix"])
        for column in (1, 2, 3):
            self.comparison.horizontalHeaderItem(column).setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.comparison.setProperty("localized_columns", [0, 4, 5])
        self.comparison_delegates = {0: ObjectiveDelegate(self), 1: FigureDelegate(self, toned=True),
                                     2: FigureDelegate(self), 3: FigureDelegate(self, strong=True),
                                     6: CompositionDelegate(self.comparison)}
        for column, delegate in self.comparison_delegates.items():
            self.comparison.setItemDelegateForColumn(column, delegate)
        self.comparison.installEventFilter(self)
        self.comparison._pane_selected = None
        # Headers change with the window language (the language controller): refit the figure columns.
        self.comparison.model().headerDataChanged.connect(lambda *args: self._fit_figure_columns())
        header = self.comparison.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in (1, 2, 3):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(6, 68)
        # The draft keeps convergence and the cap scope under the table (and in the key figures); the cells stay.
        self.comparison.setColumnHidden(4, True)
        self.comparison.setColumnHidden(5, True)
        self.comparison_note = Text("", "hint", wrap=True)
        self.comparison_card.body.addWidget(self.comparison)
        self.comparison_card.body.addStretch(1)
        self.comparison_card.body.addWidget(self.comparison_note)
        self.lanes = Lanes(self.weights_card, self.comparison_card)
        result.addWidget(self.lanes)

        # The reading: the verdict, the provider, headed bullets with the full paragraph folded, scope and notices.
        # On the canvas itself (no card): the reading is prose, quieter than the result cards above it.
        self.reading_card = QWidget()
        reading_box = QVBoxLayout(self.reading_card); reading_box.setContentsMargins(4, 12, 4, 4)
        reading_box.setSpacing(10)
        reading_box.addWidget(Text(("Reading the result", "결과 읽기"), "cardTitle"))
        self.reading_card.body = reading_box
        self.summary = label("")
        self.provenance = label("", "caption")
        for widget in (self.summary_title, self.summary, self.synthetic, self.provenance):
            widget.setProperty("reading_help_keep_visible", True)
        self.reading_card.body.addWidget(self.summary)
        self.reading_card.body.addWidget(self.provenance)
        self.reading = QWidget(); self.reading_layout = QVBoxLayout(self.reading)
        self.reading_layout.setContentsMargins(0, 0, 0, 0); self.reading_layout.setSpacing(8)
        self.reading_layout.addWidget(label("Analysis narrative · display language; original retained in export",
                                            "caption"))
        self.narrative_view = None
        self.notes = label("아직 실행한 분석이 없습니다.", "muted")
        self.notes.setProperty("reading_help_keep_visible", False)
        self.notes_fold = FullTextFold(self.notes)
        self.reading_layout.addWidget(self.notes_fold)
        self.reading_card.body.addWidget(self.reading)
        self.scope = label(SCOPE_HINT, "caption")
        self.scope.setProperty("reading_help_keep_visible", True)
        self.reading_card.body.addWidget(self.scope)
        notice = label("Historical-sample optimization, not a future return guarantee or official gate verdict. "
                       "All results are long-only and fully invested; equal weight fixes each weight at 1/N.",
                       "caption")
        notice.setProperty("reading_help_keep_visible", True)
        self.reading_card.body.addWidget(notice)
        result.addWidget(self.reading_card)
        from .report_actions import ReportActions
        self.exports = ReportActions(self.status)
        result.addWidget(self.exports)
        layout.addWidget(self.result)
        self.result.hide()
        layout.addStretch()   # before a result, keep the form and the empty-state card together at the top
        self._tab_order()

    # Settings -------------------------------------------------------------------------------------------
    def _count_symbols(self, *_):
        count = len({s.strip().upper() for s in self.symbols.text().split(",") if s.strip()})
        self.assets_fold.set_count((f"{count}", f"{count}개") if count else "")

    def _show_objective(self, index):
        if 0 <= index < len(self.objective_buttons):
            self.objective_buttons[index].setChecked(True)

    def dock_into(self, side, *, page=None, title=None):
        """The approved page draft (owner 2026-11-17): the settings move into the page's right column
        (`page_kit.SideColumn`), the run button, the status and the scope line into its pinned foot. Widgets,
        signals and the request are unchanged."""
        target = page if page is not None else side.add_page(title)
        self.layout_.removeWidget(self.input_box)
        target.addWidget(self.input_box)
        for widget in (self.run, self.status, self.fine):
            self.input_box.layout().removeWidget(widget)
        self.run.setProperty("kit", "primary")
        self.run.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        side.foot.addWidget(self.run)
        side.foot.addWidget(self.status)
        side.foot.addWidget(self.fine)
        self.docked_side = side
        self._tab_order()
        return target

    def _tab_order(self):
        """Keyboard order as read: symbols, the four objectives, cap, risk-free, then the run button."""
        chain = [self.symbols, *self.objective_buttons, self.cap, self.rf, self.run]
        for first, second in zip(chain, chain[1:]):
            QWidget.setTabOrder(first, second)

    def set_state(self, state):
        """The toolbar badge: '' (none), 'running', 'done', 'approximate', 'failed' or 'input'."""
        pairs = {"": ("", "", ""), "running": ("Calculating", "계산 중", ""),
                 "done": ("Calculated", "계산 완료", "ok"),
                 "approximate": ("Calculated · approximate", "계산 완료 · 근사치", "warn"),
                 "failed": ("Failed", "실패", "err"), "input": ("Check the inputs", "입력 확인", "warn")}
        english, korean, tone = pairs[state]
        self.badge.set_tone(tone)
        self.badge.set_pair((english, korean) if english else "")

    def _fit_figure_columns(self):
        """The comparison's figure columns as wide as their header or widest figure; the objective takes the rest and
        keeps at least 128 px (the figure columns then give way to their figures' own width)."""
        from PyQt6.QtGui import QFontMetrics
        table, header = self.comparison, self.comparison.horizontalHeader()
        metrics = QFontMetrics(header.font())
        figures, heads = {}, {}
        for column in (1, 2, 3):
            item = table.horizontalHeaderItem(column)
            figures[column] = max(table.sizeHintForColumn(column), 48)
            heads[column] = metrics.horizontalAdvance(item.text() if item is not None else "") + 22
        widths = {c: max(figures[c], heads[c]) for c in figures}
        room = table.viewport().width() - sum(widths.values()) - header.sectionSize(6)
        if table.viewport().width() > 200 and room < 128:
            widths = figures
        for column, width in widths.items():
            if header.sectionSize(column) != width:
                header.resizeSection(column, width)

    def eventFilter(self, watched, event):
        if watched is getattr(self, "comparison", None) and event.type() in (
                QEvent.Type.Show, QEvent.Type.Resize, QEvent.Type.FontChange, QEvent.Type.StyleChange,
                QEvent.Type.PolishRequest):
            self._fit_figure_columns()
        return super().eventFilter(watched, event)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.Type.FontChange, QEvent.Type.StyleChange) and hasattr(self, "comparison"):
            self._fit_figure_columns()

    def _show_weights_view(self, index):
        self.weights.setVisible(index == 0)
        self.weights_note.setVisible(index == 0 and bool(self.weights_note.text()))
        self.correlation.setVisible(index == 1)

    def submit(self):
        request=PortfolioRequest(tuple(s.strip().upper() for s in self.symbols.text().split(',') if s.strip()),
            self.source.currentData(),self.objective.currentData(),self.cap.value(),self.rf.value()/100)
        try:request.validate()
        except ValueError:
            self.clear_result()
            self.status.setText("서로 다른 2–15개 심볼과 유효한 비중·금리를 입력하세요.")
            self.set_state("input")
            return
        self.requested.emit(request)

    # Result -------------------------------------------------------------------------------------------
    def show_result(self, output):
        from .app import table_rows
        from .narrative_view import NarrativeView
        from ui.narrative_sections import ko_terms
        self.chart.set_output(output)
        chosen=output.portfolios[output.request.objective]
        self.selected_objective = self.comparison._pane_selected = output.request.objective
        disclosure=portfolio_disclosure(output.portfolios,output.request.objective)
        self.scope.setText(disclosure['summary'] + "\n" + output.portfolios['max_sharpe'].note)
        # Figures as the approved draft shows them (one decimal, signed returns); the export keeps every digit.
        table_rows(self.comparison,[[OBJECTIVE_LABELS.get(o,o),_percent(p.ann_return,sign=True),_percent(p.ann_vol),
            f"{p.sharpe:.3f}".replace("-","−"),
            "Yes" if p.converged else "No",
            cap_label(p)+(" · selected" if o==output.request.objective else " · comparison"), ""]
            for o,p in output.portfolios.items()])
        for row, (o, p) in enumerate(output.portfolios.items()):
            self.comparison.item(row, 0).setData(OBJECTIVE_ROLE, o)
            self.comparison.item(row, 1).setData(VALUE_ROLE, float(p.ann_return))
            self.comparison.item(row, 6).setData(SERIES_ROLE, [float(w) for w in p.weights])
            self.comparison.item(row, 6).setToolTip(", ".join(f"{s} {float(w):.1%}" for s, w in zip(p.symbols, p.weights)))
        _figure_cells(self.comparison, (1, 2, 3))
        self._fit_figure_columns()
        table_rows(self.weights,[[s,_percent(float(w)),_percent(float(r))] for s,w,r in zip(chosen.symbols,chosen.weights,chosen.risk_contrib)])
        for row, (w, r) in enumerate(zip(chosen.weights, chosen.risk_contrib)):
            self.weights.item(row, 1).setData(VALUE_ROLE, float(w))
            self.weights.item(row, 2).setData(VALUE_ROLE, float(r))
        _figure_cells(self.weights, (1, 2))
        self.correlation.setColumnCount(len(chosen.symbols)+1)
        self.correlation.setHorizontalHeaderLabels(["Symbol",*chosen.symbols])
        table_rows(self.correlation,[[s,*[f"{v:.3f}" for v in row]] for s,row in zip(chosen.symbols,output.stats.corr)])
        sources=[f"{h.symbol}: {h.source} · {h.first_date} → {h.last_date} · {h.note}" for h in output.histories]
        synthetic=[h.symbol for h in output.histories if h.source=='SYNTHETIC']
        notes=[f"공통 {output.stats.sessions} sessions", *sources, output.convention_warning,
            *[f"{o}: {p.note}" for o,p in output.portfolios.items() if p.note], output.narrative, disclosure['summary']]
        if synthetic:notes.insert(0,"합성 데이터: "+", ".join(synthetic)+" · 투자 배분이 아닌 계산 시연입니다.")
        self.notes.setText("\n".join(n for n in notes if n))
        # Owner issue 14: raw ids (equal_weight, risk_parity, ...) read as their Korean names in Korean.
        notes_ko=portfolio_notes(output,'ko',disclosure)
        display_variants(self.notes, portfolio_notes(output,'en',disclosure), ko_terms(notes_ko))
        display_variants(self.scope, self.scope.source_text,
                         ko_terms(portfolio_scope_korean(output.portfolios,output.request.objective)
                                  + '\n' + model_note_korean(output.portfolios['max_sharpe'].note)))
        (title_en,text_en),(title_ko,text_ko)=portfolio_summary(output,'en'),portfolio_summary(output,'ko')
        for widget,en,ko_text in ((self.summary_title,title_en,title_ko),(self.summary,text_en,text_ko),
                             (self.synthetic,synthetic_line(output.histories,'en'),synthetic_line(output.histories,'ko')),
                             (self.provenance,provenance_line(output.histories,'en'),provenance_line(output.histories,'ko'))):
            widget.setText(en);display_variants(widget,en,ko_text)
        self.synthetic.setVisible(bool(synthetic))
        if self.narrative_view is not None:
            self.narrative_view.hide();self.narrative_view.deleteLater()
        self.narrative_view=NarrativeView(portfolio_sections(output))
        self.reading_layout.insertWidget(1,self.narrative_view)
        self.notes.retranslate()
        self.status.setText("Calculation complete · no official investment verdict" if chosen.converged else
                            "Calculation complete · the solver did not report convergence; treat the weights as "
                            "approximate · no official investment verdict")
        self._show_reading(output, chosen)
        self.set_state("done" if chosen.converged else "approximate")
        self.empty.hide();self.empty_card.hide();self.result.show()
        self.exports.set_result('portfolio', output.request, [
            {'type': 'provenance', 'histories': [{'symbol': h.symbol, 'source': h.source,
                'first_date': h.first_date, 'last_date': h.last_date, 'note': h.note} for h in output.histories]},
            {'type': 'portfolios', 'data': output.portfolios},
            {'type': 'constraint_scope', 'data': disclosure},
            {'type': 'frontier', 'data': output.frontier},
            {'type': 'correlation', 'symbols': chosen.symbols, 'values': output.stats.corr},
            {'type': 'text', 'text': self.notes.source_text}])

    def _show_reading(self, output, chosen):
        """The lead line, the key figures and the cards' one-line notes, from the result's own numbers."""
        ranked = [(s, w) for s, w in sorted(zip(chosen.symbols, chosen.weights), key=lambda x: -float(x[1]))
                  if round(float(w) * 100) > 0]          # the symbols the portfolio holds, largest first
        shown = " · ".join(f"{s} {float(w) * 100:.0f}%" for s, w in ranked[:6])
        more = len(ranked) - 6
        histories = output.histories
        start = max(h.first_date for h in histories) if histories else ""
        end = min(h.last_date for h in histories) if histories else ""
        sessions = f"{output.stats.sessions:,}"
        names = lambda language: ", ".join(dict.fromkeys(source_name(h.source, language) for h in histories))
        self.lead_note.set_pair((
            f"· {shown}{f' · +{more} more' if more > 0 else ''} · {names('en')} {start} → {end} · "
            f"{sessions} shared sessions",
            f"· {shown}{f' · 외 {more}개' if more > 0 else ''} · {names('ko')} {start} → {end} · 공통 {sessions}거래일"))
        rf = output.request.rf_rate
        requested, effective = chosen.requested_max_weight, chosen.effective_max_weight
        cap = (_percent(effective, 0 if round(effective * 100, 6).is_integer() else 1) if requested == effective
               else f"{_percent(requested, 0)} → {_percent(effective, 1)}")
        self.figures.set_items((
            (("Expected return", "기대수익률"), _percent(chosen.ann_return, sign=True),
             "up" if chosen.ann_return > 0 else "down" if chosen.ann_return < 0 else ""),
            (("Volatility", "변동성"), _percent(chosen.ann_vol)),
            (("Sharpe", "샤프 지수"), f"{chosen.sharpe:.3f}".replace("-", "−")),
            (("Risk-free", "무위험 금리"), _percent(rf, 2)),
            (("Cap per asset", "종목당 상한"), cap),
            (("Converged", "최적화 수렴"), ("Yes", "예") if chosen.converged else ("No", "아니오"),
             "" if chosen.converged else "warn")))
        # Weights card: which symbol carries the most risk, and whether one offsets the others.
        rows = list(zip(chosen.symbols, chosen.weights, chosen.risk_contrib))
        top = max(rows, key=lambda r: float(r[2]))
        english = f"{top[0]}'s {float(top[1]) * 100:.0f}% weight carries {float(top[2]) * 100:.0f}% of the risk."
        korean = f"{top[0]}의 비중 {float(top[1]) * 100:.0f}%가 위험의 {float(top[2]) * 100:.0f}%를 차지해요."
        hedges = [r for r in rows if float(r[2]) <= -.0005]   # a contribution that rounds to −0.0% is no hedge
        if hedges:
            low = min(hedges, key=lambda r: float(r[2]))
            figure = _percent(float(low[2]), 1)
            english += f" {low[0]} contributes {figure}: it offsets part of the others' risk."
            korean += f" {low[0]}의 위험 기여는 {figure}로, 다른 종목의 위험을 조금 덜어 줘요."
        self.weights_note.set_pair((english, korean))
        self._show_weights_view(self.weights_view.current())
        # Comparison card: convergence of all four and the cap's scope (the hidden cells say the same).
        stalled = [o for o, p in output.portfolios.items() if not p.converged]
        if stalled:
            english = ("Not converged: " + ", ".join(OBJECTIVE_LABELS.get(o, o) for o in stalled)
                       + " · treat those weights as approximate")
            korean = ("수렴하지 않은 목적: " + ", ".join(ko(o) for o in stalled) + " · 그 비중은 근사치로 봐요")
        else:
            english, korean = "All four converged", "네 가지 모두 수렴했어요"
        self.comparison_note.set_pair((english + " · the cap applies only to the selected objective",
                                       korean + " · 상한은 선택한 목적에만 적용해요"))

    def clear_result(self):
        self.exports.clear()
        self.chart.set_output(None)
        self.selected_objective = self.comparison._pane_selected = None
        self.scope.setText(SCOPE_HINT)
        for widget in (self.comparison, self.weights, self.correlation):
            widget.setRowCount(0)
        self.notes.setText('')
        if self.narrative_view is not None:
            self.narrative_view.hide();self.narrative_view.deleteLater();self.narrative_view=None
        self.set_state("")
        self.result.hide();self.empty_card.show();self.empty.show()
