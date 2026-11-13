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


class ElidedLabel(QLabel):
    """One line that keeps its whole text (text() is the first, fullest choice) and paints the longest choice
    that fits, eliding the end of the last one when none fits (never the start). The tooltip carries the full
    text while it is cut."""

    def __init__(self, sd="", *, align=Qt.AlignmentFlag.AlignLeft):
        super().__init__()
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setProperty("qg_literal", True)
        if sd:
            self.setProperty("sd", sd)
        self.setAlignment(align | Qt.AlignmentFlag.AlignVCenter)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self._choices = ()
        self.shown = ""

    def setText(self, value):
        self._choices = (value,) if value else ()
        super().setText(value)

    def set_choices(self, choices):
        self._choices = tuple(choice for choice in choices if choice)
        super().setText(self._choices[0] if self._choices else "")
        self.update()

    def fitted(self, width=None):
        width = self.contentsRect().width() if width is None else width
        metrics = self.fontMetrics()
        for choice in self._choices:
            if metrics.horizontalAdvance(choice) <= width:
                return choice
        return metrics.elidedText(self._choices[-1], Qt.TextElideMode.ElideRight, width) if self._choices else ""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self.font())
        painter.setPen(self.palette().color(self.foregroundRole()))
        self.shown = self.fitted()
        painter.drawText(self.contentsRect(), int(self.alignment()), self.shown)
        painter.end()
        cut = self.shown != self.text()
        if (self.toolTip() == self.text()) != cut:
            self.setToolTip(self.text() if cut else "")


class ClampLabel(QLabel):
    """Wrapped text clamped to `lines` lines; the last line is elided. The full text is the tooltip when cut."""

    def __init__(self, sd="", *, lines=2):
        super().__init__()
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setProperty("qg_literal", True)
        if sd:
            self.setProperty("sd", sd)
        self.lines = lines
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

    def setText(self, value):
        super().setText(value)
        self.updateGeometry()

    def _layout(self, width):
        """The lines shown at `width` (the last one elided) and whether the text was cut."""
        from PyQt6.QtGui import QTextLayout, QTextOption
        content = self.text()
        if not content or width <= 0:
            return [], False
        layout = QTextLayout(content, self.font())
        option = QTextOption()
        option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        layout.setTextOption(option)
        layout.beginLayout()
        spans = []
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(width)
            spans.append((line.textStart(), line.textLength()))
        layout.endLayout()
        metrics = self.fontMetrics()
        shown = [content[start:start + length].rstrip() for start, length in spans[:self.lines]]
        cut = len(spans) > self.lines
        if cut:
            start = spans[self.lines - 1][0]
            shown[-1] = metrics.elidedText(content[start:].replace("\n", " "), Qt.TextElideMode.ElideRight, width)
        return shown, cut

    def sizeHint(self):
        width = self.width() if self.width() > 0 else 200
        lines = max(1, len(self._layout(width)[0]))
        return QSize(width, lines * self.fontMetrics().lineSpacing() + 2)

    def minimumSizeHint(self):
        return QSize(40, self.sizeHint().height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateGeometry()

    def paintEvent(self, event):
        rect = self.contentsRect()
        shown, cut = self._layout(rect.width())
        painter = QPainter(self)
        painter.setFont(self.font())
        painter.setPen(self.palette().color(self.foregroundRole()))
        step = self.fontMetrics().lineSpacing()
        for index, line in enumerate(shown):
            painter.drawText(QRectF(rect.x(), rect.y() + index * step, rect.width(), step),
                             int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), line)
        painter.end()
        tip = self.text() if cut else ""
        if self.toolTip() != tip and not self.property("keepTip"):
            self.setToolTip(tip)


