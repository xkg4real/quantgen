"""Native stock detail view: one stock on one screen with a chart that fills it (owner request 2026-11-11, UI-D8).

Owner, verbatim: "검색해서 한 차트를 구체적으로 볼때에는, 해당 차트로 화면을 거의 가득채워도 가능해. 정보전달과 가독성에
신경쓰고 공간 넉넉하게써줘" · "스크롤로 차트좌우이동이 가능한데, 이거 그냥 막아버리고 pc기준 좌우화살표로 차트 좌우
확인할수있게 변경해줘" · "트레이딩뷰 상세차트 목록 ui인데, 이런식으로 큼직큼직하게 하고 지표같은건 화살표로 접고펴고
할수잇게 해야하고, 우리는 이 ui를 기본으로 주린이들이 읽기 쉽게 하는 가이드를 화면에 잘 녹여야해" · "그냥 좌측에 존나큰차트
존나크게, 이런 공간 부족해서 스크롤이 필요한 메뉴들은 오른쪽으로 빼서 간소화" · "오른쪽의 스크롤 필요한 메뉴들은
움직이는거고, 차트쪽은 스크롤로 위아래 이동이 안되는거야. 오른쪽만 움직이는거지 스크롤이".

Layout: a one-row toolbar; under it the chart column (the shared MarketChartPane in detail mode, drawn by
core.market.detail_svg at its exact size, and the period bar) on the left, and one fixed-width right column
(stock_detail_side.RightColumn) that is the only thing that scrolls. While a stock is open the page never scrolls
(`PageLock`); the wheel over the chart does nothing; ←/→ (Shift: 10 bars), Home/End, +/− and 0 move the chart.
Focus mode (⤢, Shift+F) collapses the window's rail and hides the right column.

Owner 2026-11-11 (R-D9-1): "우측 가이드가 차트를 가리면 어떡해 차트영역은 절대 침범하면안돼" — nothing ever covers the chart. The
right column is always docked beside it (the chart takes the rest of the width); in a narrow window the rail folds
while a stock is shown and comes back as the owner left it. The chart's own texts (OHLC strip, legend, notices and
each sub-panel's header) sit in the bands detail_svg leaves empty for them, never over candles or lines; the data
notes open in the right column. R-D9-2: the intervals are 1분 … 60분, 일, 주, 월, 년 (the yearly one built from the
monthly history) and no Korean text on this screen says '봉'.

Kept for the rest of the app and its tests: the StockView surface (`chart`, `store`, `instrument`, `profile`,
`jobs`, `back_button`, `watch_button`, `mark`, `code`, `name`, `price`, `change`, `profile_status`,
`section_panels`, `adopt_chart()`, `show_instrument()`, `load_profile()`, `render_header()`,
`render_sections()`, `set_locale()`, `set_theme()`, `stop()`) and the profile loading epochs.
"""
from __future__ import annotations

import json
import math

from PyQt6.QtCore import QEvent, QObject, QPoint, QSize, QTimer, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QFrame, QHBoxLayout, QLineEdit, QMenu, QPushButton, QScrollArea,
                             QSizePolicy, QStyledItemDelegate, QVBoxLayout, QWidget)

from core.i18n import LocaleContext
from core.market.models import Instrument
from core.theme import DARK, LIGHT
from .company_identity import CompanyMark
from .jobs import Jobs
from .stock_detail_side import FoldSection, RightColumn
from .stock_detail_style import (ElidedLabel, icon, icon_size, label, numbers, polite, rich, set_prop, sheet,
                                 text)

from core.market.detail_model import DEFAULT_PERIOD

SETTINGS_PREFIX = "markets/detail/"
DEFAULT_STUDIES = ("sma", "volume_ma", "rsi")
SEARCH_WIDE, SEARCH_NARROW = 200, 140   # spec 2.1 / 2.2
NAME_ROOM, NAME_LEAST = 200, 120        # toolbar room the stock's name is given before other controls give way
PAGE_SIDE = 24           # the page's side margins while a stock is open (spec 2; the app's pages use 32)
SIDE_GAP = 12
CHART_ROOM = 640         # with the rail open the chart would get less than this beside the column: the rail folds
CHART_MIN = 300          # the chart's least width beside the column (the column narrows first)
SIDE_MIN = 300
OVERLAY_ROW = 24


def _lang(ctx):
    return "ko" if getattr(ctx, "language", "ko") == "ko" else "en"


def _esc(value):
    from html import escape
    return escape(str(value))


def valid_studies(keys):
    """Registry keys of `keys` in order, without duplicates; unknown keys are dropped."""
    from core.education.indicators import study
    out = []
    for key in keys:
        try:
            name = study(str(key)).key
        except ValueError:
            continue
        if name not in out:
            out.append(name)
    return tuple(out)


def panel_name(spec, lang):
    """A sub-panel's title: the Korean name with its settings ('스토캐스틱 14·3·3'), or in English the compact
    label when it has no Hangul ('Stoch 14·3·3'), else the English name."""
    import re
    numbers = "·".join(f"{value:g}" if isinstance(value, float) else str(value) for _, value in spec.params)
    if lang == "ko":
        return f"{spec.ko} {numbers}".strip()
    if re.search("[가-힣]", spec.short):
        return f"{spec.en} {numbers}".strip()
    return spec.short


# Profile rows in this view ------------------------------------------------------------------------
# Owner: the folded 주요 지표 shows the key figures; open, high, low and volume repeat the chart's strip and the
# symbol card, so they follow behind "더 보기".
KEY_FIGURE_ORDER = (("시가총액 (계산값)", "Market cap (computed)"), ("PER",), ("EPS",), ("업종", "Sector"),
                    ("거래량", "Volume"), ("시가", "Open"), ("고가", "High"), ("저가", "Low"),
                    ("상장 주식 수", "Listed shares"))
_SCALE = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}


def key_figures_first(rows):
    def rank(item):
        index, row = item
        place = next((i for i, labels in enumerate(KEY_FIGURE_ORDER) if row.label in labels), len(KEY_FIGURE_ORDER))
        return place, index
    return [row for _, row in sorted(enumerate(rows), key=rank)]


def _trim(number_text):
    return number_text.rstrip("0").rstrip(".") if "." in number_text else number_text


def korean_amount(value):
    """A large number in Korean units: 480.3조, 4,803억, 871만."""
    size = abs(value)
    if size >= 1e12:
        shown = _trim(f"{size / 1e12:,.1f}") + "조"
    elif size >= 1e8:
        shown = (f"{size / 1e8:,.0f}" if size >= 1e10 else _trim(f"{size / 1e8:,.1f}")) + "억"
    elif size >= 1e4:
        shown = f"{size / 1e4:,.0f}만"
    else:
        shown = _trim(f"{size:,.2f}")
    return ("−" if value < 0 else "") + shown


def korean_value(value):
    """'80,295 KRW' -> '80,295원', '480.3T KRW' -> '480.3조원', '9M주' -> '900만주' (the profile writes the
    compact English suffixes and the ISO currency code in both languages)."""
    import re
    match = re.fullmatch(r"([+−-]?)([\d,]+(?:\.\d+)?)([KMBT]?)\s*(KRW|주)?", value.strip())
    if match is None or not (match.group(3) or match.group(4) == "KRW"):
        return value
    sign, digits, scale, unit = match.groups()
    unit = {"KRW": "원", "주": "주"}.get(unit or "", "")
    sign = "−" if sign in ("−", "-") else sign
    if not scale:
        return f"{sign}{digits}{unit}"
    return sign + korean_amount(float(digits.replace(",", "")) * _SCALE[scale]) + unit


def korean_times(hint):
    """Times in a profile tooltip in Korea time ('2026. 11. 10. AM 6:00:00 UTC' -> '2026. 11. 10. 15:00 (한국시간)')
    and 'KRW' as 원."""
    import re
    from datetime import datetime, timedelta, timezone

    def kst(match):
        year, month, day, half, hour, minute = match.groups()
        hour = int(hour) % 12 + (12 if half in ("PM", "오후") else 0)
        try:
            moment = datetime(int(year), int(month), int(day), hour, int(minute), tzinfo=timezone.utc)
        except ValueError:
            return match.group(0)
        local = moment.astimezone(timezone(timedelta(hours=9)))
        return f"{local.year}. {local.month}. {local.day}. {local:%H:%M} (한국시간)"
    hint = re.sub(r"(\d{4})\. (\d{1,2})\. (\d{1,2})\. (AM|PM|오전|오후) (\d{1,2}):(\d{2})(?::\d{2})? UTC", kst, hint)
    return re.sub(r"(\d) KRW", r"\1원", hint)


def plain_age(seconds, lang):
    """An age in the unit a reader uses: '40초' / '5분' / '3시간' / '2일' ('40 s', '5 min', '3 h', '2 days')."""
    seconds = max(0, int(seconds))
    for size, ko, en in ((86400, "일", " days"), (3600, "시간", " h"), (60, "분", " min")):
        if seconds >= size:
            count = seconds // size
            return f"{count}{ko}" if lang == "ko" else f"{count}{en if count != 1 or size != 86400 else ' day'}"
    return f"{seconds}초" if lang == "ko" else f"{seconds} s"


def plain_ages(value, lang):
    """The chart pane's status with its ages in plain units ('마지막 수신 108294초 전' -> '마지막 수신 1일 전')."""
    import re
    if lang == "ko":
        return re.sub(r"(\d+)초 전", lambda m: f"{plain_age(int(m.group(1)), lang)} 전", str(value or ""))
    return re.sub(r"(\d+)s ago", lambda m: f"{plain_age(int(m.group(1)), lang)} ago", str(value or ""))


# Figures whose tooltip starts with what the term means (spec 6.3; review 2026-11-11: PER, EPS, 시가총액, VaR, CVaR).
TERM_TIPS = (("시가총액", "term_cap"), ("Market cap", "term_cap"), ("PER", "term_per"), ("EPS", "term_eps"),
             ("CVaR", "term_cvar"), ("VaR", "term_var"))


def term_tip(label_text, lang):
    for prefix, key in TERM_TIPS:
        if label_text.startswith(prefix) or f" {prefix}" in label_text:
            return text(lang, key)
    return ""


def display_row(row, lang):
    """A stock profile row as this view shows it: a typographic minus, Korean units and Korea time in the Korean
    window, 해요체 tooltips that start with what the term means, and no internal engine name. The profile itself
    (reports, exports) is unchanged."""
    import re
    from core.research.stock_profile import ProfileRow
    value = re.sub(r"(?<![\w.])-(?=\d)", "−", str(row.value))
    hint = str(row.hint or "")
    if lang == "ko":
        value = korean_value(value)
        hint = polite(korean_times(hint), lang)
    hint = "\n".join(line for line in hint.split("\n") if "gs_quant" not in line and "계산 엔진" not in line
                     and "engine" not in line.lower())
    term = term_tip(str(row.label), lang)
    if term:
        hint = term + ("\n" + hint if hint else "")
    return ProfileRow(row.label, value, row.tone, hint)


class PageLock(QObject):
    """Owner 2026-11-11: while a stock is open the app page never scrolls. The view is sized to the page
    viewport and the page is held at the view's top; wheel events that reach the page are dropped and any other
    scroll (wheel guards, the shell's position restore, a deferred setValue(0)) is pinned back."""

    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self.scroll = self.bar = None
        self.target = 0
        self._policy = None
        self._pinning = False
        self._value = None      # the page position before the stock opened (Back returns to it)
        self._margins = None    # the page's side margins, narrowed to PAGE_SIDE while locked (spec 2: 24 + 24)

    def _find(self):
        parent = self.view.parentWidget()
        while parent is not None and not isinstance(parent, QScrollArea):
            parent = parent.parentWidget()
        return parent

    @property
    def engaged(self):
        return self.scroll is not None

    def engage(self):
        scroll = self._find()
        if scroll is None or not self.view.isVisible():
            return False
        if scroll is not self.scroll:
            self.release()
            self.scroll, self.bar = scroll, scroll.verticalScrollBar()
            self._value = self.bar.value()
            self._policy = (scroll.verticalScrollBarPolicy(), scroll.horizontalScrollBarPolicy())
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            layout = scroll.widget().layout() if scroll.widget() is not None else None
            if layout is not None:
                margins = layout.contentsMargins()
                self._margins = (layout, margins.left(), margins.top(), margins.right(), margins.bottom())
                layout.setContentsMargins(min(PAGE_SIDE, margins.left()), margins.top(),
                                          min(PAGE_SIDE, margins.right()), margins.bottom())
            self.bar.valueChanged.connect(self._repin)
            self.bar.rangeChanged.connect(self._range)
            scroll.viewport().installEventFilter(self)
        self.refit()
        return True

    def refit(self):
        if self.scroll is None:
            return
        height = max(420, self.scroll.viewport().height())
        if self.view.minimumHeight() != height or self.view.maximumHeight() != height:
            self.view.setFixedHeight(height)
        content = self.scroll.widget()
        if content is not None and content.layout() is not None:
            content.layout().activate()
        self.target = self.view.mapTo(content, QPoint(0, 0)).y() if content is not None else 0
        self._pin()
        self.view._fit_toolbar()

    def _pin(self):
        if self.bar is None or self._pinning:
            return
        self._pinning = True
        try:
            if self.bar.value() != self.target:
                self.bar.setValue(self.target)
        finally:
            self._pinning = False

    def _repin(self, value):
        if not self._pinning and value != self.target:
            self._pin()

    def _range(self, *_):
        self._pin()

    def eventFilter(self, watched, event):
        if self.scroll is not None and watched is self.scroll.viewport():
            if event.type() == QEvent.Type.Wheel:
                event.accept()
                return True
            if event.type() == QEvent.Type.Resize:
                QTimer.singleShot(0, self.refit)
        return False

    def release(self):
        if self.scroll is None:
            return
        try:
            self.bar.valueChanged.disconnect(self._repin)
            self.bar.rangeChanged.disconnect(self._range)
        except (TypeError, RuntimeError):
            pass
        bar, value = self.bar, self._value
        try:
            self.scroll.viewport().removeEventFilter(self)
            if self._policy is not None:
                self.scroll.setVerticalScrollBarPolicy(self._policy[0])
                self.scroll.setHorizontalScrollBarPolicy(self._policy[1])
            if self._margins is not None:
                layout, *margins = self._margins
                layout.setContentsMargins(*margins)
        except RuntimeError:
            pass
        self.scroll = self.bar = None
        self._margins = self._value = None
        self.view.setMinimumHeight(0)
        self.view.setMaximumHeight(16777215)
        if value is not None:
            # The chart usually holds the focus. Hiding it would pass the focus on to the next widget of the page,
            # and the page scrolls to show that widget; with nothing focused the page stays where it is put.
            from PyQt6.QtWidgets import QApplication
            focused = QApplication.focusWidget()
            if focused is not None and (focused is self.view or self.view.isAncestorOf(focused)):
                focused.clearFocus()
            self._restore(bar, value)

    def _restore(self, bar, value):
        """Back returns the page to where it was before the stock opened. The list's height comes back over the
        next layout passes, so the position is set again each time the range grows, until it is reached, the
        page is moved by someone else (a newly chosen list scrolling to its top) or a stock opens again."""
        placed = []

        def done():
            try:
                bar.rangeChanged.disconnect(place)
            except (TypeError, RuntimeError):
                pass

        def place(*_):
            try:
                if self.scroll is not None or (placed and bar.value() != placed[-1]):
                    done()
                    return
                bar.setValue(value)
                placed.append(bar.value())
                if bar.value() == value:
                    done()
            except RuntimeError:
                pass

        bar.rangeChanged.connect(place)
        place()
        QTimer.singleShot(1500, done)


