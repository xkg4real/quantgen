"""Local company identifiers shared by Home and Markets.

These original letter marks are navigation aids, not downloaded company logos.
The symbol remains the source of identity; a mark never changes market data.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget

from core.theme import LIGHT
from .typography import scaled_font


@dataclass(frozen=True)
class CompanyIdentity:
    letters: str
    background: str
    foreground: str


_GROUPS = {
    "samsung": CompanyIdentity("S", "#202528", "#FFFFFF"),
    "sk": CompanyIdentity("SK", "#FCEEEB", "#B42822"),
    "lg": CompanyIdentity("LG", "#A91840", "#FFFFFF"),
    "hyundai": CompanyIdentity("H", "#E8F1FA", "#176394"),
    "kb": CompanyIdentity("KB", "#F3C24E", "#473A18"),
}
_SYMBOL_GROUP = {
    "005930": "samsung", "005935": "samsung", "009150": "samsung",
    "207940": "samsung", "028260": "samsung", "032830": "samsung",
    "000660": "sk", "402340": "sk", "034730": "sk",
    "373220": "lg", "051910": "lg", "066570": "lg",
    "005380": "hyundai", "005385": "hyundai", "012330": "hyundai",
    "105560": "kb",
}
_MARKET_MARKS = {
    "^GSPC": "SP", "^KS11": "K", "DEXKOUS": "$₩", "DGS10": "10Y",
    "VIXCLS": "VIX", "BTC-USD": "B",
}


def company_mark(symbol: str, name: str = "") -> CompanyIdentity:
    """A stable mark for known tickers, with a non-branded unknown fallback."""
    symbol = str(symbol).strip().upper()
    if symbol.endswith((".KS", ".KQ")):
        symbol = symbol[:-3]
    group = _SYMBOL_GROUP.get(symbol)
    if group:
        return _GROUPS[group]
    if symbol in _MARKET_MARKS:
        return CompanyIdentity(_MARKET_MARKS[symbol], "#E7EDE8", "#315A48")
    words = re.findall(r"[A-Za-z]+|[가-힣]+", str(name))
    if words:
        letters = "".join(word[0] for word in words[:2]).upper() if len(words) > 1 else words[0][:2].upper()
    else:
        letters = re.sub(r"[^A-Z0-9]", "", symbol)[:2] or "?"
    return CompanyIdentity(letters, "#E9ECE8", "#3F5146")


def _paint_mark(painter: QPainter, rect: QRectF, spec: CompanyIdentity, base: QFont) -> None:
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(spec.background))
    painter.drawEllipse(rect)
    ratio = 0.55 if len(spec.letters) == 1 else (0.42 if len(spec.letters) == 2 else 0.32)
    size = max(9, round(rect.height() * ratio))
    painter.setFont(scaled_font(base, size, 600))
    painter.setPen(QColor(spec.foreground))
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, spec.letters)
    painter.restore()


def company_icon(symbol: str, name: str = "", *, palette=LIGHT, size: int = 30, dpr: float = 1.0) -> QIcon:
    """A local, high-DPI icon for item models (no URL or network dependency)."""
    ratio = max(1.0, float(dpr))
    pixmap = QPixmap(round(size * ratio), round(size * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    _paint_mark(painter, QRectF(0, 0, size, size), company_mark(symbol, name), QApplication.font())
    painter.end()
    return QIcon(pixmap)


class CompanyMark(QWidget):
    """Scalable painted letter mark; adjacent text carries the full company name."""
    def __init__(self, symbol: str, name: str = "", *, palette=LIGHT, size: int = 30, parent=None):
        super().__init__(parent)
        self.setObjectName("companyMark")
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.colors = palette
        self.set_identity(symbol, name)

    def set_identity(self, symbol: str, name: str = "") -> None:
        self.symbol, self.name = str(symbol), str(name)
        self.spec = company_mark(self.symbol, self.name)
        self.setAccessibleName(self.name or self.symbol)
        self.setToolTip(" · ".join(part for part in (self.name, self.symbol) if part))
        self.update()

    def set_theme(self, palette) -> None:
        # Solid discs preserve the same recognizable group colours in both modes.
        self.colors = palette
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        _paint_mark(painter, QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), self.spec, self.font())
        painter.end()
