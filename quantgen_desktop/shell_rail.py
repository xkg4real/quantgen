"""Left rail chrome: the hide/show toggle, the 시장 menu and keyboard moves (owner 2026-11-11, UI-D7).

Owner points 2 and 3: clicking Markets shows sub-items to pick what to look at, and the rail can be hidden to
give the page the full width. Owner ruling UI-D10 (2026-11-11) made the sub-items the markets.

Owner ruling UI-D11 (2026-11-12, with a TradingView-style menu image), verbatim: "좋은데 시장 하위 유아이를 저렇게
두지 말고 이런식으로 큰 범주로 묶고 저기 뭐 주식 하부 유야이다 그러면 거기 마우스 휠 올려놓으면 더 하부로 국내, 미국,
글로벌 뭐 이런 식으로 볼수있고 거기서 국내에 마우스 올려놓으면 다시 거래대금 거래량 급상승 급하락 이렇게 누를수있게.
누르면 지금 ui랑 똑같이 저 화면으로 바로 넘어갈수잇게 그니까 바꾸라는게 아니야. 지금 시장 안의 ui는 괜찮다. 새꺄 그리고
코인이 뭐야 ETF라해야지". So the sub-items are the image's big categories (`MARKET_CATEGORIES`: 지수 · 주식 · 크립토 ·
선물 · 외환 · 국채 · 회사채 · ETF · 월드 이코노미), each opening cascading flyouts (`rail_menu.RailFlyouts`) whose
leaves open what the app already has (`market_menu`): a market page ranked by a category, a Research Home market
card, or an analysis tool. 글로벌 is left out: no data path for it exists, and no dead item is shown.

UI-D11 review: the nine rows show on every page, so the rail never reflows under the pointer (they appeared only on
Markets, and choosing a page below them moved it about 320 px), and a row is highlighted only for the Markets page
shown. A row with one page of its own opens it on a click (국내 / 미국 under 주식 and ETF, 크립토, 선물, 회사채).

The window (`app.ResearchWindow`) owns the state; this module holds the pieces that do not need the window: the
menu tree, the painted icons and the rail's arrow-key handling.
"""
from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QEvent, QObject, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QPushButton, QScrollArea

SETTINGS_KEY = "ui/sidebar_collapsed"

# The 시장 menu's big categories, in the order of the owner's image (R-D11-1): (key, English, Korean).
MARKET_CATEGORIES = (("indices", "Indices", "지수"), ("stocks", "Stocks", "주식"), ("crypto", "Crypto", "크립토"),
                     ("futures", "Futures", "선물"), ("fx", "Forex", "외환"), ("govt", "Government bonds", "국채"),
                     ("corp", "Corporate bonds", "회사채"), ("etf", "ETFs", "ETF"),
                     ("economy", "World economy", "월드 이코노미"))
# The market pages under 주식 / 크립토 / ETF: (category, ((page, English, Korean), ...)). 크립토 has one page, so its
# flyout lists the ranking categories directly.
MARKET_SUBS = {"stocks": (("kr", "Korea", "국내"), ("us", "US", "미국")),
               "crypto": (("crypto", "Crypto", "크립토"),),
               "etf": (("etf_kr", "Korea", "국내"), ("etf_us", "US", "미국"))}
