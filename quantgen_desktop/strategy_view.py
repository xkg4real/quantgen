"""Strategy Lab result display for the native app (owner UI review 2026-11-10; port of PR #98).

Owner issues: 06 (a run must say whether the strategy is good or bad), 09 (a validation table people can
read), 01 (a readable verdict summary), 07 (card names, not raw ids), 10/11 (an ordered page and headed
commentary instead of one wall of text) and 14 (one language per window).

Presentation only. Every verdict, check and sentence comes from core.research.strategy_display, which
reads the Score fields and validate.GATE and decides nothing new. StrategyPane records the export
sections exactly as before, separately from these widgets.

Each block holds both languages and shows the window's: `UiLabel.localized_text` for labels, and a
`_reserve_text_space` hook (LanguageController calls it on every widget after a language change) for
table cells, combo items, fold buttons and tooltips, so a language switch never reruns anything. Pass and
fail colours follow the theme: ToneScope re-derives a small style sheet from `window.colors` whenever the
window style changes. Layout stays GPT's native frame: label roles, `panel()` cards and dense tables.
"""
from __future__ import annotations

from collections import Counter
from typing import Mapping, Optional, Sequence, Union

from PyQt6.QtCore import QEvent, QPoint, QRect, QTimer, Qt
from PyQt6.QtGui import QColor, QFontMetrics
from PyQt6.QtWidgets import (QAbstractItemView, QComboBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
                             QScrollArea, QSizePolicy, QStyle, QTableWidget, QTableWidgetItem, QToolButton,
                             QVBoxLayout, QWidget)

from core.research import strategy_display as D
from core.research.strategy_exposure import exposure_lines
from core.research.strategy_workflow import FAMILY_ID
from core.theme import LIGHT
from .charts import LineChart
from .owner_ui_language.strategy import MACRO_NOTE, NO_CARDS, PAIRS

Pair = tuple[str, str]                      # (Korean, English), as in strategy_display
Text = Union[str, Pair]
CODE_ROLE = Qt.ItemDataRole.UserRole + 811  # the raw verdict code, status or card id behind a display cell


# --------------------------------------------------------------------------- #
# Both-language text
# --------------------------------------------------------------------------- #
def language_of(widget) -> str:
    window = widget.window() if widget is not None else None
    return "ko" if getattr(window, "ui_language", None) == "ko" else "en"


def variants(value: Text) -> dict:
    if isinstance(value, str):
        return {"en": value, "ko": value}
    ko, en = value
    return {"en": en, "ko": ko}


def pick(value: Text, language: str) -> str:
    return variants(value)[language]


def ui(english: str, **fields) -> Pair:
    """A fixed caption of this area's catalogue as a (ko, en) pair; a field given as a pair is filled per
    language."""
    def fill(template, index):
        return template.format(**{k: (v[index] if isinstance(v, tuple) else v) for k, v in fields.items()})
    return fill(PAIRS[english], 0), fill(english, 1)


def text_label(value: Text, role: str = ""):
    """A label written in both languages. The catalogue never rewrites it, so recorded evidence and
    provider text stay exactly as recorded."""
    from .app import label
    v = variants(value)
    widget = label(v["en"], role)
    widget.localized_text = v
    widget.retranslate()
    return widget


def sync_language(root: QWidget) -> None:
    """Show `root`'s subtree in the window language now (LanguageController does it on its next pass)."""
    from .localization import UiLabel
    for widget in [root, *root.findChildren(QWidget)]:
        if isinstance(widget, UiLabel):
            widget.retranslate()
        hook = getattr(widget, "_reserve_text_space", None)
        if hook is not None:
            hook()


class _Plain(QWidget):
    """A container that paints no background of its own (a plain QWidget takes the window colour)."""


# --------------------------------------------------------------------------- #
# Theme-following colours
# --------------------------------------------------------------------------- #
_TOKENS = ("success", "error", "accent", "muted", "text")


def tone_colour(token: Optional[str], palette) -> str:
    return getattr(palette, token if token in _TOKENS else "muted")


