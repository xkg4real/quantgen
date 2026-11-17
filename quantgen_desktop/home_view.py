"""Research Home (owner request 2026-11-11, decision UI-D7 point 4; owner-approved draft 2026-11-17).

Owner: "연구 홈 화면을 표대신 이렇게 심플하고 세련되게 화살표로 휙휙 넘길수잇게 하자 (트레이딩뷰 화면 참고) 표에
종목 너무많이 때려박는거 자체의 구조적 문제인거같아. 세로로 넓게 넓게 공간 쓰고, ... 연구 홈에서 '관심종목' 차트를
직관적으로 볼수있게 유아이를 저기로 옮기고". Owner, 2026-11-17: "시안 7개 전부 승인, 앱에 적용 진행하세요"
(docs/product/ui_drafts_2026-11-17/draft_01_home.png).

Approved layout (`ResearchWindow.make_home` places the pieces in a `page_kit.Workspace`): the canvas holds the
'주요 시장' line with the paging arrows, the market tiles (name, last value, change pill, a sparkline of the
closes already loaded; the selected tile tinted), the selected market's name line and its key figures, and the
large chart card with the period pills at its foot. The right column holds the watchlist as compact rows
(`WatchlistRows`), the latest research runs (`RecentRuns`) and the small fan card (`MiniFan`); the quotes table
stays in a closed fold (`QuotesFold`) the toolbar opens. A standalone `HomeView` (docked=False) keeps the older
single-column arrangement for callers that build it alone.

Data. The tiles show the rows the window already loads for its quotes table
(`core.research.watchlist.load_home_markets`, read through `rows_source`). The large chart reads the selected
market's daily closes from the provider its row names (`core.ficc.data.load_series` with that explicit
source: Yahoo Finance for S&P 500, KOSPI and Bitcoin, FRED for USD/KRW, the US 10-year yield and VIX). The
watchlist card router cannot serve these: `core.market.models.Instrument` has no index, rate or FX asset.
History loads off the UI thread, one market at a time, only while automatic loading is on or after the user
presses Refresh; there is no synthetic or cross-provider fallback, and a failure keeps only an authored
reason code. A tile's sparkline is drawn only from closes already loaded for that market (nothing is fetched
for it). Provider names and observation dates stay in tooltips (owner, 2026-11-04).

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
from core.theme import DARK, LIGHT
from .charts import FanChart, nice_ticks, tick_digits
from .company_identity import CompanyMark
from .jobs import Jobs
from .markets_view import (KIS_SOURCES, WatchlistGrid, _clock, _closes, _discard, _key, _price_text,
                           _stale as _snapshot_stale, _text)
from .owner_ui_language.home import MARKETS, TEXT, UNITS
from .stock_detail_style import ElidedLabel, icon as painted_icon
from .typography import TONE_COLORS, TONES, icon_dir, is_dark, mix, scaled_font, set_tone, tone_for

CARD_HEIGHT = 110             # a market tile (draft 2026-11-17: name, value with its change, sparkline)
CARD_GAP = 10
SECTION_GAP = 48              # between the standalone view's large sections (owner: "세로로 넓게 넓게 공간 쓰고")
HISTORY_DAYS = 400            # daily observations asked for: a year for every market (Bitcoin trades daily)
HISTORY_REFRESH_SECONDS = 1800
STALE_DAYS = 7
CHART_ASPECT = 0.5            # the chart is at least about half as tall as it is wide
CHART_MIN_HEIGHT = 300
CHART_MAX_HEIGHT = 640
RANGES = (("1m", 31), ("3m", 92), ("6m", 183), ("1y", 366))
DEFAULT_RANGE = "6m"
ANIMATION_MS = 260
SPARK_DAYS = "1m"             # a tile's sparkline: the last month of the closes already loaded
_TICKERS = {"^GSPC": "SPX", "^KS11": "KOSPI", "DEXKOUS": "USDKRW", "DGS10": "US10Y", "VIXCLS": "VIX",
            "BTC-USD": "BTC"}
_MONTHS_EN = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_WEEKDAYS = (("Mon", "월"), ("Tue", "화"), ("Wed", "수"), ("Thu", "목"), ("Fri", "금"), ("Sat", "토"), ("Sun", "일"))


def card_columns(width):
    """Market tiles visible at once for a strip width: four on a wide canvas (draft 2026-11-17), fewer when
    narrow. A tile needs about 180px for its value and change pill."""
    return 4 if width >= 760 else 3 if width >= 540 else 2 if width >= 340 else 1


def text(key, language, **fields):
    """Home display text in the window language (owner_ui_language.home.TEXT)."""
    english, korean = TEXT[key]
    template = korean if language == "ko" else english
    return template.format(**fields) if fields else template


def today_text(language, today=None):
    """'2026-11-17 (화)' / '2026-11-17 (Tue)': the toolbar's date."""
    day = today or date.today()
    english, korean = _WEEKDAYS[day.weekday()]
    return f"{day.isoformat()} ({korean if language == 'ko' else english})"


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


def _numbers(widget):
    from .font_policy import number_font
    widget.setFont(number_font(widget.font()))
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
    mix_ = lambda x, y: round(x + (y - x) * share)
    return QColor(mix_(a.red(), b.red()), mix_(a.green(), b.green()), mix_(a.blue(), b.blue())).name()


def hairline(p):
    """Owner 2026-11-11 ("구획 선을 연하게 ... 한칸한칸 공간을 넓게"): a 1px line half way from the border colour
    to the background; blocks are separated by whitespace and surface colour first."""
    return blend(p.border, p.bg, 0.5)


def faint(p):
    """The drafts' faint text (#9AA29C on the light theme): muted moved toward the background."""
    return blend(p.muted, p.bg, 0.4)