INTERVAL_GROUPS = (("group_minutes", ("1m", "3m", "5m", "15m", "30m", "60m")),
                   ("group_daily", ("1d", "1w", "1M", "1Y")))
STOCK_INTERVALS = tuple(key for _, keys in INTERVAL_GROUPS for key in keys)


def year_label(year, span, lang):
    """A yearly candle's date: '2025', or for a year that is not a whole calendar year of history (detail_model.
    yearly_span) '2026년 · 11월까지 (진행 중)', '2026년 · 10~11월 (진행 중)', '2013년 · 1~2월 값', '2024년 · 3월 값'."""
    if not span:
        return str(year)
    first, last, running = span
    months = text(lang, "months")
    word = (lambda month: month) if lang == "ko" else (lambda month: months[month - 1])
    if running:
        key = "year_running" if first == 1 else "year_running_one" if first == last else "year_running_from"
    else:
        key = "year_partial_one" if first == last else "year_partial"
    return text(lang, key, year=year, first=word(first), last=word(last))


def interval_words(interval, lang, long=False):
    """'5분' / '일' / '년' for the menu; '5분 단위' / '일 단위' in sentences (long=True). English: '5 min', 'Day'."""
    from core.education.study_guide import _minutes
    minutes = _minutes(interval)
    if minutes:
        return text(lang, "interval_long_min" if long else "interval_min", n=minutes)
    key = ("interval_long_" if long else "interval_") + str(interval)
    from .owner_ui_language.stock import TEXT
    return text(lang, key) if key in TEXT else str(interval)


def unit_fields(interval, lang):
    """The interval's words for the OHLC tooltips and the movement reading: {at} '이날' / '이 주에' ('on this
    day'), {this} '이날' / '이 주' ('this day'), {prev} '전날' ("the previous day's"), {one} '하루' / '5분' ('day')."""
    from core.education.study_guide import _Say, _minutes
    if lang == "ko":
        say = _Say(interval, "ko")
        return {"at": say.at, "this": say.this, "prev": say.unit[3], "one": say.one}
    minutes = _minutes(interval)
    unit = {"1d": "day", "1w": "week", "1M": "month", "1Y": "year"}.get(interval) or (
        "minute" if minutes == 1 else f"{minutes} minutes" if minutes else "candle")
    span = unit if interval in ("1d", "1w", "1M", "1Y") or minutes == 1 else (
        f"{minutes}-minute span" if minutes else "candle")
    return {"at": f"{'on' if interval == '1d' else 'in'} this {span}", "this": f"this {span}",
            "prev": f"the previous {span}'s", "one": unit}


class IntervalDelegate(QStyledItemDelegate):
    """Spec 4.4: the interval list under group captions (분 · 일·주·월·년); a caption is drawn above the first
    deliverable interval of its group."""
    HEAD = 22

    def __init__(self, combo, caption_for):
        super().__init__(combo)
        self.combo, self.caption_for = combo, caption_for

    def caption(self, row):
        data = self.combo.itemData(row)
        model = self.combo.model()
        for key, members in INTERVAL_GROUPS:
            if data in members:
                rows = [r for r in range(self.combo.count()) if self.combo.itemData(r) in members
                        and model.item(r).isEnabled()]
                return self.caption_for(key) if rows and rows[0] == row else ""
        return ""

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), 28) + (self.HEAD if self.caption(index.row()) else 0))
        return size

    def paint(self, painter, option, index):
        from PyQt6.QtWidgets import QStyleOptionViewItem
        caption = self.caption(index.row())
        if caption:
            painter.save()
            font = painter.font()
            font.setPixelSize(11)
            painter.setFont(font)
            painter.setPen(option.palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text))
            head = option.rect.adjusted(10, 0, -6, 0)
            head.setHeight(self.HEAD)
            painter.drawText(head, int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom), caption)
            painter.restore()
            option = QStyleOptionViewItem(option)
            option.rect.setTop(option.rect.top() + self.HEAD)
        super().paint(painter, option, index)


class IntervalCombo(QComboBox):
    """The toolbar's interval menu with its own items (owner R-D9-2: "1분 / 5분 … / 일 / 주 / 월 / 년"): what the
    routers cannot deliver for this stock is left out of the list. Its width follows the interval shown."""

    def __init__(self):
        super().__init__()
        self.currentIndexChanged.connect(lambda _index: self.updateGeometry())

    def fill(self, names, enabled, current):
        """Items for STOCK_INTERVALS named by `names` (key -> text), enabled by `enabled` (key -> bool), showing
        `current` (an interval key) without emitting a choice."""
        self.blockSignals(True)
        if [self.itemData(i) for i in range(self.count())] != list(STOCK_INTERVALS):
            self.clear()
            for key in STOCK_INTERVALS:
                self.addItem(names[key], key)
        model = self.model()
        for row, key in enumerate(STOCK_INTERVALS):
            if self.itemText(row) != names[key]:
                self.setItemText(row, names[key])
            model.item(row).setEnabled(bool(enabled.get(key)))
        index = self.findData(current)
        if index != self.currentIndex():
            self.setCurrentIndex(index)
        self.blockSignals(False)
        self.updateGeometry()

    def sizeHint(self):
        # Qt's own hint fits the longest name plus the frame, padding and arrow; keep that chrome around the
        # name shown instead.
        hint = super().sizeHint()
        metrics = self.fontMetrics()
        longest = max((metrics.horizontalAdvance(self.itemText(row)) for row in range(self.count())), default=0)
        chrome = max(46, hint.width() - longest)
        return QSize(max(72, metrics.horizontalAdvance(self.currentText()) + chrome), hint.height())

    def minimumSizeHint(self):
        return self.sizeHint()

    def showPopup(self):
        model, view = self.model(), self.view()
        for row in range(self.count()):
            item = model.item(row)
            view.setRowHidden(row, item is not None and not item.isEnabled())
        super().showPopup()


class ChartColumn(QFrame):
    """The chart and its period bar. It holds the keyboard focus while the chart itself is hidden (loading, empty
    or failed), so the arrows, +/−, 0 and Shift+F already belong to the chart the moment a stock opens; the chart
    takes the focus over when it appears."""

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.setObjectName("sdChartColumn")
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

    def keyPressEvent(self, event):
        if self.view.chart_key(event):
            event.accept()
            return
        super().keyPressEvent(event)


class ChartKeys(QObject):
    """Owner 2026-11-11: "pc기준 좌우화살표로 차트 좌우 확인할수있게". While the stock screen is shown, ←/→, Home/End,
    +/− and 0 move the chart wherever the focus is on it: after a click on a picker switch, a fold header, a tab,
    the column's background or a toolbar button too (buttons and the scroll areas would otherwise take the arrows).
    Text inputs keep their keys, and nothing is taken while a menu or a list is open."""
    KEYS = (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Home, Qt.Key.Key_End, Qt.Key.Key_Plus, Qt.Key.Key_Equal,
            Qt.Key.Key_Minus, Qt.Key.Key_Underscore, Qt.Key.Key_0)

    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self.installed = False

    def install(self, on):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None or on == self.installed:
            return
        (app.installEventFilter if on else app.removeEventFilter)(self)
        self.installed = on

    def eventFilter(self, watched, event):
        if event.type() != QEvent.Type.KeyPress or event.key() not in self.KEYS:
            return False
        from PyQt6.QtWidgets import QAbstractSpinBox, QApplication, QPlainTextEdit, QTextEdit
        view = self.view
        if not isinstance(watched, QWidget) or not view.isVisible() or QApplication.activePopupWidget() is not None:
            return False
        if not (watched is view or view.isAncestorOf(watched)):
            return False
        if isinstance(watched, (QLineEdit, QAbstractSpinBox, QTextEdit, QPlainTextEdit)) or \
                (isinstance(watched, QComboBox) and watched.isEditable()):
            return False
        if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier |
                                Qt.KeyboardModifier.MetaModifier):
            return False
        if view.chart_key(event):
            event.accept()
            return True
        return False


class DetailBody(QWidget):
    """Chart column and right column side by side (owner R-D9-1: nothing ever covers the chart). The column keeps
    the user's show/hide choice; focus mode hides it; the chart always takes the rest of the width."""
    mode_changed = pyqtSignal()

    def __init__(self, chart_column, side):
        super().__init__()
        self.setObjectName("sdBody")
        self.chart_column, self.side = chart_column, side
        chart_column.setParent(self)
        side.setParent(self)
        self.side_pref = True      # the user's show/hide choice
        self.focus = False         # focus mode hides the column
        self.setMinimumSize(CHART_MIN, 300)

    def side_width(self, width=None):
        width = self.width() if width is None else width
        return 380 if width >= 1320 else 360 if width >= 1120 else 340 if width >= 940 else 320

    def side_shown(self):
        return self.side_pref and not self.focus

    def chart_width(self, width=None):
        """The chart column's width at a body `width`, with the column as it is shown now."""
        width = self.width() if width is None else width
        if not self.side_shown():
            return width
        side = max(SIDE_MIN, min(self.side_width(width), width - SIDE_GAP - CHART_MIN))
        return width - side - SIDE_GAP

    def relayout(self):
        width, height = self.width(), self.height()
        chart = self.chart_width(width)
        self.chart_column.setGeometry(0, 0, chart, height)
        if self.side_shown():
            self.side.setGeometry(chart + SIDE_GAP, 0, width - chart - SIDE_GAP, height)
            self.side.show()
        else:
            self.side.hide()
        self.mode_changed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.relayout()


class FitLabel(ElidedLabel):
    """The stock's name: keeps its whole text (text() is the full name), asks for its full width and paints it
    elided only when the toolbar cannot give that much."""

    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

    def sizeHint(self):
        return QSize(self.fontMetrics().horizontalAdvance(self.text()) + 2, super().sizeHint().height())

    def minimumSizeHint(self):
        return QSize(min(self.sizeHint().width(), 64), super().minimumSizeHint().height())


class OhlcStrip(QFrame):
    """Line 1 of the chart header: the selected candle's open, high, low, close, change and volume."""

    def __init__(self):
        super().__init__()
        self.setProperty("sd", "overlay")
        row = QHBoxLayout(self)
        row.setContentsMargins(6, 0, 8, 0)
        row.setSpacing(5)
        self.title = label("ohlcTitle")
        row.addWidget(self.title)
        self.date = numbers(label("ohlcDate"))
        row.addWidget(self.date)
        row.addSpacing(6)
        self.keys, self.values = {}, {}
        for name in ("o", "h", "l", "c"):
            key, value = label("ohlcKey"), numbers(label("ohlcValue"))
            row.addWidget(key)
            row.addWidget(value)
            row.addSpacing(4)
            self.keys[name], self.values[name] = key, value
        self.change = numbers(label("ohlcValue"))
        row.addWidget(self.change)
        row.addSpacing(8)
        self.keys["v"], self.values["v"] = label("ohlcKey"), numbers(label("ohlcValue"))
        row.addWidget(self.keys["v"])
        row.addWidget(self.values["v"])
        row.addStretch(1)


