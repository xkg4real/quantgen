"""The 시장 main screen and each 시장 category's main screen (owner request 2026-11-17).

Owner, verbatim: "현재 시장 ui가 클릭해도 화면이 넘어가지지 않습니다. 물론 하부 ui가 있지만, 그래도 시장의 메인화면이
별도로 존재하긴 해야합니다 ... 시장 메인화면엔 시장의 하부 메뉴들 바로가기가 세련된 화면으로 구현되어야 하고" and "주식도
마찬가지입니다. 현재 국내주식, 미국주식 바로가기만 가능하고, 정작 '주식' 바로가기는 눌리지 않습니다". The rail keeps only the
big categories (지수 · 주식 · 크립토 · 선물 · 외환 · 국채 · 회사채 · ETF · 월드 이코노미, `shell_rail.MARKET_CATEGORIES`):
clicking 시장 opens this hub's root (a slim index strip and one card per category), clicking a category with several
destinations opens its own main screen (one card per destination; a stock or ETF market's card also lists its
rankings, each a shortcut into that market's list), and a category with one destination (크립토, 선물, 회사채) opens
it directly. Every route is the rail's (`shell_rail.market_menu`), so the hub and the rail never disagree.

The look follows the stock detail chart (`stock_detail_style.sheet`): warm background, white cards with a light line
and 16 px corners, small muted captions, pill chips, QG Interface type with the N3 tracking.
"""
from __future__ import annotations

import threading

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout,
                             QWidget)

from core.i18n import LocaleContext
from core.theme import LIGHT
from .stock_detail_style import label, line_color, sheet

# (English, Korean) screen copy.
TEXT = {
    "root_title": ("Markets", "시장"),
    "root_caption": ("Pick a market to open its lists, charts and tools.",
                     "보고 싶은 시장을 고르면 목록·차트·도구로 바로 이동해요."),
    "indices_title": ("Major indices", "주요 지수"),
    "categories_title": ("Markets", "카테고리"),
    "back": ("Markets", "시장"),
    "destinations_title": ("Open", "바로가기"),
    "rankings": ("Rankings", "순위로 보기"),
    "direct": ("Opens directly", "바로 열려요"),
    "count": ("{count} destinations", "바로가기 {count}개"),
    "preview_value": ("Top trading value", "거래대금 상위"),
    "preview_gainers": ("Top gainers", "급상승"),
    "preview_losers": ("Top losers", "급하락"),
    "preview_empty": ("Not loaded yet.", "아직 불러오지 않았어요."),
    "preview_load": ("Load", "불러오기"),
    "preview_loading": ("Loading…", "불러오는 중…"),
    "preview_failed": ("Could not load. Try again.", "불러오지 못했어요. 다시 시도해 보세요."),
    "preview_none": ("None", "해당 없음"),
    "preview_note": ("Delayed quotes · major listed names", "지연 시세 · 주요 종목 기준"),
}
PREVIEW_CATEGORIES = ("value", "gainers", "losers")
PREVIEW_ROWS = 3

# Each category's one-line description on the root card and the caption of its own screen: (English, Korean).
CATEGORY_COPY = {
    "indices": ("KOSPI, KOSDAQ, S&P 500, NASDAQ and the VIX, day by day.",
                "코스피·코스닥·S&P 500·나스닥과 VIX의 일별 흐름을 봐요."),
    "stocks": ("Korean and US stocks ranked by value, volume, moves and Q-SCORE.",
               "국내·미국 주요 종목을 거래대금·등락·Q-SCORE 순위로 골라 봐요."),
    "crypto": ("Major crypto assets ranked by trading value and daily moves.",
               "주요 가상자산을 거래대금·등락 순위로 봐요."),
    "futures": ("KOSPI 200 futures and options: prices and sensitivities.",
                "코스피200 선물·옵션의 가격과 민감도를 계산해요."),
    "fx": ("The dollar against the won, forwards, options and carry.",
           "달러/원 환율과 선물환·옵션·캐리를 살펴봐요."),
    "govt": ("The US 10-year yield, the curve and rate scenarios.",
             "미국 10년 금리와 수익률 곡선, 금리 시나리오를 봐요."),
    "corp": ("Bond prices, duration and credit spreads.",
             "채권 가격·듀레이션·스프레드를 계산해요."),
    "etf": ("Korean and US ETFs ranked by value, volume and moves.",
            "국내·미국 상장 ETF를 거래대금·등락 순위로 봐요."),
    "economy": ("Macro indicators, the daily commentary and the weekly rates & FX.",
                "매크로 지표와 일일 해설, 주간 금리·외환을 봐요."),
}