PAGE_CATEGORY = {page: category for category, pages in MARKET_SUBS.items() for page, _en, _ko in pages}
# 지수: the index cards of Research Home (`core.research.markets.SPECS`), opened there with the card selected.
INDEX_CARDS = ("^KS11", "^GSPC", "VIXCLS")
# The other categories open the analysis tools that cover them, or a Home card: (category, ((leaf, English,
# Korean), ...)); a tool leaf is ('tool', pane attribute, its sub-tool or ''), a card leaf ('home', symbol).
TOOL_LEAVES = {
    "futures": ((("tool", "derivatives", "board"), "KOSPI 200 futures & options", "코스피200 선물·옵션"),),
    "fx": ((("home", "DEXKOUS"), "US dollar / Korean won", "달러/원 환율"),
           (("tool", "fx", "forward"), "Spot, forward & carry", "현물·선물환·캐리"),
           (("tool", "fx", "option"), "Option & smile", "옵션 및 스마일"),
           (("tool", "fx", "carry"), "Carry basket", "캐리 바스켓")),
    "govt": ((("home", "DGS10"), "US 10-year yield", "미국 10년 국채 금리"),
             (("tool", "rates", "curve"), "Yield curve", "수익률 곡선"),
             (("tool", "rates", "sim"), "Rate simulation", "금리 시뮬레이션")),
    "corp": ((("tool", "bonds", ""), "Bond price & spread", "채권 가격·스프레드"),),
    "economy": ((("tool", "macro", "sheet"), "Macro sheet", "매크로 지표"),
                (("tool", "macro", "daily"), "Daily commentary", "일일 시장 해설"),
                (("tool", "macro", "weekly"), "Weekly rates & FX", "주간 금리·외환")),
}
# Where a tool leaf opens and what it shows, for its tooltip (the menu names no page on the row itself).
_TOOL_TIPS = {"derivatives": ("Analysis tools › Derivatives", "분석 도구 › 파생상품"),
              "fx": ("Analysis tools › FX", "분석 도구 › 외환"), "rates": ("Analysis tools › Rates", "분석 도구 › 금리"),
              "bonds": ("Analysis tools › Bonds: price, yield and z-spread over the Treasury curve",
                        "분석 도구 › 채권: 가격·수익률과 국채 곡선 대비 스프레드(z-spread)"),
              "macro": ("Analysis tools › Macro sheet", "분석 도구 › 매크로 지표")}
_HOME_TIP = ("Research Home › Major markets: the daily chart", "연구 홈 › 주요 시장: 일별 차트")


@dataclass(frozen=True)
class MenuNode:
    """One row of the 시장 menu. A row with `children` opens a flyout when pointed at; `leaf` is what a click opens:
    ('market', page, category), ('home', symbol) or ('tool', pane, sub-tool). A row with both (국내 under 주식, 크립토,
    선물) opens its page on a click (category '': the page's own last ranking) and its flyout when pointed at. `mark`
    names what the row stands for, so the row of what is shown can be marked; `tip` says where a leaf opens.
    The flyouts carry no notes about rankings a page leaves out (UI-D11 review: they read as disabled items); the
    page's footnote says why."""
    key: str
    text: str
    children: tuple = ()
    leaf: tuple = ()
    mark: tuple = ()
    tip: str = ""


def _pick(language, english, korean):
    return korean if language == "ko" else english


def page_categories(page):
    """The ranking categories a market page can rank by (`screen.category_note` leaves the others out)."""
    from core.market import rankings as R
    from core.market.screen import category_note
    return tuple(key for key in R.CATEGORY_KEYS if not category_note(page, key))


def _ranking_nodes(page, language):
    from core.market import rankings as R
    return tuple(MenuNode(key, R.text(R.CATEGORIES, key, language), leaf=("market", page, key),
                          mark=("market", page, key)) for key in page_categories(page))