class ChartOverlays(QObject):
    """Qt text over the SVG chart, placed from detail_svg.ChartLayout: the OHLC strip, the overlay legend, one
    header per sub-panel (values and the beginner reading at the selected candle, ⓘ, ×) and notice chips."""
    info_requested = pyqtSignal(str)
    off_requested = pyqtSignal(str)

    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self.chart = view.chart.chart
        self.ohlc = OhlcStrip()
        self.ohlc.setParent(self.chart)
        self.legend = QFrame(self.chart)
        self.legend.setProperty("sd", "overlay")
        legend = QHBoxLayout(self.legend)
        legend.setContentsMargins(6, 0, 8, 0)
        legend.setSpacing(14)
        self.legend_label = rich("legend")
        legend.addWidget(self.legend_label)
        legend.addStretch(1)
        self.heads = {}
        self.notice = QFrame(self.chart)
        self.notice.setProperty("sd", "overlayClear")
        notice = QHBoxLayout(self.notice)
        notice.setContentsMargins(0, 0, 0, 0)
        notice.setSpacing(6)
        # A wheel turn over the chart changes nothing (owner 2026-11-11); for a moment the keys are named instead.
        self.wheel_label = label("notice")
        self.wheel_label.hide()
        notice.addWidget(self.wheel_label)
        self.wheel_timer = QTimer(self)
        self.wheel_timer.setSingleShot(True)
        self.wheel_timer.setInterval(2600)
        self.wheel_timer.timeout.connect(self.refresh)
        self.chart.wheel_ignored.connect(self.wheel_turned)
        self.hidden_label = label("notice")
        notice.addWidget(self.hidden_label)
        self.latest_button = QPushButton()
        self.latest_button.setProperty("sd", "notice")
        self.latest_button.setProperty("qg_literal", True)
        self.latest_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.latest_button.clicked.connect(lambda: (view.chart.follow_latest(), view.focus_chart()))
        notice.addWidget(self.latest_button)
        for widget in (self.ohlc, self.legend, self.notice):
            widget.hide()

    def wheel_turned(self):
        first = not self.wheel_timer.isActive()
        self.wheel_timer.start()
        if first:
            self.refresh()

    def _head(self, key):
        head = self.heads.get(key)
        if head is None:
            head = QFrame(self.chart)
            head.setProperty("sd", "overlayClear")
            row = QHBoxLayout(head)
            row.setContentsMargins(4, 0, 2, 0)
            row.setSpacing(8)
            head.title = rich("panelTitle")
            row.addWidget(head.title)
            head.reading = label("reading")
            head.reading.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            row.addWidget(head.reading, 1)
            head.info = QPushButton()
            head.info.setProperty("sd", "mini")
            head.info.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            head.info.clicked.connect(lambda checked=False, k=key: self.info_requested.emit(k))
            row.addWidget(head.info)
            head.off = QPushButton()
            head.off.setProperty("sd", "mini")
            head.off.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            head.off.clicked.connect(lambda checked=False, k=key: self.off_requested.emit(k))
            row.addWidget(head.off)
            head.full = ""
            self.heads[key] = head
        return head

    def hide_all(self):
        for widget in (self.ohlc, self.legend, self.notice, *self.heads.values()):
            widget.hide()

    def refresh(self):
        """Texts at the selected candle and positions from the chart's last layout. Everything stays in the bands
        detail_svg leaves empty (owner R-D9-1): the OHLC strip on the header's first row, the legend and the
        notices on its second, each sub-panel's header in its own top rows."""
        from core.education import indicators as engine
        from core.education.study_guide import availability_short, line_readout, short_reading, study_reading
        from core.market.detail_model import yearly_span
        from core.market.detail_svg import compact
        from core.market.presentation import study_colors
        view, pane = self.view, self.view.chart
        layout = self.chart.layout_info
        snapshot = pane.snapshot
        if layout is None or snapshot is None or not snapshot.candles or not self.chart.isVisible():
            self.hide_all()
            return
        lang, dark = _lang(view.ctx), view.dark
        candles = snapshot.candles
        n = len(candles)
        cursor = max(0, min(n - 1, layout.cursor))
        candle = candles[cursor]
        width = layout.plot_right - layout.plot_left
        band = layout.width - layout.plot_left - 6     # the header band runs over the price axis too
        compact_labels = width < 600
        # OHLC strip.
        strip = self.ohlc
        interval = snapshot.request.interval
        strip.title.setText(f"{view.name.text()} · {interval_words(interval, lang, long=True)}")
        strip.title.setVisible(width >= 700)
        stamp = str(candle.timestamp)
        if interval == "1Y":
            year = int(stamp[:4])
            date = year_label(year, yearly_span(snapshot).get(year), lang)
            strip.date.setText(date)
            strip.date.setToolTip(date)
            strip.date.setVisible(True)
        else:
            intraday = interval not in ("1d", "1w", "1M")
            shown = stamp[5:16].replace("T", " ") if intraday else stamp[:7] if interval == "1M" else stamp[:10]
            strip.date.setText(shown if cursor != n - 1 else "")
            strip.date.setVisible(cursor != n - 1)
        terms = {"o": "term_open", "h": "term_high", "l": "term_low", "c": "term_close"}
        values = {"o": candle.open, "h": candle.high, "l": candle.low, "c": candle.close}
        words = unit_fields(interval, lang)
        for name in ("o", "h", "l", "c"):
            strip.keys[name].setText(text(lang, f"{name}_short" if compact_labels else name))
            strip.values[name].setText(view.price_text(values[name]))
            strip.keys[name].setToolTip(text(lang, terms[name], **words))
            strip.values[name].setToolTip(text(lang, terms[name], **words))
        previous = candles[cursor - 1].close if cursor > 0 else None
        tone = ""
        if previous:
            change = candle.close - previous
            pct = change / previous * 100
            arrow = "▲" if change > 0 else "▼" if change < 0 else "–"
            tone = "up" if change > 0 else "down" if change < 0 else ""
            sign = "+" if change > 0 else "−" if change < 0 else ""
            strip.change.setText(f"{arrow} {sign}{view.price_text(abs(change))} ({sign}{abs(pct):.2f}%)")
            short_change = f"{arrow} {sign}{abs(pct):.2f}%"
        else:
            strip.change.setText("")
        set_prop(strip.change, "tone", tone)
        set_prop(strip.values["c"], "tone", tone)
        strip.change.setToolTip(text(lang, "term_change", **words))
        volume = candle.volume
        # Korean units in the Korean view, like the legend's volume average and the right column (871만, not 8.71M).
        strip.values["v"].setText(view.volume_text(volume))
        full = f"{volume:,.0f}" if volume is not None and math.isfinite(volume) else "—"
        strip.keys["v"].setText(text(lang, "v"))
        for widget in (strip.keys["v"], strip.values["v"]):
            widget.setToolTip(text(lang, "term_volume", full=full, **words))
        # Never a cut figure: when the row is too long the change keeps its percent, then a running year's date
        # its short form (the full one stays in its tooltip), then the volume leaves the row.
        strip.keys["v"].show()
        strip.values["v"].show()
        if strip.sizeHint().width() > band and previous:
            strip.change.setText(short_change)
        if strip.sizeHint().width() > band and interval == "1Y" and "(" in strip.date.text():
            strip.date.setText(strip.date.text().split(" (")[0])
        if strip.sizeHint().width() > band:
            strip.keys["v"].hide()
            strip.values["v"].hide()
        strip.setGeometry(int(layout.plot_left), 6, int(band), OVERLAY_ROW)
        strip.show()
        strip.raise_()
        # Notices: the header's second row, at its right end (hidden panels, back to the latest, the wheel's keys).
        hidden = len(layout.hidden_panels)
        names = ", ".join(engine.study(key).name(lang) for key in layout.hidden_panels)
        self.hidden_label.setText(text(lang, "hidden_panels", count=hidden))
        self.hidden_label.setToolTip(text(lang, "hidden_panels_tip", names=names) if hidden else "")
        self.hidden_label.setVisible(bool(hidden))
        panned = pane._end is not None
        self.latest_button.setText(text(lang, "to_latest"))
        self.latest_button.setToolTip(text(lang, "to_latest_tip"))
        self.latest_button.setVisible(panned)
        wheel = self.wheel_timer.isActive()
        self.wheel_label.setText(text(lang, "wheel_hint"))
        self.wheel_label.setVisible(wheel)
        notice_width = 0
        if hidden or panned or wheel:
            self.notice.adjustSize()
            size = self.notice.sizeHint()
            notice_width = min(size.width(), int(band))
            self.notice.setGeometry(int(layout.plot_left + band - notice_width), 32, notice_width, min(24, size.height()))
            self.notice.show()
            self.notice.raise_()
        else:
            self.notice.hide()
        # Overlay legend: the same row, left of the notices.
        bars = view.engine_bars()
        chips = []
        tips = []
        for key in pane.selected_indicators():
            spec = engine.study(key)
            if not spec.overlay:
                continue
            colors = study_colors(key, dark)
            if key in layout.unavailable:
                chips.append(f'<span style="color:{colors[spec.lines[0].id]}">●</span>&ensp;{_esc(spec.name(lang))} '
                             f'<span style="color:{view.palette.muted}">— {_esc(polite(availability_short(layout.unavailable[key], lang), lang))}</span>')
                continue
            try:
                readout = line_readout(key, bars, cursor, language=lang, supply=pane.supply)
            except Exception:
                readout = ()
            parts = " · ".join(f'<span style="color:{colors[line.id]}">{_esc(name)}</span> '
                               f'{_esc(view.study_value(key, line, cursor, value))}'
                               for line, (name, value) in zip(spec.lines, readout))
            chips.append(f'<span style="color:{colors[spec.lines[0].id]}">●</span>&ensp;{parts}')
            tips.append(spec.name(lang))
        # One row: the chips that fit, then '외 n개' for the rest (their names in the tooltip), never a cut word.
        room = int(band) - 8 - (notice_width + 12 if notice_width else 0)
        for count in range(len(chips), 0, -1):
            rest = len(chips) - count
            more = (f'&nbsp;&nbsp;<span style="color:{view.palette.muted}">'
                    f'{_esc(text(lang, "legend_more", count=rest))}</span>') if rest else ""
            self.legend_label.setText("&nbsp;&nbsp;&nbsp;".join(chips[:count]) + more)
            if self.legend_label.sizeHint().width() <= room:
                break
        self.legend_label.setToolTip(" · ".join(tips) if len(tips) > 1 else "")
        self.legend.setVisible(bool(chips))
        if chips:
            self.legend.setGeometry(int(layout.plot_left), 32, max(40, room), 22)
            self.legend.raise_()
        # Panel headers: the short reading on the panel (the full one in the tooltip and behind ⓘ).
        shown = set()
        for key, top, bottom in layout.panels:
            spec = engine.study(key)
            head = self._head(key)
            shown.add(key)
            colors = study_colors(key, dark)
            name = spec.name(lang)
            if key in layout.unavailable:
                head.title.setText(f'<span style="color:{colors[spec.lines[0].id]}">●</span>&ensp;'
                                   f'<b>{_esc(panel_name(spec, lang))}</b>')
                reading = polite(availability_short(layout.unavailable[key], lang), lang)
                brief = reading
                head.full = text(lang, "panel_info", name=name) + "\n" + reading
            else:
                try:
                    readout = line_readout(key, bars, cursor, language=lang, supply=pane.supply)
                    reading = study_reading(key, bars, cursor, language=lang, supply=pane.supply)
                    brief = short_reading(key, bars, cursor, language=lang, supply=pane.supply)
                except Exception:
                    readout, reading, brief = (), "", ""
                head.title.setText(f'<span style="color:{colors[spec.lines[0].id]}">●</span>&ensp;'
                                   f'<b>{_esc(panel_name(spec, lang))}</b>&nbsp; '
                                   f'{view.values_html(key, spec, readout, cursor, colors)}')
                head.full = polite(reading, lang)
            # The title already shows the values: the header keeps the words after them ('내린 폭이 훨씬 컸어요'),
            # and only when they fit whole.
            head.brief = brief.split(" · ", 1)[1] if " · " in brief and any(ch.isdigit() for ch in brief.split(" · ", 1)[0]) else brief
            room = int(band) - head.title.sizeHint().width() - 70
            fits = head.reading.fontMetrics().horizontalAdvance(head.brief) <= room
            head.reading.setText(head.brief if fits else "")
            head.reading.setToolTip(head.full)
            head.title.setToolTip(head.full)
            head.info.setIcon(icon("info", view.palette.muted, 15))
            head.off.setIcon(icon("close", view.palette.muted, 15))
            head.info.setToolTip(text(lang, "panel_info", name=name))
            head.info.setAccessibleName(text(lang, "panel_info", name=name))
            head.off.setToolTip(text(lang, "panel_off", name=name))
            head.off.setAccessibleName(text(lang, "panel_off", name=name))
            # The header row runs over the price axis too (the axis labels start under it).
            head.setGeometry(int(layout.plot_left), int(top + 1), int(band), OVERLAY_ROW)
            head.show()
            head.raise_()
        for key, head in self.heads.items():
            if key not in shown:
                head.hide()

class PeriodBar(QWidget):
    """Period chips on the left; pan, zoom and the default view on the right."""

    def __init__(self, view):
        super().__init__()
        from core.market.detail_model import PERIOD_KEYS
        self.view = view
        self.setObjectName("sdPeriods")
        self.setFixedHeight(40)
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 2, 4, 2)
        row.setSpacing(2)
        self.buttons = {}
        for key in PERIOD_KEYS:
            button = QPushButton()
            button.setProperty("sd", "period")
            button.setProperty("qg_literal", True)
            button.setCheckable(True)
            button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, k=key: view.choose_period(k))
            row.addWidget(button)
            self.buttons[key] = button
        row.addStretch(1)
        self.hint = label("hint")
        row.addWidget(self.hint)
        row.addSpacing(8)
        self.left, self.right, self.zoom_out, self.zoom_in = (QPushButton() for _ in range(4))
        actions = ((self.left, lambda: view.chart.pan(-10)), (self.right, lambda: view.chart.pan(10)),
                   (self.zoom_out, lambda: view.chart.zoom(-1)), (self.zoom_in, lambda: view.chart.zoom(1)))
        for button, action in actions:
            button.setProperty("sd", "tool")
            button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            button.setAutoRepeat(True)
            button.clicked.connect(lambda checked=False, a=action: (a(), view.focus_chart()))
            row.addWidget(button)
        self.reset = QPushButton()
        self.reset.setProperty("sd", "text")
        self.reset.setProperty("qg_literal", True)
        self.reset.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.reset.clicked.connect(lambda: (view.chart.reset_view(), view.focus_chart()))
        row.addSpacing(4)
        row.addWidget(self.reset)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()

    def fit(self):
        """Keep the period chips; then, as room allows, the zoom buttons, '기본 보기', the pan arrows and the
        key hint '← → 이동 · + − 확대' (the wheel no longer moves the chart, so the keys are named on the bar
        whenever it fits; spec 4.1)."""
        layout = self.layout()
        margins = layout.contentsMargins()
        spacing = layout.spacing()
        room = self.width() - margins.left() - margins.right()
        chips = sum(button.sizeHint().width() + spacing for button in self.buttons.values())
        zoom = sum(button.sizeHint().width() + spacing for button in (self.zoom_out, self.zoom_in))
        reset = self.reset.sizeHint().width() + spacing + 4
        pan = sum(button.sizeHint().width() + spacing for button in (self.left, self.right))
        hint = self.hint.sizeHint().width() + spacing + 8
        used = chips + zoom + 16
        show_reset = used + reset <= room
        used += reset if show_reset else 0
        show_pan = used + pan <= room
        used += pan if show_pan else 0
        self.reset.setVisible(show_reset)
        for button in (self.left, self.right):
            button.setVisible(show_pan)
        self.hint.setVisible(used + hint <= room)