def _sheet(p) -> str:
    rules = [
        f"QFrame[qgTile='true'] {{ background: {p.surface_2}; border: 1px solid {p.border}; border-radius: 12px; }}",
        f"QFrame[qgTile='true'][qgStatus='fail'] {{ border: 1px solid {p.error}; }}",
        "QLabel[qgRole='verdictTitle'] { font-size: 20px; font-weight: 600; }",
        "QLabel[qgStrong='true'] { font-weight: 600; }",
    ]
    for t in _TOKENS:
        c = getattr(p, t)
        rules += [
            f"QFrame[qgBox='{t}'] {{ background: {p.surface}; border: 1px solid {c}; border-radius: 14px; }}",
            f"QFrame[qgBox='{t}'][qgStrong='true'] {{ border: 2px solid {c}; }}",
            f"QLabel[qgTone='{t}'] {{ color: {c}; }}",
            # Qt draws square corners when a radius exceeds half the height: 9px suits a 13px pill.
            f"QLabel[qgPill='{t}'] {{ color: {c}; background: {p.surface}; border: 1px solid {c}; border-radius: 9px; "
            "padding: 3px 10px; font-size: 13px; font-weight: 600; }",
        ]
    return "\n".join(rules)


class ToneScope(QWidget):
    """A result block (one column of widgets) whose pass/fail colours follow the window theme."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sheet = None
        self._restyle_timer = QTimer(self)
        self._restyle_timer.setSingleShot(True)
        self._restyle_timer.timeout.connect(self.restyle)
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(0, 0, 0, 0)
        self.column.setSpacing(14)
        self.restyle()

    def restyle(self):
        sheet = _sheet(getattr(self.window(), "colors", None) or LIGHT)
        if sheet != self._sheet:
            self._sheet = sheet
            self.setStyleSheet(sheet)

    def event(self, event):
        result = super().event(event)
        if event.type() in (QEvent.Type.StyleChange, QEvent.Type.ParentChange, QEvent.Type.Show):
            self._restyle_timer.start(0)
        return result


# --------------------------------------------------------------------------- #
# Small blocks
# --------------------------------------------------------------------------- #
def bullets(lines: Sequence[Text], *, token: str = "text") -> QVBoxLayout:
    column = QVBoxLayout()
    column.setContentsMargins(0, 0, 0, 0)
    column.setSpacing(6)
    for line in lines:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        dot = text_label("•")
        dot.setProperty("qgTone", token)
        dot.setProperty("qgStrong", True)
        row.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)
        row.addWidget(text_label(line), 1)
        column.addLayout(row)
    return column


def pill(value: Text, token: str):
    widget = text_label(value)
    widget.setProperty("qgPill", token if token in _TOKENS else "muted")
    widget.setWordWrap(False)
    return widget


def notice(lines: Sequence[Text], token: str) -> QFrame:
    """A bordered notice that stays in the main body (assumptions, conventions)."""
    box = QFrame()
    box.setProperty("qgBox", token)
    box.setProperty("reading_help_keep_visible", True)
    column = QVBoxLayout(box)
    column.setContentsMargins(16, 12, 16, 12)
    column.setSpacing(6)
    for line in lines:
        column.addWidget(text_label(line))
    return box


class Fold(QWidget):
    """A closed-by-default section: recorded raw lines and long disclosures stay one click away."""

    def __init__(self, title: Text, widgets: Sequence[QWidget], parent=None):
        super().__init__(parent)
        self.title = title
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.toggle = QToolButton()
        self.toggle.setCheckable(True)
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle.toggled.connect(self._toggled)
        layout.addWidget(self.toggle, 0, Qt.AlignmentFlag.AlignLeft)
        self.body = _Plain()
        body = QVBoxLayout(self.body)
        body.setContentsMargins(18, 0, 0, 0)
        body.setSpacing(6)
        for widget in widgets:
            body.addWidget(widget)
        layout.addWidget(self.body)
        self._toggled(False)
        self._reserve_text_space()

    def _toggled(self, expanded):
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        self.body.setVisible(expanded)

    def _reserve_text_space(self):
        shown = pick(self.title, language_of(self))
        if self.toggle.text() != shown:
            self.toggle.setText(shown)
            self.toggle.setAccessibleName(shown)


class TileGrid(_Plain):
    """Equal tiles in one row; two per row (then one) when the column is narrow."""

    def __init__(self, tiles: Sequence[QWidget], *, min_width: int = 170):
        super().__init__()
        self.tiles, self.min_width, self.columns = list(tiles), min_width, 0
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(10)
        self._place(len(self.tiles))

    def _columns_for(self, width: int) -> int:
        for columns in sorted({len(self.tiles), min(2, len(self.tiles)), 1}, reverse=True):
            if columns * self.min_width + (columns - 1) * self.grid.horizontalSpacing() <= width:
                return columns
        return 1

    def _place(self, columns: int):
        if columns == self.columns or not self.tiles:
            return
        while self.grid.count():
            self.grid.takeAt(0)
        for column in range(len(self.tiles)):
            self.grid.setColumnStretch(column, 1 if column < columns else 0)
        for index, tile in enumerate(self.tiles):
            self.grid.addWidget(tile, index // columns, index % columns)
        self.columns = columns
        self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._place(self._columns_for(event.size().width()))


# --------------------------------------------------------------------------- #
# Tables that read in either language
# --------------------------------------------------------------------------- #
def cell(text: Text, *, tone: Optional[str] = None, tip: Optional[Text] = None, code=None) -> dict:
    return {"text": text, "tone": tone, "tip": tip, "code": code}


class LocalizedTable(QTableWidget):
    """A read-only result table holding both languages per cell.

    Columns share the width by fixed weights and wrap their text, and the table is exactly as tall as its
    rows (no inner scroll bar), so a long reason or a two-line value is never cut. The raw code behind a
    display cell (a verdict, a status, a card id) stays in CODE_ROLE."""

    def __init__(self, headers: Sequence[Pair], rows: Sequence[Sequence[dict]], weights: Sequence[int]):
        super().__init__(len(rows), len(headers))
        self.header_text, self.rows, self.weights = list(headers), [list(r) for r in rows], list(weights)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setWordWrap(True)
        self.setShowGrid(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        header.setStretchLastSection(False)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setMinimumSectionSize(40)
        self.verticalHeader().setMinimumSectionSize(34)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setHorizontalHeaderLabels([en for _, en in self.header_text])
        for r, row in enumerate(self.rows):
            for c, value in enumerate(row):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                if value.get("code") is not None:
                    item.setData(CODE_ROLE, value["code"])
                self.setItem(r, c, item)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.refresh)
        self.sync()

    def sync(self):
        """Headers, cells, tooltips and tones in the window language and theme; then re-fit."""
        self._apply()
        self.schedule()

    def _apply(self):
        language = language_of(self)
        palette = getattr(self.window(), "colors", None) or LIGHT
        for c, value in enumerate(self.header_text):
            item = self.horizontalHeaderItem(c)
            if item is not None and item.text() != pick(value, language):
                item.setText(pick(value, language))
        for r, row in enumerate(self.rows):
            for c, value in enumerate(row):
                item = self.item(r, c)
                shown = pick(value["text"], language)
                if item.text() != shown:
                    item.setText(shown)
                tip = pick(value["tip"], language) if value.get("tip") else ""
                if item.toolTip() != tip:
                    item.setToolTip(tip)
                if value.get("tone"):
                    colour = QColor(tone_colour(value["tone"], palette))
                    if item.foreground().color().name() != colour.name():
                        item.setForeground(colour)

    def _reserve_text_space(self):
        self.sync()

    def schedule(self, *args):
        if not self._timer.isActive():
            self._timer.start(0)

    def refresh(self):
        """Re-colour for the current theme, share the width by the weights and show every row."""
        self._apply()
        width = self.viewport().width()
        if width <= 0:
            return
        metrics = QFontMetrics(self.font())
        inset = 2 * (8 + self.style().pixelMetric(QStyle.PixelMetric.PM_FocusFrameHMargin, None, self) + 1) + 4
        widths = self._widths(width, metrics, inset)
        for c, w in enumerate(widths):
            if self.columnWidth(c) != w:
                self.setColumnWidth(c, w)
        # Row heights from the wrapped text itself: the item delegate's size hint leaves out the style
        # sheet's cell padding, which cut a wrapped second line short ('90% 구간 -0.10 ~ ...').
        for r in range(self.rowCount()):
            tallest = metrics.height()
            for c in range(self.columnCount()):
                item = self.item(r, c)
                if item is not None and item.text():
                    box = metrics.boundingRect(QRect(0, 0, max(16, widths[c] - inset), 100000),
                                               Qt.TextFlag.TextWordWrap.value, item.text())
                    tallest = max(tallest, box.height())
            height = max(34, tallest + 16)
            if self.rowHeight(r) != height:
                self.setRowHeight(r, height)
        header = self.horizontalHeader()
        height = (2 * self.frameWidth() + max(header.height(), header.sizeHint().height())
                  + sum(self.rowHeight(r) for r in range(self.rowCount())))
        if self.minimumHeight() != height or self.maximumHeight() != height:
            self.setFixedHeight(height)

    def _widths(self, width: int, metrics: QFontMetrics, inset: int) -> list[int]:
        """Each column at least as wide as its longest word (no 'Strat…' elision), the rest by weight."""
        header_metrics = QFontMetrics(self.horizontalHeader().font())
        minima = []
        for c in range(self.columnCount()):
            header = self.horizontalHeaderItem(c)
            widest = header_metrics.horizontalAdvance(header.text()) + 20 if header is not None else 0
            for r in range(self.rowCount()):
                item = self.item(r, c)
                if item is not None:
                    widest = max([widest, *(metrics.horizontalAdvance(word) + inset
                                            for word in item.text().split())])
            minima.append(min(max(40, widest), width // 2))
        widths, remaining, available = list(minima), set(range(len(minima))), width
        while remaining:
            weight = float(sum(self.weights[c] for c in remaining))
            shares = {c: int(available * self.weights[c] / weight) for c in remaining}
            fixed = {c for c in remaining if minima[c] > shares[c]}
            if not fixed:
                for c in remaining:
                    widths[c] = shares[c]
                break
            available -= sum(minima[c] for c in fixed)
            remaining -= fixed
        widths[-1] = max(minima[-1], width - sum(widths[:-1]))
        return widths

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.schedule()

    def event(self, event):
        result = super().event(event)
        if event.type() in (QEvent.Type.StyleChange, QEvent.Type.FontChange, QEvent.Type.Show,
                            QEvent.Type.ParentChange):
            self.schedule()
        return result


# --------------------------------------------------------------------------- #
# The validation checklist (one row per gate criterion)
# --------------------------------------------------------------------------- #
# A short meaning per row (issue 09); the full explanation (Check.help) is the criterion's tooltip.
MEANING: dict[str, Pair] = {
    "interval": ("처음 보는 구간(표본 외)에서 낸 위험 대비 수익", "Return per unit of risk on data the rule never saw"),
    "dsr": ("여러 설정을 시험한 것을 감안해도 성과가 운이 아닐 확률",
            "Chance the result is not luck, allowing for every setup tried"),
    "pbo": ("과거 최적 설정이 처음 보는 구간에서 하위권으로 떨어질 확률 (낮을수록 좋음)",
            "Chance the in-sample best ends in the bottom half out of sample (lower is better)"),
    "pbo_share": ("과거 최적 설정이 처음 보는 구간에서 진 비율 (낮을수록 좋음)",
                  "Share of splits the in-sample best lost out of sample (lower is better)"),
    "oos_is": ("처음 보는 구간 성과가 학습 구간의 몇 배인지 (0.5 미만이면 과거에만 맞춘 설정)",
               "Out-of-sample Sharpe as a share of in-sample (below 0.5: it only fitted the past)"),
    "bench": ("같은 자산을 동일 비중으로 그냥 보유한 것보다 나은지", "Whether it beats simply holding the same assets"),
    "years": ("한 해 단위로 수익을 낸 비율 (몇몇 해에만 기대는지)", "Share of calendar years with a profit"),
    "stress": ("거래비용이 두 배여도 수익이 남는지", "Whether a profit remains when trading costs double"),
    "plateau": ("설정을 조금 바꿔도 성과가 유지되는지", "Whether nearby setups keep the result"),
    "trades": ("처음 보는 구간에서 포지션을 바꾼 횟수 (너무 적으면 판단 불가)",
               "Position changes out of sample (too few cannot be judged)"),
    "mdd": ("고점에서 가장 크게 떨어진 폭 (판정에 쓰지 않는 참고값)", "Largest fall from a peak (reference, not gated)"),
    "haircut": ("발표 후 성과 감소를 반영한 고정 할인 참고값 (예측 아님)",
                "Fixed post-publication discount, for reference (not a forecast)"),
}
CHECK_HEADERS = [ui("Criterion"), ui("Result"), ui("Threshold"), ui("Verdict"), ui("Meaning")]


def meaning(check: D.Check) -> Pair:
    if check.key == "pbo" and check.label[1].startswith("Over-search"):
        return MEANING["pbo_share"]
    return MEANING.get(check.key, check.help)


def check_value(check: D.Check) -> Pair:
    """'0.83\\n90% 구간 -0.10 ~ 1.77', '5회': the headline number with its detail and unit."""
    ko = en = check.value
    if check.key == "trades" and check.value != "—":
        ko = f"{check.value}회"
    ko += f"\n{check.detail[0]}" if check.detail[0] else ""
    en += f"\n{check.detail[1]}" if check.detail[1] else ""
    return ko, en


def checklist_table(checks: Sequence[D.Check]) -> LocalizedTable:
    rows = [[cell(c.label, tip=c.help), cell(check_value(c)), cell(c.threshold),
             cell(D.STATUS[c.status], tone=D.STATUS_TOKEN[c.status], code=c.status),
             cell(meaning(c), tone="muted", tip=c.help)] for c in checks]
    return LocalizedTable(CHECK_HEADERS, rows, (21, 21, 19, 10, 29))


# --------------------------------------------------------------------------- #
# Run result: verdict first, four headline tiles, chart, every criterion
# --------------------------------------------------------------------------- #
class VerdictBanner(QFrame):
    """Is this a good strategy or a bad one (issue 06): the verdict in words, why, and what to do next."""

    def __init__(self, verdict: Mapping):
        super().__init__()
        token = verdict["token"]
        self.setProperty("qgBox", token)
        self.setProperty("qgStrong", True)
        self.setProperty("reading_help_keep_visible", True)
        column = QVBoxLayout(self)
        column.setContentsMargins(20, 16, 20, 16)
        column.setSpacing(10)
        code = verdict["code"]
        name = D.VERDICT.get(verdict["decision"], ("판정 없음", "No verdict"))
        self.pill = pill((f"{name[0]} · {code}", code), token)
        column.addWidget(self.pill, 0, Qt.AlignmentFlag.AlignLeft)
        self.title = text_label(verdict["title"])
        self.title.setProperty("qgRole", "verdictTitle")
        column.addWidget(self.title)
        column.addLayout(bullets(verdict["reasons"], token=token))
        if verdict["next"]:
            column.addWidget(text_label(ui("Next step: {step}", step=verdict["next"]), "muted"))


class MetricTile(QFrame):
    """One headline number: what it is, the value, pass or fail, and the bar it had to clear."""

    def __init__(self, check: D.Check):
        super().__init__()
        self.check = check
        token = D.STATUS_TOKEN[check.status]
        self.setProperty("qgTile", True)
        self.setProperty("qgStatus", check.status)
        column = QVBoxLayout(self)
        column.setContentsMargins(14, 12, 14, 12)
        column.setSpacing(4)
        column.addWidget(text_label(check.label, "caption"))
        value = text_label(check.value, "number")
        value.setWordWrap(False)
        if check.status in ("pass", "fail"):
            value.setProperty("qgTone", token)
        column.addWidget(value)
        status = text_label(D.STATUS[check.status])
        status.setProperty("qgTone", token)
        status.setProperty("qgStrong", True)
        column.addWidget(status)
        threshold = check.threshold
        if check.gated and threshold[1]:
            threshold = (f"기준 {threshold[0]}", f"Needs {threshold[1]}")
        for line in (threshold, check.detail):
            if line[0] or line[1]:
                column.addWidget(text_label(line, "caption"))
        column.addStretch(1)
        self._reserve_text_space()

    def _reserve_text_space(self):
        tip = pick(self.check.help, language_of(self))
        if self.toolTip() != tip:
            self.setToolTip(tip)


class EquityChart(LineChart):
    """The walk-forward equity chart with reader-facing axis and legend text in both languages; the
    export keeps its 'OOS observations' / 'Equity' labels and series names."""

    LEGEND = {"Strategy": D.KIND["strategy"], "Benchmark": ui("Benchmark (equal-weight hold)")}

    def _legend_names(self):
        language = language_of(self)
        return [pick(self.LEGEND.get(name, name), language) for name, _ in getattr(self, "series", ())]

    def _footer_text(self):
        return pick(ui("Out-of-sample sessions · growth of 1"), language_of(self))


def provenance(d: Mapping) -> Pair:
    """Which provider answered for each symbol, and the walk-forward in plain words."""
    data_ko, data_en = [], []
    for symbol, source, note in zip(d["symbols"], d["sources"], d["notes"]):
        ko, en = D.source_label(source)
        cached = "cached" in str(note)
        data_ko.append(f"{symbol} {ko}" + (" (캐시)" if cached else ""))
        data_en.append(f"{symbol} {en}" + (" (cached)" if cached else ""))
    ko, en = ui("Data: {data} · walk-forward: {walk}", data=(", ".join(data_ko), ", ".join(data_en)),
                walk=D.walk_forward_text(d["wf"].note))
    if d.get("ledger_n"):
        lk, le = ui("{family} ledger: {count} configurations", family=FAMILY_ID[d["family"]],
                    count=f"{d['ledger_n']:,}")
        ko, en = f"{ko} · {lk}", f"{en} · {le}"
    return ko, en


class RunView(ToneScope):
    """A Lab run, in reading order: verdict, notices, data, four headline numbers, the equity chart and
    the full checklist. The commentary (narrative_sections) sits in the ToolPane's reading column."""

    def __init__(self, d: Mapping, x, series, colors=None):
        super().__init__()
        from .app import panel
        column = self.column
        self.verdict = verdict = D.run_verdict(d)
        self.banner = VerdictBanner(verdict)
        column.addWidget(self.banner)
        if d.get("convention"):
            column.addWidget(notice([D.convention_text(d["convention"])], "error"))
        english = exposure_lines(d.get("exposure"))
        if english:
            column.addWidget(notice(list(zip(D.exposure_lines_ko(d.get("exposure")), english)), "accent"))
        column.addWidget(text_label(provenance(d), "caption"))
        self.tiles = TileGrid([MetricTile(c) for c in D.headline_checks(verdict["checks"])])
        column.addWidget(self.tiles)
        column.addWidget(text_label(ui("Four headline numbers; all {count} criteria are under 'Result per "
                                       "criterion' below.", count=len(verdict["checks"])), "caption"))
        chart_box, chart_column = panel(None)
        title = ("Out-of-sample growth of 1: strategy and benchmark (equal-weight hold)"
                 if d.get("bench_equity") is not None else "Out-of-sample growth of 1")
        chart_column.addWidget(text_label(ui(title), "heading"))
        self.chart = EquityChart("OOS observations", "Equity")
        self.chart.colors = colors or LIGHT
        self.chart.set_series(x, series)
        chart_column.addWidget(self.chart)
        column.addWidget(chart_box)
        checks_box, checks_column = panel(None)
        checks_column.addWidget(text_label(ui("Result per criterion"), "heading"))
        self.checklist = checklist_table(verdict["checks"])
        checks_column.addWidget(self.checklist)
        checks_column.addWidget(Fold(ui("Full gate lines"), [text_label("• " + line, "caption")
                                                              for line in d["score"].lines]))
        column.addWidget(checks_box)
        notes = " · ".join(n for n in d.get("notes") or () if n)
        if notes:
            column.addWidget(text_label(ui("Provider notes (original text): {notes}", notes=notes), "caption"))


