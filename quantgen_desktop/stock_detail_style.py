"""Look and small helpers of the native stock detail view (UI-D8, owner 2026-11-11).

The view sets `sheet(palette, dark)` on itself: a closer style sheet wins over the window sheet in Qt, so
typography.py stays untouched. Font rules follow UI-D6 (QG Interface, weights 400/500/600, N3 tracking); figures
use font_policy.number_font; separating lines are the light line typography.mix(border, bg, 0.5). Icons the
interface face lacks (pause, play, info, focus, side panel) are painted, as shell_rail does; fold arrows are the
bundled chevron SVGs (never '▸'/'▾' as text: QG Interface has no such glyphs).
"""
from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy

from .owner_ui_language.stock import TEXT


def text(language, key, **fields):
    """TEXT[key] in the window language ('ko' or anything else = English), templates filled."""
    en, ko = TEXT[key]
    value = ko if language == "ko" else en
    return value.format(**fields) if fields and isinstance(value, str) else value


def numbers(widget):
    from .font_policy import number_font
    widget.setFont(number_font(widget.font()))
    return widget


def label(sd="", *, wrap=False, selectable=False):
    """A plain-text label rendered in the window language by the view (the language controller skips it)."""
    widget = QLabel()
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(wrap)
    if sd:
        widget.setProperty("sd", sd)
    widget.setProperty("qg_literal", True)
    if selectable:
        widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    if wrap:
        widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
    return widget


def rich(sd=""):
    widget = QLabel()
    widget.setTextFormat(Qt.TextFormat.RichText)
    if sd:
        widget.setProperty("sd", sd)
    widget.setProperty("qg_literal", True)
    return widget


