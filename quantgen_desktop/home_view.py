"""Research Home (owner request 2026-11-11, decision UI-D7 point 4).

Owner: "연구 홈 화면을 표대신 이렇게 심플하고 세련되게 화살표로 휙휙 넘길수잇게 하자 (트레이딩뷰 화면 참고) 표에
종목 너무많이 때려박는거 자체의 구조적 문제인거같아. 세로로 넓게 넓게 공간 쓰고, ... 연구 홈에서 '관심종목' 차트를
직관적으로 볼수있게 유아이를 저기로 옮기고".

Top to bottom: a row of market cards that pages left and right (four at a time on a wide window), one large
chart for the selected card, and the user's watchlist chart cards (`markets_view.WatchlistGrid`, moved here
from Markets). `ResearchWindow.make_home` adds the research sections and the full quotes table (in a closed
fold) below.

Data. The cards show the rows the window already loads for its quotes table
(`core.research.watchlist.load_home_markets`, read through `rows_source`). The large chart reads the selected
market's daily closes from the provider its row names (`core.ficc.data.load_series` with that explicit
source: Yahoo Finance for S&P 500, KOSPI and Bitcoin, FRED for USD/KRW, the US 10-year yield and VIX). The
watchlist card router cannot serve these: `core.market.models.Instrument` has no index, rate or FX asset.
History loads off the UI thread, one market at a time, only while automatic loading is on or after the user
presses Refresh; there is no synthetic or cross-provider fallback, and a failure keeps only an authored
reason code. Provider names and observation dates stay in tooltips (owner, 2026-11-04).

The view follows the window's language, theme and quote rows on its own (`_reserve_text_space`, called by
`LanguageController.apply` after every language switch and view refresh, and Qt's style-change event), so a
language or theme switch re-renders text and colours without fetching anything.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from PyQt6.QtCore import (QEasingCurve, QEvent, QPoint, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer,
                          pyqtSignal, pyqtSlot)
from PyQt6.QtGui import QBrush, QColor, QFontMetricsF, QIcon, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QToolButton,
                             QVBoxLayout, QWidget)

from core.i18n import LocaleContext
from core.research.markets import SPECS, MarketDataUnavailable, provider_failure_reason
from core.theme import LIGHT
from .charts import nice_ticks, tick_digits
from .company_identity import CompanyMark
from .jobs import Jobs
from .owner_ui_language.home import MARKETS, TEXT, UNITS
from .typography import TONE_COLORS, TONES, icon_dir, is_dark, scaled_font, set_tone, tone_for

CARD_HEIGHT = 136
CARD_GAP = 16
SECTION_GAP = 48              # between the page's large sections (owner: "세로로 넓게 넓게 공간 쓰고")
HISTORY_DAYS = 400            # daily observations asked for: a year for every market (Bitcoin trades daily)
HISTORY_REFRESH_SECONDS = 1800
STALE_DAYS = 7
CHART_ASPECT = 0.5            # the chart's height is about half its width
CHART_MIN_HEIGHT = 300
CHART_MAX_HEIGHT = 640
RANGES = (("1m", 31), ("3m", 92), ("6m", 183), ("1y", 366))
DEFAULT_RANGE = "6m"
ANIMATION_MS = 260
_TICKERS = {"^GSPC": "SPX", "^KS11": "KOSPI", "DEXKOUS": "USDKRW", "DGS10": "US10Y", "VIXCLS": "VIX",
            "BTC-USD": "BTC"}
_MONTHS_EN = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def card_columns(width):
    """Market cards visible at once for a strip width: four on a wide window, fewer when narrow."""
    return 4 if width >= 960 else 3 if width >= 690 else 2 if width >= 430 else 1


def text(key, language, **fields):
    """Home display text in the window language (owner_ui_language.home.TEXT)."""
    english, korean = TEXT[key]
    template = korean if language == "ko" else english
    return template.format(**fields) if fields else template


@dataclass(frozen=True)
class MarketInfo:
    """One home market card: the core.research.markets symbol, its provider and its unit."""
    symbol: str
    provider: str
    unit: str

    @property
    def ticker(self):
        return _TICKERS.get(self.symbol, self.symbol)

    def name(self, language):
        english, korean = MARKETS.get(self.symbol, (self.symbol, self.symbol))
        return korean if language == "ko" else english

    def unit_text(self, language):
        english, korean = UNITS.get(self.unit, (self.unit, self.unit))
        return korean if language == "ko" else english


HOME_MARKETS = tuple(MarketInfo(symbol, provider, unit) for _label, symbol, provider, unit, _route in SPECS)


def _finite(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def value_text(value, ctx, digits=2):
    value = _finite(value)
    return "—" if value is None else ctx.number(value, digits)


def change_text(change, unit, ctx):
    """('+0.84%', 'up'); a yield moves in basis points, as the quotes table shows it. ('', None) when unknown."""
    change = _finite(change)
    if change is None:
        return "", None
    sign = "+" if change > 0 else ""
    body = ctx.number(change, 2) + " bp" if unit == "%" else ctx.percent(change / 100, 2)
    return sign + body, tone_for(change)


def _row_status(row, ctx):
    """The quotes table's own status words (watchlist._status), so a card and its table row agree."""
    from .watchlist import _status
    return _status(row, ctx)


def directory_name(directory, instrument, language):
    """A watchlist card's name from the symbol directory (as MarketsWorkspace.display_name), else the code."""
    if directory is not None and instrument.asset in ("domestic_stock", "overseas_stock"):
        listing = directory.lookup(instrument.asset, instrument.code, instrument.exchange)
        if listing is not None:
            return listing.label(language)
    return instrument.code


# History --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class MarketHistory:
    """One market's daily closes, or the authored reason they could not be read."""
    symbol: str
    dates: tuple = ()
    values: tuple = ()
    source: str = ""
    reason: str = ""
    loaded_at: str = ""

    @property
    def ok(self):
        return not self.reason and len(self.values) >= 2