def home_stylesheet(p, dark):
    """Tile, figure and control rules for the home canvas (draft 2026-11-17, qg.css); the window and page-kit
    sheets keep everything else. Light lines, 16px card corners, the selected tile in the accent tint, a visible
    accent focus line."""
    t = TONE_COLORS[dark]
    line = hairline(p)
    hover = blend(p.surface, p.surface_2, 0.6)
    chosen_line = blend(p.accent, p.accent_soft, 0.8)
    return f"""
      .QWidget {{ background: transparent; }}
      QFrame#homeMarketCard {{ background: {p.surface}; border: 1px solid {line}; border-radius: 14px; }}
      QFrame#homeMarketCard:hover {{ background: {hover}; }}
      QFrame#homeMarketCard[selected='true'], QFrame#homeMarketCard[selected='true']:hover {{ background: {p.accent_soft}; border: 1px solid {chosen_line}; }}
      QFrame#homeMarketCard:focus, QFrame#homeMarketCard[selected='true']:focus {{ border: 1px solid {p.accent}; }}
      QFrame#homeMarketCard QLabel {{ background: transparent; }}
      QFrame#homeChartPanel {{ background: {p.surface}; border: 1px solid {line}; border-radius: 16px; }}
      QFrame#homeChartPanel > QWidget {{ background: transparent; }}
      QLabel[homeRole='section'] {{ font-size: 15px; font-weight: 600; letter-spacing: -0.3px; color: {p.text}; }}
      QLabel[homeRole='note'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[homeRole='cardName'] {{ font-size: 13px; font-weight: 500; letter-spacing: -0.2px; color: {p.text}; }}
      QLabel[homeRole='ticker'] {{ font-size: 11px; font-weight: 500; color: {faint(p)}; letter-spacing: 0.2px; }}
      QLabel[homeRole='value'] {{ font-family: "QG Interface"; font-size: 18px; font-weight: 600; letter-spacing: -0.3px; color: {p.text}; }}
      QLabel[homeRole='unit'] {{ font-size: 12px; font-weight: 500; color: {p.muted}; letter-spacing: 0px; padding-bottom: 2px; }}
      QLabel[homeRole='change'] {{ font-family: "QG Interface"; font-size: 12px; font-weight: 600; letter-spacing: 0px;
                                   padding: 2px 7px; border-radius: 7px; color: {t['flat']}; background: {t['flat_tint']}; }}
      QLabel[homeRole='change'][tone='up'] {{ color: {t['up']}; background: {t['up_tint']}; }}
      QLabel[homeRole='change'][tone='down'] {{ color: {t['down']}; background: {t['down_tint']}; }}
      QLabel[homeRole='state'] {{ font-size: 12px; font-weight: 500; color: {p.muted}; }}
      QLabel[homeRole='state'][level='warn'] {{ color: {p.warning}; }}
      QLabel[homeRole='pageLabel'] {{ font-family: "QG Interface"; font-size: 12px; color: {p.muted}; letter-spacing: 0px; }}
      QLabel[homeRole='chartName'] {{ font-size: 15px; font-weight: 600; letter-spacing: -0.3px; color: {p.text}; }}
      QLabel[homeRole='chartTicker'] {{ font-size: 13px; color: {p.muted}; }}
      QLabel[homeRole='figKey'] {{ font-size: 13px; color: {p.muted}; }}
      QLabel[homeRole='figValue'], QLabel[homeRole='bigValue'] {{ font-family: "QG Interface"; font-size: 13px; font-weight: 500;
                                     letter-spacing: 0px; color: {p.text}; }}
      QLabel[homeRole='figUnit'], QLabel[homeRole='bigUnit'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[homeRole='bigChange'], QLabel[homeRole='period'] {{ font-family: "QG Interface"; font-size: 13px; font-weight: 500;
                                     letter-spacing: 0px; color: {t['flat']}; }}
      QLabel[homeRole='bigChange'][tone='up'], QLabel[homeRole='period'][tone='up'] {{ color: {t['up']}; }}
      QLabel[homeRole='bigChange'][tone='down'], QLabel[homeRole='period'][tone='down'] {{ color: {t['down']}; }}
      QLabel[homeRole='chartStatus'] {{ font-size: 12px; color: {p.muted}; }}
      QPushButton[homeQuiet='true'] {{ padding: 6px 14px; border: 1px solid {line}; border-radius: 9px; background: transparent; }}
      QPushButton[homeQuiet='true']:hover {{ background: {p.accent_soft}; border: 1px solid {p.accent_soft}; }}
      QPushButton[homeQuiet='true']:focus {{ border: 1px solid {p.accent}; }}
      QPushButton[homeArrow='true'] {{ min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; padding: 0px;
                                      border-radius: 8px; border: 1px solid transparent; background: {p.surface_2}; }}
      QPushButton[homeArrow='true']:hover {{ background: {p.accent_soft}; }}
      QPushButton[homeArrow='true']:focus {{ border: 1px solid {p.accent}; }}
      QPushButton[homeArrow='true']:disabled {{ background: transparent; border: 1px solid transparent; }}
      QPushButton[homeRange='true'] {{ padding: 6px 11px; min-height: 18px; border: 1px solid transparent; border-radius: 8px;
                                      background: transparent; color: {p.muted}; font-size: 13px; font-weight: 500; }}
      QPushButton[homeRange='true']:hover {{ background: {p.surface_2}; color: {p.text}; }}
      QPushButton[homeRange='true']:checked {{ background: {p.accent_soft}; color: {p.accent}; font-weight: 600; }}
      QPushButton[homeRange='true']:focus {{ border: 1px solid {p.accent}; }}
    """


class Spark(QWidget):
    """Recent daily closes as one thin line in a rise/fall tone; no axes, nothing inferred. Draws nothing until
    it has two closes."""

    def __init__(self, height=30, width=None):
        super().__init__()
        self.values, self.color = (), QColor("#646E68")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        if width is None:
            self.setFixedHeight(height)
            self.setMinimumWidth(40)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setFixedSize(width, height)

    def set_values(self, values, color):
        values = tuple(float(v) for v in values if _finite(v) is not None)
        color = QColor(color)
        if values != self.values or color != self.color:
            self.values, self.color = values, color
            self.update()

    def paintEvent(self, event):
        if len(self.values) < 2:
            return
        low, high = min(self.values), max(self.values)
        span = (high - low) or 1.0
        w, h, pad = self.width(), self.height(), 2.0
        step = (w - 2 * pad) / (len(self.values) - 1)
        path = QPainterPath()
        for index, value in enumerate(self.values):
            point = QPointF(pad + index * step, h - pad - (h - 2 * pad) * (value - low) / span)
            path.moveTo(point) if index == 0 else path.lineTo(point)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(self.color, 1.5)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.end()