def market_menu(language):
    """The 시장 menu in `language`: one `MenuNode` per `MARKET_CATEGORIES` row, each with its flyout's rows.

    주식 › 국내 / 미국 › the rankings that market has; 크립토 › its rankings; ETF › 국내 / 미국 › rankings (no market
    cap); 지수 › Research Home's index cards; 선물 · 외환 · 국채 · 회사채 · 월드 이코노미 › the analysis tools (and Home
    cards) that cover them. A row with one page of its own also opens it on a click (`MenuNode.leaf`). Pure apart
    from reading the text tables; nothing is fetched."""
    from .owner_ui_language.home import MARKETS as HOME_NAMES
    language = "ko" if language == "ko" else "en"
    rows = []
    for key, english, korean in MARKET_CATEGORIES:
        text = _pick(language, english, korean)
        leaf = ()
        if key == "indices":
            children = tuple(MenuNode(symbol, _pick(language, *HOME_NAMES[symbol]), leaf=("home", symbol),
                                      mark=("home", symbol), tip=_pick(language, *_HOME_TIP))
                             for symbol in INDEX_CARDS)
        elif key == "crypto":
            children, leaf = _ranking_nodes("crypto", language), ("market", "crypto", "")
        elif key in MARKET_SUBS:
            children = tuple(MenuNode(page, _pick(language, sub_en, sub_ko), _ranking_nodes(page, language),
                                      leaf=("market", page, ""), mark=("page", page))
                             for page, sub_en, sub_ko in MARKET_SUBS[key])
        else:
            children = tuple(
                MenuNode(":".join(leaf), _pick(language, leaf_en, leaf_ko), leaf=leaf, mark=leaf,
                         tip=_pick(language, *(_HOME_TIP if leaf[0] == "home" else _TOOL_TIPS[leaf[1]])))
                for leaf, leaf_en, leaf_ko in TOOL_LEAVES[key])
            if len(children) == 1:  # 선물, 회사채: one tool, so a click opens it
                leaf = children[0].leaf
        rows.append(MenuNode(key, text, children, leaf=leaf, mark=("category", key)))
    return tuple(rows)


def market_sections():
    """(key, English title) for each 시장 row (`MARKET_CATEGORIES`)."""
    return tuple((key, english) for key, english, _korean in MARKET_CATEGORIES)


def market_section_text(key, language):
    """A 시장 row's text in the window language ('주식', 'Stocks')."""
    for each, english, korean in MARKET_CATEGORIES:
        if each == key:
            return _pick("ko" if language == "ko" else "en", english, korean)
    raise KeyError(key)


def stored_flag(store, key=SETTINGS_KEY):
    """A remembered yes/no from a QSettings-like store; anything unreadable means no."""
    reader = getattr(store, "value", None)
    if not callable(reader):
        return False
    try:
        value = reader(key, False)
    except (TypeError, ValueError):
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes")


def _pixmaps(size, paint):
    icon = QIcon()
    for scale in (1, 2):
        pixmap = QPixmap(size * scale, size * scale)
        pixmap.setDevicePixelRatio(scale)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        paint(painter)
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def toggle_icon(color, *, rail_open, size=18):
    """A panel outline with the rail column on the left and a chevron toward where the rail goes.

    Open rail: the column is shaded and the chevron points left (hide). Hidden rail: an empty column
    and a chevron pointing right (show). Painted, so no glyph or asset file is needed.
    """
    stroke = QColor(color)

    def paint(painter):
        pen = QPen(stroke, 1.4)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        frame = QRectF(1.7, 2.7, size - 3.4, size - 5.4)
        divider = frame.left() + 5.2
        if rail_open:
            shade = QColor(stroke)
            shade.setAlphaF(0.28)
            column = QPainterPath()
            column.addRoundedRect(QRectF(frame.left(), frame.top(), divider - frame.left(), frame.height()), 2.6, 2.6)
            painter.fillPath(column, shade)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(frame, 2.6, 2.6)
        painter.drawLine(QPointF(divider, frame.top()), QPointF(divider, frame.bottom()))
        middle_x = (divider + frame.right()) / 2
        middle_y = frame.center().y()
        reach = 1.9 if rail_open else -1.9
        chevron = QPainterPath(QPointF(middle_x + reach, middle_y - 3.2))
        chevron.lineTo(QPointF(middle_x - reach, middle_y))
        chevron.lineTo(QPointF(middle_x + reach, middle_y + 3.2))
        painter.drawPath(chevron)

    return _pixmaps(size, paint)


def stop_icon(color, size=16):
    """A filled rounded square: the paper engine's emergency stop in the hidden rail."""
    fill = QColor(color)

    def paint(painter):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        inset = size * 0.24
        painter.drawRoundedRect(QRectF(inset, inset, size - 2 * inset, size - 2 * inset), 2.2, 2.2)

    return _pixmaps(size, paint)