def load_market_history(info, *, loader=None, days=HISTORY_DAYS, today=None):
    """Daily closes from the provider the card's row names; never synthetic, never another provider.

    `loader` follows core.ficc.data.load_series (id, source=, days=) -> Series. Never raises: a failure
    returns a MarketHistory with only an authored reason code (provider text can hold credential URLs).
    """
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        if loader is None:
            from core.ficc.data import load_series as loader
        series = loader(info.symbol, source=info.provider, days=days)
        if str(series.source).upper() != info.provider.upper():
            raise MarketDataUnavailable("invalid_response")  # a fallback answer is not this market's data
        dates = [str(day)[:10] for day in series.dates]
        values = list(series.values)
        if len(dates) != len(values) or dates != sorted(set(dates)):
            raise MarketDataUnavailable("invalid_response")
        pairs = [(day, float(value)) for day, value in zip(dates, values) if _finite(value) is not None]
        if len(pairs) < 2:
            raise MarketDataUnavailable("no_observations" if not pairs else "insufficient_observations")
        if date.fromisoformat(pairs[-1][0]) > (today or datetime.now(timezone.utc).date()) + timedelta(days=1):
            raise MarketDataUnavailable("invalid_response")  # a future observation
        return MarketHistory(info.symbol, tuple(day for day, _ in pairs), tuple(value for _, value in pairs),
                             str(series.source).upper(), "", stamp)
    except Exception as exc:
        return MarketHistory(info.symbol, reason=provider_failure_reason(exc), loaded_at=stamp)


def crop(history, range_key):
    """The closes inside a range ending at the last observation (at least two points)."""
    if history is None or not history.ok:
        return (), ()
    days = dict(RANGES)[range_key]
    start = (date.fromisoformat(history.dates[-1]) - timedelta(days=days)).isoformat()
    index = next((i for i, day in enumerate(history.dates) if day >= start), len(history.dates))
    index = min(index, len(history.dates) - 2)
    return history.dates[index:], history.values[index:]


def _age_seconds(stamp):
    try:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(stamp)).total_seconds()
    except (TypeError, ValueError):
        return float("inf")


def _stale(history, today=None):
    try:
        last = date.fromisoformat(history.dates[-1])
    except (IndexError, TypeError, ValueError):
        return False
    return ((today or date.today()) - last).days > STALE_DAYS


# Widgets ----------------------------------------------------------------------------------------
def _plain(home_role, value="", *, role="", wrap=False):
    """A label whose text the view writes in the window language itself (the catalogue leaves it alone)."""
    widget = QLabel(value)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(wrap)
    widget.setProperty("homeRole", home_role)
    if role:
        widget.setProperty("role", role)
    widget.setProperty("qg_literal", True)
    return widget


def _tone(widget, tone):
    if tone in TONES:
        set_tone(widget, tone)
    elif widget.property("tone"):
        widget.setProperty("tone", "")
        widget.style().unpolish(widget)
        widget.style().polish(widget)