class MarketCard(QFrame):
    """One market tile (draft 2026-11-17): name and ticker, the last value with its unit and the day's change
    pill in the Korean rise/fall tones, and a sparkline of the closes already loaded."""
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
        layout.setContentsMargins(14, 11, 14, 10)
        layout.setSpacing(6)
        head = QHBoxLayout()
        head.setSpacing(6)
        # The painted mark stays for callers; the approved tile shows the name and ticker only.
        self.mark = CompanyMark(info.symbol, info.ticker, size=30)
        self.mark.hide()
        self.name = ElidedLabel()            # text() is the whole name; it paints elided only when it must
        self.name.setProperty("homeRole", "cardName")
        self.full_name = ""
        self.ticker = _plain("ticker")
        # A row status ('조회 전', '오래된 자료') takes the ticker's corner, so it stays in sight beside a change.
        self.state = _plain("state")
        head.addWidget(self.name, 1, Qt.AlignmentFlag.AlignVCenter)
        head.addWidget(self.ticker, 0, Qt.AlignmentFlag.AlignVCenter)
        head.addWidget(self.state, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(head)
        figures = QHBoxLayout()
        figures.setSpacing(4)
        self.value = _numbers(_plain("value"))
        self.unit = _plain("unit")
        self.change = _numbers(_plain("change"))
        figures.addWidget(self.value, 0, Qt.AlignmentFlag.AlignBottom)
        figures.addWidget(self.unit, 0, Qt.AlignmentFlag.AlignBottom)
        figures.addStretch(1)
        figures.addWidget(self.change, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(figures)
        self.spark = Spark(28)
        layout.addWidget(self.spark)
        self._unit_text = ""
        for widget in (self.name, self.ticker, self.value, self.unit, self.change, self.state):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def render(self, row, ctx):
        language, info = ctx.language, self.info
        row = row or {"status": "NOT_LOADED"}
        name = info.name(language)
        self.mark.set_identity(info.symbol, name)
        self.full_name = name
        self.name.setText(name)
        self.ticker.setText(info.ticker)
        value = _finite(row.get("value"))
        self.value.setText(value_text(value, ctx))
        self._unit_text = info.unit_text(language) if value is not None else ""
        self.unit.setText(self._unit_text)
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
        self._fit()

    def set_spark(self, values, tone):
        colors = TONE_COLORS[bool(getattr(self, "_dark", False))]
        self.spark.set_values(values, colors.get(tone or "flat", colors["flat"]))

    def _fit(self):
        """Ticker and unit give way first when the tile is narrow: the name keeps its room (elided only when it
        must be, the whole name in the tooltip and accessible name) and the value never squeezes its change."""
        inner = self.contentsRect().width() - 28
        if inner <= 20:
            return
        for widget in (self.name, self.ticker, self.value, self.unit, self.change, self.state):
            widget.ensurePolished()
        name_width = QFontMetricsF(self.name.font()).horizontalAdvance(self.full_name)
        ticker_width = self.ticker.sizeHint().width()
        show_ticker = self.state.isHidden() and name_width + 6 + ticker_width <= inner
        if self.ticker.isHidden() == show_ticker:
            self.ticker.setVisible(show_ticker)
        side = self.change if not self.change.isHidden() else None
        needed = self.value.sizeHint().width() + (side.sizeHint().width() + 8 if side is not None else 0)
        # Index points carry no unit on the tile (draft 2026-11-17); the accessible name keeps it.
        show_unit = (bool(self._unit_text) and self.info.unit != "pt"
                     and needed + 4 + self.unit.sizeHint().width() <= inner)
        if self.unit.isHidden() == show_unit:
            self.unit.setVisible(show_unit)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit()

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
    and a crosshair readout under the pointer. Nothing is inferred: no smoothing, no projected values.

    At least about half as tall as it is wide (owner 2026-11-11); in the approved page it also takes the rest of
    the canvas height (draft 2026-11-17)."""

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
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(CHART_MIN_HEIGHT)

    @staticmethod
    def height_for(width):
        return max(CHART_MIN_HEIGHT, min(CHART_MAX_HEIGHT, round(width * CHART_ASPECT)))

    def sizeHint(self):
        width = max(600, self.width())
        return QSize(width, self.height_for(width))

    def minimumSizeHint(self):
        return QSize(280, self.height_for(max(280, self.width())))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        wanted = self.height_for(event.size().width())
        if self.minimumHeight() != wanted:
            self.setMinimumHeight(wanted)  # owner 2026-11-11: never flatter than about half as tall as wide

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
            painter.setFont(scaled_font(self.font(), 14, 400))
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
            painter.setPen(QPen(grid, 1, Qt.PenStyle.DashLine))
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
        top.setAlpha(40 if self.dark else 26)
        bottom.setAlpha(8 if self.dark else 6)
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
        readout = f"{self.dates[self.hover]} · {self.ctx.number(self.values[self.hover], self.decimals)}"
        painter.setFont(self._number_font(13, 500))
        metrics = QFontMetricsF(painter.font())
        box = QRectF(plot.left() + 8, plot.top() + 6, metrics.horizontalAdvance(readout) + 24, metrics.height() + 12)
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


class ChartLegend(QWidget):
    """'— 일별 종가   - - 기간 첫 종가' at the chart card's foot: the close line in the period's tone, the dashed
    first-close line in muted."""

    def __init__(self):
        super().__init__()
        self.items = ()
        self.colors, self.tone = LIGHT, "flat"
        # It gives way on a narrow canvas: the entries that do not fit whole are left out (the period pills stay).
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_items(self, close_label, base_label, tone, colors):
        items = (close_label, base_label)
        if (items, tone, colors) != (self.items, self.tone, self.colors):
            self.items, self.tone, self.colors = items, tone or "flat", colors
            self.updateGeometry()
            self.update()

    def _font(self):
        return scaled_font(self.font(), 12, 400)

    def sizeHint(self):
        metrics = QFontMetricsF(self._font())
        width = sum(20 + metrics.horizontalAdvance(label) for label in self.items) + 16 * max(0, len(self.items) - 1)
        return QSize(math.ceil(width) + 2, math.ceil(metrics.height()) + 6)

    def minimumSizeHint(self):
        return QSize(0, self.sizeHint().height())

    def shown(self):
        """The entries drawn at the current width: whole ones only, in order."""
        metrics = QFontMetricsF(self._font())
        out, x = [], 1.0
        for label in self.items:
            x += 20 + metrics.horizontalAdvance(label)
            if x > self.width():
                break
            out.append(label)
            x += 16
        return out

    def paintEvent(self, event):
        if not self.items:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self._font())
        metrics = QFontMetricsF(painter.font())
        middle = self.height() / 2
        shown = self.shown()
        used = sum(20 + metrics.horizontalAdvance(label) for label in shown) + 16 * max(0, len(shown) - 1)
        x = max(1.0, self.width() - used - 1)       # right-aligned, as the draft's legend
        tone = TONE_COLORS[is_dark(self.colors)].get(self.tone, TONE_COLORS[is_dark(self.colors)]["flat"])
        for index, label in enumerate(shown):
            if index == 0:
                painter.setPen(QPen(QColor(tone), 2))
            else:
                base = QColor(self.colors.muted)
                painter.setPen(QPen(base, 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(x, middle), QPointF(x + 14, middle))
            x += 20
            painter.setPen(QColor(self.colors.muted))
            width = metrics.horizontalAdvance(label)
            painter.drawText(QRectF(x, 0, width + 2, self.height()),
                             int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), label)
            x += width + 16
        painter.end()


class PeriodLabel(QLabel):
    """The period's change in the key-figure line: '6개월 변동' muted, '+5.66%' in the period's tone. `text()` is
    the plain reading ('6개월 변동 +5.66%'); the label draws the two parts in their colours."""

    def __init__(self):
        super().__init__()
        self.setProperty("homeRole", "period")
        self.setProperty("qg_literal", True)
        self.setTextFormat(Qt.TextFormat.RichText)
        self._plain_text, self._parts, self._key_color = "", ("", ""), LIGHT.muted

    def text(self):  # the plain reading for callers, tests and the accessible name
        return self._plain_text

    def set_parts(self, key, value, key_color):
        from html import escape
        plain = f"{key} {value}".strip() if value else ""
        if (plain, (key, value), key_color) == (self._plain_text, self._parts, self._key_color):
            return
        self._plain_text, self._parts, self._key_color = plain, (key, value), key_color
        super().setText(f'<span style="color:{key_color}; font-weight:400">{escape(key)}</span>&nbsp;'
                        f'{escape(value)}' if value else "")
        self.setAccessibleName(plain)


class HomeView(QWidget):
    """Market tiles that page left/right, the selected market's key figures and chart, and the watchlist rows.

    `docked=True` (Research Home since the approved draft of 2026-11-17): the view is the page's canvas; the host
    places `refresh_button` in its toolbar and `grid` with `add_button` in its right column. `docked=False` keeps
    them in this view's own column."""
    refresh_requested = pyqtSignal()
    stock_requested = pyqtSignal(object)
    add_requested = pyqtSignal()

    def __init__(self, *, store, card_router_factory=None, name_fn=None, rows_source=None, history_loader=None,
                 locale=None, auto_load=True, docked=False, parent=None):
        super().__init__(parent)
        self._ready = False
        self.docked = docked
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
        layout.setSpacing(12)

        # Section line: heading, its note, the page position and the two arrows.
        head = QHBoxLayout()
        head.setSpacing(8)
        self.heading = _plain("section")
        head.addWidget(self.heading, 0, Qt.AlignmentFlag.AlignVCenter)
        self.section_note = ElidedLabel()    # gives way on a narrow canvas (the whole note stays its tooltip)
        self.section_note.setProperty("homeRole", "note")
        head.addSpacing(2)
        head.addWidget(self.section_note, 1, Qt.AlignmentFlag.AlignVCenter)
        self.page_label = _numbers(_plain("pageLabel"))
        head.addWidget(self.page_label, 0, Qt.AlignmentFlag.AlignVCenter)
        head.addSpacing(4)
        self.refresh_button = QPushButton()
        self.refresh_button.setProperty("qg_literal", True)
        self.refresh_button.clicked.connect(self.refresh)
        if not docked:
            self.refresh_button.setProperty("homeQuiet", True)
            head.addWidget(self.refresh_button, 0, Qt.AlignmentFlag.AlignVCenter)
            head.addSpacing(4)
        self.previous_button, self.next_button = QPushButton(), QPushButton()
        for button, step in ((self.previous_button, -1), (self.next_button, 1)):
            button.setProperty("homeArrow", True)
            button.setProperty("qg_literal", True)
            button.setIconSize(QSize(14, 14))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, s=step: self.page(s))
            head.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
        head.setContentsMargins(0, 0, 0, 0)
        head_host = QWidget()
        head_host.setLayout(head)
        head_host.setMinimumHeight(28)
        layout.addWidget(head_host)

        # The tiles.
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

        # The selected market: its name line and key figures (the chart's OHLC-like line), then the chart card.
        lead = QVBoxLayout()
        lead.setContentsMargins(0, 4, 0, 0)
        lead.setSpacing(7)
        names = QHBoxLayout()
        names.setSpacing(8)
        self.chart_mark = CompanyMark(HOME_MARKETS[0].symbol, size=40)
        self.chart_mark.hide()               # the approved name line carries no mark
        self.chart_name = _plain("chartName")
        self.chart_ticker = ElidedLabel()
        self.chart_ticker.setProperty("homeRole", "chartTicker")
        names.addWidget(self.chart_name, 0, Qt.AlignmentFlag.AlignBaseline)
        names.addWidget(self.chart_ticker, 1, Qt.AlignmentFlag.AlignBaseline)
        lead.addLayout(names)
        from .page_kit import Flow
        self.figures = QWidget()
        self.figures_flow = Flow(self.figures, gap=18, line_gap=4)
        self.figure_keys = {}

        def figure(key, *values):
            host = QWidget()
            row = QHBoxLayout(host)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(5)
            if key:
                caption = _plain("figKey")
                self.figure_keys[key] = caption
                row.addWidget(caption, 0, Qt.AlignmentFlag.AlignBaseline)
            for value in values:
                row.addWidget(value, 0, Qt.AlignmentFlag.AlignBaseline)
            self.figures_flow.add(host)
            return host
        self.chart_value = _numbers(_plain("bigValue"))
        self.chart_unit = _plain("bigUnit")
        self.chart_change = _numbers(_plain("bigChange"))
        self.chart_period = _numbers(PeriodLabel())
        self.chart_high = _numbers(_plain("figValue"))
        self.chart_low = _numbers(_plain("figValue"))
        self.figure_hosts = {"close": figure("fig_close", self.chart_value, self.chart_unit),
                             "change": figure("fig_change", self.chart_change),
                             "period": figure("", self.chart_period),
                             "high": figure("fig_high", self.chart_high),
                             "low": figure("fig_low", self.chart_low)}
        lead.addWidget(self.figures)
        layout.addLayout(lead)

        panel = QFrame()
        panel.setObjectName("homeChartPanel")  # a light surface, not the heavier global panel (owner 2026-11-11)
        panel.setProperty("reading_help_keep_visible", True)
        self.chart_panel = panel
        inner = QVBoxLayout(panel)
        inner.setContentsMargins(14, 12, 14, 10)
        inner.setSpacing(4)
        self.chart = HistoryChart()
        inner.addWidget(self.chart, 1)
        self.chart_status = _plain("chartStatus", role="caption", wrap=True)
        self.chart_status.hide()
        inner.addWidget(self.chart_status)
        foot = QHBoxLayout()
        foot.setContentsMargins(0, 2, 0, 0)
        foot.setSpacing(4)
        self.range_buttons = {}
        self.range_group = QButtonGroup(self)
        self.range_group.setExclusive(True)
        for key, _days in RANGES:
            button = QPushButton()
            button.setCheckable(True)
            button.setProperty("homeRange", True)
            button.setProperty("qg_literal", True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setChecked(key == self.range_key)
            button.clicked.connect(lambda _checked=False, k=key: self.set_range(k))
            self.range_group.addButton(button)
            self.range_buttons[key] = button
            foot.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
        foot.addStretch(1)
        self.legend = ChartLegend()
        foot.addWidget(self.legend, 0, Qt.AlignmentFlag.AlignVCenter)
        inner.addLayout(foot)
        layout.addWidget(panel, 1)

        # The watchlist rows (moved here from Markets on 2026-11-11). Docked: the host's right column shows them.
        self.grid = WatchlistRows(store, router_factory=card_router_factory, name_fn=name_fn, locale=self.ctx,
                                  auto_load=auto_load)
        self.grid.setProperty("reading_help_keep_visible", True)
        self.grid.open_requested.connect(self.stock_requested)
        self.add_button = QPushButton()
        self.add_button.setProperty("qg_literal", True)
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.clicked.connect(self.add_requested)
        if not docked:
            self.add_button.setProperty("homeQuiet", True)
            layout.addSpacing(SECTION_GAP - layout.spacing())
            row = QHBoxLayout()
            row.addStretch(1)
            row.addWidget(self.add_button)
            layout.addLayout(row)
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
        if self.docked:
            self.refresh_button.setIcon(painted_icon("refresh", colors.text, 14))
            self.refresh_button.setIconSize(QSize(14, 14))
        for card in self.cards.values():
            card._dark = dark
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
        """The user's Refresh: the window reloads its quote rows; the selected chart reloads here; the watchlist
        rows reload too (in the approved page the toolbar's 새로고침 is the only refresh)."""
        self.refresh_requested.emit()
        self.ensure_history(manual=True)
        if self.docked:
            self.grid.refresh(manual=True)

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
        self.render_sparks()
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
        self.refresh_button.setToolTip(text("refresh_name", language))
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
        for key, caption in self.figure_keys.items():
            caption.setText(text(key, language))
        for symbol, card in self.cards.items():
            card.render(self.rows.get(symbol), self.ctx)
        self.render_sparks()
        self._sync_paging()
        self.render_chart()

    def render_sparks(self):
        """Each tile's sparkline from the closes already loaded for its market (nothing is fetched for it)."""
        for symbol, card in self.cards.items():
            _dates, values = crop(self.histories.get(symbol), SPARK_DAYS)
            row = self.rows.get(symbol) or {}
            change = _finite(row.get("change"))
            tone = tone_for(change) if change is not None else (tone_for(values[-1] - values[0]) if values else "flat")
            card.set_spark(values, tone)

    def render_chart(self):
        language, ctx = self.ctx.language, self.ctx
        info = self.infos[self.selected]
        row = self.rows.get(self.selected) or {}
        history = self.histories.get(self.selected)
        failure = self.failures.get(self.selected)
        name = info.name(language)
        self.chart_mark.set_identity(info.symbol, name)
        self.chart_name.setText(name)
        range_label = text("range_" + self.range_key, language)
        self.chart_ticker.setText(f"· {info.ticker} · {text('daily', language)} · {range_label}")
        dates, values = crop(history, self.range_key)
        latest = _finite(row.get("value"))
        if latest is None and values:
            latest = values[-1]
        self.chart_value.setText(value_text(latest, ctx))
        self.chart_unit.setText(info.unit_text(language) if latest is not None else "")
        self.chart_unit.setVisible(bool(self.chart_unit.text()) and info.unit != "pt")
        change, tone = change_text(row.get("change"), info.unit, ctx)
        self.chart_change.setText(change)
        self.chart_change.setVisible(bool(change))
        self.figure_hosts["change"].setVisible(bool(change))
        _tone(self.chart_change, tone)
        period = ""
        if len(values) >= 2:
            move = (values[-1] - values[0]) * 100 if info.unit == "%" else (
                (values[-1] / values[0] - 1) * 100 if values[0] else None)
            moved, period_tone = change_text(move, info.unit, ctx)
            period = text("period", language, range=range_label, change=moved) if moved else ""
        else:
            moved, period_tone = "", None
        key = period[: len(period) - len(moved)].strip() if period and moved and period.endswith(moved) else period
        self.chart_period.set_parts(key, moved if period else "", self.colors.muted)
        self.chart_period.setVisible(bool(period))
        self.figure_hosts["period"].setVisible(bool(period))
        _tone(self.chart_period, period_tone)
        if len(values) >= 2:
            self.chart_high.setText(ctx.number(max(values), 2))
            self.chart_low.setText(ctx.number(min(values), 2))
        for part in ("high", "low"):
            self.figure_hosts[part].setVisible(len(values) >= 2)
        self.figures_flow.place()
        self.figures.updateGeometry()
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
        line_tone = tone_for(values[-1] - values[0]) if len(values) >= 2 else "flat"
        self.legend.set_items(text("legend_close", language), text("legend_base", language), line_tone, self.colors)
        self.legend.setVisible(len(values) >= 2)


def fold_stylesheet(p):
    """The "전체 시세 표" toggle, a quiet toolbar action since the approved draft (2026-11-17): muted text on no
    background, the accent tint while the table is open, and Home's 1px `accent` focus line while it has the
    keyboard focus (Tab; a QToolButton takes no focus on click). The focused padding is 1px smaller so the
    button keeps its size; the unfocused look is unchanged. Set on the toggle itself, so the window sheet's
    rules never hide it."""
    return ("QToolButton#homeFoldToggle { font-size: 13px; font-weight: 500; border: 0px; border-radius: 9px; "
            f"padding: 8px 12px; background: transparent; color: {p.muted}; }}"
            f" QToolButton#homeFoldToggle:hover {{ background: {p.surface_2}; color: {p.text}; }}"
            f" QToolButton#homeFoldToggle:checked {{ background: {p.accent_soft}; color: {p.accent}; }}"
            f" QToolButton#homeFoldToggle:focus {{ border: 1px solid {p.accent}; border-radius: 9px; "
            "padding: 7px 11px; }")


class QuotesFold(QWidget):
    """A closed-by-default section holding the full quotes table (owner: no big table on Research Home).

    It sits in the Home page beside `HomeView`, not inside it, so it follows the window's theme itself
    (`colors`, on every style change) for its toggle's focus line. In the approved page (2026-11-17) the toggle
    is the toolbar's '전체 시세 표' action (`dock_toggle`); the table opens below the chart."""

    def __init__(self, title, body, note="", parent=None):
        super().__init__(parent)
        from .localization import UiLabel
        self.setObjectName("homeQuotesFold")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
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
        self.docked = False
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

    def dock_toggle(self):
        """Hand the toggle to a toolbar (text only, no arrow); the note shows above the table while it is open."""
        self.docked = True
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.layout().itemAt(0).layout().removeWidget(self.toggle)
        self._toggled(self.toggle.isChecked())
        return self.toggle

    def _toggled(self, expanded):
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)
        self.body.setVisible(expanded)
        if self.docked:
            self.note.setVisible(expanded)

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


# The right column (approved draft 2026-11-17) -------------------------------------------------------
def home_side_stylesheet(p, dark):
    """Rules for the Home page's right column: watchlist rows, research run rows and the small links."""
    t = TONE_COLORS[dark]
    line = hairline(p)
    soft = mix(p.surface_2, p.bg, 0.3)
    return f"""
      QWidget#homeSide, QWidget#homeSide .QWidget {{ background: transparent; }}
      QWidget#homeSide QWidget#homeRows, QWidget#homeSide QWidget#homeRuns {{ background: transparent; }}
      QFrame[homeRole='watchRow'] {{ background: transparent; border: 0; border-radius: 10px; }}
      QFrame[homeRole='watchRow']:hover {{ background: {soft}; }}
      QFrame[homeRole='watchRow']:focus {{ background: {p.accent_soft}; }}
      QLabel[homeRole='rowName'] {{ font-size: 13px; font-weight: 500; color: {p.text}; background: transparent; }}
      QLabel[homeRole='rowCode'] {{ font-size: 11px; color: {p.muted}; background: transparent; }}
      QLabel[homeRole='rowPrice'] {{ font-family: "QG Interface"; font-size: 13px; font-weight: 500; color: {p.text};
                                    letter-spacing: 0px; background: transparent; }}
      QLabel[homeRole='rowChange'] {{ font-family: "QG Interface"; font-size: 12px; font-weight: 500; color: {p.muted};
                                     letter-spacing: 0px; background: transparent; }}
      QLabel[homeRole='rowChange'][tone='up'] {{ color: {t['up']}; }}
      QLabel[homeRole='rowChange'][tone='down'] {{ color: {t['down']}; }}
      QPushButton[homeRole='rowRemove'] {{ min-width: 22px; max-width: 22px; min-height: 22px; max-height: 22px; padding: 0;
                                          border: 0; border-radius: 6px; background: transparent; color: {p.muted};
                                          font-size: 14px; }}
      QPushButton[homeRole='rowRemove']:hover {{ background: {p.accent_soft}; color: {p.text}; }}
      QPushButton[homeRole='rowRemove']:focus {{ border: 1px solid {p.accent}; }}
      QLabel[homeRole='gridStatus'], QLabel[homeRole='runEmpty'], QLabel[homeRole='gridEmpty'] {{ font-size: 12px;
          color: {p.muted}; background: transparent; }}
      QPushButton[homeRole='link'] {{ padding: 4px 6px; border: 1px solid transparent; border-radius: 7px; background: transparent;
                                     color: {p.accent}; font-size: 12px; font-weight: 500; }}
      QPushButton[homeRole='link'][quiet='true'] {{ color: {p.muted}; font-weight: 400; }}
      QPushButton[homeRole='link']:hover {{ background: {p.accent_soft}; }}
      QPushButton[homeRole='link']:focus {{ border: 1px solid {p.accent}; }}
      QFrame[homeRole='runRow'] {{ background: transparent; border: 0; border-top: 1px solid {line}; }}
      QFrame[homeRole='runRow'][first='true'] {{ border-top: 0; }}
      QLabel[homeRole='runIcon'] {{ min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px;
                                   border-radius: 9px; background: {p.surface_2}; color: {p.accent};
                                   font-size: 11px; font-weight: 600; }}
      QLabel[homeRole='runTitle'] {{ font-size: 13px; font-weight: 500; color: {p.text}; background: transparent; }}
      QLabel[homeRole='runDetail'] {{ font-size: 11px; color: {p.muted}; background: transparent; }}
      QLabel[homeRole='countKey'] {{ font-size: 12px; color: {p.muted}; background: transparent; }}
      QLabel[homeRole='countValue'] {{ font-family: "QG Interface"; font-size: 13px; font-weight: 600; color: {p.text};
                                      letter-spacing: 0px; background: transparent; }}
    """


class HomeSide(QWidget):
    """The Home page's right-column content. Its rules (`home_side_stylesheet`) follow the window theme on every
    style change, as `QuotesFold` does, so the rows and links inside need no theme calls of their own."""

    def __init__(self):
        super().__init__()
        self.setObjectName("homeSide")
        self.colors = None
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(0, 0, 0, 0)
        self.column.setSpacing(12)
        self.set_theme(LIGHT)

    def set_theme(self, colors):
        if colors is not None and colors != self.colors:
            self.colors = colors
            self.setStyleSheet(home_side_stylesheet(colors, is_dark(colors)))

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.StyleChange:
            self.set_theme(getattr(self.window(), "colors", None))


def style_link(button, *, quiet=False):
    """A button as a small fold-header link ('+ 종목 추가' in the accent, '연구 보관함 ›' quiet)."""
    button.setProperty("homeQuiet", None)
    button.setProperty("homeRole", "link")
    if quiet:
        button.setProperty("quiet", True)
    _repolish(button)
    return button


class WatchRow(QFrame):
    """One watchlist stock as a compact row (draft 2026-11-17): mark, name and code, a sparkline of its daily
    closes, the last price and the day's change. Same contract as `markets_view.WatchCard` (the grid's loading
    and polling are `WatchlistGrid`'s): Enter or a click opens it; Delete or the × shown on hover removes it."""
    opened = pyqtSignal(object)
    removed = pyqtSignal(object)

    def __init__(self, instrument, name_fn):
        super().__init__()
        self.instrument, self.name_fn = instrument, name_fn
        self.result = None
        self.failure = None
        self.failures = 0
        self.attempted_at = None
        self._ctx, self._dark = LocaleContext("ko_KR"), False
        self.setProperty("homeRole", "watchRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 6, 6, 6)
        row.setSpacing(10)
        self.mark = CompanyMark(instrument.code, size=30)
        row.addWidget(self.mark, 0, Qt.AlignmentFlag.AlignVCenter)
        who = QVBoxLayout()
        who.setSpacing(1)
        self.title = ElidedLabel()
        self.title.setProperty("homeRole", "rowName")
        self.code = ElidedLabel()
        self.code.setProperty("homeRole", "rowCode")
        who.addWidget(self.title)
        who.addWidget(self.code)
        row.addLayout(who, 1)
        self.spark = Spark(22, 52)
        row.addWidget(self.spark, 0, Qt.AlignmentFlag.AlignVCenter)
        figures = QVBoxLayout()
        figures.setSpacing(1)
        self.price = _numbers(_plain("rowPrice"))
        self.price.setProperty("homeRole", "rowPrice")
        self.change = _numbers(_plain("rowChange"))
        for label in (self.price, self.change):
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            figures.addWidget(label)
        figures_host = QWidget()
        figures_host.setLayout(figures)
        figures.setContentsMargins(0, 0, 0, 0)
        figures_host.setMinimumWidth(72)
        row.addWidget(figures_host, 0, Qt.AlignmentFlag.AlignVCenter)
        self.remove_button = QPushButton("×")
        self.remove_button.setProperty("homeRole", "rowRemove")
        self.remove_button.setProperty("qg_literal", True)
        self.remove_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)   # Delete on the focused row removes it
        self.remove_button.clicked.connect(lambda: self.removed.emit(self.instrument))
        self.remove_button.hide()
        row.addWidget(self.remove_button, 0, Qt.AlignmentFlag.AlignVCenter)
        for widget in (self.title, self.code, self.price, self.change, figures_host):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def name(self):
        return self.name_fn(self.instrument, self._ctx.language)

    def render(self, ctx, dark=False):
        self._ctx, self._dark = ctx, dark
        name = self.name()
        self.mark.set_identity(self.instrument.code, name)
        self.mark.set_theme(DARK if dark else LIGHT)
        self.title.setText(name)
        place = self.instrument.exchange or ("KRX" if self.instrument.asset == "domestic_stock" else "")
        code = f"{self.instrument.code} · {place}" if place else self.instrument.code
        self.remove_button.setToolTip(_text(ctx, "관심종목에서 빼기", "Remove from watchlist"))
        self.remove_button.setAccessibleName(_text(ctx, f"{name} 관심종목에서 빼기", f"Remove {name} from watchlist"))
        snapshot = self.result.snapshot if self.result else None
        colors = TONE_COLORS[bool(dark)]
        if snapshot is None:
            self.price.setText("—")
            state = (_text(ctx, "조회 전", "Not loaded") if self.result is None
                     else _text(ctx, "불러오지 못함", "Not loaded") + f" ({self.result.error})")
            self.change.setText(_text(ctx, "조회 전", "Not loaded") if self.result is None
                                else _text(ctx, "불러오지 못함", "Failed"))
            _tone(self.change, None)
            self.code.setText(code)
            self.spark.set_values((), colors["flat"])
            self.setToolTip(state)
            self.setAccessibleName(f"{name} {state}")
            return
        dates, closes = _closes(snapshot)
        quote = getattr(snapshot, "quote", None)
        last = quote.price if quote is not None and quote.price is not None else (closes[-1] if closes else None)
        pct = quote.change_pct if quote is not None and quote.change_pct is not None else (
            (closes[-1] / closes[-2] - 1) * 100 if len(closes) >= 2 and closes[-2] else None)
        self.price.setText(_price_text(last, self.instrument))
        change, tone = (f"{pct:+.2f}%", tone_for(pct)) if pct is not None and _finite(pct) is not None else ("", None)
        self.change.setText(change)
        _tone(self.change, tone)
        self.spark.set_values(closes[-22:], colors.get(tone or "flat", colors["flat"]))
        # Not shown as text: provider and observation date (owner request). They stay in the tooltip.
        source = str(getattr(snapshot, "source", "") or "")
        states = []
        if source and source not in KIS_SOURCES:
            states.append(_text(ctx, "지연", "Delayed"))
        if _snapshot_stale(snapshot):
            states.append(_text(ctx, "오래된 자료", "Stale data"))
        if self.failure is not None:
            states.append(_text(ctx, "갱신 실패", "Refresh failed"))
        self.code.setText(" · ".join([code, *states]))
        self.setToolTip(_text(ctx, "출처 ", "Source ") + source + (" · " + dates[-1] if dates else "")
                        + _text(ctx, " · 확인 ", " · checked ") + _clock(getattr(snapshot, "fetched_at", ""))
                        + (" · " + " · ".join(states) if states else ""))
        self.setAccessibleName(f"{name} {self.price.text()} {change}".strip())

    def render_chart(self):  # WatchCard's name; the sparkline is drawn in render
        self.render(self._ctx, self._dark)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.remove_button.show()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if not self.hasFocus():
            self.remove_button.hide()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.remove_button.show()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if not self.underMouse():
            self.remove_button.hide()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.opened.emit(self.instrument)
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.opened.emit(self.instrument)
            return
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.removed.emit(self.instrument)
            return
        super().keyPressEvent(event)


class WatchlistRows(WatchlistGrid):
    """The watchlist as compact rows (`WatchRow`) in Research Home's right column. Loading, polling, retries and
    the shared store are `WatchlistGrid`'s; the fold header above carries the title, count and '+ 종목 추가'."""

    def __init__(self, store, **kwargs):
        super().__init__(store, **kwargs)
        self.setObjectName("homeRows")
        self.layout().setSpacing(4)
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.heading.hide()
        self.refresh_button.hide()          # the page's 새로고침 refreshes the rows too (HomeView.refresh)
        self.status.setProperty("homeRole", "gridStatus")
        self.status.setProperty("role", None)
        self.empty.setProperty("homeRole", "gridEmpty")
        self.empty.setProperty("role", None)
        self.empty.setWordWrap(True)
        self.jobs.busy_changed.connect(lambda _busy: self._sync_status())
        self._sync_status()
        self.render()

    def sync(self):
        """As `WatchlistGrid.sync`, with rows."""
        wanted = {_key(i): i for i in self.store.items()}
        for key in list(self.cards):
            if key not in wanted:
                card = self.cards.pop(key)
                self.grid.removeWidget(card)
                _discard(card)
        for key, instrument in wanted.items():
            if key not in self.cards:
                card = WatchRow(instrument, self.name_fn)
                card.opened.connect(self.open_requested)
                card.removed.connect(self.store.remove)
                self.cards[key] = card
        order = [self.cards[key] for key in wanted]
        self.cards = {key: self.cards[key] for key in wanted}
        self._columns = 0
        self._arrange(order)
        self.render()
        if self.isVisible() and self.auto_load and any(card.attempted_at is None for card in order):
            QTimer.singleShot(0, self.refresh)

    def _arrange(self, order=None):
        order = order if order is not None else list(self.cards.values())
        self._columns = 1
        for card in order:
            self.grid.removeWidget(card)
        for index, card in enumerate(order):
            self.grid.addWidget(card, index, 0)
        for column in range(4):
            self.grid.setColumnStretch(column, 1 if column == 0 else 0)

    def resizeEvent(self, event):
        QWidget.resizeEvent(self, event)    # one column at every width

    def refresh(self, *, manual=False):
        started = super().refresh(manual=manual)
        self._sync_status()
        return started

    def _failed(self, code):
        super()._failed(code)
        self._sync_status()

    def _sync_status(self):
        status = getattr(self, "status", None)
        if status is not None:
            status.setVisible(bool(status.text()))

    def render(self):
        super().render()
        ctx = self.ctx
        self.empty.setText(_text(ctx, "아직 관심종목이 없어요. 시장에서 종목을 열고 ☆를 누르면 여기에 추가돼요.",
                                 "No stocks yet. Open a stock on Markets and press ☆ to add it here."))
        self._sync_status()


class MiniFan(FanChart):
    """The latest Monte Carlo result as a small fan (draft 2026-11-17): the P5–P95 and P25–P75 bands and the median
    path from the start price, no axes. A `FanChart` (same `result`, `colors`, `set_result`) sized for the right
    column; before a run it draws one faint dashed line."""
    HEIGHT = 46

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, self.HEIGHT)
        self.setMaximumWidth(16777215)
        self.setFixedHeight(self.HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def hasHeightForWidth(self):
        return False

    def heightForWidth(self, width):
        return self.HEIGHT

    def sizeHint(self):
        return QSize(240, self.HEIGHT)

    def minimumSizeHint(self):
        return QSize(120, self.HEIGHT)

    def _reserve_text_space(self):  # no axes, legends or footer to make room for
        pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        p = self.colors
        r = self.result
        w, h = self.width(), self.height()
        if r is None:
            painter.setPen(QPen(QColor(hairline(p)), 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(2, h / 2), QPointF(w - 2, h / 2))
            painter.end()
            return
        lo, hi = min(r.fan[5]), max(r.fan[95])
        span = (hi - lo) or max(abs(hi) * 0.01, 0.01)
        lo, hi = lo - span * 0.04, hi + span * 0.04
        n = max(1, r.horizon_days)

        def point(i, value):
            return QPointF(2 + (w - 4) * i / n, h - 1 - (h - 2) * (float(value) - lo) / (hi - lo))
        for low, high, alpha in ((5, 95, 46), (25, 75, 84)):
            area = QPainterPath(point(0, r.fan[low][0]))
            for i, v in enumerate(r.fan[low]):
                area.lineTo(point(i, v))
            for i in range(n, -1, -1):
                area.lineTo(point(i, r.fan[high][i]))
            area.closeSubpath()
            color = QColor(p.accent)
            color.setAlpha(alpha)
            painter.fillPath(area, color)
        painter.setPen(QPen(QColor(p.accent), 1.6))
        line = QPainterPath(point(0, r.fan[50][0]))
        for i, v in enumerate(r.fan[50]):
            line.lineTo(point(i, v))
        painter.drawPath(line)
        painter.end()


class RecentRuns(QWidget):
    """This session's latest research runs, newest first (at most `limit`): a short icon, the run's name and
    settings, and its execution status. Read from `runs_source` (the window's session) whenever the window's
    language pass runs (after every refresh_views), so nothing calls it; `changed(count, latest completed run)`
    lets the page update the fold's count and the fan card's note."""
    changed = pyqtSignal(int, object)

    STATUS = {"COMPLETED": (("Done", "완료"), "ok"), "RUNNING": (("Running", "진행 중"), "warn"),
              "FAILED": (("Failed", "실패"), "err")}

    def __init__(self, runs_source, *, limit=3):
        super().__init__()
        self.setObjectName("homeRuns")
        self.runs_source, self.limit = runs_source, limit
        self._signature = None
        self.rows = []
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(0, 0, 0, 0)
        self.column.setSpacing(0)
        self.empty = _plain("runEmpty", wrap=True)
        self.column.addWidget(self.empty)

    def language(self):
        return "ko" if getattr(self.window(), "ui_language", "ko") == "ko" else "en"

    def _reserve_text_space(self):  # LanguageController.apply calls this after every refresh_views
        self.refresh()

    def refresh(self):
        try:
            runs = list(self.runs_source() or ())
        except Exception:
            runs = []
        language = self.language()
        shown = runs[:self.limit]
        signature = (language, len(runs), tuple((r.get("run_id"), r.get("execution_status"), r.get("verdict"))
                                                for r in shown))
        if signature == self._signature:
            return False
        self._signature = signature
        for row in self.rows:
            self.column.removeWidget(row)
            _discard(row)
        self.rows = []
        self.empty.setText("아직 실행한 연구가 없어요. 아래 버튼으로 설계/검증을 열어 시작하세요." if language == "ko"
                           else "No research yet. Open Build & Test below to start one.")
        self.empty.setVisible(not shown)
        for index, run in enumerate(shown):
            row = self._row(run, language, first=index == 0)
            self.column.addWidget(row)
            self.rows.append(row)
        latest = next((r for r in runs if r.get("execution_status") == "COMPLETED"), None)
        self.changed.emit(len(runs), latest)
        return True

    @staticmethod
    def _when(stamp, language):
        try:
            at = datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).astimezone()
        except (TypeError, ValueError):
            return ""
        if at.date() == datetime.now().astimezone().date():
            return ("오늘 " if language == "ko" else "Today ") + at.strftime("%H:%M")
        return at.strftime("%m-%d")

    def _row(self, run, language, *, first):
        from .page_kit import Pill
        from .risk_display import MC_MODEL_LABELS, ko
        params = run.get("parameters") or {}
        symbol = str(params.get("symbol") or "—")
        kind = str(run.get("kind") or "")
        model = MC_MODEL_LABELS.get(params.get("model"), str(params.get("model") or ""))
        paths = params.get("n_paths")
        when = self._when(run.get("created_at"), language)
        if kind == "monte_carlo":
            icon, title = "MC", f"{symbol} {'몬테카를로' if language == 'ko' else 'Monte Carlo'}"
            path_text = ((f"경로 {paths:,}개" if language == "ko" else f"{paths:,} paths")
                         if isinstance(paths, int) else "")
            detail = " · ".join(part for part in ((ko(model) if language == "ko" else model), path_text, when) if part)
        else:
            icon, title = (kind[:2] or "R").upper(), symbol
            detail = when
        host = QFrame()
        host.setProperty("homeRole", "runRow")
        host.setProperty("first", first)
        line = QHBoxLayout(host)
        line.setContentsMargins(6, 8, 4, 8)
        line.setSpacing(10)
        badge = _plain("runIcon", icon)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        line.addWidget(badge, 0, Qt.AlignmentFlag.AlignVCenter)
        who = QVBoxLayout()
        who.setSpacing(1)
        name = ElidedLabel()
        name.setProperty("homeRole", "runTitle")
        name.setText(title)
        info = ElidedLabel()
        info.setProperty("homeRole", "runDetail")
        info.setText(detail)
        _numbers(info)
        who.addWidget(name)
        who.addWidget(info)
        line.addLayout(who, 1)
        status = str(run.get("execution_status") or "")
        pair, tone = self.STATUS.get(status, ((status, status), ""))
        pill = Pill(pair, tone)
        pill.set_language(language)
        line.addWidget(pill, 0, Qt.AlignmentFlag.AlignVCenter)
        host.setAccessibleName(f"{title} {detail} {pill.text()}")
        return host


class TodayText(QLabel):
    """The toolbar's date ('2026-11-17 (화)'), rendered for the window language each time it is shown."""

    def __init__(self):
        super().__init__()
        self.setProperty("kit", "sub")
        self.setProperty("qg_literal", True)
        self.language = "ko"
        _numbers(self)
        self.render()

    def set_language(self, language):
        self.language = "ko" if str(language or "ko").startswith("ko") else "en"
        self.render()

    def render(self):
        value = today_text(self.language)
        if self.text() != value:
            self.setText(value)

    def showEvent(self, event):
        super().showEvent(event)
        self.render()


__all__ = ["HomeView", "MarketCard", "MarketStrip", "HistoryChart", "QuotesFold", "fold_stylesheet", "MarketHistory",
           "MarketInfo", "WatchlistRows", "WatchRow", "RecentRuns", "MiniFan", "HomeSide", "TodayText", "ChartLegend",
           "PeriodLabel", "Spark", "style_link", "today_text",
           "HOME_MARKETS", "SECTION_GAP", "card_columns", "crop", "load_market_history", "directory_name",
           "change_text", "value_text", "text"]