class NotesBox(QFrame):
    """ⓘ: the pane's availability note, data notes, notices and the update settings, at the end of the right
    column's stock page (owner R-D9-1: no popup over the chart)."""

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.setProperty("sd", "notesBox")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        self.title = label("cardTitle")
        head.addWidget(self.title, 1)
        self.close_button = QPushButton()
        self.close_button.setProperty("sd", "mini")
        self.close_button.clicked.connect(self.hide)
        head.addWidget(self.close_button)
        layout.addLayout(head)
        self.body = label("body", wrap=True, selectable=True)
        layout.addWidget(self.body)
        self.poll = QCheckBox()
        self.poll.setProperty("qg_literal", True)
        self.poll.toggled.connect(lambda on: view.chart.poll_button.setChecked(on))
        layout.addWidget(self.poll)
        self.stream = QPushButton()
        self.stream.setProperty("sd", "text")
        self.stream.setProperty("qg_literal", True)
        self.stream.clicked.connect(lambda: (view.chart.start_stream(), self.hide()))
        layout.addWidget(self.stream, 0, Qt.AlignmentFlag.AlignLeft)

    def fill(self):
        """Titles, icons and texts in the window's language and theme, then the notes themselves."""
        view = self.view
        lang = _lang(view.ctx)
        self.title.setText(text(lang, "notes_section"))
        self.close_button.setIcon(icon("close", view.palette.muted, 15))
        self.close_button.setToolTip(text(lang, "notes_close"))
        self.close_button.setAccessibleName(text(lang, "notes_close"))
        self.poll.setText(text(lang, "notes_poll"))
        self.poll.setToolTip(text(lang, "notes_poll_tip"))
        self.stream.setText(text(lang, "notes_stream"))
        self.stream.setToolTip(text(lang, "notes_stream_tip"))
        self.refresh()

    def refresh(self):
        """The notes of the chart shown now (the view calls this whenever the feed's state or the chart changes,
        so the box never keeps another stock's or another interval's notes)."""
        view, pane = self.view, self.view.chart
        lang = _lang(view.ctx)
        facts = pane.feed_facts()
        lines = [plain_ages(facts["status"], lang), facts["notice"], facts["availability"], facts["note"]]
        body = polite("\n\n".join(line for line in dict.fromkeys(lines) if line), lang)
        if body != self.body.text():
            self.body.setText(body)
        self.poll.blockSignals(True)
        self.poll.setChecked(pane.poll_button.isChecked())
        self.poll.setEnabled(pane.poll_button.isEnabled())
        self.poll.blockSignals(False)
        self.stream.setEnabled(pane.stream_button.isEnabled())