# 합니다체 -> 해요체 (owner wording rule for this view; the engine's readings and guides are written formally).
# Exact forms first: irregular verbs and contractions the general rules below would get wrong.
_POLITE_WORDS = {
    "아닙니다": "아니에요", "합니다": "해요", "됩니다": "돼요", "봅니다": "봐요", "둡니다": "둬요", "줍니다": "줘요",
    "보여줍니다": "보여줘요", "보여 줍니다": "보여 줘요", "나타냅니다": "나타내요", "그립니다": "그려요",
    "흔들립니다": "흔들려요", "뒤집힙니다": "뒤집혀요", "커집니다": "커져요", "이뤄집니다": "이뤄져요",
    "이루어집니다": "이루어져요", "올라갑니다": "올라가요", "오갑니다": "오가요", "셉니다": "세요",
    "벗어납니다": "벗어나요", "바뀝니다": "바뀌어요", "머뭅니다": "머물러요", "다릅니다": "달라요",
    "다가갑니다": "다가가요", "넘어갑니다": "넘어가요", "넘나듭니다": "넘나들어요", "쉽습니다": "쉬워요",
    "어렵습니다": "어려워요", "가깝습니다": "가까워요", "읽습니다": "읽어요", "늦습니다": "늦어요",
    "있습니다": "있어요", "없습니다": "없어요", "않습니다": "않아요", "같습니다": "같아요", "높습니다": "높아요",
    "낮습니다": "낮아요", "잦습니다": "잦아요", "많습니다": "많아요", "적습니다": "적어요", "작습니다": "작아요",
    "좋습니다": "좋아요", "넓습니다": "넓어요", "좁습니다": "좁아요", "깁니다": "길어요", "짧습니다": "짧아요",
    "큽니다": "커요", "씁니다": "써요", "냅니다": "내요", "납니다": "나요", "갑니다": "가요", "옵니다": "와요",
    "삽니다": "사요", "팝니다": "팔아요", "지납니다": "지나요", "움직입니다": "움직여요", "보입니다": "보여요",
    "쌓입니다": "쌓여요", "줄어듭니다": "줄어들어요", "늘어납니다": "늘어나요", "나뉩니다": "나뉘어요",
    "바꿉니다": "바꿔요", "모읍니다": "모아요", "채웁니다": "채워요", "맞춥니다": "맞춰요", "그칩니다": "그쳐요",
    "살핍니다": "살펴요", "돕습니다": "도와요",
}
_HA_SUFFIX = ("합니다",)          # 필요합니다 -> 필요해요, 표시합니다 -> 표시해요
_FINAL = lambda ch: "가" <= ch <= "힣" and (ord(ch) - 0xAC00) % 28 != 0
_DIGIT_FINAL = {"0": True, "1": True, "2": False, "3": True, "4": False, "5": False, "6": True, "7": True,
                "8": True, "9": False}


def _copula(before):
    """'이에요' or '예요' after the text `before` (a noun, a number, a percent sign or a closing bracket)."""
    for ch in reversed(before.rstrip(")]’'\" ")):
        if "가" <= ch <= "힣":
            return "이에요" if _FINAL(ch) else "예요"
        if ch.isdigit():
            return "이에요" if _DIGIT_FINAL[ch] else "예요"
        if ch == "%":
            return "예요"
        if ch.isalpha():
            return "예요" if ch.lower() in "aeiouy" else "이에요"
    return "이에요"


def _polite_word(match):
    word, start, source = match.group(0), match.start(), match.string
    if word in _POLITE_WORDS:
        return _POLITE_WORDS[word]
    stem = word[:-2]                                     # without '니다'
    if stem.endswith("입"):                               # noun + 입니다
        noun = stem[:-1]
        before = noun if noun else source[:start]
        return noun + _copula(before)
    if word.endswith(_HA_SUFFIX):                        # X합니다
        return word[:-3] + "해요"
    if word.endswith("됩니다"):                           # 갱신됩니다 -> 갱신돼요
        return word[:-3] + "돼요"
    if stem.endswith("습") and len(stem) >= 2:
        prior = stem[-2]
        jong = (ord(prior) - 0xAC00) % 28 if "가" <= prior <= "힣" else -1
        if jong == 20:                                   # ㅆ: past tense 했습니다/컸습니다 -> 했어요/컸어요
            return stem[:-1] + "어요"
        exact = _POLITE_WORDS.get(stem[-2:] + "니다")
        if exact:
            return stem[:-2] + exact
    return word


# Noun endings the profile's notes and the engine's asides use ('…수 있음', '(… 높음)'), at the end of a sentence,
# an aside or a dotted part only: a label such as '자료 없음' stays as it is.
_NOUN_ENDINGS = {"수 있음": "수 있어요", "아님": "아니에요", "없었음": "없었어요", "높음": "높아요", "낮음": "낮아요",
                 "같음": "같아요"}