# --------------------------------------------------------------------------- #
# Study cards: verdict summary, readable scorecard, one card in detail
# --------------------------------------------------------------------------- #
class VerdictCountTile(QFrame):
    """How many cards got one verdict, and what that verdict means (issue 01)."""

    def __init__(self, code: str, count: int):
        super().__init__()
        token = D.VERDICT_TOKEN.get(code, "muted")
        self.setProperty("qgBox", token)
        column = QVBoxLayout(self)
        column.setContentsMargins(16, 14, 16, 14)
        column.setSpacing(8)
        head = QHBoxLayout()
        head.setSpacing(12)
        number = text_label(str(count), "number")
        number.setWordWrap(False)
        number.setProperty("qgTone", token)
        head.addWidget(number, 0, Qt.AlignmentFlag.AlignVCenter)
        names = QVBoxLayout()
        names.setSpacing(0)
        names.addWidget(text_label(D.VERDICT.get(code, D.VERDICT["UNKNOWN"]), "cardTitle"))
        code_label = text_label(code, "caption")
        code_label.setProperty("qgTone", token)
        names.addWidget(code_label)
        head.addLayout(names, 1)
        column.addLayout(head)
        column.addWidget(text_label(D.VERDICT_MEANING.get(code, D.VERDICT_MEANING["UNKNOWN"]), "caption"))
        column.addStretch(1)