def repolish(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def set_prop(widget, name, value):
    if widget.property(name) != value:
        widget.setProperty(name, value)
        repolish(widget)


def line_color(p):
    from .typography import mix
    return mix(p.border, p.bg, 0.5)


def chevron(direction, dark, size=14):
    """The bundled chevron SVG ('down', 'right', 'up', 'left') as an icon for the theme."""
    from .typography import icon_dir
    return QIcon(f"{icon_dir()}/chevron-{direction}-{'dark' if dark else 'light'}.svg")


def icon(kind, color, size=18):
    """Painted toolbar icons: pause, play, info, focus, unfocus, panel, refresh, left, right, minus, plus, close."""
    ratio = 2
    pixmap = QPixmap(size * ratio, size * ratio)
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.GlobalColor.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(QColor(color), 1.7)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    s = float(size)
    m = s * 0.2
    if kind == "pause":
        p.drawLine(QPointF(s * .38, m), QPointF(s * .38, s - m))
        p.drawLine(QPointF(s * .62, m), QPointF(s * .62, s - m))
    elif kind == "play":
        path = QPainterPath(QPointF(s * .34, m))
        path.lineTo(QPointF(s * .74, s / 2))
        path.lineTo(QPointF(s * .34, s - m))
        path.closeSubpath()
        p.drawPath(path)
    elif kind == "info":
        p.drawEllipse(QRectF(m * .7, m * .7, s - 1.4 * m, s - 1.4 * m))
        p.drawLine(QPointF(s / 2, s * .46), QPointF(s / 2, s * .7))
        p.setBrush(QColor(color))
        p.drawEllipse(QPointF(s / 2, s * .32), .9, .9)
    elif kind in ("focus", "unfocus"):
        a, b = m, s - m
        k = s * .17
        corners = ((a, a, 1, 1), (b, a, -1, 1), (a, b, 1, -1), (b, b, -1, -1))
        for x, y, dx, dy in corners:
            if kind == "focus":
                p.drawLine(QPointF(x, y), QPointF(x + dx * k, y))
                p.drawLine(QPointF(x, y), QPointF(x, y + dy * k))
            else:
                cx, cy = x + dx * k, y + dy * k
                p.drawLine(QPointF(cx, cy), QPointF(cx - dx * k, cy))
                p.drawLine(QPointF(cx, cy), QPointF(cx, cy - dy * k))
    elif kind == "panel":
        p.drawRoundedRect(QRectF(m * .7, m, s - 1.4 * m, s - 2 * m), 2.5, 2.5)
        p.drawLine(QPointF(s * .62, m), QPointF(s * .62, s - m))
    elif kind == "refresh":
        rect = QRectF(m, m, s - 2 * m, s - 2 * m)
        p.drawArc(rect, 40 * 16, 290 * 16)
        tip = QPointF(s - m - .4, s * .36)
        p.drawLine(tip, QPointF(tip.x() - s * .2, tip.y() - s * .02))
        p.drawLine(tip, QPointF(tip.x() + s * .02, tip.y() - s * .2))
    elif kind in ("left", "right"):
        d = -1 if kind == "left" else 1
        c = s / 2
        p.drawLine(QPointF(c - d * s * .12, s * .28), QPointF(c + d * s * .12, s / 2))
        p.drawLine(QPointF(c + d * s * .12, s / 2), QPointF(c - d * s * .12, s * .72))
    elif kind in ("minus", "plus"):
        p.drawLine(QPointF(s * .28, s / 2), QPointF(s * .72, s / 2))
        if kind == "plus":
            p.drawLine(QPointF(s / 2, s * .28), QPointF(s / 2, s * .72))
    elif kind == "close":
        p.drawLine(QPointF(s * .32, s * .32), QPointF(s * .68, s * .68))
        p.drawLine(QPointF(s * .68, s * .32), QPointF(s * .32, s * .68))
    p.end()
    return QIcon(pixmap)


def icon_size(size=18):
    return QSize(size, size)


def sheet(p, dark):
    """Scoped rules for StockDetailView and its children."""
    from .typography import TONE_COLORS, mix
    t = TONE_COLORS[bool(dark)]
    line = line_color(p)
    soft = mix(p.surface_2, p.bg, 0.3)
    overlay = mix(p.bg, p.surface, 0.0)
    return f"""
      QWidget#stockDetail {{ background: {p.bg}; }}
      QFrame#sdToolbar, QWidget#sdBody, QFrame#sdChartColumn, QWidget#sdPeriods {{ background: transparent; border: 0; }}
      QLabel[sd] {{ background: transparent; letter-spacing: -0.2px; }}
      QLabel[sd='name'] {{ font-size: 20px; font-weight: 600; letter-spacing: -0.5px; color: {p.text}; }}
      QLabel[sd='code'] {{ font-size: 12px; font-weight: 400; color: {p.muted}; letter-spacing: -0.1px; }}
      QLabel[sd='chip'] {{ font-size: 12px; font-weight: 500; padding: 3px 10px; border-radius: 11px;
                           color: {p.muted}; background: {p.surface_2}; letter-spacing: -0.1px; }}
      QLabel[sd='chip'][tone='success'] {{ color: {p.success}; background: {p.accent_soft}; }}
      QLabel[sd='chip'][tone='warning'] {{ color: {p.warning}; background: {t['flat_tint']}; }}
      QLabel[sd='chip'][tone='error'] {{ color: {p.error}; background: {t['up_tint']}; }}
      QPushButton[sd='tool'] {{ padding: 0; min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px;
                                border: 0; border-radius: 9px; background: transparent; }}
      QPushButton[sd='tool']:hover {{ background: {p.accent_soft}; }}
      QPushButton[sd='tool']:checked {{ background: {p.accent_soft}; }}
      QPushButton[sd='tool']:focus {{ border: 2px solid {p.accent}; }}
      QPushButton[sd='text'] {{ padding: 6px 12px; border: 0; border-radius: 9px; background: {p.surface_2};
                                color: {p.text}; font-size: 13px; font-weight: 500; }}
      QPushButton[sd='text']:hover {{ background: {p.accent_soft}; }}
      QPushButton[sd='text']:checked {{ background: {p.accent_soft}; color: {p.accent}; font-weight: 600; }}
      QPushButton[sd='text']:focus {{ border: 2px solid {p.accent}; }}
      QPushButton[sd='back'] {{ padding: 6px 10px; border: 0; border-radius: 9px; background: transparent;
                                color: {p.muted}; font-size: 13px; font-weight: 500; }}
      QPushButton[sd='back']:hover {{ background: {p.accent_soft}; color: {p.text}; }}
      QPushButton[sd='back']:focus {{ border: 2px solid {p.accent}; }}
      QLineEdit#sdSearch {{ min-height: 22px; padding: 5px 12px; border: 1px solid {line}; border-radius: 17px;
                            background: {p.surface}; font-size: 13px; }}
      QLineEdit#sdSearch:focus {{ border: 2px solid {p.accent}; }}
      QComboBox#sdInterval {{ border: 0; border-radius: 9px; background: {p.surface_2}; min-height: 22px;
                              font-size: 13px; font-weight: 500; }}
      QComboBox#sdInterval:focus {{ border: 2px solid {p.accent}; }}
      QPushButton[sd='period'] {{ padding: 5px 11px; min-height: 20px; border: 0; border-radius: 8px;
                                  background: transparent; color: {p.muted}; font-size: 13px; font-weight: 500; }}
      QPushButton[sd='period']:hover {{ background: {p.accent_soft}; color: {p.text}; }}
      QPushButton[sd='period']:checked {{ background: {p.accent_soft}; color: {p.accent}; font-weight: 600; }}
      QPushButton[sd='period']:disabled {{ color: {mix(p.muted, p.bg, 0.45)}; background: transparent; }}
      QPushButton[sd='period']:focus {{ border: 2px solid {p.accent}; }}
      QLabel[sd='hint'] {{ font-size: 12px; color: {p.muted}; }}
      QFrame#sdChartColumn QLabel[role='caption'], QFrame#sdChartColumn QLabel[role='muted'] {{ font-size: 13px; }}
      QFrame[sd='overlay'] {{ background: {overlay}; border: 0; border-radius: 6px; }}
      QFrame[sd='overlayClear'] {{ background: transparent; border: 0; }}
      QLabel[sd='ohlcKey'] {{ font-size: 13px; color: {p.muted}; }}
      QLabel[sd='ohlcValue'] {{ font-size: 13px; font-weight: 500; color: {p.text}; letter-spacing: 0px; }}
      QLabel[sd='ohlcValue'][tone='up'] {{ color: {t['up']}; }}
      QLabel[sd='ohlcValue'][tone='down'] {{ color: {t['down']}; }}
      QLabel[sd='ohlcTitle'] {{ font-size: 13px; font-weight: 600; color: {p.text}; }}
      QLabel[sd='ohlcDate'] {{ font-size: 13px; color: {p.muted}; }}
      QLabel[sd='legend'] {{ font-size: 13px; color: {p.text}; }}
      QLabel[sd='panelTitle'] {{ font-size: 13px; color: {p.text}; }}
      QLabel[sd='reading'] {{ font-size: 13px; color: {p.muted}; }}
      QPushButton[sd='mini'] {{ padding: 0; min-width: 22px; max-width: 22px; min-height: 22px; max-height: 22px;
                                border: 0; border-radius: 6px; background: transparent; }}
      QPushButton[sd='mini']:hover {{ background: {p.accent_soft}; }}
      QPushButton[sd='notice'] {{ padding: 3px 10px; border: 0; border-radius: 11px; background: {p.surface_2};
                                  color: {p.text}; font-size: 12px; font-weight: 500; }}
      QPushButton[sd='notice']:hover {{ background: {p.accent_soft}; }}
      QLabel[sd='notice'] {{ padding: 3px 10px; border-radius: 11px; background: {p.surface_2}; color: {p.muted};
                             font-size: 12px; }}
      QFrame#sdSide {{ background: {p.surface}; border: 1px solid {line}; border-radius: 16px; }}
      QFrame#sdSide QWidget#sdPage, QFrame#sdSide QScrollArea, QFrame#sdSide QScrollArea > QWidget > QWidget
          {{ background: transparent; border: 0; }}
      QFrame#sdSegment {{ background: {p.surface_2}; border: 0; border-radius: 10px; }}
      QPushButton[sd='seg'] {{ padding: 6px 10px; border: 0; border-radius: 8px; background: transparent;
                               color: {p.muted}; font-size: 14px; font-weight: 500; }}
      QPushButton[sd='seg']:checked {{ background: {p.surface}; color: {p.text}; font-weight: 600; }}
      QPushButton[sd='seg']:focus {{ border: 2px solid {p.accent}; }}
      QFrame[sd='rule'] {{ background: {line}; border: 0; min-height: 1px; max-height: 1px; }}
      QFrame[sd='foldHead'] {{ background: transparent; border: 0; border-radius: 9px; }}
      QFrame[sd='foldHead']:hover {{ background: {soft}; }}
      QFrame[sd='foldHead'][focusRing='true'] {{ background: {p.accent_soft}; }}
      QLabel[sd='foldTitle'] {{ font-size: 15px; font-weight: 500; color: {p.text}; letter-spacing: -0.3px; }}
      QLabel[sd='foldCount'], QLabel[sd='digest'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[sd='rowLabel'] {{ font-size: 13px; color: {p.muted}; }}
      QLabel[sd='rowValue'] {{ font-size: 14px; font-weight: 500; color: {p.text}; letter-spacing: 0px; }}
      QLabel[sd='rowValue'][tone='up'] {{ color: {t['up']}; }}
      QLabel[sd='rowValue'][tone='down'] {{ color: {t['down']}; }}
      QLabel[sd='rowNote'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[sd='studyName'] {{ font-size: 14px; font-weight: 500; color: {p.text}; }}
      QLabel[sd='studyValues'] {{ font-size: 13px; color: {p.text}; letter-spacing: 0px; }}
      QLabel[sd='studyReading'] {{ font-size: 13px; color: {p.muted}; }}
      QPushButton[sd='link'] {{ padding: 2px 4px; border: 0; background: transparent; color: {p.accent};
                                font-size: 13px; font-weight: 500; text-align: left; }}
      QPushButton[sd='link']:hover {{ text-decoration: underline; }}
      QPushButton[sd='link']:focus {{ border: 1px solid {p.accent}; border-radius: 4px; }}
      QLabel[sd='cardTitle'] {{ font-size: 15px; font-weight: 500; color: {p.text}; letter-spacing: -0.3px; }}
      QLabel[sd='sector'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[sd='price'] {{ font-size: 30px; font-weight: 600; color: {p.text}; letter-spacing: -0.6px; }}
      QLabel[sd='change'] {{ font-size: 14px; font-weight: 600; padding: 2px 8px; border-radius: 7px;
                             color: {t['flat']}; background: {t['flat_tint']}; letter-spacing: 0px; }}
      QLabel[sd='change'][tone='up'] {{ color: {t['up']}; background: {t['up_tint']}; }}
      QLabel[sd='change'][tone='down'] {{ color: {t['down']}; background: {t['down_tint']}; }}
      QLabel[sd='state'] {{ font-size: 13px; color: {p.muted}; }}
      QLabel[sd='state'][tone='success'] {{ color: {p.success}; }}
      QLabel[sd='state'][tone='warning'] {{ color: {p.warning}; }}
      QLabel[sd='state'][tone='error'] {{ color: {p.error}; }}
      QLabel[sd='small'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[sd='body'] {{ font-size: 13px; color: {p.text}; }}
      QLabel[sd='topic'] {{ font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 8px;
                            color: {p.accent}; background: {p.accent_soft}; }}
      QLabel[sd='qscore'] {{ font-size: 12px; font-weight: 500; padding: 3px 9px; border-radius: 9px;
                             color: {p.text}; background: {p.surface_2}; }}
      QFrame[sd='nowRow'] {{ background: transparent; border: 0; border-radius: 9px; }}
      QFrame[sd='nowRow']:hover {{ background: {soft}; }}
      QFrame[sd='watchRow'] {{ background: transparent; border: 0; border-radius: 9px; }}
      QFrame[sd='watchRow']:hover {{ background: {soft}; }}
      QFrame[sd='watchRow'][current='true'] {{ background: {p.accent_soft}; border-left: 3px solid {p.accent};
                                               border-top-left-radius: 2px; border-bottom-left-radius: 2px; }}
      QLabel[sd='watchName'] {{ font-size: 14px; font-weight: 500; color: {p.text}; }}
      QLabel[sd='watchCode'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[sd='watchPrice'] {{ font-size: 14px; font-weight: 500; color: {p.text}; letter-spacing: 0px; }}
      QLabel[sd='watchChange'] {{ font-size: 12px; font-weight: 600; padding: 1px 6px; border-radius: 6px;
                                  color: {t['flat']}; background: {t['flat_tint']}; letter-spacing: 0px; }}
      QLabel[sd='watchChange'][tone='up'] {{ color: {t['up']}; background: {t['up_tint']}; }}
      QLabel[sd='watchChange'][tone='down'] {{ color: {t['down']}; background: {t['down_tint']}; }}
      QLabel[sd='watchTag'] {{ font-size: 11px; color: {p.warning}; }}
      QLineEdit#sdPickerSearch {{ min-height: 22px; padding: 6px 12px; border: 1px solid {line}; border-radius: 17px;
                                  background: {p.bg}; font-size: 13px; }}
      QLineEdit#sdPickerSearch:focus {{ border: 2px solid {p.accent}; }}
      QFrame[sd='pickRow'] {{ background: transparent; border: 0; border-radius: 10px; }}
      QFrame[sd='pickRow']:hover {{ background: {soft}; }}
      QFrame[sd='pickRow'][focusRing='true'] {{ background: {p.accent_soft}; }}
      QLabel[sd='pickName'] {{ font-size: 15px; font-weight: 500; color: {p.text}; letter-spacing: -0.3px; }}
      QLabel[sd='pickName'][dim='true'] {{ color: {p.muted}; }}
      QLabel[sd='pickDesc'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[sd='pickDesc'][reason='true'] {{ color: {p.warning}; }}
      QLabel[sd='place'] {{ font-size: 11px; font-weight: 500; padding: 1px 6px; border-radius: 6px;
                            color: {p.muted}; background: {p.surface_2}; }}
      QLabel[sd='pickValue'] {{ font-size: 13px; font-weight: 500; color: {p.text}; letter-spacing: 0px; }}
      QFrame[sd='guide'] {{ background: {soft}; border: 0; border-radius: 10px; }}
      QLabel[sd='guideHead'] {{ font-size: 12px; font-weight: 600; color: {p.accent}; }}
      QLabel[sd='guideText'] {{ font-size: 13px; color: {p.text}; }}
      QFrame#sdNotes {{ background: {p.surface}; border: 1px solid {line}; border-radius: 12px; }}
      QFrame#sdNotes QLabel {{ font-size: 13px; }}
    """


__all__ = ["text", "numbers", "label", "rich", "repolish", "set_prop", "line_color", "chevron", "icon", "icon_size",
           "sheet"]