# A destination's description on its category screen, by the rail leaf's key: (English, Korean).
DESTINATION_COPY = {
    "kr": ("Major KOSPI and KOSDAQ stocks as ranked lists; a stock opens its chart.",
           "코스피·코스닥 주요 종목을 순위로 보고, 종목을 누르면 차트가 열려요."),
    "us": ("Major US stocks as ranked lists; a stock opens its chart.",
           "미국 주요 종목을 순위로 보고, 종목을 누르면 차트가 열려요."),
    "etf_kr": ("ETFs listed in Korea as ranked lists.", "국내 상장 주요 ETF를 순위로 봐요."),
    "etf_us": ("ETFs listed in the US as ranked lists.", "미국 상장 주요 ETF를 순위로 봐요."),
    "^KS11": ("The whole KOSPI market in one line.", "유가증권시장 전체의 흐름이에요."),
    "^KQ11": ("The whole KOSDAQ market in one line.", "코스닥 시장 전체의 흐름이에요."),
    "^GSPC": ("500 large US companies.", "미국 대형주 500개의 흐름이에요."),
    "^IXIC": ("Every NASDAQ-listed stock.", "나스닥 상장 종목 전체의 흐름이에요."),
    "VIXCLS": ("30-day volatility priced into S&P 500 options.", "S&P 500 옵션에 담긴 30일 변동성 기대치예요."),
    "series:fx:DEXKOUS": ("How many won one dollar buys, day by day.", "1달러가 몇 원인지, 일별 흐름이에요."),
    "workspace:fx:fx:forward": ("Spot, the rate gap, the forward and the carry.",
                                "현물과 금리 차이로 선물환과 캐리를 계산해요."),
    "workspace:fx:fx:option": ("Currency option prices and the volatility smile.",
                               "환율 옵션 가격과 변동성 스마일을 봐요."),
    "workspace:fx:fx:carry": ("A basket of currencies by their rate gaps.", "여러 통화의 금리 차이를 바구니로 봐요."),
    "series:govt:DGS10": ("The US 10-year Treasury yield, day by day.", "미국 10년 만기 국채 금리의 일별 흐름이에요."),
    "workspace:govt:rates:curve": ("Yields across maturities, joined as a curve.", "만기별 금리를 이은 수익률 곡선이에요."),
    "workspace:govt:rates:sim": ("Paths for rates and what they do to a position.",
                                 "금리 경로 시나리오로 손익을 따져봐요."),
    "workspace:economy:macro:sheet": ("Prices, jobs, growth and other macro indicators.",
                                      "물가·고용·성장 같은 주요 매크로 지표예요."),
    "workspace:economy:macro:daily": ("What moved the markets today.", "하루 시장 움직임을 정리한 해설이에요."),
    "workspace:economy:macro:weekly": ("Rates and FX over the week.", "한 주의 금리·외환 흐름을 정리해요."),
}

# The painted mark of each category (and of a destination, by its leaf).
GLYPHS = {"indices": "line", "stocks": "candles", "crypto": "coin", "futures": "contract", "fx": "exchange",
          "govt": "columns", "corp": "bond", "etf": "basket", "economy": "globe"}


def _pick(language, pair):
    english, korean = pair
    return korean if language == "ko" else english


def say(language, key, **fields):
    value = _pick(language, TEXT[key])
    return value.format(**fields) if fields else value


def hub_sheet(p, dark):
    """The hub's rules on top of the detail view's (`stock_detail_style.sheet`)."""
    from .typography import mix
    line = line_color(p)
    hover = mix(p.accent, line, 0.35)
    return sheet(p, dark) + f"""
      QWidget#marketHub {{ background: transparent; }}
      QLabel[sd='hubTitle'] {{ font-size: 26px; font-weight: 600; letter-spacing: -0.9px; color: {p.text}; }}
      QLabel[sd='hubCaption'] {{ font-size: 13px; color: {p.muted}; letter-spacing: -0.14px; }}
      QLabel[sd='hubSection'] {{ font-size: 15px; font-weight: 600; color: {p.text}; letter-spacing: -0.36px; }}
      QLabel[sd='hubSectionNote'] {{ font-size: 12px; color: {p.muted}; }}
      QFrame[sd='hubCard'] {{ background: {p.surface}; border: 1px solid {line}; border-radius: 16px; }}
      QFrame[sd='hubCard'][hover='true'] {{ border: 1px solid {hover}; background: {mix(p.surface, p.accent_soft, 0.35)}; }}
      QFrame[sd='hubCard'][focusRing='true'] {{ border: 2px solid {p.accent}; }}
      QLabel[sd='hubCardTitle'] {{ font-size: 17px; font-weight: 600; color: {p.text}; letter-spacing: -0.45px; }}
      QLabel[sd='hubCardText'] {{ font-size: 13px; color: {p.muted}; letter-spacing: -0.14px; }}
      QLabel[sd='hubMeta'] {{ font-size: 12px; font-weight: 500; color: {p.muted}; }}
      QPushButton[sd='hubChip'] {{ padding: 4px 11px; min-height: 18px; border: 0; border-radius: 12px;
                                   background: {p.surface_2}; color: {p.text}; font-size: 12px; font-weight: 500; }}
      QPushButton[sd='hubChip']:hover {{ background: {p.accent_soft}; color: {p.accent}; }}
      QPushButton[sd='hubChip']:focus {{ border: 2px solid {p.accent}; }}
      QWidget#hubChips, QWidget#hubPreview {{ background: transparent; }}
      QFrame[sd='hubPreviewColumn'] {{ background: {mix(p.surface_2, p.surface, 0.35)}; border: 0; border-radius: 12px; }}
      QLabel[sd='hubPreviewHead'] {{ font-size: 12px; font-weight: 600; color: {p.muted}; }}
      QPushButton[sd='hubPreviewRow'] {{ border: 0; border-radius: 8px; padding: 4px 6px; text-align: left;
                                         background: transparent; color: {p.text}; font-size: 13px; }}
      QPushButton[sd='hubPreviewRow']:hover {{ background: {p.accent_soft}; }}
      QPushButton[sd='hubPreviewRow']:focus {{ border: 2px solid {p.accent}; }}
      QLabel[sd='hubPreviewEmpty'] {{ font-size: 12px; color: {p.muted}; }}
    """