def _repolish(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def blend(first, second, share=0.5):
    """`first` moved `share` of the way to `second` (hex colours): the very light lines of owner 2026-11-11."""
    a, b = QColor(first), QColor(second)
    mix = lambda x, y: round(x + (y - x) * share)
    return QColor(mix(a.red(), b.red()), mix(a.green(), b.green()), mix(a.blue(), b.blue())).name()


def hairline(p):
    """Owner 2026-11-11 ("구획 선을 연하게 ... 한칸한칸 공간을 넓게"): a 1px line half way from the border colour
    to the background; blocks are separated by whitespace and surface colour first."""
    return blend(p.border, p.bg, 0.5)


def home_stylesheet(p, dark):
    """Card, figure and control rules for the home view; the window stylesheet keeps everything else.

    Owner 2026-11-11: light section lines and generous space. Cards and the chart block are surfaces with a
    hairline, no heavy box; the selected card is a soft accent tint; focus stays visible as a 1px accent line."""
    t = TONE_COLORS[dark]
    line = hairline(p)
    hover = blend(p.surface, p.surface_2, 0.6)
    chosen = blend(p.surface, p.accent_soft, 0.8)
    chosen_line = blend(p.accent, p.accent_soft, 0.55)
    return f"""
      QFrame#homeMarketCard {{ background: {p.surface}; border: 1px solid {line}; border-radius: 18px; }}
      QFrame#homeMarketCard:hover {{ background: {hover}; }}
      QFrame#homeMarketCard[selected='true'], QFrame#homeMarketCard[selected='true']:hover {{ background: {chosen}; border: 1px solid {chosen_line}; }}
      QFrame#homeMarketCard:focus, QFrame#homeMarketCard[selected='true']:focus {{ border: 1px solid {p.accent}; }}
      QFrame#homeMarketCard QLabel {{ background: transparent; }}
      QFrame#homeChartPanel {{ background: {p.surface}; border: 1px solid {line}; border-radius: 20px; }}
      QLabel[homeRole='cardName'] {{ font-size: 15px; font-weight: 500; letter-spacing: -0.2px; }}
      QLabel[homeRole='ticker'] {{ font-size: 12px; font-weight: 500; color: {p.muted}; letter-spacing: 0.2px; }}
      QLabel[homeRole='value'] {{ font-family: "QG Interface"; font-size: 24px; font-weight: 600; letter-spacing: 0px; }}
      QLabel[homeRole='unit'] {{ font-size: 12px; font-weight: 500; color: {p.muted}; letter-spacing: 0.3px; padding-bottom: 4px; }}
      QLabel[homeRole='change'] {{ font-family: "QG Interface"; font-size: 14px; font-weight: 600; letter-spacing: 0px; color: {t['flat']}; }}
      QLabel[homeRole='change'][tone='up'] {{ color: {t['up']}; }}
      QLabel[homeRole='change'][tone='down'] {{ color: {t['down']}; }}
      QLabel[homeRole='state'] {{ font-size: 12px; font-weight: 500; color: {p.muted}; }}
      QLabel[homeRole='state'][level='warn'] {{ color: {p.warning}; }}
      QLabel[homeRole='pageLabel'] {{ font-family: "QG Interface"; font-size: 13px; color: {p.muted}; letter-spacing: 0px; }}
      QLabel[homeRole='chartName'] {{ font-size: 20px; font-weight: 500; letter-spacing: -0.4px; }}
      QLabel[homeRole='bigValue'] {{ font-family: "QG Interface"; font-size: 34px; font-weight: 600; letter-spacing: -0.3px; }}
      QLabel[homeRole='bigUnit'] {{ font-size: 13px; font-weight: 500; color: {p.muted}; letter-spacing: 0.3px; padding-bottom: 7px; }}
      QFrame#homeChartPanel QLabel[homeRole='bigChange'] {{ font-family: "QG Interface"; font-size: 14px; font-weight: 600; letter-spacing: 0px; padding: 3px 9px; border-radius: 8px; color: {t['flat']}; background: {t['flat_tint']}; }}
      QFrame#homeChartPanel QLabel[homeRole='bigChange'][tone='up'] {{ color: {t['up']}; background: {t['up_tint']}; }}
      QFrame#homeChartPanel QLabel[homeRole='bigChange'][tone='down'] {{ color: {t['down']}; background: {t['down_tint']}; }}
      QLabel[homeRole='period'] {{ font-family: "QG Interface"; font-size: 14px; font-weight: 500; letter-spacing: 0px; color: {p.muted}; }}
      QLabel[homeRole='period'][tone='up'] {{ color: {t['up']}; }}
      QLabel[homeRole='period'][tone='down'] {{ color: {t['down']}; }}
      QPushButton[homeQuiet='true'] {{ padding: 6px 14px; border: 1px solid {line}; border-radius: 13px; background: transparent; }}
      QPushButton[homeQuiet='true']:hover {{ background: {p.accent_soft}; border: 1px solid {p.accent_soft}; }}
      QPushButton[homeQuiet='true']:focus {{ border: 1px solid {p.accent}; }}
      QPushButton[homeArrow='true'] {{ min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px; padding: 0px; border-radius: 17px; border: 1px solid {line}; background: transparent; }}
      QPushButton[homeArrow='true']:hover {{ background: {p.accent_soft}; border: 1px solid {p.accent_soft}; }}
      QPushButton[homeArrow='true']:focus {{ border: 1px solid {p.accent}; }}
      QPushButton[homeArrow='true']:disabled {{ background: transparent; border: 1px solid transparent; }}
      QPushButton[homeRange='true'] {{ padding: 5px 12px; border: 1px solid transparent; border-radius: 12px; background: transparent; color: {p.muted}; }}
      QPushButton[homeRange='true']:hover {{ background: {p.surface_2}; color: {p.text}; }}
      QPushButton[homeRange='true']:checked {{ background: {p.accent_soft}; color: {p.accent}; font-weight: 600; }}
      QPushButton[homeRange='true']:focus {{ border: 1px solid {p.accent}; }}
    """


class MarketCard(QFrame):
    """One market: name, value with its unit, signed change in the Korean rise/fall tones."""
    activated = pyqtSignal(str)
    stepped = pyqtSignal(int)
    focused = pyqtSignal(str)

    def __init__(self, info, parent=None):
        super().__init__(parent)
        self.info = info
        self.setObjectName("homeMarketCard")
        self.setProperty("selected", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 15)
        layout.setSpacing(0)
        head = QHBoxLayout()
        head.setSpacing(10)
        self.mark = CompanyMark(info.symbol, info.ticker, size=30)
        head.addWidget(self.mark, 0, Qt.AlignmentFlag.AlignVCenter)
        names = QVBoxLayout()
        names.setSpacing(0)
        self.name = _plain("cardName")
        self.name.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)  # elided to fit
        self.full_name = ""
        self.ticker = _plain("ticker")
        names.addWidget(self.name)
        names.addWidget(self.ticker)
        head.addLayout(names, 1)
        layout.addLayout(head)
        layout.addStretch(1)
        figures = QHBoxLayout()
        figures.setSpacing(6)
        self.value = _plain("value")
        self.unit = _plain("unit")
        figures.addWidget(self.value, 0, Qt.AlignmentFlag.AlignBottom)
        figures.addWidget(self.unit, 0, Qt.AlignmentFlag.AlignBottom)
        figures.addStretch(1)
        layout.addLayout(figures)
        layout.addSpacing(2)
        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        self.change = _plain("change")
        self.state = _plain("state")
        bottom.addWidget(self.change)
        bottom.addStretch(1)
        bottom.addWidget(self.state)
        layout.addLayout(bottom)
        for widget in (self.name, self.ticker, self.value, self.unit, self.change, self.state):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def render(self, row, ctx):
        language, info = ctx.language, self.info
        row = row or {"status": "NOT_LOADED"}
        name = info.name(language)
        self.mark.set_identity(info.symbol, name)
        self.full_name = name
        self._fit_name()
        self.ticker.setText(info.ticker)
        value = _finite(row.get("value"))
        self.value.setText(value_text(value, ctx))
        self.unit.setText(info.unit_text(language) if value is not None else "")
        change, tone = change_text(row.get("change"), info.unit, ctx)
        self.change.setText(change)
        self.change.setVisible(bool(change))
        _tone(self.change, tone)
        status = row.get("status") or "NOT_LOADED"
        state = "" if status == "OBSERVED" else _row_status(row, ctx)
        self.state.setText(state)
        self.state.setVisible(bool(state))
        level = "warn" if status in ("STALE", "UNAVAILABLE") else ""
        if self.state.property("level") != level:
            self.state.setProperty("level", level)
            _repolish(self.state)
        source = str(row.get("provider") or info.provider.upper())
        self.setToolTip(text("source", language, source=source, date=row.get("observation_date") or "—"))
        self.setAccessibleName(text("card_name", language, name=name,
                                    value=f"{self.value.text()} {self.unit.text()}".strip(),
                                    change=" ".join(part for part in (change, state) if part)).strip())

    def _fit_name(self):
        """The whole name when it fits, else elided (the accessible name and tooltip keep it whole)."""
        width = self.name.width()
        if width < 20:
            self.name.setText(self.full_name)
            return
        self.name.ensurePolished()
        metrics = QFontMetricsF(self.name.font())
        self.name.setText(metrics.elidedText(self.full_name, Qt.TextElideMode.ElideRight, width))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_name()

    def set_selected(self, selected):
        if bool(self.property("selected")) != bool(selected):
            self.setProperty("selected", bool(selected))
            _repolish(self)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.activated.emit(self.info.symbol)
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.activated.emit(self.info.symbol)
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            self.stepped.emit(-1 if key == Qt.Key.Key_Left else 1)
        elif key in (Qt.Key.Key_Home, Qt.Key.Key_End):
            self.stepped.emit(-len(HOME_MARKETS) if key == Qt.Key.Key_Home else len(HOME_MARKETS))
        else:
            super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focused.emit(self.info.symbol)