CARD_HEADERS = [ui("Card"), ui("Kind"), ui("Verdict"), ui("Why"), ui("Key numbers")]


def scorecard_table(cards: Sequence[Mapping]) -> LocalizedTable:
    """Card names in words (issue 07); the id is the tooltip and the detail's secondary line."""
    rows = []
    for c in cards:
        t = D.card_text(c)
        reason, _ = D.reason_text(c["decision_reason"], c)
        numbers = tuple(D.key_numbers(c, language).replace(" · ", "\n") for language in ("ko", "en"))
        tip = (f"{c['card_id']} · {t.what[0]}", f"{c['card_id']} · {t.what[1]}")
        rows.append([cell(t.name, tip=tip, code=c["card_id"]), cell(D.kind_label(c["kind"])),
                     cell(D.verdict_label(c["decision"]), tone=D.VERDICT_TOKEN.get(c["decision"], "muted"),
                          code=c["decision"]),
                     cell(reason), cell(numbers, tone="muted")])
    return LocalizedTable(CARD_HEADERS, rows, (24, 9, 14, 30, 23))


class CardPicker(QComboBox):
    """'BTC 무기한선물 펀딩비 신호 — 통과 · PASS'; the card id is the item data and tooltip."""

    def __init__(self, cards: Sequence[Mapping]):
        super().__init__()
        self.cards = list(cards)
        for c in self.cards:
            self.addItem(c["card_id"], c["card_id"])
            self.setItemData(self.count() - 1, c["card_id"], Qt.ItemDataRole.ToolTipRole)
        self.setAccessibleName("Choose a validation card")
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.setMinimumContentsLength(24)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMaximumWidth(640)
        self._reserve_text_space()

    @staticmethod
    def option_text(card: Mapping, language: str) -> str:
        return (f"{pick(D.card_text(card).name, language)} — "
                f"{pick(D.verdict_label(card['decision']), language)}")

    def _reserve_text_space(self):
        language = language_of(self)
        for index, card in enumerate(self.cards):
            shown = self.option_text(card, language)
            if self.itemText(index) != shown:
                self.setItemText(index, shown)
        if self.toolTip() != (self.currentData() or ""):
            self.setToolTip(self.currentData() or "")