class Glyph(QWidget):
    """A category's mark: a line drawing on a soft rounded square (the interface face has no such symbols)."""

    def __init__(self, kind, size=44):
        super().__init__()
        self.kind, self.box = kind, size
        self.colors = (LIGHT.accent, LIGHT.accent_soft)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_colors(self, ink, soft):
        self.colors = (ink, soft)
        self.update()

    def sizeHint(self):
        return QSize(self.box, self.box)

    def paintEvent(self, _event):
        ink, soft = self.colors
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        s = float(self.box)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(soft))
        p.drawRoundedRect(QRectF(0, 0, s, s), s * .28, s * .28)
        pen = QPen(QColor(ink), max(1.6, s / 26))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        u = s / 44.0
        P = lambda x, y: QPointF(x * u, y * u)
        kind = self.kind
        if kind == "line":
            path = QPainterPath(P(11, 29))
            for x, y in ((17, 22), (22, 25), (28, 16), (33, 19)):
                path.lineTo(P(x, y))
            p.drawPath(path)
            p.drawLine(P(11, 33), P(33, 33))
        elif kind == "candles":
            for x, top, body_top, body_bottom, bottom in ((14, 12, 16, 26, 30), (22, 15, 19, 29, 33), (30, 10, 14, 22, 27)):
                p.drawLine(P(x, top), P(x, body_top))
                p.drawLine(P(x, body_bottom), P(x, bottom))
                p.drawRoundedRect(QRectF(P(x - 2.6, body_top), P(x + 2.6, body_bottom)), 1, 1)
        elif kind == "coin":
            p.drawEllipse(P(22, 22), 11 * u, 11 * u)
            p.drawLine(P(20, 15), P(20, 29))
            p.drawLine(P(24, 15), P(24, 29))
            p.drawLine(P(18, 18), P(26, 18))
            p.drawLine(P(18, 26), P(26, 26))
        elif kind == "contract":
            p.drawRoundedRect(QRectF(P(12, 11), P(32, 33)), 3 * u, 3 * u)
            p.drawLine(P(16, 17), P(28, 17))
            p.drawLine(P(16, 22), P(28, 22))
            path = QPainterPath(P(16, 28))
            path.lineTo(P(28, 28))
            path.moveTo(P(25, 25.5))
            path.lineTo(P(28, 28))
            path.lineTo(P(25, 30.5))
            p.drawPath(path)
        elif kind == "exchange":
            path = QPainterPath(P(12, 17))
            path.lineTo(P(31, 17))
            path.moveTo(P(27, 13))
            path.lineTo(P(31, 17))
            path.lineTo(P(27, 21))
            path.moveTo(P(32, 27))
            path.lineTo(P(13, 27))
            path.moveTo(P(17, 23))
            path.lineTo(P(13, 27))
            path.lineTo(P(17, 31))
            p.drawPath(path)
        elif kind == "columns":
            path = QPainterPath(P(11, 18))
            path.lineTo(P(22, 11))
            path.lineTo(P(33, 18))
            path.closeSubpath()
            p.drawPath(path)
            for x in (15, 22, 29):
                p.drawLine(P(x, 21), P(x, 29))
            p.drawLine(P(11, 32), P(33, 32))
        elif kind == "bond":
            p.drawRoundedRect(QRectF(P(11, 13), P(33, 31)), 3 * u, 3 * u)
            p.drawEllipse(P(22, 22), 4 * u, 4 * u)
            p.drawLine(P(14, 17), P(17, 17))
            p.drawLine(P(27, 27), P(30, 27))
        elif kind == "basket":
            p.drawEllipse(P(22, 22), 11 * u, 11 * u)
            p.drawLine(P(22, 22), P(22, 11))
            p.drawLine(P(22, 22), P(31.5, 27.5))
            p.drawLine(P(22, 22), P(13, 28))
        elif kind == "globe":
            p.drawEllipse(P(22, 22), 11 * u, 11 * u)
            p.drawEllipse(P(22, 22), 5 * u, 11 * u)
            p.drawLine(P(11.5, 22), P(32.5, 22))
            p.drawLine(P(13.5, 16), P(30.5, 16))
            p.drawLine(P(13.5, 28), P(30.5, 28))
        elif kind == "arrow":
            p.drawLine(P(14, 22), P(30, 22))
            p.drawLine(P(25, 17), P(30, 22))
            p.drawLine(P(25, 27), P(30, 22))
        p.end()