class MarketStrip(QWidget):
    """The cards on one sliding track: `visible` of them fit the width; paging slides the track."""
    moved = pyqtSignal()

    def __init__(self, cards, parent=None):
        super().__init__(parent)
        self.cards = list(cards)
        self.first, self.visible = 0, min(4, len(self.cards))
        self.track = QWidget(self)
        for card in self.cards:
            card.setParent(self.track)
        self.animation = QPropertyAnimation(self.track, b"pos", self)
        self.animation.setDuration(ANIMATION_MS)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setFixedHeight(CARD_HEIGHT)
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def card_width(self):
        return (self.width() - CARD_GAP * (self.visible - 1)) / max(1, self.visible)

    def arrange(self, *, animate=False):
        count = len(self.cards)
        self.visible = max(1, min(card_columns(self.width()), count))
        width = self.card_width()
        for index, card in enumerate(self.cards):
            card.setGeometry(round(index * (width + CARD_GAP)), 0, max(1, round(width)), CARD_HEIGHT)
        self.track.resize(max(1, round(count * width + (count - 1) * CARD_GAP)), CARD_HEIGHT)
        self.first = max(0, min(self.first, count - self.visible))
        target = QPoint(-round(self.first * (width + CARD_GAP)), 0)
        self.animation.stop()
        if animate and self.isVisible() and self.track.pos() != target:
            self.animation.setStartValue(self.track.pos())
            self.animation.setEndValue(target)
            self.animation.start()
        else:
            self.track.move(target)
        self.moved.emit()

    def can_page(self, step):
        return self.first > 0 if step < 0 else self.first + self.visible < len(self.cards)

    def page(self, step):
        """One page left or right (a page is the cards that fit); the last page is always full."""
        if not self.can_page(step):
            return False
        self.first += self.visible if step > 0 else -self.visible
        self.arrange(animate=True)
        return True

    def reveal(self, index):
        if index < self.first:
            self.first = index
        elif index >= self.first + self.visible:
            self.first = index - self.visible + 1
        else:
            return
        self.arrange(animate=True)

    def shown(self):
        return list(range(self.first, min(len(self.cards), self.first + self.visible)))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.arrange()