class StockDetailView(QWidget):
    """Toolbar, the large chart with its period bar, and the right column for one instrument."""
    back_requested = pyqtSignal()
    watch_toggled = pyqtSignal(object, bool)
    open_requested = pyqtSignal(object)
    guide_requested = pyqtSignal(str)

    def __init__(self, chart, *, store, profile_loader=None, name_fn=None, locale=None, auto_load=True,
                 directory=None, directory_loader=None, quote_router_factory=None):
        super().__init__()
        self.setObjectName("stockDetail")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # The page gives this view its width; the toolbar adapts (_fit_toolbar) instead of widening the page.
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.chart, self.store = chart, store
        self.profile_loader = profile_loader
        self.name_fn = name_fn or (lambda instrument, lang: instrument.code)
        self.ctx, self.dark, self.auto_load = locale or LocaleContext("ko_KR"), False, auto_load
        self.palette = LIGHT
        self.instrument, self.profile = None, None
        self.directory, self.directory_loader = directory, directory_loader
        self._epoch = 0
        self._live_price = None
        self._reload, self._job_epoch = False, -1
        self._routable = None
        self._bars_cache = (None, None)
        self._side_snapshot = None
        self._rail_owner = None      # the rail as the owner left it, while this screen folded it (focus or narrow)
        self._rail_yield = False     # the owner moved the rail themselves while this screen was shown
        self._rail_saved = None      # the shell's saved rail choice when this screen folded the rail
        self._rail_hooked = None
        self._window_width = None
        self._compact, self._level = False, 0
        self.studies = self._stored_studies()
        self._technical_open = set()   # studies whose reading row is unfolded (자세히)
        self.period = self._stored_period()   # the last period chip; an interval choice leaves it as it was
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._profile_loaded)
        self.jobs.failed.connect(self._profile_failed)
        self.jobs.busy_changed.connect(self._jobs_busy)
        self.lock = PageLock(self)
        self.keys = ChartKeys(self)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 12, 0, 12)
        root.setSpacing(10)
        root.addWidget(self._build_toolbar())
        self.chart_column = ChartColumn(self)
        column = QVBoxLayout(self.chart_column)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)
        self.chart_slot = QVBoxLayout()
        self.chart_slot.setContentsMargins(0, 0, 0, 0)
        column.addLayout(self.chart_slot, 1)
        self.periods = PeriodBar(self)
        column.addWidget(self.periods)
        factory = quote_router_factory or self._window_card_router
        self.side = RightColumn(store=store, name_fn=self.name_fn, router_factory=factory, auto_load=auto_load,
                                locale=self.ctx)
        self.side.watchlist.open_requested.connect(self._open)
        self.side.now.study_requested.connect(self.turn_on)
        self.side.page_changed.connect(lambda index: self._refresh_side(force=True) if index == 1 else None)
        self.side.retry_button.clicked.connect(self.load_profile)
        for key, section in self.side.sections.items():
            section.set_open(self._section_open(key, section.is_open))
            section.toggled.connect(self._section_toggled)
        from .indicator_picker import IndicatorPicker
        self.picker = IndicatorPicker(locale=self.ctx)
        self.picker.price_format = self.price_text
        self.picker.volume_format = self.volume_text
        self.picker.set_selected(self.studies)
        self.picker.changed.connect(self.set_studies)
        self.side.indicator_layout.addWidget(self.picker)
        self.body = DetailBody(self.chart_column, self.side)
        self.body.side_pref = self._setting("side", "shown") != "hidden"
        root.addWidget(self.body, 1)
        self.profile_status = self.side.profile_status
        self.price, self.change = self.side.card.price, self.side.card.change
        self.section_panels = []
        self.notes = NotesBox(self)
        self.notes.hide()
        page = self.side.stock_page.layout()
        page.insertWidget(page.count() - 1, self.notes)
        self.overlays = ChartOverlays(self)
        self.overlays.info_requested.connect(self.explain)
        self.overlays.off_requested.connect(self.turn_off)
        self.side_timer = QTimer(self)
        self.side_timer.setSingleShot(True)
        self.side_timer.setInterval(1200)
        self.side_timer.timeout.connect(self._refresh_side)
        chart.snapshot_loaded.connect(self._chart_loaded)
        chart.trade_received.connect(self._chart_tick)
        chart.rendered.connect(self._chart_rendered)
        chart.q_score_changed.connect(self._render_qscore)
        chart.age_timer.timeout.connect(self._render_state)
        # Loading and failing change the feed mode without a render: the chip and card follow the mode itself.
        chart.feed_state_changed.connect(self._feed_state_changed)
        # One overlay pass per event-loop turn: a render emits both layout_changed and rendered.
        self.overlay_timer = QTimer(self)
        self.overlay_timer.setSingleShot(True)
        self.overlay_timer.setInterval(0)
        self.overlay_timer.timeout.connect(self.overlays.refresh)
        # (Bound methods, not lambdas: Qt drops them with this view, the shared pane outlives it.)
        chart.chart.layout_changed.connect(self._chart_layout_changed)
        store.changed.connect(self._watch_changed)
        self.set_theme(False)
        self.set_locale(self.ctx)

    def _feed_state_changed(self, _mode):
        self._render_state()

    def _chart_layout_changed(self, _layout):
        self.overlay_timer.start()

    # Construction ----------------------------------------------------------------------------
    def _build_toolbar(self):
        bar = QFrame()
        bar.setObjectName("sdToolbar")
        self.toolbar = bar
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self.back_button = QPushButton()
        self.back_button.setProperty("sd", "back")
        self.back_button.setProperty("qg_literal", True)
        self.back_button.clicked.connect(self.back_requested)
        row.addWidget(self.back_button)
        row.addSpacing(4)
        self.mark = CompanyMark("", size=34)
        self.mark.hide()
        row.addWidget(self.mark, 0, Qt.AlignmentFlag.AlignVCenter)
        names = QVBoxLayout()
        names.setSpacing(0)
        names.setContentsMargins(0, 0, 0, 0)
        self.names_box = names
        self.name = FitLabel()
        self.name.setProperty("sd", "name")
        names.addWidget(self.name)
        code_row = QHBoxLayout()
        code_row.setContentsMargins(0, 0, 0, 0)
        code_row.setSpacing(8)
        self.code_row = code_row
        self.code = label("code")
        code_row.addWidget(self.code)
        # Narrow windows: the market state moves under the name instead of leaving the toolbar.
        self.state_inline = label("stateInline")
        self.state_inline.hide()
        code_row.addWidget(self.state_inline)
        code_row.addStretch(1)
        names.addLayout(code_row)
        row.addLayout(names)
        row.addSpacing(6)
        self.state_chip = label("chip")
        row.addWidget(self.state_chip, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addStretch(1)
        self.search = QLineEdit()
        self.search.setObjectName("sdSearch")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(SEARCH_WIDE)
        self.search.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.search.returnPressed.connect(self._search_submit)
        row.addWidget(self.search)
        self.completer = None
        if self.directory is not None:
            from .markets_view import STOCK_ASSETS, attach_symbol_search
            self.completer = attach_symbol_search(self.search, self.directory, assets=STOCK_ASSETS, locale=self.ctx,
                                                  loader=self.directory_loader)
            self.completer.chosen.connect(self._search_chosen)
        else:
            self.search.hide()
        self.interval_combo = IntervalCombo()
        self.interval_combo.setObjectName("sdInterval")
        self.interval_combo.setProperty("qg_literal", True)
        self.interval_combo.view().setMinimumWidth(160)   # the popup lists the names at full width
        self.interval_combo.setItemDelegate(IntervalDelegate(self.interval_combo,
                                                             lambda key: text(_lang(self.ctx), key)))
        self.interval_combo.activated.connect(self._interval_chosen)
        self.chart.interval.currentIndexChanged.connect(self._sync_interval)
        row.addWidget(self.interval_combo)
        self.indicators_button = QPushButton()
        self.indicators_button.setProperty("sd", "text")
        self.indicators_button.setProperty("qg_literal", True)
        self.indicators_button.clicked.connect(self.show_indicators)
        row.addWidget(self.indicators_button)
        self.watch_button = QPushButton()
        self.watch_button.setCheckable(True)
        self.watch_button.setProperty("sd", "text")
        self.watch_button.setProperty("qg_literal", True)
        self.watch_button.clicked.connect(self._toggle_watch)
        row.addWidget(self.watch_button)
        tools = QHBoxLayout()
        tools.setContentsMargins(0, 0, 0, 0)
        tools.setSpacing(2)
        self.tools_box = tools
        self.refresh_button, self.pause_button, self.notes_button, self.focus_button, self.side_button, \
            self.more_button = (QPushButton() for _ in range(6))
        for button in (self.refresh_button, self.pause_button, self.notes_button, self.more_button,
                       self.focus_button, self.side_button):
            button.setProperty("sd", "tool")
            button.setProperty("qg_literal", True)
            button.setIconSize(icon_size(18))
            tools.addWidget(button)
        row.addLayout(tools)
        self.focus_button.setCheckable(True)
        self.side_button.setCheckable(True)
        self.refresh_button.clicked.connect(self.refresh)
        self.pause_button.clicked.connect(self._pause_clicked)
        self.notes_button.clicked.connect(self._show_notes)
        self.focus_button.clicked.connect(lambda checked: self.set_focus_mode(checked))
        self.side_button.clicked.connect(lambda checked: self.set_side_shown(checked))
        # Spec 2.3, under 1000px: stop/reconnect and the data notes move into a ⋯ menu.
        self.more_menu = QMenu(self.more_button)
        self.more_pause = self.more_menu.addAction("")
        self.more_pause.triggered.connect(self._pause_clicked)
        self.more_notes = self.more_menu.addAction("")
        self.more_notes.triggered.connect(lambda: self._show_notes(anchor=self.more_button))
        self.more_button.clicked.connect(self._show_more)
        self.more_button.hide()
        return bar

    # Settings --------------------------------------------------------------------------------
    def _settings(self):
        return getattr(self.store, "settings", None)

    def _setting(self, key, default):
        settings = self._settings()
        if settings is None:
            return getattr(self, "_memory", {}).get(key, default)
        value = settings.value(SETTINGS_PREFIX + key)
        return default if value is None else value

    def _remember(self, key, value):
        settings = self._settings()
        if settings is None:
            self.__dict__.setdefault("_memory", {})[key] = value
        else:
            settings.setValue(SETTINGS_PREFIX + key, value)

    def _stored_json(self, key, kind):
        """A JSON setting of the given type, or None. Saved settings are shared by every build of the app, so a
        value written by another version (a renamed study, a number where a list belongs) is never trusted."""
        raw = self._setting(key, None)
        try:
            value = json.loads(raw) if isinstance(raw, str) else None
        except ValueError:
            return None
        return value if isinstance(value, kind) else None

    def _stored_studies(self):
        keys = self._stored_json("indicators", list)
        if keys is None:
            return DEFAULT_STUDIES
        chosen = valid_studies(keys)
        # Every stored key unknown (another build's names): the starter set instead of an empty chart.
        return chosen if chosen or not keys else DEFAULT_STUDIES

    def _stored_period(self):
        from core.market.detail_model import DEFAULT_PERIOD, PERIOD_KEYS
        value = self._setting("period", DEFAULT_PERIOD)
        return value if value in PERIOD_KEYS else DEFAULT_PERIOD

    def _section_open(self, key, default):
        states = self._stored_json("sections", dict) or {}
        return bool(states.get(key, default))

    def _section_toggled(self, key, is_open):
        states = self._stored_json("sections", dict) or {}
        states[key] = bool(is_open)
        self._remember("sections", json.dumps(states))

    def _window_card_router(self):
        factory = getattr(self.window(), "card_router_factory", None)
        if factory is None:
            from .app import _production_card_router as factory
        return factory()

    # Chart adoption and the open stock ----------------------------------------------------------
    def adopt_chart(self):
        """Move the shared chart pane into this view (it lives in one place at a time) in detail mode."""
        if self.chart.parent() is not self.chart_column:
            self.chart_slot.addWidget(self.chart, 1)
        self.chart.empty_hint = self._empty_hint
        self.chart.chart.key_handler = self.chart_key
        self.chart.set_detail_mode(True)
        if self.chart._studies is None:
            self.chart.set_indicators(self.studies)
        if self.chart.period is None and self.chart.snapshot is None:
            self.chart.apply_period(self.period if self.period in self.periods.buttons else DEFAULT_PERIOD)
        self._sync_interval(force=True)
        self.chart.show()

    def _empty_hint(self, mode, waiting):
        lang = _lang(self.ctx)
        if waiting:
            return text(lang, "empty_waiting")
        if mode == "loading":
            return text(lang, "empty_loading")
        if mode in ("error", "stale"):
            return text(lang, "empty_error")
        return text(lang, "empty_idle")

    def show_instrument(self, instrument, *, load=True):
        self.instrument = instrument
        self.profile = None
        self._live_price = None
        self._epoch += 1
        self._side_snapshot = None
        self.adopt_chart()
        if self.chart.asset.currentData() != instrument.asset:
            self.chart.set_asset_class(instrument.asset)
        index = self.chart.exchange.findData(instrument.exchange)
        if index >= 0:
            self.chart.exchange.setCurrentIndex(index)
        self.chart.symbol.setText(instrument.code)
        self.chart.supply = None
        self._routable = None
        self.chart.apply_period(self.opening_period())
        self._clear_sections()
        self.render_header()
        self._watch_changed()
        self.side.watchlist.set_current(instrument)
        lang = _lang(self.ctx)
        self.profile_status.setText("" if instrument.asset in ("domestic_stock", "overseas_stock") else
                                    text(lang, "profile_stocks_only"))
        self.profile_status.setVisible(bool(self.profile_status.text()))
        self.side.retry_button.hide()
        self.render_sections()
        self._refresh_side(force=True)
        if load and self.auto_load:
            # Opening a stock loads its chart and details; with automatic refresh off (tests) both stay explicit.
            self.chart.refresh(manual=True)
            self.load_profile()
        # Focus leaves the search box or row the stock was opened from now, and again after the page settles.
        self.focus_chart()
        QTimer.singleShot(0, self.focus_chart)

    def _open(self, instrument):
        if self.receivers(self.open_requested) > 0:
            self.open_requested.emit(instrument)
        else:
            self.show_instrument(instrument)

    def _search_chosen(self, listing):
        self.search.clear()
        self._open(Instrument(listing.asset, listing.code, listing.exchange))

    def focus_search(self):
        """The rail's 검색 and Home's 'add to watchlist' while a stock is open: focus the toolbar search."""
        if self.completer is None or not self.search.isVisible():
            return False
        self.search.setFocus(Qt.FocusReason.OtherFocusReason)
        self.search.selectAll()
        return True

    def _search_submit(self):
        query = self.search.text().strip()
        if not query or self.directory is None:
            return
        from .markets_view import STOCK_ASSETS
        listing = self.directory.resolve(query, assets=STOCK_ASSETS)
        if listing is None and self.completer is not None:
            rows = self.completer.results(query)
            listing = rows[0] if rows else None
        if listing is not None:
            self._search_chosen(listing)

    def focus_chart(self):
        """Keyboard focus to the chart, or to its column while the chart is hidden (loading, empty, failed), so
        the arrows never go to the search box or row the stock was opened from (spec 4.1)."""
        target = self.chart.chart if self.chart.chart.isVisible() else self.chart_column
        if target.isVisible():
            target.setFocus(Qt.FocusReason.OtherFocusReason)

    def _chart_appeared(self):
        """The chart became visible while its column held the focus for it: hand the focus on."""
        if self.chart.chart.isVisible() and self.chart_column.hasFocus():
            self.chart.chart.setFocus(Qt.FocusReason.OtherFocusReason)

    # Profile -----------------------------------------------------------------------------------
    def load_profile(self):
        lang = _lang(self.ctx)
        if self.instrument is None or self.profile_loader is None or \
                self.instrument.asset not in ("domestic_stock", "overseas_stock"):
            self.profile_status.setText("" if self.instrument is None or
                                        self.instrument.asset in ("domestic_stock", "overseas_stock")
                                        else text(lang, "profile_stocks_only"))
            self.profile_status.setVisible(bool(self.profile_status.text()))
            return False
        self.profile_status.setText(text(lang, "profile_loading"))
        self.profile_status.show()
        self.side.retry_button.hide()
        if self.jobs.busy:
            # Another stock's details are still loading; load this one when that job ends.
            self._reload = True
            return False
        self._reload = False
        epoch, instrument, loader = self._epoch, self.instrument, self.profile_loader
        self._job_epoch = epoch
        return self.jobs.start(lambda: (epoch, loader(instrument)))

    @pyqtSlot(bool)
    def _jobs_busy(self, busy):
        # Jobs emits succeeded/failed before it clears its job, so a refused load is retried here.
        if not busy and self._reload and self._job_epoch != self._epoch:
            QTimer.singleShot(0, self.load_profile)

    @pyqtSlot(object)
    def _profile_loaded(self, value):
        epoch, profile = value
        if epoch != self._epoch:
            return  # a newer stock was opened meanwhile; _jobs_busy loads it
        self.profile = profile
        self.profile_status.setText("")
        self.profile_status.hide()
        self.chart.supply = self._supply()
        self.render_header()
        self.render_sections()
        self.chart.render()
        self._refresh_side(force=True)

    @pyqtSlot(str)
    def _profile_failed(self, code):
        if self._job_epoch != self._epoch:
            return  # the failure belongs to a stock that is no longer open
        self.profile_status.setText(text(_lang(self.ctx), "profile_failed", code=code))
        self.profile_status.show()
        self.side.retry_button.setText(text(_lang(self.ctx), "retry"))
        self.side.retry_button.show()

    def _supply(self):
        """KIS supply/demand rows the profile already read (investor flows, short sales) for the chart studies."""
        from core.education.indicators import Supply
        if self.profile is None:
            return None
        nan = lambda v: math.nan if v is None else float(v)
        flows = (self.profile.values.get("flows") or {}).get("daily") or ()
        shorts = (self.profile.values.get("short_selling") or {}).get("daily") or ()
        if not flows and not shorts:
            return None
        return Supply(tuple((d, nan(f), nan(i), nan(p)) for d, f, i, p in flows),
                      tuple((d, nan(r), nan(q)) for d, r, q in shorts))

    # Chart events ------------------------------------------------------------------------------
    def _chart_loaded(self, snapshot):
        instrument = snapshot.request.instrument
        if self.instrument is None or not _same(instrument, self.instrument):
            return
        quote = getattr(snapshot, "quote", None)
        if quote is not None and quote.price is not None:
            self._live_price = (quote.price, quote.change_pct, quote.change)
            self.render_header()

    def _chart_tick(self, tick):
        if self.instrument is None or not _same(tick.instrument, self.instrument):
            return
        self._live_price = (tick.price, tick.change_pct, tick.change)
        self.render_header()

    def _chart_rendered(self):
        if self.instrument is None:
            return
        self._chart_appeared()
        self.overlay_timer.start()
        self._sync_periods()
        self._render_state()
        self._render_qscore()
        snapshot = self.chart.snapshot
        if snapshot is not self._side_snapshot:
            if self._side_snapshot is None or snapshot is None:
                self._refresh_side(force=True)
            elif not self.side_timer.isActive():
                self.side_timer.start()

    def engine_bars(self):
        """core.education.indicators Bars of the chart's snapshot (cached per snapshot)."""
        from core.education.indicators import bars_from_candles
        snapshot = self.chart.snapshot
        if snapshot is None or not snapshot.candles:
            return None
        cached, bars = self._bars_cache
        if cached is snapshot:
            return bars
        bars = bars_from_candles(snapshot.candles, snapshot.request.interval)
        self._bars_cache = (snapshot, bars)
        return bars

    # Indicators --------------------------------------------------------------------------------
    def set_studies(self, keys):
        """The picker, a reading row or a panel's × changed the selection: draw it and remember it."""
        self.studies = valid_studies(keys)
        self._remember("indicators", json.dumps(list(self.studies)))
        if tuple(self.picker.selected) != self.studies:
            self.picker.set_selected(self.studies)
        self.chart.set_indicators(self.studies)
        self._refresh_side(force=True)

    def turn_on(self, key):
        if key and key not in self.studies:
            self.set_studies((*self.studies, key))
        self.focus_chart()

    def turn_off(self, key):
        self.set_studies(tuple(k for k in self.studies if k != key))
        self.focus_chart()

    def explain(self, key):
        """ⓘ on a panel: the right column's indicator page with that study's guide unfolded."""
        self.show_indicators()
        from core.education.indicators import study
        category = study(key).category
        group = self.picker.groups[category]
        group.set_open(True)
        row = group.rows[key]
        row.open_guide(True)
        self.picker.render()
        QTimer.singleShot(0, lambda: self._reveal(row))
        self.guide_requested.emit(key)

    def _reveal(self, row):
        """Scroll the indicator page down to `row`; the page never scrolls sideways (it has no horizontal bar)."""
        scroll = self.side.indicator_scroll
        scroll.ensureWidgetVisible(row, 0, 40)
        scroll.horizontalScrollBar().setValue(0)

    def show_indicators(self):
        """The right column's indicator page, docked beside the chart (owner R-D9-1: never over it)."""
        if self.body.focus:
            self.set_focus_mode(False)
        self.body.side_pref = True
        self._sync_rail()
        self.body.relayout()
        self._sync_side_button()
        self.side.set_page(1)

    # Period and interval -----------------------------------------------------------------------
    def routable(self):
        if self._routable is None and self.instrument is not None:
            from core.market.detail_model import routable_intervals
            try:
                self._routable = routable_intervals(self.chart.router, self.instrument, paper=self.chart._paper())
            except Exception:
                self._routable = ()
        return self._routable or ()

    def period_reason(self, key):
        """'' when the period chip can be used for the open stock, else a reason code ('unknown' for anything
        that is not a period key, such as None)."""
        from core.market.detail_model import PERIOD_KEYS, period_reason
        if key not in PERIOD_KEYS:
            return "unknown"
        if self.instrument is None:
            return ""
        return period_reason(key, self.instrument, self.routable())

    def opening_period(self):
        """The period a newly opened stock starts with: the last chip chosen, when this stock can use it."""
        from core.market.detail_model import DEFAULT_PERIOD
        return self.period if self.period_reason(self.period) == "" else DEFAULT_PERIOD

    def choose_period(self, key):
        if self.period_reason(key):
            return False
        self.period = key
        self._remember("period", key)
        self.chart.apply_period(key)
        self._sync_periods()
        self.focus_chart()
        return True

    def _sync_periods(self):
        self._sync_interval()
        lang = _lang(self.ctx)
        for key, button in self.periods.buttons.items():
            reason = self.period_reason(key)
            button.setEnabled(not reason)
            tip = text(lang, f"period_tip_{key}")
            if reason:
                tip += "\n" + text(lang, f"period_{reason}")
            button.setToolTip(tip)
            button.setChecked(self.chart.period == key and self.chart.period_view)

    def _interval_chosen(self, index):
        interval = self.interval_combo.itemData(index)
        if interval:
            # The chart leaves its period (no chip is highlighted); `self.period` keeps the last chip, which the
            # next stock opens with.
            self.chart.set_interval(interval)
            self._sync_periods()
        self.focus_chart()

    def _sync_interval(self, *_, force=False):
        """The toolbar menu follows the pane: its interval, the names in the window language and what the
        routers can deliver (the pane's own items keep their enabled state)."""
        lang = _lang(self.ctx)
        model, pane = self.chart.interval.model(), self.chart.interval
        enabled = {}
        for key in STOCK_INTERVALS:
            index = pane.findData(key)
            enabled[key] = index >= 0 and model.item(index).isEnabled()
        current = pane.currentData()
        before = (self.interval_combo.currentData(), self.interval_combo.currentText())
        self.interval_combo.fill({key: interval_words(key, lang) for key in STOCK_INTERVALS}, enabled, current)
        if force or before != (self.interval_combo.currentData(), self.interval_combo.currentText()):
            self._fit_toolbar()

    def interval_name(self, interval):
        """The interval in a sentence: '일 단위', '5분 단위', 'Daily'."""
        return interval_words(interval, _lang(self.ctx), long=True)

    # Toolbar actions ---------------------------------------------------------------------------
    def refresh(self):
        self.chart.refresh(manual=True)
        if self.profile_loader is not None:
            self.load_profile()
        self.side.watchlist.refresh(manual=True)
        self.focus_chart()

    def _pause_clicked(self):
        facts = self.chart.feed_facts()
        if facts["streaming"] or facts["polling"] or facts["busy"] or facts["auto"]:
            self.chart.stop()
        else:
            self.chart.refresh(manual=True)
        self._render_state()

    def _show_notes(self, *_, anchor=None):
        """ⓘ: the data notes at the end of the right column's stock page, beside the chart (owner R-D9-1)."""
        if self.notes.isVisible() and self.side.isVisible() and self.side.pages.currentIndex() == 0:
            self.notes.hide()
            return
        if self.body.focus:
            self.set_focus_mode(False)
        self.body.side_pref = True
        self._sync_rail()
        self.body.relayout()
        self._sync_side_button()
        self.side.set_page(0)
        self.notes.fill()
        self.notes.show()
        QTimer.singleShot(0, lambda: self.side.stock_scroll.ensureWidgetVisible(self.notes, 0, 24))

    def _show_more(self):
        """⋯ (narrow windows): stop or reconnect, and the data notes."""
        lang = _lang(self.ctx)
        facts = self.chart.feed_facts()
        streaming = facts["streaming"] or facts["polling"] or facts["busy"] or facts["auto"]
        self.more_pause.setText(text(lang, "pause" if streaming else "resume"))
        self.more_notes.setText(text(lang, "notes"))
        self.more_menu.popup(self.more_button.mapToGlobal(QPoint(0, self.more_button.height() + 4)))

    def set_focus_mode(self, on):
        """⤢ / Shift+F: collapse the window's rail and hide the right column; off restores both."""
        on = bool(on)
        self.body.focus = on
        if on:
            self._rail_yield = False    # asked for now: focus mode folds the rail again
        self._sync_rail()
        self.body.relayout()
        self.focus_button.setChecked(on)
        self._toolbar_texts()
        self._sync_side_button()
        self.focus_chart()

    # The window's rail ---------------------------------------------------------------------------
    def _rail_folds(self):
        """True when this screen wants the rail folded: focus mode, or the column shown in a window too narrow for
        the chart to keep CHART_ROOM beside it with the rail open (owner R-D9-1: make room, never cover)."""
        if self._rail_yield:
            return False
        if self.body.focus:
            return True
        if not self.body.side_shown() or self.lock.scroll is None:
            return False
        window = self.window()
        sidebar = getattr(window, "sidebar", None)
        expanded = getattr(window, "sidebar_expanded_width", None)
        if sidebar is None or expanded is None:
            return False
        width = self.width() - (expanded - sidebar.width() if getattr(window, "sidebar_collapsed", False) else 0)
        return self.body.chart_width(width) < CHART_ROOM

    def _sync_rail(self):
        """Fold the rail while this screen needs it and give the owner's own choice back when it no longer does."""
        window = self.window()
        if not hasattr(window, "sidebar_collapsed") or not self.isVisible():
            return
        want = self._rail_folds()
        collapsed = bool(window.sidebar_collapsed)
        if want and not collapsed:
            if self._rail_owner is None:
                self._rail_owner = collapsed
                self._rail_saved = self._saved_rail(window)
            self._set_rail(window, True)
            self._refit_soon()
        elif not want and self._rail_owner is not None:
            owner = self._owner_rail(window)
            if owner is not None and collapsed != owner:
                self._set_rail(window, owner)
                self._refit_soon()

    @staticmethod
    def _saved_rail(window):
        """The rail choice the shell has saved for the owner (it changes only when the owner toggles the rail)."""
        from .shell_rail import SETTINGS_KEY
        store = getattr(window, "language_store", None)
        try:
            return repr(store.value(SETTINGS_KEY)) if store is not None else None
        except Exception:
            return None

    def _owner_rail(self, window):
        """The rail as the owner left it before this screen folded it, or None when there is nothing to give back:
        this screen holds no rail, or the owner saved a new choice meanwhile (the rail already shows it)."""
        owner, self._rail_owner = self._rail_owner, None
        if owner is None or self._saved_rail(window) != self._rail_saved:
            return None
        return owner

    def _refit_soon(self):
        """The rail changed the page's width: the page above the view reflows over the next layout passes, so the
        page lock measures the view's place again once they are done."""
        self.lock.refit()
        QTimer.singleShot(0, self.lock.refit)
        QTimer.singleShot(60, self.lock.refit)

    def _restore_rail(self, *, leaving=False):
        window = self.window()
        if self._rail_owner is not None and hasattr(window, "sidebar_collapsed"):
            owner = self._owner_rail(window)
            if owner is not None and bool(window.sidebar_collapsed) != owner:
                self._set_rail(window, owner)
                if leaving and getattr(window, "_page_position", None):
                    # The shell keeps the page where it was while the rail moves: it read the page lock's target
                    # here and would set it again one turn later, over the lock's own return of the list to where
                    # it was before the stock opened (Back).
                    window._page_position = None

    def _hook_rail(self):
        """The owner's own rail toggles (its two buttons and the shortcut) end this screen's hold on the rail."""
        window = self.window()
        if window is self or self._rail_hooked is window:
            return
        self._rail_hooked = window
        for name in ("sidebar_hide", "sidebar_show"):
            button = getattr(window, name, None)
            if button is not None and hasattr(button, "clicked"):
                button.clicked.connect(self._owner_moved_rail)
        shortcut = getattr(window, "sidebar_shortcut", None)
        if shortcut is not None and hasattr(shortcut, "activated"):
            shortcut.activated.connect(self._owner_moved_rail)

    def _owner_moved_rail(self, *_):
        """The owner opened or closed the rail while this screen held it: their choice stands (it is saved by the
        shell) and this screen leaves the rail alone until it is opened again or focus mode is asked for."""
        if not self.isVisible():
            return
        self._rail_owner = None
        self._rail_yield = True

    @staticmethod
    def _set_rail(window, collapsed):
        rail = getattr(window, "set_rail_collapsed", None)
        if callable(rail):
            rail(collapsed)
            return
        sidebar = getattr(window, "set_sidebar_collapsed", None)
        if callable(sidebar):
            sidebar(collapsed, remember=False)

    def set_side_shown(self, shown):
        shown = bool(shown)
        if self.body.focus and shown:
            self.set_focus_mode(False)
        self.body.side_pref = shown
        self._remember("side", "shown" if shown else "hidden")
        self._sync_rail()
        self.body.relayout()
        self._sync_side_button()

    def _sync_side_button(self):
        shown = self.body.side_shown()
        self.side_button.setChecked(shown)
        lang = _lang(self.ctx)
        tip = text(lang, "side_hide" if shown else "side_show")
        self.side_button.setToolTip(tip)
        self.side_button.setAccessibleName(tip)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_toolbar()
        # The rail follows the window's width, not the view's own (the rail itself changes the view's width).
        window = self.window()
        if window is not self and window.width() != self._window_width:
            self._window_width = window.width()
            QTimer.singleShot(0, self._sync_rail)

    # Toolbar compaction (spec 2.3), applied one step at a time until the stock's name has its room:
    # 1 the star drops its words, 2 back keeps only its arrow, 3 the search narrows to 140, 4 stop/reconnect and
    # the data notes move into ⋯, 5 the company mark goes, 6 the market state moves under the name. Only when the
    # name would still get less than NAME_LEAST: 7 the search, 8 the Indicators button give way (the column and
    # its tab remain).
    LEVELS = 8

    def _apply_level(self, level):
        self._level = level
        self._compact = level >= 1
        lang = _lang(self.ctx)
        self.back_button.setText("←" if level >= 2 else text(lang, "back"))
        self.search.setFixedWidth(SEARCH_NARROW if level >= 3 else SEARCH_WIDE)
        menu = level >= 4
        self.pause_button.setVisible(not menu)
        self.notes_button.setVisible(not menu)
        self.more_button.setVisible(menu)
        self.mark.setVisible(level < 5 and self.instrument is not None and
                             self.instrument.asset in ("domestic_stock", "overseas_stock"))
        inline = level >= 6
        self.state_chip.setVisible(not inline)
        self.state_inline.setVisible(inline and bool(self.state_inline.text()))
        self.search.setVisible(self.completer is not None and level < 7)
        self.indicators_button.setVisible(level < 8)
        self._sync_watch()

    def _toolbar_need(self):
        """Width the toolbar's controls ask for, without the stock's name (the layout's own sums: hidden
        widgets and spacers take no spacing)."""
        row = self.toolbar.layout()
        total, items = 0, 0
        for index in range(row.count()):
            item = row.itemAt(index)
            widget, inner, spacer = item.widget(), item.layout(), item.spacerItem()
            if widget is not None:
                if not widget.isHidden():
                    total += max(widget.sizeHint().width(), widget.minimumWidth())
                    items += 1
            elif inner is self.names_box:
                code = self.code.sizeHint().width()
                if not self.state_inline.isHidden():
                    code += self.code_row.spacing() + self.state_inline.sizeHint().width()
                total += code
                items += 1
            elif inner is self.tools_box:
                shown = [inner.itemAt(i).widget() for i in range(inner.count())]
                shown = [w for w in shown if w is not None and not w.isHidden()]
                total += sum(w.sizeHint().width() for w in shown) + inner.spacing() * max(0, len(shown) - 1)
                items += 1
            elif spacer is not None and spacer.expandingDirections() == Qt.Orientation(0):
                total += spacer.sizeHint().width()
        return total + row.spacing() * max(0, items - 1)

    def _fit_toolbar(self):
        scroll = self.lock.scroll
        width = scroll.viewport().width() - self._side_margins() if scroll is not None else self.width()
        if width <= 0:
            return
        full = self.name.fontMetrics().horizontalAdvance(self.name.text()) + 4
        code = self.code.sizeHint().width()
        for level in range(self.LEVELS + 1):
            self._apply_level(level)
            least = NAME_ROOM if level < 6 else NAME_LEAST
            if self._toolbar_need() - code + max(code, min(full, least)) <= width:
                break

    def _side_margins(self):
        """The page margins around this view (the view is laid out inside the page's content)."""
        content = self.lock.scroll.widget() if self.lock.scroll is not None else None
        if content is None or content.layout() is None:
            return 0
        margins = content.layout().contentsMargins()
        return margins.left() + margins.right()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.body.focus:
            self.set_focus_mode(False)
            return
        super().keyPressEvent(event)

    def chart_key(self, event):
        """The chart's keys: Shift+F and Esc here, everything else the pane's (arrows, Home/End, +/-, 0)."""
        if event.key() == Qt.Key.Key_F and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.set_focus_mode(not self.body.focus)
            return True
        if event.key() == Qt.Key.Key_Escape and self.body.focus:
            self.keyPressEvent(event)
            return True
        return self.chart.chart_key(event)

    # Watchlist ---------------------------------------------------------------------------------
    def _toggle_watch(self):
        if self.instrument is None:
            return
        if self.store.contains(self.instrument):
            self.store.remove(self.instrument)
            self.watch_toggled.emit(self.instrument, False)
        elif self.store.add(self.instrument):
            self.watch_toggled.emit(self.instrument, True)
        self._watch_changed()

    def _watch_changed(self):
        self._sync_watch()
        self._fit_toolbar()   # ☆ 관심종목 추가 and ★ 관심종목 differ in width

    def _sync_watch(self):
        lang = _lang(self.ctx)
        watched = self.instrument is not None and self.store.contains(self.instrument)
        self.watch_button.setChecked(watched)
        full = not watched and self.store.full()
        self.watch_button.setEnabled(self.instrument is not None and not full)
        words = text(lang, "watch_on" if watched else "watch_add")
        self.watch_button.setText(words[:1] if self._compact else words)
        self.watch_button.setAccessibleName(words[2:])
        self.watch_button.setToolTip(text(lang, "watch_full", limit=self.store.limit) if full else "")

    # Presentation ------------------------------------------------------------------------------
    def price_text(self, value):
        from .markets_view import _price_text
        if self.instrument is None or value is None:
            return "—"
        if self.instrument.asset == "domestic_stock":
            return f"{value:,.0f}"
        if abs(value) < 1:
            return f"{value:,.4f}".rstrip("0").rstrip(".")
        return _price_text(value, self.instrument)

    def volume_text(self, volume):
        """Volume as the OHLC strip shows it: 871만 in Korean, 8.71M in English."""
        from core.market.detail_svg import compact
        if volume is None or not math.isfinite(volume):
            return "—"
        return korean_amount(volume) if _lang(self.ctx) == "ko" else compact(volume)

    def study_value(self, key, line, index, fallback):
        """A study value for the chart overlays: prices in the instrument's own precision, volume in the strip's
        compact unit, the rest as the guide formats them."""
        if line.kind == "quantity" and key == "volume_ma":
            from core.education.indicators import compute_study
            try:
                return self.volume_text(float(compute_study(key, self.engine_bars())[line.id][index]))
            except Exception:
                return fallback
        if line.kind != "price":
            return fallback
        from core.education.indicators import compute_study
        bars = self.engine_bars()
        try:
            value = float(compute_study(key, bars, supply=self.chart.supply)[line.id][index])
        except Exception:
            return fallback
        return self.price_text(value) if math.isfinite(value) else "—"

    def values_html(self, key, spec, readout, index, colors):
        """A study's values at `index` for a panel header: a study with one line shows its number (the panel
        title names it); with more lines every number carries its line's name ('MACD −593 · 신호선 −182 ·
        막대 −411'), so signal and histogram, +DI and −DI are never guessed (spec 6.1)."""
        parts = []
        for line, (name, value) in zip(spec.lines, readout):
            shown = _esc(self.study_value(key, line, index, value))
            if len(spec.lines) == 1:
                parts.append(f'<span style="color:{colors[line.id]}">{shown}</span>')
            else:
                parts.append(f'<span style="color:{colors[line.id]}">{_esc(name)}</span> {shown}')
        return " · ".join(parts)

    def _current_price(self):
        """(price, change %, change) from a live trade, the chart's quote, the profile or the last candle."""
        if self._live_price is not None:
            return self._live_price
        snapshot = self.chart.snapshot
        if snapshot is not None and snapshot.request.instrument == self.instrument and snapshot.candles:
            quote = snapshot.quote
            if quote is not None and quote.price is not None:
                return quote.price, quote.change_pct, quote.change
        if self.profile is not None and self.profile.last_price is not None:
            return self.profile.last_price, self.profile.change_pct, self.profile.change
        return None, None, None

    def render_header(self):
        lang = _lang(self.ctx)
        instrument = self.instrument
        card = self.side.card
        if instrument is None:
            self.mark.hide()
            for field in (self.code, self.name, self.price, self.change, card.name, card.sector):
                field.setText("")
            return
        # The directory name first, so the header does not change name when the details arrive; the profile's
        # name only when the directory does not know the stock.
        name = self.name_fn(instrument, lang)
        if self.profile is not None and name == instrument.code:
            from core.research.stock_profile import display_name
            name = display_name(self.profile, lang) or name
        self.mark.set_identity(instrument.code, name)
        self.mark.setVisible(self._level < 5 and instrument.asset in ("domestic_stock", "overseas_stock"))
        self.mark.setAccessibleName(name)
        place = instrument.exchange or ("KRX" if instrument.asset == "domestic_stock" else "")
        self.code.setText(f"{instrument.code} · {place}" if place else instrument.code)
        if self.name.text() != name:
            self.name.setText(name)
            self._fit_toolbar()
        card.name.setText(name)
        sector = ""
        if self.profile is not None:
            figures = self.profile.values.get("key_figures") or {}
            sector = str(figures.get("sector") or "")
            if lang != "ko":
                from core.research.stock_profile import _HANGUL
                sector = "" if _HANGUL.search(sector) else sector
        card.sector.setText(sector)
        price, pct, change = self._current_price()
        self.price.setText(self.price_text(price))
        if pct is not None:
            arrow = "▲" if pct > 0 else "▼" if pct < 0 else "–"
            tone = "up" if pct > 0 else "down" if pct < 0 else "flat"
            amount = ""
            if change is not None:
                sign = "+" if change > 0 else "−" if change < 0 else ""
                amount = f"{sign}{self.price_text(abs(change))} "
            self.change.setText(f"{arrow} {amount}({pct:+.2f}%)".replace("-", "−").replace("(+", "(+"))
            set_prop(self.change, "tone", tone)
        else:
            self.change.setText("")
        self.change.setVisible(bool(self.change.text()))
        self.price.setAccessibleName(f"{name} {self.price.text()} {self.change.text()}")
        self._render_state()

    def _render_state(self):
        from core.market.detail_model import quote_state
        from .markets_view import _clock
        if self.instrument is None:
            return
        lang = _lang(self.ctx)
        facts = self.chart.feed_facts()
        state = quote_state(self.instrument, source=facts["source"], mode=facts["mode"], has_data=facts["has_data"],
                            last_trade_at=facts["last_trade_at"], market_time=facts["market_time"])
        chip = text(lang, f"state_{state.code}")
        changed = chip != self.state_chip.text()
        self.state_chip.setText(chip)
        set_prop(self.state_chip, "tone", state.tone)
        self.state_inline.setText(self.state_chip.text())
        set_prop(self.state_inline, "tone", state.tone)
        self.state_inline.setVisible(self._level >= 6)
        line = text(lang, f"state_{state.code}_long", age=state.age if state.age is not None else "—")
        if facts["last_received"] and facts["has_data"]:
            from core.market.detail_model import _age
            from datetime import datetime, timezone
            age = _age(facts["last_received"], datetime.now(timezone.utc))
            if age is not None and state.code not in ("closed", "holiday"):
                line += " · " + text(lang, "received_ago", age=plain_age(age, lang))
        card_state = self.side.card.state
        card_state.setText(line)
        set_prop(card_state, "tone", state.tone)
        tip = ""
        if facts["has_data"]:
            tip = text(lang, "state_tip", source=facts["source"], fetched=_clock(facts["fetched_at"]) or "—",
                       market=_clock(facts["market_time"]) or "—")
            # A closed market's label wins, but a delay or fallback qualifier stays readable (12-claims, 09).
            if not facts["source"].upper().startswith("KIS"):
                key = "state_fallback_long"
            elif self.instrument.asset == "overseas_stock":
                key = "state_us_free_long" if state.venue == "US" else "state_delayed15_long"
            else:
                key = ""
            if key and key != f"state_{state.code}_long":
                tip += "\n" + text(lang, key).lstrip("● ")
        for widget in (self.state_chip, self.state_inline, card_state, self.price, self.change):
            widget.setToolTip(tip)
        streaming = facts["streaming"] or facts["polling"] or facts["busy"] or facts["auto"]
        self.pause_button.setIcon(icon("pause" if streaming else "play", self.palette.muted))
        tip = text(lang, "pause" if streaming else "resume")
        self.pause_button.setToolTip(tip)
        self.pause_button.setAccessibleName(tip)
        if not self.notes.isHidden():
            self.notes.refresh()  # the open data notes follow the chart shown now (stock, interval, feed state)
        if changed:
            self._fit_toolbar()   # the chip's words changed width

    def _render_qscore(self):
        """The Q-SCORE chip says what Q-SCORE is (the glossary summary), not where a table's '?' would be."""
        chip = self.side.card.qscore
        shown = self.chart.q_score_text()
        chip.setVisible(shown is not None)
        if shown is not None:
            chip.setText(shown[0])
            chip.setToolTip(text(_lang(self.ctx), "qscore_tip"))

    def _clear_sections(self):
        self.__dict__["_technical_blocks"] = {}     # the sections delete their blocks: build new ones
        for section in self.side.sections.values():
            section.set_rows([], ctx=self.ctx, dark=self.dark)
            section.hide()
        self.section_panels = []
        self.side.unavailable.setText("")
        self.side.unavailable.hide()

    def render_sections(self):
        """Profile sections folded in the right column (owner: 3-4 figures each, the rest folded)."""
        from core.research.stock_profile import sections
        lang = _lang(self.ctx)
        by_key = {}
        if self.profile is not None:
            for section in sections(self.profile, lang):
                by_key[section.key] = section
        groups = {
            "key_figures": (("key_figures",), "section_key_figures"),
            "range": (("returns", "range"), "section_range"),
            "risk": (("risk",), "section_risk"),
            "supply": (("short_selling", "flows"), "section_supply"),
        }
        self.section_panels = []
        for key, (sources, title) in groups.items():
            panel = self.side.sections[key]
            rows = [display_row(row, lang) for source in sources if source in by_key for row in by_key[source].rows]
            if key == "key_figures":
                rows = key_figures_first(rows)
            notes = " · ".join(dict.fromkeys(polite(by_key[s].note, lang) for s in sources
                                             if s in by_key and by_key[s].note))
            panel.set_title(text(lang, title))
            panel.set_rows(rows, note=notes, ctx=self.ctx, dark=self.dark)
            panel.setVisible(bool(rows))
            if rows:
                self.section_panels.append(panel)
        technical = self.side.sections["technical"]
        technical.set_title(text(lang, "section_technical"))
        entries = self._technical_rows()
        # The profile's own signal rows repeat the studies above with sub-scores a beginner cannot read (an 'RSI'
        # of −22.6 next to the RSI of 31.1, a verdict): only the composite score follows, its scale in its name
        # and a plain tooltip (review 2026-11-11).
        extra = []
        if "signals" in by_key and by_key["signals"].rows:
            from core.research.stock_profile import ProfileRow
            score = display_row(by_key["signals"].rows[0], lang)
            extra = [ProfileRow(text(lang, "signals_label"), score.value, score.tone, text(lang, "signals_tip"))]
        technical.set_rows([*entries, *extra], note="", ctx=self.ctx, dark=self.dark)
        technical.setVisible(True)
        order = ["key_figures", "range", "risk", "technical", "supply"]
        self.section_panels = [self.side.sections[k] for k in order if self.side.sections[k].isVisibleTo(self.side)
                               and (k == "technical" or self.side.sections[k] in self.section_panels)]
        unavailable = by_key.get("unavailable")
        if unavailable is not None and unavailable.rows:
            items = " · ".join(row.label for row in unavailable.rows)
            self.side.unavailable.setText(text(lang, "unavailable", items=items))
            self.side.unavailable.setToolTip("\n".join(
                f"{row.label}: {row.value}" + (f" — {polite(row.hint, lang)}" if row.hint else "")
                for row in unavailable.rows))
            self.side.unavailable.show()
        else:
            self.side.unavailable.hide()

    def _technical_rows(self):
        """One block per study that is on, at the guide card's budget (owner R-D9-3: no walls of names and numbers):
        the coloured name with '자세히 ›' at its end, then the reading in one short sentence with its pill, then the
        gauge. The lines' values sit in the name's tooltip and the full reading behind 자세히. A study that cannot
        be drawn here, or has too little data yet, is one muted line after its name. Blocks are kept per study and
        refilled, so a refresh does not rebuild the column's widgets."""
        from PyQt6 import sip
        from core.education import indicators as engine
        from core.education.study_guide import availability_short, availability_text, line_readout, unit_count
        from core.market.presentation import study_colors
        from .indicator_picker import GuideCard, guide_parts, state_tone, state_word
        lang = _lang(self.ctx)
        bars = self.engine_bars()
        snapshot = self.chart.snapshot
        cache = self.__dict__.setdefault("_technical_blocks", {})
        for key in list(cache):
            if key not in self.studies or sip.isdeleted(cache[key][0]):
                cache.pop(key)       # the section deletes a block it no longer lists (sdOwned)
        if not self.studies:
            note = label("rowNote", wrap=True)
            note.setText(text(lang, "technical_none"))
            note.setProperty("sdOwned", True)
            return [note]
        asset = self.instrument.asset if self.instrument is not None else "domestic_stock"
        interval = snapshot.request.interval if snapshot is not None else "1d"
        has_volume = bool(bars is not None and any(math.isfinite(v) for v in bars.volume))
        out = []
        for key in self.studies:
            spec = engine.study(key)
            if key not in cache:
                block = QWidget()
                block.setProperty("sdOwned", True)
                layout = QVBoxLayout(block)
                layout.setContentsMargins(0, 4, 0, 10)
                layout.setSpacing(6)
                top = QHBoxLayout()
                top.setContentsMargins(0, 0, 0, 0)
                top.setSpacing(8)
                head = rich("studyName")
                head.setWordWrap(True)
                card = GuideCard(compact=True)
                card.more.toggled.connect(lambda on, k=key: self._technical_more(k, on))
                top.addWidget(head, 1)
                card.layout().removeWidget(card.more)
                top.addWidget(card.more, 0, Qt.AlignmentFlag.AlignTop)   # 자세히 › ends the name's line
                layout.addLayout(top)
                layout.addWidget(card)
                cache[key] = (block, head, card)
            block, head, card = cache[key]
            color = study_colors(key, self.dark)[spec.lines[0].id]
            name = f'<span style="color:{color}">●</span>&ensp;{_esc(spec.name(lang))}'
            reason = engine.availability(key, asset=asset, interval=interval, supply=self.chart.supply,
                                         has_volume=has_volume) if bars is not None else ""
            values, quiet, tip = None, "", ""
            if bars is not None and reason:
                quiet = polite(availability_short(reason, lang), lang)
                tip = polite(availability_text(reason, lang), lang)
            elif bars is not None:
                try:
                    values = engine.compute_study(key, bars, supply=self.chart.supply)
                    ready = all(self._finite_at(values, line, len(bars) - 1) for line in engine.reading_lines(key))
                except Exception:
                    values, ready = None, False
                if not ready and spec.category != "supply":
                    needed = engine.warmup(key) + 1
                    quiet = text(lang, "technical_wait")
                    tip = text(lang, "technical_wait_tip", needed=unit_count(interval, needed, lang),
                               have=unit_count(interval, len(bars), lang))
            if bars is None or quiet:
                muted = f' <span style="color:{self.palette.muted}; font-weight:400">· {_esc(quiet)}</span>' \
                    if quiet else ""
                head.setText(name + muted)
                head.setToolTip(tip)
                card.hide()
                card.more.hide()
            else:
                readout = line_readout(key, bars, -1, language=lang, supply=self.chart.supply)
                head.setText(name)
                head.setToolTip(" · ".join(f"{n} {self.study_value(key, line, len(bars) - 1, v)}"
                                           for line, (n, v) in zip(spec.lines, readout)))
                reading, code, gauge, _short, long_texts = guide_parts(
                    key, bars, language=lang, interval=interval, supply=self.chart.supply, values=values)
                card.show_guide(language=lang, name=spec.name(lang), reading=reading,
                                state=state_word(key, code, lang), tone=state_tone(code),
                                gauge=gauge, gauge_labels=self.picker.gauge_labels(key, gauge, lang),
                                long_texts=long_texts[:1], colors=self.gauge_colors())
                card.set_open(key in self._technical_open)
                card.show()
            out.append(block)
        return out

    @staticmethod
    def _finite_at(values, line, index):
        try:
            return math.isfinite(float(values[line][index]))
        except (KeyError, IndexError, TypeError, ValueError):
            return False

    def _technical_more(self, key, on):
        if on:
            self._technical_open.add(key)
        else:
            self._technical_open.discard(key)

    def gauge_colors(self):
        from .typography import TONE_COLORS, mix
        p, t = self.palette, TONE_COLORS[bool(self.dark)]
        return {"track": mix(p.border, p.bg, 0.25), "up": t["up"], "down": t["down"], "up_tint": t["up_tint"],
                "down_tint": t["down_tint"], "accent": p.accent, "muted": p.muted, "band": p.accent_soft,
                "bg": p.surface}

    def _refresh_side(self, force=False):
        """The parts of the right column that follow the data (not the cursor): card, readings, picker."""
        if self.instrument is None:
            return
        self._side_snapshot = self.chart.snapshot
        self._render_card()
        self._render_now()
        technical = self.side.sections["technical"]
        if technical.isVisibleTo(self.side) or force:
            self.render_sections()
        bars = self.engine_bars()
        snapshot = self.chart.snapshot
        from core.market.detail_svg import max_panels
        limit = max_panels(self.chart.chart.height()) if self.chart.chart.isVisible() else None
        layout = self.chart.chart.layout_info
        self.picker.gauge_colors = self.gauge_colors()
        self.picker.set_context(bars, asset=self.instrument.asset,
                                interval=snapshot.request.interval if snapshot is not None else
                                self.chart.interval.currentData() or "1d",
                                supply=self.chart.supply, panel_limit=limit,
                                hidden_panels=layout.hidden_panels if layout is not None else ())

    def _daily_candles(self):
        if self.profile is not None and self.profile.candles:
            return self.profile.candles
        snapshot = self.chart.snapshot
        if snapshot is not None and snapshot.request.interval == "1d":
            return snapshot.candles
        return ()

    def volume_ratio(self):
        from core.market.detail_model import volume_vs_average
        candles = self._daily_candles()
        today = None
        snapshot = self.chart.snapshot
        if snapshot is not None and snapshot.last_cumulative_volume is not None and \
                self.instrument is not None and self.instrument.asset == "domestic_stock":
            today = float(snapshot.last_cumulative_volume)
        elif self.profile is not None:
            figures = self.profile.values.get("key_figures") or {}
            if figures.get("basis") == "quote" and figures.get("volume") is not None:
                today = float(figures["volume"])
        return volume_vs_average(candles, today)

    def _render_card(self):
        from .typography import mix
        card = self.side.card
        lang = _lang(self.ctx)
        p = self.palette
        colors = (mix(p.border, p.bg, 0.2), p.accent, p.muted)
        ratio = self.volume_ratio()
        if ratio.volume is not None:
            unit = "주" if lang == "ko" and self.instrument.asset == "domestic_stock" else ""
            card.volume.setText(text(lang, "volume_line", volume=f"{ratio.volume:,.0f}{unit}"))
            if ratio.ratio is not None:
                card.volume_ratio.setText(text(lang, "volume_ratio_cap") if ratio.ratio >= 2 else
                                          text(lang, "volume_ratio", ratio=f"{ratio.ratio:.1f}"))
                card.volume_ratio.setToolTip(text(lang, "volume_tip", sessions=ratio.sessions))
            else:
                card.volume_ratio.setText(text(lang, "volume_short"))
            card.volume_bar.set_value(ratio.ratio, colors)
            for widget in (card.volume, card.volume_ratio, card.volume_bar):
                widget.show()
        else:
            for widget in (card.volume, card.volume_ratio, card.volume_bar):
                widget.hide()
        span = (self.profile.values.get("range") or {}) if self.profile is not None else {}
        card.range_title.setText(text(lang, "range_title"))
        card.range_title.setToolTip(text(lang, "range_tip"))
        if span.get("position") is not None or ("high" in span and "low" in span):
            card.range_bar.set_value(span.get("position"), colors)
            card.range_low.setText(f"{self.price_text(span['low'])} ({span['low_date'][5:]})")
            card.range_high.setText(f"{self.price_text(span['high'])} ({span['high_date'][5:]})")
            high = f"{span['from_high'] * 100:+.1f}%".replace("-", "−")
            low = f"{span['from_low'] * 100:+.1f}%".replace("-", "−")
            card.range_from.setText(text(lang, "range_from", high=high, low=low))
            for widget in (card.range_title, card.range_bar, card.range_low, card.range_high, card.range_from):
                widget.show()
        elif span.get("sessions"):
            card.range_from.setText(text(lang, "range_short", sessions=span["sessions"]))
            for widget in (card.range_bar, card.range_low, card.range_high):
                widget.hide()
            card.range_title.show()
            card.range_from.show()
        else:
            for widget in (card.range_title, card.range_bar, card.range_low, card.range_high, card.range_from):
                widget.hide()

    def _unit(self, interval, n):
        """n periods of the interval in words: '20일', '20주', '20개월', '20년', '20개 5분 구간'."""
        from core.education.study_guide import unit_count
        return unit_count(interval, n, _lang(self.ctx))

    def _render_now(self):
        from core.market.detail_model import now_summary
        from core.education.indicators import bars_from_candles, study
        from core.education.study_guide import josa
        lang = _lang(self.ctx)
        now = self.side.now
        now.title.setText(text(lang, "now_title"))
        now.disclaimer.setText(text(lang, "disclaimer"))
        bars = self.engine_bars()
        interval = self.chart.snapshot.request.interval if bars is not None else "1d"
        if bars is None:
            daily = self._daily_candles()
            bars = bars_from_candles(daily, "1d") if daily else None
        if bars is None or not len(bars):
            now.caption.setText("")
            for row in now.rows:
                row.hide()
            now.setVisible(False)
            self.side.now_rule.setVisible(False)
            return
        now.setVisible(True)
        self.side.now_rule.setVisible(True)
        now.caption.setText(text(lang, "now_caption", interval=self.interval_name(interval),
                                 date=str(bars.timestamps[-1])[:10]))
        ratio = self.volume_ratio()
        intraday = ""
        if self.side.card.state.property("tone") == "success" or self.chart.feed_facts()["polling"]:
            intraday = text(lang, "volume_intraday")
        rows = now_summary(bars, volume=ratio)
        for row, item in zip(now.rows, rows):
            values = dict(item.values)
            fields = {"n20": self._unit(interval, 20), "n60": self._unit(interval, 60), "intraday": intraday,
                      "one": unit_fields(interval, lang)["one"]}
            if item.topic != "trading":
                for name in ("needed", "have", "bars"):
                    if name in values:
                        values[name] = self._unit(interval, values[name])
                if "bars" in values and lang == "ko":
                    values["bars"] = josa(values["bars"], "과")    # '최근 120일과 비교하면' (the text adds none)
            for name, value in values.items():
                if name in ("pct20", "pct60"):
                    fields["pct"] = f"{value:+.1f}%".replace("-", "−")
                elif name == "pct":
                    fields["pct"] = f"{value:.1f}%"
                elif name == "rsi":
                    fields["rsi"] = f"{value:.1f}"          # as the RSI panel prints it
                elif name == "ratio":
                    fields["ratio"] = f"{value:.1f}"
                else:
                    fields[name] = value
            row.topic.setText(text(lang, f"topic_{item.topic}"))
            row.topic.setFixedWidth(60 if lang == "ko" else 84)
            row.set_reading(text(lang, f"now_{item.topic}_{item.code}", **fields))
            row.study = item.study if item.study not in self.studies else ""
            row.setCursor(Qt.CursorShape.PointingHandCursor if row.study else Qt.CursorShape.ArrowCursor)
            name = study(item.study).name(lang) if row.study else ""
            row.setToolTip(text(lang, "now_turn_on", name=josa(name, "을") if lang == "ko" else name)
                           if row.study else "")
            row.show()

    def _toolbar_texts(self):
        lang = _lang(self.ctx)
        p = self.palette
        self.back_button.setText(text(lang, "back"))
        self.back_button.setAccessibleName(text(lang, "back_name"))
        self.back_button.setToolTip(text(lang, "back_name"))
        self.search.setPlaceholderText(text(lang, "search"))
        self.search.setAccessibleName(text(lang, "search_name"))
        self.interval_combo.setAccessibleName(text(lang, "interval_name"))
        self.interval_combo.setToolTip(text(lang, "interval_name"))
        self.indicators_button.setText(text(lang, "indicators_button"))
        for button, kind, tip in ((self.refresh_button, "refresh", "refresh"), (self.notes_button, "info", "notes")):
            button.setIcon(icon(kind, p.muted))
            button.setToolTip(text(lang, tip))
            button.setAccessibleName(text(lang, tip))
        focus = self.body.focus
        self.focus_button.setIcon(icon("unfocus" if focus else "focus", p.muted))
        self.focus_button.setToolTip(text(lang, "focus_off" if focus else "focus"))
        self.focus_button.setAccessibleName(text(lang, "focus_off" if focus else "focus"))
        self.side_button.setIcon(icon("panel", p.muted))
        self._sync_side_button()
        periods = self.periods
        for key, button in periods.buttons.items():
            button.setText(text(lang, f"period_{key}"))
        periods.hint.setText(text(lang, "keys_hint"))
        for button, kind, tip in ((periods.left, "left", "pan_left"), (periods.right, "right", "pan_right"),
                                  (periods.zoom_out, "minus", "zoom_out"), (periods.zoom_in, "plus", "zoom_in")):
            button.setIcon(icon(kind, p.muted))
            button.setToolTip(text(lang, tip))
            button.setAccessibleName(text(lang, tip))
        periods.reset.setText(text(lang, "reset"))
        periods.reset.setToolTip(text(lang, "reset_tip"))
        periods.fit()
        self.more_button.setIcon(icon("more", p.muted))
        self.more_button.setToolTip(text(lang, "more_tools"))
        self.more_button.setAccessibleName(text(lang, "more_tools"))
        self._fit_toolbar()
        self.chart.chart.setAccessibleName(text(lang, "chart_name"))
        self.side.stock_tab.setText(text(lang, "tab_stock"))
        self.side.indicators_tab.setText(text(lang, "tab_indicators"))

    def set_locale(self, ctx):
        self.ctx = ctx
        lang = _lang(ctx)
        self.chart.chart.months = text(lang, "months")
        if self.completer is not None:
            self.completer.set_locale(ctx)
        self._toolbar_texts()
        self._sync_interval(force=True)
        self._sync_watch()
        if not self.notes.isHidden():
            self.notes.fill()
        self.side.watchlist.set_locale(ctx)
        self.picker.set_locale(ctx)
        self.render_header()
        self.render_sections()
        self._sync_periods()
        if self.instrument is not None:
            self._refresh_side(force=True)
            if self.chart.detail:
                self.chart.render()  # the chart's month labels and every overlay follow; nothing is fetched

    def set_theme(self, dark):
        self.dark = bool(dark)
        self.palette = p = DARK if self.dark else LIGHT
        self.setStyleSheet(sheet(p, self.dark))
        self.mark.set_theme(p)
        self.chart.chart.theme = {"bg": p.bg, "text": p.text, "muted": p.muted, "border": p.border}
        if self.completer is not None:
            self.completer.set_theme(p, self.dark)
        for section in self.side.sections.values():
            section.set_theme(self.dark)
        self.side.watchlist.set_theme(self.dark)
        self.picker.set_theme(self.dark)
        self._toolbar_texts()
        if not self.notes.isHidden():
            self.notes.fill()     # its close icon follows the theme
        if self.instrument is not None:
            self._refresh_side(force=True)
            if self.chart.detail and self.chart.snapshot is not None:
                self.chart.render()

    def stop(self):
        self._epoch += 1
        self.side.watchlist.stop()
        self.side_timer.stop()
        if self.body.focus:
            self.set_focus_mode(False)

    # Visibility --------------------------------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        self._hook_rail()
        self.keys.install(True)
        self.lock.engage()
        QTimer.singleShot(0, self.lock.engage)
        QTimer.singleShot(0, self._sync_rail)

    def hideEvent(self, event):
        if event.spontaneous():
            # The window was minimised: the stock is still open, so focus mode and the page lock stay as they are.
            super().hideEvent(event)
            return
        self.notes.hide()
        self.keys.install(False)
        if self.body.focus:
            self.set_focus_mode(False)
        self._restore_rail(leaving=True)
        self._rail_yield = False
        self.lock.release()
        super().hideEvent(event)


def _same(a, b):
    return (a.asset, a.code, a.exchange) == (b.asset, b.code, b.exchange)


class ProfileSectionPanel(QFrame):
    """Kept for compatibility with code that imports it from markets_view; the stock screen folds its sections
    in the right column (stock_detail_side.FoldSection) since 2026-11-11."""

    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        self.title = label("foldTitle")
        layout.addWidget(self.title)
        self.section = FoldSection("compat")
        layout.addWidget(self.section)

    def show_section(self, section):
        self.title.setText(section.title)
        self.section.set_rows(section.rows, note=section.note)


__all__ = ["StockDetailView", "PageLock", "ChartKeys", "DetailBody", "ChartOverlays", "PeriodBar",
           "ProfileSectionPanel", "NotesBox", "DEFAULT_STUDIES", "STOCK_INTERVALS", "interval_words", "year_label",
           "plain_age", "TERM_TIPS"]