def card_detail(card: Mapping) -> QFrame:
    """Everything one card recorded, in plain words first and the original lines folded below."""
    from .app import panel
    box, column = panel(None)
    t = D.card_text(card)
    code = card["decision"]
    head = QHBoxLayout()
    head.setSpacing(12)
    head.addWidget(text_label(t.name, "cardTitle"), 1)
    head.addWidget(pill(D.verdict_label(code), D.VERDICT_TOKEN.get(code, "muted")), 0, Qt.AlignmentFlag.AlignTop)
    column.addLayout(head)
    kind = D.kind_label(card["kind"])
    named = t.name[1] != card["card_id"]          # a card the catalogue does not know shows its id as its name
    column.addWidget(text_label((f"{card['card_id']} · {kind[0]}", f"{card['card_id']} · {kind[1]}") if named
                                else kind, "caption"))

    def block(title: str, widgets):
        column.addWidget(text_label(ui(title), "eyebrow"))
        for widget in widgets:
            column.addWidget(widget)

    if t.what[1]:
        block("What was tested", [text_label(t.what)])
    reason, _ = D.reason_text(card["decision_reason"], card)
    block("Verdict and why", [text_label(D.VERDICT_MEANING.get(code, D.VERDICT_MEANING["UNKNOWN"]), "muted"),
                              text_label(reason)])
    target = D.revise_target_text(card.get("revise_target"))
    if target:
        block("Next step", [text_label(target)])
    numbers = (D.key_numbers(card, "ko"), D.key_numbers(card, "en"))
    if numbers[1] != "—":
        block("Key numbers", [text_label(numbers)])
    stats = card.get("stats") or {}
    if isinstance(stats.get("sr_oos"), (int, float)):
        checks = D.strategy_checks({**stats, "ci90": (card.get("tests") or {}).get("ci90")})
        block("Result per criterion", [checklist_table(checks)])
    evidence = [text_label(card["hypothesis"])] if card.get("hypothesis") else []
    evidence += [text_label("• " + line) for line in card.get("lines", [])]
    if card.get("seed") is not None or card.get("results_md5"):
        evidence.append(text_label(f"seed {card.get('seed')} · results md5 {str(card.get('results_md5', ''))[:8]}",
                                   "caption"))
    column.addWidget(Fold(ui("Recorded evidence ({count} lines)", count=len(card.get("lines", []))), evidence))
    if card.get("citations"):
        block("Sources", [text_label("; ".join(card["citations"]), "caption")])
    return box