class HistoryChart(QWidget):
    """The selected market's daily closes: an area line in the period's rise/fall tone, a dashed line at the
    range's first close, the price scale on the right with the last close tagged, month (or day) ticks below
    and a crosshair readout under the pointer. Nothing is inferred: no smoothing, no projected values."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dates, self.values = (), ()
        self.colors, self.dark = LIGHT, False
        self.ctx = LocaleContext("en_US")
        self.range_key, self.decimals = DEFAULT_RANGE, 2
        self.message = ""
        self.hover = None
        self.setMouseTracking(True)
        self.setMinimumWidth(280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(CHART_MIN_HEIGHT)

    @staticmethod
    def height_for(width):
        return max(CHART_MIN_HEIGHT, min(CHART_MAX_HEIGHT, round(width * CHART_ASPECT)))

    def sizeHint(self):
        width = max(600, self.width())
        return QSize(width, self.height_for(width))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        wanted = self.height_for(event.size().width())
        if self.height() != wanted:
            self.setFixedHeight(wanted)  # owner 2026-11-11: about half as tall as wide

    def set_series(self, dates, values, *, decimals=2, range_key=DEFAULT_RANGE, message=""):
        self.dates, self.values = tuple(dates), tuple(float(v) for v in values)
        self.decimals, self.range_key, self.message = decimals, range_key, message
        self.hover = None
        self.update()

    def set_style(self, colors, ctx):
        self.colors, self.dark, self.ctx = colors, is_dark(colors), ctx
        self.update()

    # Geometry ---------------------------------------------------------------------------------
    def _scale(self):
        values = self.values
        low, high = min(values), max(values)
        span = high - low
        pad = span * 0.08 if span > 0 else max(abs(high) * 0.01, 0.01)
        low, high = low - pad, high + pad
        ticks, step = nice_ticks(low, high, 5)
        digits = min(4, tick_digits(step)) if step else self.decimals
        number = self._number_font(12, 400)
        metrics = QFontMetricsF(number)
        labels = [self.ctx.number(v, digits) for v in ticks]
        last = self.ctx.number(values[-1], self.decimals)
        axis = max(metrics.horizontalAdvance(s) for s in [*labels, last]) + 30
        line = metrics.height()
        plot = QRectF(4, 16, max(40., self.width() - axis - 4), max(40., self.height() - 16 - line - 20))
        return low, high, list(zip(ticks, labels)), last, plot, number, metrics

    def _number_font(self, size, weight):
        from .font_policy import number_font
        return number_font(scaled_font(self.font(), size, weight))

    def _x(self, plot, index):
        return plot.left() + plot.width() * index / max(1, len(self.values) - 1)

    @staticmethod
    def _y(plot, low, high, value):
        return plot.bottom() - (value - low) / ((high - low) or 1) * plot.height()

    def _date_ticks(self):
        """(index, label) at month starts (the year at January) for 3M and longer; about weekly for 1M."""
        korean = self.ctx.language == "ko"
        out = []
        if self.range_key == "1m":
            step = max(1, len(self.dates) // 5)
            for index in range(len(self.dates) - 1, -1, -step):
                day = self.dates[index]
                month, dom = int(day[5:7]), int(day[8:10])
                out.append((index, f"{month}.{dom:02d}" if korean else f"{_MONTHS_EN[month - 1]} {dom}"))
            return out[::-1]
        for index in range(1, len(self.dates)):
            if self.dates[index][:7] != self.dates[index - 1][:7]:
                year, month = int(self.dates[index][:4]), int(self.dates[index][5:7])
                if month == 1:
                    out.append((index, str(year)))
                else:
                    out.append((index, f"{month}월" if korean else _MONTHS_EN[month - 1]))
        return out

    # Painting ---------------------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = self.colors
        if len(self.values) < 2:
            painter.setPen(QPen(QColor(hairline(c)), 1, Qt.PenStyle.DashLine))
            for k in range(1, 4):
                y = self.height() * k / 4
                painter.drawLine(QPointF(4, y), QPointF(self.width() - 4, y))
            painter.setFont(scaled_font(self.font(), 15, 400))
            box = QRectF(self.rect()).adjusted(40, 0, -40, 0)
            metrics = QFontMetricsF(painter.font())
            needed = metrics.boundingRect(box, int(Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter),
                                          self.message).adjusted(-18, -12, 18, 12)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(c.bg))
            painter.drawRoundedRect(needed, 12, 12)
            painter.setPen(QColor(c.muted))
            painter.drawText(box, int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap), self.message)
            return
        tones = TONE_COLORS[self.dark]
        low, high, ticks, last_label, plot, number, metrics = self._scale()
        first, last = self.values[0], self.values[-1]
        tone = tones[tone_for(last - first)]
        y = lambda value: self._y(plot, low, high, value)
        painter.setFont(number)
        grid = QColor(hairline(c))
        last_y = y(last)
        for value, label in ticks:
            gy = y(value)
            if not plot.top() - 1 <= gy <= plot.bottom() + 1:
                continue
            painter.setPen(QPen(grid, 1))
            painter.drawLine(QPointF(plot.left(), gy), QPointF(plot.right(), gy))
            if abs(gy - last_y) < metrics.height() + 4:
                continue  # the last close's tag takes this place on the scale
            painter.setPen(QColor(c.muted))
            painter.drawText(QRectF(plot.right() + 12, gy - metrics.height() / 2, 200, metrics.height()),
                             int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), label)
        # The range's first close: the line the period's rise or fall is read against.
        base = QColor(c.muted)
        base.setAlpha(120)
        painter.setPen(QPen(base, 1, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(plot.left(), y(first)), QPointF(plot.right(), y(first)))
        points = [QPointF(self._x(plot, i), y(v)) for i, v in enumerate(self.values)]
        line = QPainterPath(points[0])
        for point in points[1:]:
            line.lineTo(point)
        area = QPainterPath(line)
        area.lineTo(points[-1].x(), plot.bottom())
        area.lineTo(points[0].x(), plot.bottom())
        area.closeSubpath()
        fill = QLinearGradient(0, plot.top(), 0, plot.bottom())
        top, bottom = QColor(tone), QColor(tone)
        top.setAlpha(54 if self.dark else 46)
        bottom.setAlpha(0)
        fill.setColorAt(0, top)
        fill.setColorAt(1, bottom)
        painter.fillPath(area, QBrush(fill))
        pen = QPen(QColor(tone), 2)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(line)
        painter.setPen(QPen(grid, 1))
        painter.drawLine(QPointF(plot.left(), plot.bottom()), QPointF(plot.right(), plot.bottom()))
        self._draw_date_ticks(painter, plot, metrics)
        # Last close: a dot on the line and a tag on the price scale.
        end = points[-1]
        painter.setPen(QPen(QColor(c.surface), 2))
        painter.setBrush(QColor(tone))
        painter.drawEllipse(end, 4.5, 4.5)
        painter.setFont(self._number_font(12, 600))
        tag_metrics = QFontMetricsF(painter.font())
        tag = QRectF(plot.right() + 6, end.y() - tag_metrics.height() / 2 - 3,
                     tag_metrics.horizontalAdvance(last_label) + 14, tag_metrics.height() + 6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(tone))
        painter.drawRoundedRect(tag, 5, 5)
        painter.setPen(QColor(c.bg if self.dark else "#FFFFFF"))
        painter.drawText(tag, int(Qt.AlignmentFlag.AlignCenter), last_label)
        if self.hover is not None and 0 <= self.hover < len(points):
            self._draw_hover(painter, plot, points[self.hover], tone)

    def _draw_date_ticks(self, painter, plot, metrics):
        painter.setFont(self._number_font(12, 400))
        painter.setPen(QColor(self.colors.muted))
        right_edge, previous = self.width() - 2, -1e9
        for index, label in self._date_ticks():
            width = metrics.horizontalAdvance(label) + 6
            x = self._x(plot, index)
            left = min(max(plot.left(), x - width / 2), plot.right() - width)
            if left < previous + 14 or left + width > right_edge:
                continue
            painter.setPen(QPen(QColor(hairline(self.colors)), 1))
            painter.drawLine(QPointF(x, plot.bottom()), QPointF(x, plot.bottom() + 4))
            painter.setPen(QColor(self.colors.muted))
            painter.drawText(QRectF(left, plot.bottom() + 8, width, metrics.height()),
                             int(Qt.AlignmentFlag.AlignCenter), label)
            previous = left + width

    def _draw_hover(self, painter, plot, point, tone):
        c = self.colors
        painter.setPen(QPen(QColor(c.muted), 1, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(point.x(), plot.top()), QPointF(point.x(), plot.bottom()))
        painter.setPen(QPen(QColor(c.surface), 2))
        painter.setBrush(QColor(tone))
        painter.drawEllipse(point, 4, 4)
        readout = f"{self.dates[self.hover]}   {self.ctx.number(self.values[self.hover], self.decimals)}"
        painter.setFont(self._number_font(13, 500))
        metrics = QFontMetricsF(painter.font())
        box = QRectF(plot.left() + 8, plot.top() + 6, metrics.horizontalAdvance(readout) + 20, metrics.height() + 10)
        painter.setPen(QPen(QColor(hairline(c)), 1))
        painter.setBrush(QColor(c.surface))
        painter.drawRoundedRect(box, 8, 8)
        painter.setPen(QColor(c.text))
        painter.drawText(box, int(Qt.AlignmentFlag.AlignCenter), readout)

    def mouseMoveEvent(self, event):
        if len(self.values) >= 2:
            plot = self._scale()[4]
            fraction = (event.position().x() - plot.left()) / max(1., plot.width())
            index = max(0, min(len(self.values) - 1, round(fraction * (len(self.values) - 1))))
            if index != self.hover:
                self.hover = index
                self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self.hover is not None:
            self.hover = None
            self.update()
        super().leaveEvent(event)


class HomeView(QWidget):
    """Market cards that page left/right, the selected market's chart and the watchlist chart cards."""
    refresh_requested = pyqtSignal()
    stock_requested = pyqtSignal(object)
    add_requested = pyqtSignal()

    def __init__(self, *, store, card_router_factory=None, name_fn=None, rows_source=None, history_loader=None,
                 locale=None, auto_load=True, parent=None):
        super().__init__(parent)
        from .markets_view import WatchlistGrid
        self._ready = False
        self.ctx = locale or LocaleContext("ko_KR")
        self.colors, self.auto_load = LIGHT, auto_load
        self.rows_source, self.history_loader = rows_source, history_loader
        self.infos = {info.symbol: info for info in HOME_MARKETS}
        self.rows, self._row_signature = {}, None
        self.histories, self.failures = {}, {}
        # KOSPI first, as the owner's TradingView reference opens (2026-11-11); falls back to the first card.
        self.selected = next((i.symbol for i in HOME_MARKETS if i.symbol == "^KS11"), HOME_MARKETS[0].symbol)
        self.range_key = DEFAULT_RANGE
        self._loading, self._wanted, self._epoch = None, None, 0
        self.jobs = Jobs(self)
        self.jobs.succeeded.connect(self._history_loaded)
        self.jobs.failed.connect(self._history_failed)
        self.jobs.busy_changed.connect(self._history_busy)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Section header: heading, page position, refresh and the two arrows.
        head = QHBoxLayout()
        head.setSpacing(8)
        self.heading = _plain("section", role="heading")
        head.addWidget(self.heading, 0, Qt.AlignmentFlag.AlignVCenter)
        self.section_note = _plain("note", role="caption")
        head.addSpacing(6)
        head.addWidget(self.section_note, 0, Qt.AlignmentFlag.AlignVCenter)
        head.addStretch(1)
        self.page_label = _plain("pageLabel")
        head.addWidget(self.page_label, 0, Qt.AlignmentFlag.AlignVCenter)
        head.addSpacing(6)
        self.refresh_button = QPushButton()
        self.refresh_button.setProperty("qg_literal", True)
        self.refresh_button.setProperty("homeQuiet", True)
        self.refresh_button.clicked.connect(self.refresh)
        head.addWidget(self.refresh_button, 0, Qt.AlignmentFlag.AlignVCenter)
        head.addSpacing(4)
        self.previous_button, self.next_button = QPushButton(), QPushButton()
        for button, step in ((self.previous_button, -1), (self.next_button, 1)):
            button.setProperty("homeArrow", True)
            button.setProperty("qg_literal", True)
            button.setIconSize(QSize(14, 14))
            button.clicked.connect(lambda _checked=False, s=step: self.page(s))
            head.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(head)
        layout.addSpacing(16)

        # The cards.
        self.cards = {}
        for info in HOME_MARKETS:
            card = MarketCard(info)
            card.activated.connect(self.select)
            card.stepped.connect(self._step)
            card.focused.connect(self._card_focused)
            self.cards[info.symbol] = card
        self.strip = MarketStrip(self.cards.values())
        self.strip.moved.connect(self._sync_paging)
        self.strip.setProperty("reading_help_keep_visible", True)  # the glossary overlay never covers these
        layout.addWidget(self.strip)
        layout.addSpacing(28)

        # The selected market's chart.
        panel = QFrame()
        panel.setObjectName("homeChartPanel")  # a light surface, not the heavier global panel (owner 2026-11-11)
        panel.setProperty("reading_help_keep_visible", True)
        self.chart_panel = panel
        inner = QVBoxLayout(panel)
        inner.setContentsMargins(28, 24, 28, 22)
        inner.setSpacing(0)
        top = QHBoxLayout()
        top.setSpacing(12)
        self.chart_mark = CompanyMark(HOME_MARKETS[0].symbol, size=40)
        top.addWidget(self.chart_mark, 0, Qt.AlignmentFlag.AlignVCenter)
        names = QVBoxLayout()
        names.setSpacing(1)
        self.chart_name = _plain("chartName")
        self.chart_ticker = _plain("ticker")
        names.addWidget(self.chart_name)
        names.addWidget(self.chart_ticker)
        top.addLayout(names, 1)
        self.range_buttons = {}
        self.range_group = QButtonGroup(self)
        self.range_group.setExclusive(True)
        for key, _days in RANGES:
            button = QPushButton()
            button.setCheckable(True)
            button.setProperty("homeRange", True)
            button.setProperty("qg_literal", True)
            button.setChecked(key == self.range_key)
            button.clicked.connect(lambda _checked=False, k=key: self.set_range(k))
            self.range_group.addButton(button)
            self.range_buttons[key] = button
            top.addWidget(button, 0, Qt.AlignmentFlag.AlignTop)
        inner.addLayout(top)
        inner.addSpacing(14)
        figures = QHBoxLayout()
        figures.setSpacing(8)
        self.chart_value = _plain("bigValue")
        self.chart_unit = _plain("bigUnit")
        self.chart_change = _plain("bigChange")
        self.chart_period = _plain("period")
        figures.addWidget(self.chart_value, 0, Qt.AlignmentFlag.AlignBottom)
        figures.addWidget(self.chart_unit, 0, Qt.AlignmentFlag.AlignBottom)
        figures.addSpacing(6)
        figures.addWidget(self.chart_change, 0, Qt.AlignmentFlag.AlignVCenter)
        figures.addSpacing(6)
        figures.addWidget(self.chart_period, 0, Qt.AlignmentFlag.AlignVCenter)
        figures.addStretch(1)
        inner.addLayout(figures)
        inner.addSpacing(16)
        self.chart = HistoryChart()
        inner.addWidget(self.chart)
        self.chart_status = _plain("chartStatus", role="caption", wrap=True)
        self.chart_status.hide()
        inner.addSpacing(6)
        inner.addWidget(self.chart_status)
        layout.addWidget(panel)
        layout.addSpacing(SECTION_GAP)

        # The watchlist chart cards (moved here from Markets; the grid itself is markets_view's).
        self.grid = WatchlistGrid(store, router_factory=card_router_factory, name_fn=name_fn, locale=self.ctx,
                                  auto_load=auto_load)
        self.grid.setProperty("reading_help_keep_visible", True)
        self.grid.open_requested.connect(self.stock_requested)
        self.add_button = QPushButton()
        self.add_button.setProperty("qg_literal", True)
        self.add_button.setProperty("homeQuiet", True)
        self.add_button.clicked.connect(self.add_requested)
        self.grid.refresh_button.setProperty("homeQuiet", True)  # the same light buttons as this view's
        grid_head = self.grid.layout().itemAt(0).layout()
        grid_head.insertWidget(grid_head.indexOf(self.grid.refresh_button), self.add_button)
        layout.addWidget(self.grid)

        self.select(self.selected, load=False)
        self.set_locale(self.ctx)
        self._apply_theme(LIGHT)
        self._ready = True
        if rows_source is not None:
            self.set_rows(rows_source() or ())

    # Window state ------------------------------------------------------------------------------
    def follow_window(self):
        """Pick up the window's language, theme and quote rows; a no-op when nothing changed."""
        if not self._ready:
            return
        window = self.window()
        ctx = getattr(window, "ctx", None)
        if ctx is not None and ctx is not self.ctx:
            self.set_locale(ctx)
        colors = getattr(window, "colors", None)
        if colors is not None and colors != self.colors:
            self.set_theme(colors)
        if self.rows_source is not None:
            self.set_rows(self.rows_source() or ())

    def _reserve_text_space(self):  # LanguageController.apply calls this on every widget
        self.follow_window()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.Type.StyleChange, QEvent.Type.LocaleChange):
            self.follow_window()

    def set_rows(self, rows):
        """The home market rows of the window's quotes table (other rows are ignored)."""
        wanted = {str(row.get("symbol")): row for row in rows if str(row.get("symbol")) in self.infos}
        signature = tuple((symbol, *(str(row.get(field)) for field in (
            "value", "change", "status", "observation_date", "reason_code", "provider")))
            for symbol, row in sorted(wanted.items()))
        if signature == self._row_signature:
            return False
        self._row_signature = signature
        self.rows = {symbol: dict(row) for symbol, row in wanted.items()}
        self.render()
        return True

    def set_locale(self, ctx):
        self.ctx = ctx
        self.grid.set_locale(ctx)
        self.render()

    def set_theme(self, colors):
        self._apply_theme(colors)
        self.render()

    def _apply_theme(self, colors):
        self.colors = colors
        dark = is_dark(colors)
        sheet = home_stylesheet(colors, dark)
        if self.styleSheet() != sheet:
            self.setStyleSheet(sheet)
        theme = "dark" if dark else "light"
        self.previous_button.setIcon(QIcon(f"{icon_dir()}/chevron-left-{theme}.svg"))
        self.next_button.setIcon(QIcon(f"{icon_dir()}/chevron-right-{theme}.svg"))
        for card in self.cards.values():
            card.mark.set_theme(colors)
        self.chart_mark.set_theme(colors)
        self.grid.set_theme(dark)

    def set_busy(self, busy):
        """The window's quote refresh is running: one refresh at a time."""
        self.refresh_button.setEnabled(not busy)

    # Selection and paging ----------------------------------------------------------------------
    def select(self, symbol, *, load=True):
        if symbol not in self.infos:
            return False
        self.selected = symbol
        for key, card in self.cards.items():
            card.set_selected(key == symbol)
        self.strip.reveal(list(self.cards).index(symbol))
        self.render_chart()
        if load:
            self.ensure_history()
        return True

    def page(self, step):
        moved = self.strip.page(step)
        self._sync_paging()
        return moved

    def _step(self, delta):
        order = list(self.cards)
        index = max(0, min(len(order) - 1, order.index(self.selected) + delta))
        self.select(order[index])
        self.cards[order[index]].setFocus(Qt.FocusReason.OtherFocusReason)

    def _card_focused(self, symbol):
        self.strip.reveal(list(self.cards).index(symbol))

    def _sync_paging(self):
        shown = self.strip.shown()
        self.previous_button.setEnabled(self.strip.can_page(-1))
        self.next_button.setEnabled(self.strip.can_page(1))
        if shown:
            self.page_label.setText(text("page", self.ctx.language, first=shown[0] + 1, last=shown[-1] + 1,
                                         total=len(self.cards)))
        self.page_label.setVisible(len(shown) < len(self.cards))

    def set_range(self, key):
        if key not in dict(RANGES):
            return
        self.range_key = key
        self.range_buttons[key].setChecked(True)
        self.render_chart()

    # Loading -------------------------------------------------------------------------------------
    def refresh(self):
        """The user's Refresh: the window reloads its quote rows; the selected chart reloads here."""
        self.refresh_requested.emit()
        self.ensure_history(manual=True)

    def ensure_history(self, symbol=None, *, manual=False):
        """Load a market's closes unless loaded recently. Only manual loads run with automatic loading off."""
        symbol = symbol or self.selected
        if not manual:
            if not self.auto_load:
                return False
            known = self.histories.get(symbol) or self.failures.get(symbol)
            if known is not None and _age_seconds(known.loaded_at) < HISTORY_REFRESH_SECONDS:
                return False
        if symbol == self._loading:
            return False
        if self.jobs.busy:
            self._wanted = symbol
            return False
        info, loader, epoch = self.infos[symbol], self.history_loader, self._epoch
        self._loading = symbol
        started = self.jobs.start(lambda: (epoch, load_market_history(info, loader=loader)))
        self.render_chart()
        return started

    @pyqtSlot(object)
    def _history_loaded(self, value):
        epoch, history = value
        if epoch != self._epoch:
            return
        previous = self.histories.get(history.symbol)
        if not history.ok and previous is not None and previous.ok:
            self.failures[history.symbol] = history  # keep the last good chart and say so
        else:
            self.histories[history.symbol] = history
            self.failures.pop(history.symbol, None)

    @pyqtSlot(str)
    def _history_failed(self, code):  # load_market_history never raises; kept for completeness
        if self._loading:
            self._history_loaded((self._epoch, MarketHistory(
                self._loading, reason="provider_unavailable",
                loaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))))

    @pyqtSlot(bool)
    def _history_busy(self, busy):
        if busy:
            return
        self._loading = None
        self.render_chart()
        wanted, self._wanted = self._wanted, None
        if wanted is not None:
            self.ensure_history(wanted, manual=True)

    def stop(self):
        """Drop late answers and stop the watchlist cards (the window is closing)."""
        self._epoch += 1
        self._wanted = None
        self.grid.stop()

    def showEvent(self, event):
        super().showEvent(event)
        if self.auto_load:
            QTimer.singleShot(0, self.ensure_history)

    def hideEvent(self, event):
        super().hideEvent(event)
        if not self.window().isVisible():
            self.stop()

    # Presentation --------------------------------------------------------------------------------
    def render(self):
        language = self.ctx.language
        self.heading.setText(text("section", language))
        self.section_note.setText(text("section_note", language))
        self.refresh_button.setText(text("refresh", language))
        self.refresh_button.setAccessibleName(text("refresh_name", language))
        self.previous_button.setAccessibleName(text("previous", language))
        self.previous_button.setToolTip(text("previous", language))
        self.next_button.setAccessibleName(text("next", language))
        self.next_button.setToolTip(text("next", language))
        self.add_button.setText("+ " + text("add", language))
        self.add_button.setToolTip(text("add_tip", language))
        self.add_button.setAccessibleName(text("add", language))
        for key, button in self.range_buttons.items():
            label = text("range_" + key, language)
            button.setText(label)
            button.setAccessibleName(text("range_name", language, range=label))
        for symbol, card in self.cards.items():
            card.render(self.rows.get(symbol), self.ctx)
        self._sync_paging()
        self.render_chart()

    def render_chart(self):
        language, ctx = self.ctx.language, self.ctx
        info = self.infos[self.selected]
        row = self.rows.get(self.selected) or {}
        history = self.histories.get(self.selected)
        failure = self.failures.get(self.selected)
        name = info.name(language)
        self.chart_mark.set_identity(info.symbol, name)
        self.chart_name.setText(name)
        self.chart_ticker.setText(f"{info.ticker} · {text('daily', language)}")
        dates, values = crop(history, self.range_key)
        latest = _finite(row.get("value"))
        if latest is None and values:
            latest = values[-1]
        self.chart_value.setText(value_text(latest, ctx))
        self.chart_unit.setText(info.unit_text(language) if latest is not None else "")
        change, tone = change_text(row.get("change"), info.unit, ctx)
        self.chart_change.setText(change)
        self.chart_change.setVisible(bool(change))
        _tone(self.chart_change, tone)
        range_label = text("range_" + self.range_key, language)
        period = ""
        if len(values) >= 2:
            move = (values[-1] - values[0]) * 100 if info.unit == "%" else (
                (values[-1] / values[0] - 1) * 100 if values[0] else None)
            moved, period_tone = change_text(move, info.unit, ctx)
            period = text("period", language, range=range_label, change=moved) if moved else ""
        else:
            period_tone = None
        self.chart_period.setText(period)
        self.chart_period.setVisible(bool(period))
        _tone(self.chart_period, period_tone)
        source_history = history if history is not None and history.ok else None
        if source_history is not None:
            self.chart_value.setToolTip(text("source", language, source=source_history.source,
                                             date=source_history.dates[-1]))
        else:
            self.chart_value.setToolTip(text("source", language, source=str(row.get("provider") or info.provider.upper()),
                                             date=row.get("observation_date") or "—"))
        reason = lambda item: _row_status({"status": "UNAVAILABLE", "reason_code": item.reason}, ctx)
        if len(values) < 2:
            if self._loading == self.selected:
                message = text("chart_loading", language)
            elif history is not None and not history.ok:
                message = text("chart_failed", language, reason=reason(history))
            elif history is not None:
                message = text("chart_short", language)
            elif not self.auto_load:
                message = text("chart_off", language)
            else:
                message = text("chart_waiting", language)
            status = ""
        else:
            message = ""
            notes = []
            if self._loading == self.selected:
                notes.append(text("loading", language))
            if failure is not None:
                notes.append(text("chart_kept", language, reason=reason(failure)))
            if _stale(history):
                notes.append(text("chart_stale", language, days=STALE_DAYS))
            status = " · ".join(notes)
        self.chart.set_style(self.colors, ctx)
        self.chart.set_series(dates, values, decimals=2, range_key=self.range_key, message=message)
        self.chart.setAccessibleName(text("chart_name", language, name=name, range=range_label))
        self.chart_status.setText(status)
        self.chart_status.setVisible(bool(status))