def markets_icon(color, size=18):
    """A small line chart over a baseline: the 시장 menu's button in the hidden rail."""
    stroke = QColor(color)

    def paint(painter):
        pen = QPen(stroke, 1.5)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        unit = size / 18
        painter.drawLine(QPointF(2.5 * unit, 15 * unit), QPointF(15.5 * unit, 15 * unit))
        line = QPainterPath(QPointF(3 * unit, 11.5 * unit))
        for x, y in ((6.5, 7.5), (9.5, 10), (14.5, 4)):
            line.lineTo(QPointF(x * unit, y * unit))
        painter.drawPath(line)

    return _pixmaps(size, paint)


def icon_button(accessible_name, tooltip, size):
    """A square, text-free rail button (styled by QPushButton[railIcon='true'] in typography)."""
    button = QPushButton()
    button.setProperty("railIcon", True)
    button.setFixedSize(size, size)
    button.setAccessibleName(accessible_name)
    button.setToolTip(tooltip)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button


KEYBOARD_FOCUS = (Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason,
                  Qt.FocusReason.ShortcutFocusReason)


def set_focus_ring(button, shown):
    """The `focusRing` property the rail styles use instead of :focus (Qt has no :focus-visible)."""
    shown = bool(shown)
    if bool(button.property("focusRing")) == shown:
        return
    button.setProperty("focusRing", shown)
    style = button.style()
    style.unpolish(button)
    style.polish(button)
    button.update()


class RailKeys(QObject):
    """Up/Down (Home/End) move between the rail's visible buttons; Return/Enter press the focused one.

    A button with the `flyout` property (the 시장 rows, UI-D11) also opens its flyout with Right (`expand`) and
    closes it with Left or Esc (`collapse`); moving to another rail button closes it too.

    The focus ring follows keyboard focus only: Tab, Backtab and these arrow moves show it; a mouse
    click or the window gaining focus does not, so no ring lingers on a clicked menu item.
    """

    def __init__(self, buttons, parent=None, *, expand=None, collapse=None):
        super().__init__(parent)
        self.buttons = buttons  # callable returning the rail's buttons in visual order
        self.expand, self.collapse = expand, collapse

    def watch(self, button):
        button.installEventFilter(self)

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QEvent.Type.FocusIn:
            set_focus_ring(watched, event.reason() in KEYBOARD_FOCUS)
            scroll = watched.parentWidget()
            while scroll is not None and not isinstance(scroll, QScrollArea):
                scroll = scroll.parentWidget()
            if scroll is not None:  # a short window scrolls the rail; keep the focused item in view
                scroll.ensureWidgetVisible(watched, 0, 6)
            return False
        if kind == QEvent.Type.FocusOut:
            set_focus_ring(watched, False)
            return False
        if kind != QEvent.Type.KeyPress:
            return False
        if event.modifiers() not in (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.KeypadModifier):
            return False
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            watched.click()
            return True
        if watched.property("flyout"):
            if key == Qt.Key.Key_Right and self.expand is not None:
                self.expand(watched)
                return True
            if key in (Qt.Key.Key_Left, Qt.Key.Key_Escape) and self.collapse is not None:
                return bool(self.collapse(watched))
        if key not in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Home, Qt.Key.Key_End):
            return False
        if self.collapse is not None:
            self.collapse(None)  # another rail button: an open flyout closes
        shown = [b for b in self.buttons() if b.isVisible() and b.isEnabled()]
        if watched not in shown:
            return False
        index = shown.index(watched)
        target = {Qt.Key.Key_Up: index - 1, Qt.Key.Key_Down: index + 1,
                  Qt.Key.Key_Home: 0, Qt.Key.Key_End: len(shown) - 1}[key]
        shown[max(0, min(len(shown) - 1, target))].setFocus(Qt.FocusReason.TabFocusReason)
        return True


__all__ = ["SETTINGS_KEY", "KEYBOARD_FOCUS", "MARKET_CATEGORIES", "MARKET_SUBS", "PAGE_CATEGORY", "INDEX_CARDS",
           "TOOL_LEAVES", "MenuNode", "market_menu", "page_categories",
           "market_sections", "market_section_text", "stored_flag", "toggle_icon", "stop_icon", "markets_icon",
           "icon_button", "set_focus_ring", "RailKeys"]