class CardsView(ToneScope):
    """The study scorecard: how many cards passed, one readable row per card, and one card in detail."""

    def __init__(self, cards: Sequence[Mapping]):
        super().__init__()
        self.cards = list(cards)
        column = self.column
        column.addWidget(text_label(ui("Validation summary"), "heading"))
        if not self.cards:
            column.addWidget(notice([ui(NO_CARDS)], "accent"))
            column.addWidget(text_label(ui(MACRO_NOTE), "caption"))
            self.table = self.picker = None
            return
        column.addWidget(text_label(ui("How the strategies and models of the validation study were judged, "
                                       "at a glance."), "caption"))
        counts = Counter(c["decision"] for c in self.cards)
        column.addWidget(TileGrid([VerdictCountTile(code, counts.get(code, 0)) for code in verdict_order(counts)],
                                  min_width=200))
        column.addWidget(text_label(ui("{count} study cards · the verdicts as the study recorded them",
                                       count=len(self.cards)), "caption"))
        column.addWidget(text_label(ui(MACRO_NOTE), "caption"))
        column.addWidget(text_label(ui("Result per card"), "heading"))
        column.addWidget(text_label(ui("What each card tested and why it got its verdict, in plain words. Click "
                                       "a row for the details below."), "caption"))
        self.table = scorecard_table(self.cards)
        column.addWidget(self.table)
        self.details_heading = text_label(ui("Card details"), "heading")
        column.addWidget(self.details_heading)
        self.picker = CardPicker(self.cards)
        column.addWidget(self.picker)
        self.detail_host = _Plain()
        self.detail_layout = QVBoxLayout(self.detail_host)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        column.addWidget(self.detail_host)
        self.detail = None
        self.picker.currentIndexChanged.connect(self.show_card)
        self.table.cellClicked.connect(self.pick_row)
        self.show_card(0)

    def show_card(self, index: int):
        if self.detail is not None:
            self.detail_layout.removeWidget(self.detail)
            self.detail.hide()
            self.detail.deleteLater()
        self.detail = card_detail(self.cards[index]) if 0 <= index < len(self.cards) else None
        if self.detail is not None:
            self.detail_layout.addWidget(self.detail)
            sync_language(self.detail)
        self.picker._reserve_text_space()

    def pick_row(self, row: int, column: int = 0):
        """A clicked row opens that card below and scrolls its details into view."""
        self.picker.setCurrentIndex(row)
        QTimer.singleShot(0, self._scroll_to_details)

    def _scroll_to_details(self):
        area = self.parentWidget()
        while area is not None and not isinstance(area, QScrollArea):
            area = area.parentWidget()
        if area is None or area.widget() is None:
            return
        top = self.details_heading.mapTo(area.widget(), QPoint(0, 0)).y()
        area.verticalScrollBar().setValue(max(0, top - 16))