class Chevron(QWidget):
    """The card's corner arrow."""

    def __init__(self):
        super().__init__()
        self.color = LIGHT.muted
        self.setFixedSize(18, 18)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(QColor(self.color), 1.7)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(7, 4.5), QPointF(11.5, 9))
        p.drawLine(QPointF(11.5, 9), QPointF(7, 13.5))
        p.end()


class HubCard(QFrame):
    """One clickable card: a mark, a title, a short description and optional shortcut chips. Enter or Space (with
    focus) and a click anywhere outside a chip activate it."""
    activated = pyqtSignal()

    def __init__(self, glyph, *, wide=False):
        super().__init__()
        self.setProperty("sd", "hubCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 18, 18)
        layout.setSpacing(10)
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(12)
        self.glyph = Glyph(glyph, 44)
        top.addWidget(self.glyph, 0, Qt.AlignmentFlag.AlignTop)
        names = QVBoxLayout()
        names.setContentsMargins(0, 1, 0, 0)
        names.setSpacing(3)
        self.title = label("hubCardTitle")
        names.addWidget(self.title)
        self.meta = label("hubMeta")
        names.addWidget(self.meta)
        top.addLayout(names, 1)
        self.chevron = Chevron()
        top.addWidget(self.chevron, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)
        self.text = label("hubCardText", wrap=True)
        layout.addWidget(self.text)
        self.chips = QWidget()
        self.chips.setObjectName("hubChips")
        self.chip_row = FlowRow(self.chips, gap=6)
        layout.addWidget(self.chips)
        self.preview = None      # a market card's PreviewBoard (`MarketHub._build_category`)
        layout.addStretch(1)
        self.wide = wide
        self.setMinimumHeight(156 if not wide else 168)

    def set_content(self, title, text, meta="", chips=()):
        self.title.setText(title)
        self.text.setText(text)
        self.meta.setText(meta)
        self.meta.setVisible(bool(meta))
        self.setAccessibleName(title)
        self.setAccessibleDescription(text)
        self.chip_row.clear()
        for chip_text, callback in chips:
            chip = QPushButton(chip_text.replace("&", "&&"))
            chip.setProperty("sd", "hubChip")
            chip.setProperty("qg_literal", True)
            chip.setCursor(Qt.CursorShape.PointingHandCursor)
            chip.setFocusPolicy(Qt.FocusPolicy.TabFocus)
            chip.clicked.connect(lambda checked=False, c=callback: c())
            self.chip_row.add(chip)
        self.chips.setVisible(bool(chips))

    def set_colors(self, p):
        self.glyph.set_colors(p.accent, p.accent_soft)
        self.chevron.color = p.muted
        self.chevron.update()

    def _set_hover(self, on):
        if self.property("hover") != ("true" if on else "false"):
            self.setProperty("hover", "true" if on else "false")
            self.style().unpolish(self)
            self.style().polish(self)

    def enterEvent(self, event):
        super().enterEvent(event)
        self._set_hover(True)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._set_hover(False)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.activated.emit()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.activated.emit()
            return
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if event.reason() in (Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason):
            self.setProperty("focusRing", "true")
            self.style().unpolish(self)
            self.style().polish(self)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.property("focusRing") == "true":
            self.setProperty("focusRing", "false")
            self.style().unpolish(self)
            self.style().polish(self)


class FlowRow:
    """Chips laid out left to right, wrapping onto new lines inside `host` (a plain QWidget)."""

    def __init__(self, host, gap=6):
        self.host, self.gap, self.items = host, gap, []
        host.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        original = host.resizeEvent

        def resized(event, original=original):
            original(event)
            self.place()
        host.resizeEvent = resized
        host.hasHeightForWidth = lambda: True
        host.heightForWidth = self.height_for
        host.sizeHint = lambda: QSize(max(120, host.width()), self.height_for(max(120, host.width())))
        host.minimumSizeHint = lambda: QSize(80, self.height_for(max(120, host.width())))

    def clear(self):
        for item in self.items:
            item.hide()
            item.setParent(None)
            item.deleteLater()
        self.items = []
        self.host.updateGeometry()

    def add(self, widget):
        widget.setParent(self.host)
        widget.show()
        self.items.append(widget)
        self.place()
        self.host.updateGeometry()

    def _rows(self, width):
        x = y = line = 0
        spots = []
        for item in self.items:
            size = item.sizeHint()
            if x and x + size.width() > width:
                x, y, line = 0, y + line + self.gap, 0
            spots.append((item, x, y, size))
            x += size.width() + self.gap
            line = max(line, size.height())
        return spots, (y + line if self.items else 0)

    def height_for(self, width):
        return self._rows(width)[1]

    def place(self):
        spots, height = self._rows(self.host.width())
        for item, x, y, size in spots:
            item.setGeometry(x, y, size.width(), size.height())
        if self.host.height() != height:
            self.host.setFixedHeight(height)


class PreviewBoard(QWidget):
    """Three short lists of a market (거래대금 상위 · 급상승 · 급하락, top 3 each) from the market page's own ranked
    quotes (`core.market.rankings.rank`); a name opens its stock screen."""
    open_stock = pyqtSignal(object)
    load = pyqtSignal()

    def __init__(self, page):
        super().__init__()
        self.setObjectName("hubPreview")
        self.page = page
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 0)
        outer.setSpacing(6)
        self.columns_host = QWidget()
        self.columns_host.setObjectName("hubPreview")
        self.columns = QHBoxLayout(self.columns_host)
        self.columns.setContentsMargins(0, 0, 0, 0)
        self.columns.setSpacing(8)
        outer.addWidget(self.columns_host)
        self.empty_row = QHBoxLayout()
        self.empty = label("hubPreviewEmpty")
        self.empty_row.addWidget(self.empty)
        self.load_button = QPushButton()
        self.load_button.setProperty("sd", "text")
        self.load_button.setProperty("qg_literal", True)
        self.load_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_button.clicked.connect(self.load.emit)
        self.empty_row.addWidget(self.load_button)
        self.empty_row.addStretch(1)
        outer.addLayout(self.empty_row)
        self.note = label("hubPreviewEmpty")
        outer.addWidget(self.note)
        self.blocks = []

    def show_batch(self, batch, *, language, tones, state=""):
        from core.market import rankings as R
        for block in self.blocks:
            self.columns.removeWidget(block)
            block.setParent(None)
            block.deleteLater()
        self.blocks = []
        has = batch is not None and bool(batch.records)
        self.columns_host.setVisible(has)
        self.empty.setVisible(not has)
        self.load_button.setVisible(not has and state != "loading")
        self.note.setVisible(has)
        self.note.setText(say(language, "preview_note"))
        self.empty.setText(say(language, {"loading": "preview_loading", "failed": "preview_failed"}.get(state, "preview_empty")))
        self.load_button.setText(say(language, "preview_load"))
        if not has:
            return
        for category in PREVIEW_CATEGORIES:
            block = QFrame()
            block.setProperty("sd", "hubPreviewColumn")
            column = QVBoxLayout(block)
            column.setContentsMargins(10, 9, 10, 9)
            column.setSpacing(2)
            head = label("hubPreviewHead")
            head.setText(say(language, f"preview_{category}"))
            column.addWidget(head)
            rows = R.rank(batch.records, category, market=self.page, limit=PREVIEW_ROWS)
            for row in rows:
                record = row.record
                change, tone = R.change_text(record.change_pct)
                button = PreviewRow(record.member.label(language), change, tones.get(tone, tones["flat"]))
                instrument = record.member.instrument
                button.setEnabled(instrument is not None)
                button.clicked.connect(lambda checked=False, i=instrument: self.open_stock.emit(i))
                column.addWidget(button)
            if not rows:
                none = label("hubPreviewEmpty")
                none.setText(say(language, "preview_none"))
                column.addWidget(none)
            column.addStretch(1)
            self.columns.addWidget(block, 1)
            self.blocks.append(block)