def polite(value, language="ko"):
    """Korean text in 해요체 (the engine and the stock profile write 합니다체 and noun endings); other languages
    unchanged."""
    import re
    if language != "ko" or not value:
        return value
    if "니다" in value:
        value = re.sub(r"[가-힣]*니다", _polite_word, value)
    if "음" in value:
        value = re.sub(r"(수 있음|아님|없었음|높음|낮음|같음)(?=$|[)\].\n]| ·)",
                       lambda match: _NOUN_ENDINGS[match.group(1)], value)
    return value


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
    """Painted toolbar icons: pause, play, info, focus, unfocus, panel, refresh, left, right, minus, plus, more,
    close."""
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
    elif kind == "more":
        p.setBrush(QColor(color))
        for x in (s * .28, s * .5, s * .72):
            p.drawEllipse(QPointF(x, s / 2), .9, .9)
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
      QLabel[sd='stateInline'] {{ font-size: 12px; font-weight: 500; color: {p.muted}; }}
      QLabel[sd='stateInline'][tone='success'] {{ color: {p.success}; }}
      QLabel[sd='stateInline'][tone='warning'] {{ color: {p.warning}; }}
      QLabel[sd='stateInline'][tone='error'] {{ color: {p.error}; }}
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
      QLabel[sd='nowDetail'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[sd='topic'] {{ font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 8px;
                            color: {p.accent}; background: {p.accent_soft}; }}
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
      QFrame[sd='guideCard'] {{ background: {soft}; border: 0; border-radius: 14px; }}
      QFrame[sd='guideCompact'] {{ background: transparent; border: 0; }}
      QLabel[sd='guideReading'] {{ font-size: 16px; font-weight: 600; color: {p.text}; letter-spacing: -0.3px; }}
      QLabel[sd='guideReadingSmall'] {{ font-size: 14px; font-weight: 500; color: {p.text}; letter-spacing: -0.2px; }}
      QLabel[sd='guideOne'] {{ font-size: 13px; color: {p.muted}; }}
      QLabel[sd='guideCaution'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[sd='guideLong'] {{ font-size: 13px; color: {p.text}; }}
      QLabel[sd='cue'] {{ font-size: 12px; font-weight: 500; padding: 3px 8px; border-radius: 10px;
                          color: {p.text}; background: {p.surface}; border: 1px solid {line}; }}
      QLabel[sd='pill'] {{ font-size: 12px; font-weight: 600; padding: 2px 10px; border-radius: 10px;
                           color: {p.text}; background: {p.surface}; border: 1px solid {line}; }}
      QLabel[sd='pill'][tone='up'] {{ color: {t['up']}; background: {t['up_tint']}; border-color: {t['up_tint']}; }}
      QLabel[sd='pill'][tone='down'] {{ color: {t['down']}; background: {t['down_tint']}; border-color: {t['down_tint']}; }}
      QLabel[sd='limitNote'] {{ font-size: 12px; color: {p.warning}; background: {t['flat_tint']}; border-radius: 9px; }}
      QPushButton[sd='qbadge'] {{ padding: 3px 10px; min-height: 18px; border: 0; border-radius: 11px;
                                  background: {p.surface_2}; color: {p.muted}; font-size: 12px; font-weight: 600;
                                  letter-spacing: 0px; }}
      QPushButton[sd='qbadge'][tone='ready'] {{ background: {p.accent_soft}; color: {p.accent}; }}
      QPushButton[sd='qbadge']:hover {{ background: {p.accent_soft}; color: {p.accent}; }}
      QPushButton[sd='qbadge']:focus {{ border: 2px solid {p.accent}; }}
      QFrame#sdQScore QWidget {{ background: transparent; }}
      QLabel[sd='qsTitle'] {{ font-size: 13px; font-weight: 600; color: {p.accent}; letter-spacing: 0px; }}
      QLabel[sd='qsAsOf'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[sd='qsScore'] {{ font-size: 34px; font-weight: 600; color: {p.text}; letter-spacing: -0.8px; }}
      QLabel[sd='qsOutOf'] {{ font-size: 13px; color: {p.muted}; padding-bottom: 5px; }}
      QLabel[sd='qsStars'] {{ font-size: 18px; letter-spacing: 1px; padding-bottom: 4px; }}
      QLabel[sd='qsReading'] {{ font-size: 15px; font-weight: 500; color: {p.text}; letter-spacing: -0.3px; }}
      QLabel[sd='qsPart'] {{ font-size: 13px; color: {p.text}; }}
      QLabel[sd='qsWeight'] {{ font-size: 12px; color: {p.muted}; letter-spacing: 0px; }}
      QLabel[sd='qsValue'] {{ font-size: 13px; font-weight: 600; color: {p.text}; letter-spacing: 0px; }}
      QFrame[sd='notesBox'] {{ background: {soft}; border: 0; border-radius: 12px; }}
    """


__all__ = ["text", "numbers", "label", "rich", "repolish", "set_prop", "line_color", "chevron", "icon", "icon_size",
           "sheet", "ElidedLabel", "ClampLabel", "polite"]