def fold_stylesheet(p):
    """The "전체 시세 표" fold toggle: a borderless title, and Home's 1px `accent` focus line while it has the
    keyboard focus (Tab; a QToolButton takes no focus on click). The focused padding is 1px smaller so the
    button keeps its size; the unfocused look is unchanged. Set on the toggle itself, so the window sheet's
    rules never hide it."""
    return ("QToolButton#homeFoldToggle { font-size: 17px; font-weight: 500; letter-spacing: -0.3px; border: 0px; "
            "padding: 4px 2px; background: transparent; }"
            f" QToolButton#homeFoldToggle:focus {{ border: 1px solid {p.accent}; border-radius: 6px; "
            "padding: 3px 1px; }")


class QuotesFold(QWidget):
    """A closed-by-default section holding the full quotes table (owner: no big table on Research Home).

    It sits in the Home page beside `HomeView`, not inside it, so it follows the window's theme itself
    (`colors`, on every style change) for its toggle's focus line."""

    def __init__(self, title, body, note="", parent=None):
        super().__init__(parent)
        from .localization import UiLabel
        self.setObjectName("homeQuotesFold")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        head = QHBoxLayout()
        head.setSpacing(10)
        self.toggle = QToolButton()
        self.toggle.setObjectName("homeFoldToggle")
        self.toggle.setText(title)
        self.toggle.setAccessibleName(title)
        self.toggle.setCheckable(True)
        self.toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.colors = None
        self.set_theme(LIGHT)
        self.toggle.toggled.connect(self._toggled)
        head.addWidget(self.toggle, 0, Qt.AlignmentFlag.AlignVCenter)
        self.note = UiLabel(note)
        self.note.setTextFormat(Qt.TextFormat.PlainText)
        self.note.setProperty("role", "caption")
        head.addWidget(self.note, 1, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(head)
        self.body = body
        layout.addWidget(body)
        self._toggled(False)

    def _toggled(self, expanded):
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        self.body.setVisible(expanded)

    def set_theme(self, colors):
        if colors is not None and colors != self.colors:
            self.colors = colors
            self.toggle.setStyleSheet(fold_stylesheet(colors))

    def follow_window(self):
        self.set_theme(getattr(self.window(), "colors", None))

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.StyleChange:
            self.follow_window()

    def showEvent(self, event):
        super().showEvent(event)
        self.follow_window()

    def expanded(self):
        return self.toggle.isChecked()


__all__ = ["HomeView", "MarketCard", "MarketStrip", "HistoryChart", "QuotesFold", "fold_stylesheet", "MarketHistory",
           "MarketInfo",
           "HOME_MARKETS", "SECTION_GAP", "card_columns", "crop", "load_market_history", "directory_name",
           "change_text", "value_text", "text"]