def verdict_order(counts: Mapping[str, int]) -> list[str]:
    return ["PASS", "REVISE", "REJECT"] + [k for k in ("INSUFFICIENT_DATA", "UNKNOWN") if counts.get(k)]


def cards_sections(cards: Sequence[Mapping]) -> dict:
    """Headed commentary for the reading column: the counts, what each verdict means, how to read it."""
    from .translations import translate
    stored = "저장된 연구 기록입니다. 조회는 카드를 재실행하거나 판정을 바꾸지 않습니다."
    stored = (stored, translate(stored, "en"))
    if not cards:
        return {lang: [(pick(ui("Validation summary"), lang), [pick(ui(NO_CARDS), lang)])] for lang in ("ko", "en")}
    counts = Counter(c["decision"] for c in cards)
    order = verdict_order(counts)
    tally = (" · ".join(f"{D.VERDICT[k][0]} {counts.get(k, 0)}개" for k in order),
             " · ".join(f"{D.VERDICT[k][1]} {counts.get(k, 0)}" for k in order))
    meanings = [(f"{D.VERDICT[k][0]} · {k}: {D.VERDICT_MEANING[k][0]}", f"{k}: {D.VERDICT_MEANING[k][1]}")
                for k in order]
    out = {}
    for lang in ("ko", "en"):
        out[lang] = [
            (pick(ui("Validation summary"), lang), [pick(ui("{count} study cards: {counts}", count=len(cards),
                                                            counts=tally), lang), pick(stored, lang)]),
            (pick(ui("What each verdict means"), lang), [pick(m, lang) for m in meanings]),
            (pick(ui("Reading the scorecard"), lang),
             [pick(ui("Every record states the number, the threshold and the sample behind it; pick a card to "
                      "read its recorded evidence."), lang), pick(ui(MACRO_NOTE), lang)]),
        ]
    return out