class PreviewRow(QPushButton):
    """A name and its change, the change in the market's up/down colour."""

    def __init__(self, name, change, color):
        super().__init__()
        self.setProperty("sd", "hubPreviewRow")
        self.setProperty("qg_literal", True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setAccessibleName(f"{name} {change}")
        row = QHBoxLayout(self)
        row.setContentsMargins(6, 3, 6, 3)
        row.setSpacing(6)
        from .stock_detail_style import ElidedLabel, numbers
        self.name = ElidedLabel("hubPreviewName")
        self.name.setText(name)
        self.name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(self.name, 1)
        self.change = numbers(QLabel(change))
        self.change.setProperty("qg_literal", True)
        self.change.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600; background: transparent;")
        self.change.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        row.addWidget(self.change)
        self.setMinimumHeight(28)

    def sizeHint(self):
        return QSize(150, 28)


class _StripHolder(QWidget):
    """Holds the index strip without letting its width widen the page: the hub drops sparklines and trailing tiles
    until the strip fits (`MarketHub._fit_strip`); anything still wider is clipped, never scrolled sideways."""

    def __init__(self, strip):
        super().__init__()
        self.strip = strip
        strip.setParent(self)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

    def sizeHint(self):
        return QSize(0, self.strip.sizeHint().height() if self.strip.isVisibleTo(self) else 0)

    def minimumSizeHint(self):
        return self.sizeHint()

    def place(self):
        hint = self.strip.sizeHint()
        self.strip.setGeometry(0, 0, min(max(hint.width(), self.strip.minimumSizeHint().width()), max(0, self.width())),
                               hint.height())
        if self.height() != hint.height():
            self.updateGeometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.place()


class _HubJobs:
    """The window waits for both of the hub's jobs before closing (`ResearchWindow.closeEvent`)."""

    def __init__(self, *jobs):
        self.all = jobs

    @property
    def busy(self):
        return any(job.busy for job in self.all)


class MarketHub(QWidget):
    """The 시장 main screen (category=None) or one category's main screen."""
    open_leaf = pyqtSignal(object)      # a shell_rail leaf: ('market', page, ranking) / ('series', ...) / ...
    open_category = pyqtSignal(str)     # a category with several destinations
    open_stock = pyqtSignal(object)     # an Instrument from a preview list
    back = pyqtSignal()

    def __init__(self, *, ctx=None, summary_loader=None, auto_load=True):
        super().__init__()
        from .market_summary import MarketSummary
        self.setObjectName("marketHub")
        self.ctx = ctx or LocaleContext("ko_KR")
        self.colors, self.dark = LIGHT, False
        self.category = None
        self.cards = []
        self._columns = 0
        from .jobs import Jobs
        self.auto_load = auto_load
        self.board = None                      # the market page's RankingBoard (its loader and its cached batches)
        self.preview_jobs = Jobs(self)
        self.preview_jobs.succeeded.connect(self._preview_loaded)
        self.preview_jobs.failed.connect(self._preview_failed)
        self.preview_jobs.busy_changed.connect(lambda busy: None if busy else self._next_preview())
        self._pending_groups = ()
        self._preview_state = {}               # group -> 'loading' | 'failed'
        self._preview_cancel, self._stopped = None, False
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        self.back_button = QPushButton()
        self.back_button.setProperty("sd", "back")
        self.back_button.setProperty("qg_literal", True)
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.clicked.connect(self.back.emit)
        column.addWidget(self.back_button, 0, Qt.AlignmentFlag.AlignLeft)
        column.addSpacing(4)
        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(14)
        self.head_glyph = Glyph("line", 48)
        head.addWidget(self.head_glyph, 0, Qt.AlignmentFlag.AlignVCenter)
        names = QVBoxLayout()
        names.setContentsMargins(0, 0, 0, 0)
        names.setSpacing(4)
        self.title = label("hubTitle")
        names.addWidget(self.title)
        self.caption = label("hubCaption", wrap=True)
        names.addWidget(self.caption)
        head.addLayout(names, 1)
        column.addLayout(head)
        column.addSpacing(24)
        # The index strip (root only): Research Home's keyless daily closes, as on each market page.
        self.strip_head = QHBoxLayout()
        self.strip_title = label("hubSection")
        self.strip_head.addWidget(self.strip_title)
        self.strip_head.addStretch(1)
        column.addLayout(self.strip_head)
        column.addSpacing(10)
        self.summary = MarketSummary(loader=summary_loader, locale=self.ctx, auto_load=auto_load)
        self.summary.set_page("hub")
        # Five tiles never widen the page: sparklines drop first (compact), then the last tiles (`_fit_strip`).
        self.summary.changed.connect(self._strip_shown)
        self.summary.loaded.connect(lambda *_: self._strip_shown())
        self.strip_holder = _StripHolder(self.summary)
        column.addWidget(self.strip_holder)
        self.strip_gap = QWidget()
        self.strip_gap.setFixedHeight(28)
        column.addWidget(self.strip_gap)
        section = QHBoxLayout()
        section.setContentsMargins(0, 0, 0, 0)
        self.section_title = label("hubSection")
        section.addWidget(self.section_title)
        section.addSpacing(8)
        self.section_note = label("hubSectionNote")
        section.addWidget(self.section_note, 0, Qt.AlignmentFlag.AlignBottom)
        section.addStretch(1)
        column.addLayout(section)
        column.addSpacing(12)
        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        column.addWidget(self.grid_host)
        column.addStretch(1)
        self.set_theme(LIGHT)
        self.show_root()

    # Routes -------------------------------------------------------------------------------------
    @property
    def jobs(self):
        return _HubJobs(self.summary.jobs, self.preview_jobs)

    def attach_board(self, board):
        """The market page's ranking board: previews reuse its loader and share its per-group cache, so a list
        loaded here opens at once on the market page (and the other way round)."""
        self.board = board
        signal = getattr(board, "loaded", None)
        if signal is not None:
            signal.connect(lambda *_: self._refresh_previews())

    def _batch(self, group):
        return self.board.batches.get(group) if self.board is not None else None

    def load_previews(self, groups, *, manual=False):
        """Fetch the first group of `groups` with no cached batch (one job at a time; the next follows)."""
        from core.market import rankings as R
        board = self.board
        if board is None or getattr(board, "loader", None) is None or self._stopped or self.preview_jobs.busy:
            return False
        if not manual and not self.auto_load:
            return False
        missing = [g for g in groups if self._batch(g) is None and (manual or self._preview_state.get(g) != "failed")]
        if not missing:
            return False
        group, loader, cancel = missing[0], board.loader, threading.Event()
        members = R.members_of(group)
        self._preview_cancel = cancel
        self._preview_state[group] = "loading"
        self._pending_groups, self._pending_manual = tuple(missing[1:]), manual
        self._refresh_previews()
        return self.preview_jobs.start(lambda: (group, loader(group, members, cancel.is_set, None)))

    @pyqtSlot(object)
    def _preview_loaded(self, value):
        from core.market import rankings as R
        group, batch = value
        if self._stopped:
            return
        self._preview_state.pop(group, None)
        if isinstance(batch, R.Batch) and self.board is not None and self.board.batches.get(group) is None:
            self.board.batches[group] = batch
        self._refresh_previews()

    def _next_preview(self):
        rest, self._pending_groups = self._pending_groups, ()
        if rest and not self._stopped:
            self.load_previews(rest, manual=getattr(self, "_pending_manual", False))

    @pyqtSlot(str)
    def _preview_failed(self, _code):
        for group, state in list(self._preview_state.items()):
            if state == "loading":
                self._preview_state[group] = "failed"
        self._refresh_previews()

    def _refresh_previews(self):
        from .typography import TONE_COLORS
        tones = TONE_COLORS[self.dark]
        tones = {"up": tones["up"], "down": tones["down"], "flat": self.colors.muted}
        for card in self.cards:
            if card.preview is not None:
                from core.market import rankings as R
                group = R.group_of(card.preview.page)
                batch = self._batch(group)
                card.preview.show_batch(batch, language=self.ctx.language, tones=tones,
                                        state=self._preview_state.get(group, ""))

    def nodes(self):
        from .shell_rail import market_menu
        return market_menu(self.ctx.language)

    def node(self, key):
        return next(node for node in self.nodes() if node.key == key)

    def show_root(self):
        self.category = None
        self.render()   # the strip loads itself when shown with automatic loading on (MarketSummary.showEvent)

    def show_category(self, key):
        node = self.node(key)
        if not node.children:
            raise ValueError(f"{key!r} has one destination; open it directly")
        self.category = key
        self.render()

    def current_category(self):
        return self.category

    def showEvent(self, event):
        super().showEvent(event)
        if self.category is not None:
            self.load_previews(self._preview_groups())

    def _activate_category(self, key):
        node = self.node(key)
        if node.children:
            self.open_category.emit(key)
        elif node.leaf:
            self.open_leaf.emit(node.leaf)

    # Drawing ------------------------------------------------------------------------------------
    def render(self):
        lang = self.ctx.language
        root = self.category is None
        self.back_button.setVisible(not root)
        self.back_button.setText("‹  " + say(lang, "back"))
        self.summary.setVisible(root)
        self.strip_holder.setVisible(root)
        self.strip_title.setText(say(lang, "indices_title"))
        self._strip_shown()
        if root:
            self.title.setText(say(lang, "root_title"))
            self.caption.setText(say(lang, "root_caption"))
            self.head_glyph.hide()
            self.section_title.setText(say(lang, "categories_title"))
            self.section_note.setText("")
            self._build_root()
        else:
            node = self.node(self.category)
            self.title.setText(node.text)
            self.caption.setText(_pick(lang, CATEGORY_COPY[self.category]))
            self.head_glyph.kind = GLYPHS[self.category]
            self.head_glyph.show()
            self.head_glyph.update()
            self.section_title.setText(say(lang, "destinations_title"))
            self.section_note.setText(say(lang, "count", count=len(node.children)))
            self._build_category(node)
        self._layout_cards(force=True)

    def _strip_shown(self):
        shown = self.category is None and self.summary.isVisibleTo(self) and any(
            not tile.isHidden() for tile in self.summary.tiles.values())
        self.strip_title.setVisible(shown)
        self.strip_gap.setVisible(shown)
        self.strip_holder.setVisible(self.category is None and not self.summary.isHidden())
        self._fit_strip()

    def _fit_strip(self):
        """Sparklines drop first, then the last tiles, until the strip fits the page's width."""
        if getattr(self, "_fitting", False):
            return       # set_compact / render re-announce `changed`
        self._fitting = True
        summary = self.summary
        summary.blockSignals(True)
        try:
            width = self.width() or 1100

            def needed():
                tiles = [summary.tiles[symbol] for symbol in summary.shown_symbols()]
                for tile in tiles:
                    if tile.layout() is not None:
                        tile.layout().invalidate()
                        tile.layout().activate()
                spacing = summary.layout().spacing()
                state = summary.state.sizeHint().width() if summary.has_data() else 0
                return sum(tile.sizeHint().width() for tile in tiles) + spacing * (len(tiles) + 1) + 4 + state

            summary.max_tiles = None
            summary.set_compact(False)
            summary.render()
            if needed() > width:
                summary.set_compact(True)
                summary.render()
            count = len(summary.shown_symbols())
            while count > 2 and needed() > width:
                count -= 1
                summary.max_tiles = count
                summary.render()
        finally:
            summary.blockSignals(False)
            self._fitting = False
        self.strip_holder.updateGeometry()
        self.strip_holder.place()

    def _clear_cards(self):
        for card in self.cards:
            self.grid.removeWidget(card)
            card.hide()
            card.setParent(None)
            card.deleteLater()
        self.cards = []

    def _build_root(self):
        lang = self.ctx.language
        self._clear_cards()
        for node in self.nodes():
            card = HubCard(GLYPHS[node.key])
            chips = tuple((child.text, (lambda leaf=child.leaf: self.open_leaf.emit(leaf))) for child in node.children)
            meta = say(lang, "count", count=len(node.children)) if node.children else say(lang, "direct")
            card.set_content(node.text, _pick(lang, CATEGORY_COPY[node.key]), meta, chips)
            card.activated.connect(lambda key=node.key: self._activate_category(key))
            card.category = node.key
            self.cards.append(card)
        self._paint_cards()

    def _build_category(self, node):
        from .markets_view import RANKING_CATEGORIES
        from .shell_rail import page_categories
        lang = self.ctx.language
        self._clear_cards()
        for child in node.children:
            leaf = child.leaf
            key = self._leaf_key(leaf)
            glyph = ("candles" if node.key == "stocks" else "basket" if node.key == "etf" else
                     "line" if leaf[0] == "series" else GLYPHS[node.key])
            chips = ()
            meta = ""
            if leaf[0] == "market":
                page = leaf[1]
                allowed = set(page_categories(page))
                chips = tuple((_pick(lang, (english, korean)), (lambda p=page, c=rank: self.open_leaf.emit(("market", p, c))))
                              for rank, english, korean in RANKING_CATEGORIES if rank in allowed)
                meta = say(lang, "rankings")
            card = HubCard(glyph, wide=True)
            card.set_content(child.text, _pick(lang, DESTINATION_COPY.get(key, ("", ""))), meta, chips)
            card.activated.connect(lambda leaf=leaf: self.open_leaf.emit(leaf))
            card.leaf = leaf
            if leaf[0] == "market" and leaf[1] in ("kr", "us", "etf_kr", "etf_us"):
                card.preview = PreviewBoard(leaf[1])
                card.preview.open_stock.connect(self.open_stock.emit)
                card.preview.load.connect(lambda: self.load_previews(self._preview_groups(), manual=True))
                card.layout().insertWidget(card.layout().count() - 1, card.preview)
            self.cards.append(card)
        self._paint_cards()
        self._refresh_previews()
        if self.isVisible():
            self.load_previews(self._preview_groups())

    def _preview_groups(self):
        groups = []
        for card in self.cards:
            if card.preview is not None:
                from core.market import rankings as R
                group = R.group_of(card.preview.page)
                if group not in groups:
                    groups.append(group)
        return tuple(groups)

    @staticmethod
    def _leaf_key(leaf):
        if leaf[0] == "market":
            return leaf[1]
        if leaf[0] == "series" and leaf[1] == "indices":
            return leaf[2]
        return ":".join(leaf)

    def _paint_cards(self):
        for card in self.cards:
            card.set_colors(self.colors)

    def _columns_for(self, width):
        if self.category is not None and len(self.cards) <= 2:
            return 2 if width >= 720 else 1
        return 3 if width >= 940 else 2 if width >= 560 else 1

    def _layout_cards(self, force=False):
        columns = self._columns_for(self.width() or 1100)
        if not force and columns == self._columns:
            return
        self._columns = columns
        for card in self.cards:
            self.grid.removeWidget(card)
        for index, card in enumerate(self.cards):
            self.grid.addWidget(card, index // columns, index % columns)
            card.show()
        for c in range(4):
            self.grid.setColumnStretch(c, 1 if c < columns else 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_cards()
        self._fit_strip()

    # Language, theme, lifetime ---------------------------------------------------------------------
    def set_locale(self, ctx):
        self.ctx = ctx
        self.summary.set_locale(ctx)
        self.render()

    def set_theme(self, colors):
        from .typography import is_dark
        self.colors, self.dark = colors, is_dark(colors)
        self.setStyleSheet(hub_sheet(colors, self.dark))
        self.summary.set_theme(self.dark)
        self.head_glyph.set_colors(colors.accent, colors.accent_soft)
        self._paint_cards()
        self._refresh_previews()

    def stop(self):
        self._stopped = True
        if self._preview_cancel is not None:
            self._preview_cancel.set()
        stop = getattr(self.summary, "stop", None)
        if callable(stop):
            stop()


__all__ = ["MarketHub", "HubCard", "Glyph", "CATEGORY_COPY", "DESTINATION_COPY", "TEXT"]
