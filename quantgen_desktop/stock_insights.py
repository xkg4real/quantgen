"""Compact educational valuation, investor-flow and REST microstructure cards.

The parent supplies an already-loaded profile. This widget never starts a worker,
timer, provider, credential lookup or network request.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from PyQt6.QtCore import QEvent, QRect, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
                             QSizePolicy, QToolTip, QVBoxLayout, QWidget)

from core.market.detail_insights import build_insights, number
from core.theme import DARK, LIGHT
from .stock_detail_style import chevron, label, numbers, sheet
from .typography import tone_colors


def _fmt(value, digits=2):
    n = number(value)
    return "—" if n is None else f"{n:,.{digits}f}"


def _shares(value, language):
    """A signed share count short enough for one sidebar line: 만주 in Korean, K/M in English."""
    size = abs(value)
    sign = "+" if value > 0 else "−" if value < 0 else ""
    if language == "ko":
        if size >= 1e7:                     # 1,000만주 and up: whole 만 keep the line short
            return f"{sign}{size / 10000:,.0f}만주"
        return f"{sign}{size / 10000:,.1f}만주" if size >= 10000 else f"{sign}{size:,.0f}주"
    if size >= 1e6:
        return f"{sign}{size / 1e6:,.1f}M"
    return f"{sign}{size / 1e3:,.1f}K" if size >= 1e4 else f"{sign}{size:,.0f}"


def display_split(buy_fraction):
    """Round displayed tenths of a percent as complementary parts of100.0%.

    This affects labels only: quantities, model fractions and bar geometry retain
    their original precision. A missing/invalid fraction stays unavailable.
    """
    fraction = number(buy_fraction)
    if fraction is None or not 0 <= fraction <= 1:
        return None, None
    buy_tenths = min(1000, math.floor(fraction * 1000 + 0.5))
    return f"{buy_tenths / 10:.1f}%", f"{(1000 - buy_tenths) / 10:.1f}%"


class FlowBar(QWidget):
    """Gross buy/sell shares when supplied; otherwise a separate signed net bar."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(12)
        self.setMinimumWidth(0)
        self.fraction = self.net = None
        self.scale = 1.0
        self.dark = False

    def set_reading(self, fraction, net, scale, dark):
        self.fraction, self.net, self.scale, self.dark = fraction, net, max(1.0, scale), dark
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()
        palette = DARK if self.dark else LIGHT
        tones = tone_colors(self.dark)
        # The same six-pixel rounded track as the existing stock volume/range bars.
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        track = QPainterPath()
        track.addRoundedRect(QRectF(0, (h - 6) / 2, w, 6), 3, 3)
        painter.setClipPath(track)
        painter.fillRect(0, 0, w, h, QColor(palette.surface_2))
        buy, sell = QColor(tones["up"]), QColor(tones["down"])
        if self.fraction is not None:
            split = round(w * self.fraction)
            painter.fillRect(0, 0, split, h, buy)
            painter.fillRect(split, 0, w - split, h, sell)
        elif self.net is not None:
            half = w // 2
            size = round(half * min(1.0, abs(self.net) / self.scale))
            painter.fillRect(half if self.net >= 0 else half - size, 0, size, h, buy if self.net >= 0 else sell)
            painter.fillRect(half, 0, 1, h, QColor(palette.muted))
        painter.end()


class ValuationReferenceStrip(QWidget):
    """A neutral position guide, not a red/green investment rating.

    Three equal segments with their labels underneath; the segment holding the
    supplied value is tinted and a dot marks the value. No band is coloured as
    good or bad.
    """
    TRACK_TOP, TRACK_HEIGHT = 7, 8

    def __init__(self, metric, reference, dark, parent=None):
        super().__init__(parent)
        self.metric, self.reference, self.dark = metric, reference, bool(dark)
        self.setFixedHeight(42)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setToolTip(reference.hover)
        self.setAccessibleName(metric.upper() + ' · ' + reference.reading)
        self.setAccessibleDescription(reference.hover)

    def paintEvent(self, event):
        from .font_policy import number_font
        from .typography import scaled_font
        painter = QPainter(self)
        palette = DARK if self.dark else LIGHT
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        width = max(0., self.width() - 2.)
        third = width / 3
        top, height = self.TRACK_TOP, self.TRACK_HEIGHT
        band = self.reference.band_index
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(3):
            # Two-pixel gaps keep the three segments readable without tick marks.
            rect = QRectF(1 + i * third + (1 if i else 0), top, third - (2 if i in (0, 2) else 2), height)
            if i == band:
                tint = QColor(palette.accent)
                tint.setAlpha(110 if self.dark else 80)
                painter.setBrush(tint)
            else:
                painter.setBrush(QColor(palette.surface_2))
            painter.drawRoundedRect(rect, height / 2, height / 2)
        font = number_font(scaled_font(self.font(), 12, 400))
        strong = number_font(scaled_font(self.font(), 12, 600))
        for i, text in enumerate(self.reference.labels):
            painter.setFont(strong if i == band else font)
            painter.setPen(QColor(palette.text if i == band else palette.muted))
            painter.drawText(QRectF(1 + i * third, top + height + 4, third, 18),
                             int(Qt.AlignmentFlag.AlignCenter), text)
        if self.reference.position is not None:
            x = 1 + width * self.reference.position
            x = min(max(x, 1 + 6), 1 + width - 6)
            painter.setPen(QPen(QColor(palette.surface), 2))
            painter.setBrush(QColor(palette.accent))
            painter.drawEllipse(QRectF(x - 6, top + height / 2 - 6, 12, 12))
        painter.end()


class DailyNetBars(QWidget):
    """One investor group's net buying per session as up/down columns.

    Each column is one session, oldest on the left. Net buying rises above the
    zero line in the rise tone, net selling falls below it in the fall tone; the
    caller passes one scale shared by every group so columns compare across
    groups. A missing session shows a small dot on the zero line, never a zero
    column. Hover a column for its date and quantity.
    """
    def __init__(self, days, scale, dark, describe, parent=None):
        super().__init__(parent)
        self.days = tuple(days)            # ((date, value or None), ...)
        self.scale = max(1.0, float(scale or 0))
        self.dark = bool(dark)
        self.describe = describe          # (date, value) -> tooltip text
        self.hover = None
        self.setFixedHeight(46)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)

    def _index_at(self, x):
        if not self.days or self.width() <= 0:
            return None
        return min(len(self.days) - 1, max(0, int(x / (self.width() / len(self.days)))))

    def mouseMoveEvent(self, event):
        index = self._index_at(event.position().x())
        if index != self.hover:
            self.hover = index
            self.update()
        if index is not None:
            QToolTip.showText(event.globalPosition().toPoint(), self.describe(*self.days[index]), self)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hover = None
        self.update()
        QToolTip.hideText()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        palette = DARK if self.dark else LIGHT
        tones = tone_colors(self.dark)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        count = len(self.days)
        mid = h / 2
        painter.fillRect(QRectF(0, mid - .5, w, 1), QColor(palette.border))
        if not count:
            painter.end()
            return
        slot = w / count
        gap = 2 if slot >= 7 else 1
        reach = mid - 2
        for index, (_, value) in enumerate(self.days):
            x = index * slot + gap / 2
            if index == self.hover:
                shade = QColor(palette.surface_2)
                painter.fillRect(QRectF(index * slot, 0, slot, h), shade)
                painter.fillRect(QRectF(0, mid - .5, w, 1), QColor(palette.border))
            if value is None:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(palette.muted))
                painter.drawEllipse(QRectF(x + (slot - gap) / 2 - 1.5, mid - 1.5, 3, 3))
                continue
            size = reach * min(1.0, abs(value) / self.scale)
            if value != 0:
                size = max(size, 1.5)
            color = QColor(tones["up"] if value > 0 else tones["down"] if value < 0 else palette.muted)
            top = mid - size if value > 0 else mid
            painter.fillRect(QRectF(x, top, max(1., slot - gap), max(1., size)), color)
        painter.end()


class SideShareBar(QWidget):
    """Waiting sell size (left, fall tone) against waiting buy size (right, rise tone)."""
    def __init__(self, ask, bid, dark, parent=None):
        super().__init__(parent)
        self.ask, self.bid, self.dark = ask, bid, bool(dark)
        self.setFixedHeight(10)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        palette = DARK if self.dark else LIGHT
        tones = tone_colors(self.dark)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        track = QPainterPath()
        track.addRoundedRect(QRectF(0, 0, w, h), h / 2, h / 2)
        painter.setClipPath(track)
        painter.fillRect(0, 0, w, h, QColor(palette.surface_2))
        total = (self.ask or 0) + (self.bid or 0)
        if total > 0:
            split = w * (self.ask or 0) / total
            painter.fillRect(QRectF(0, 0, split, h), QColor(tones["down"]))
            painter.fillRect(QRectF(split, 0, w - split, h), QColor(tones["up"]))
        painter.end()


class DepthQuantityBar(QWidget):
    """Observed shares on one common full-snapshot scale, mirrored by side."""
    def __init__(self, side, quantity, scale, dark, parent=None):
        super().__init__(parent)
        self.side, self.quantity, self.scale = side, quantity, scale
        self.dark = bool(dark)
        self.color = tone_colors(self.dark)['down' if side == 'ask' else 'up']
        self.fraction = None if quantity is None else min(1., quantity/scale) if scale > 0 else 0.
        # Keep QWidget's explicit minimum at zero: a hard minimum of42 would
        # override the layout's larger intrinsic width for long quantities.
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        box = QVBoxLayout(self)
        box.setContentsMargins(5, 2, 5, 2)
        self.label = label('rowValue')
        self.label.setText(_fmt(quantity, 0))
        self.label.setProperty('insightRole', 'value')
        self.label.setProperty('depthRole', 'quantity')
        self.label.setProperty('tone', 'down' if side == 'ask' else 'up')
        self.label.setAlignment((Qt.AlignmentFlag.AlignRight if side == 'ask' else Qt.AlignmentFlag.AlignLeft)
                                | Qt.AlignmentFlag.AlignVCenter)
        self.label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        numbers(self.label)
        box.addWidget(self.label)

    def minimumSizeHint(self):
        hint = super().minimumSizeHint()
        margins = self.layout().contentsMargins()
        full_text = self.label.fontMetrics().horizontalAdvance(self.label.text())
        return QSize(max(42, hint.width(), full_text + margins.left() + margins.right()), hint.height())

    def sizeHint(self):
        return super().sizeHint().expandedTo(self.minimumSizeHint())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if self.fraction is not None and self.fraction > 0:
            # A clearly filled bar (owner, 2026-11-24: "진한 잔량 막대 호가창"). The
            # figure sits on the bar, so the fill stays light enough for its digits.
            width = max(3., self.width()*self.fraction)
            start = self.width()-width if self.side == 'ask' else 0
            color = QColor(self.color)
            color.setAlpha(120 if self.dark else 96)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(QRectF(start, 1, width, max(0, self.height()-2)), 3, 3)
        painter.end()


@dataclass(frozen=True)
class DepthRow:
    side: str
    level: int
    price: float | None
    quantity: float | None
    price_label: QLabel
    quantity_bar: DepthQuantityBar
    widgets: tuple


class _DepthViewport(QScrollArea):
    """Keep full read-only figures at the page's normal type size.

    Ordinary sidebar widths fit four columns. Exceptionally wide figures get a
    horizontal scroll, rather than overlapping adjacent prices or reducing text.
    """
    def __init__(self, grid):
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(0)
        table = QWidget()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(7)
        table.setLayout(grid)
        self.setWidget(table)
        table.installEventFilter(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_to_contents()

    def eventFilter(self, watched, event):
        if watched is self.widget() and event.type() in (
                QEvent.Type.LayoutRequest, QEvent.Type.Show,
                QEvent.Type.FontChange, QEvent.Type.StyleChange):
            self._fit_to_contents()
        return super().eventFilter(watched, event)

    def _fit_to_contents(self):
        if getattr(self, "_fitting", False):
            return
        table = self.widget()
        if table is None:
            return
        self._fitting = True
        try:
            labels = table.findChildren(QLabel)
            for item in labels:
                item.ensurePolished()
            grid = table.layout()
            # Initial style polish can change the fonts after the first resize.
            # Recompute the actual row geometry, not a stale pre-polish hint.
            signature = (self.viewport().width(), tuple(
                (item.text(), item.font().toString(), item.font().letterSpacing(),
                 item.sizeHint().width(), item.sizeHint().height(), item.isHidden())
                for item in labels))
            if signature != getattr(self, "_layout_signature", None):
                self._layout_signature = signature
                grid.invalidate()
            minimum = table.minimumSizeHint()
            table.setMinimumWidth(minimum.width())
            width = max(minimum.width(), self.viewport().width())
            # A wide price leaves less room for the wrapped quantity headers.
            # Their actual row height is width-dependent, unlike minimumSizeHint.
            height = max(minimum.height(), grid.totalHeightForWidth(width))
            grid.setGeometry(QRect(0, 0, width, height))
            visible_bottom = max((grid.itemAt(i).widget().geometry().bottom() + 1
                                  for i in range(grid.count())
                                  if grid.itemAt(i).widget() is not None
                                  and not grid.itemAt(i).widget().isHidden()), default=0)
            height = max(height, visible_bottom + grid.contentsMargins().bottom())
            chrome = max(0, self.height() - self.viewport().height())
            if minimum.width() > self.viewport().width():
                chrome = max(chrome, self.horizontalScrollBar().sizeHint().height())
            height += chrome
            if self.height() != height:
                self.setFixedHeight(height)
            grid.activate()
        finally:
            self._fitting = False


class DepthLadder(_DepthViewport):
    """Sell levels above buy levels, with the price in one central column."""
    def __init__(self, levels, language='ko', dark=False, parent=None, *, last_price=None, price_basis=''):
        levels = tuple(levels)
        self.current_label = None
        scale = max((row[side+'_qty'] for row in levels for side in ('ask', 'bid')
                     if row[side+'_qty'] is not None), default=0.)
        grid = QGridLayout()
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)
        headers = ('매도 수량', '가격', '매수 수량') if language == 'ko' else ('Sell size', 'Price', 'Buy size')
        for column, text in enumerate(headers):
            title = label('rowNote', wrap=True)
            title.setText(text)
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(title, 0, column)
        rows = []
        at = 1
        for side, ordered in (('ask', reversed(levels)), ('bid', levels)):
            if side == 'bid':
                names = {'quote': ('현재가', 'Last', '시세 조회의 현재가예요. 호가 조회 시각과 다를 수 있어요.',
                                   'Last price from the quote; its time may differ from the depth snapshot.'),
                         'daily_close': ('마지막 거래일 종가', 'Last daily close',
                                         '시세 조회값이 없어 마지막 거래일 종가를 보여줘요. 지금 호가와 시각이 달라요.',
                                         'No quote was received, so this is the last daily close; it is older than the depth.')}
                named = names.get(price_basis)
                if last_price is None or named is None:
                    gap = QWidget()
                    gap.setFixedHeight(6)
                    grid.addWidget(gap, at, 0, 1, 3)
                else:
                    # The price between the two sides, with rules either side, across all three columns.
                    line = QWidget()
                    row_box = QHBoxLayout(line)
                    row_box.setContentsMargins(0, 0, 0, 0)
                    row_box.setSpacing(6)
                    current = label('rowNote')
                    digits = 2 if last_price % 1 else 0
                    current.setText(named[0 if language == 'ko' else 1] + ' ' + _fmt(last_price, digits))
                    current.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    current.setProperty('depthRole', 'last')
                    current.setToolTip(named[2 if language == 'ko' else 3])
                    numbers(current)
                    for item in ('rule', current, 'rule'):
                        if item == 'rule':
                            rule = QFrame()
                            rule.setProperty('sd', 'rule')
                            rule.setFixedHeight(1)
                            row_box.addWidget(rule, 1, Qt.AlignmentFlag.AlignVCenter)
                        else:
                            row_box.addWidget(item, 0)
                    grid.addWidget(line, at, 0, 1, 3)
                    self.current_label = current
                at += 1
            for row in ordered:
                price, quantity = row[side+'_price'], row[side+'_qty']
                bar = DepthQuantityBar(side, quantity, scale, dark)
                value = label('rowValue')
                digits = 2 if price is not None and price % 1 else 0
                value.setText(_fmt(price, digits))
                value.setProperty('insightRole', 'value')
                value.setProperty('depthRole', 'price')
                value.setProperty('tone', 'down' if side == 'ask' else 'up')
                value.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
                value.setAlignment(Qt.AlignmentFlag.AlignCenter)
                numbers(value)
                blank = QWidget()
                blank.setMinimumWidth(42)
                cells = (bar, value, blank) if side == 'ask' else (blank, value, bar)
                for column, widget in enumerate(cells):
                    grid.addWidget(widget, at, column)
                rows.append(DepthRow(side, row['level'], price, quantity, value, bar, cells))
                at += 1
        super().__init__(grid)
        self.levels, self.scale, self.rows = levels, scale, tuple(rows)
        self.language, self.dark = language, bool(dark)
        grid.setVerticalSpacing(2)
        if parent is not None:
            self.setParent(parent)
        # setVisible follows parenting, so construction cannot expose child windows.
        self.set_expanded(False)

    def set_expanded(self, expanded):
        self.expanded = bool(expanded)
        limit = 10 if self.expanded else 3
        self.visible_rows = tuple(row for row in self.rows if row.level <= limit)
        for row in self.rows:
            for widget in row.widgets:
                widget.setVisible(row.level <= limit)
        self._fit_to_contents()
        self.updateGeometry()


class StockInsightsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("stockInsights")
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(0, 2, 0, 2)
        self.body.setSpacing(12)
        self.model = None
        self.covered_key_figures = frozenset()
        self.covered_sections = frozenset()
        self.setVisible(False)

    def _label(self, text, *, role="", tip="", numeric=False, wrap=True):
        # Use the very same roles and number face as the surrounding stock rows.
        sd = {"title": "cardTitle", "muted": "rowNote", "value": "rowValue"}.get(role, "body")
        widget = label(sd, wrap=wrap)
        widget.setText(text)
        if numeric or role == "value":
            numbers(widget)
        widget.setMinimumWidth(0)
        widget.setSizePolicy(QSizePolicy.Policy.Ignored if wrap else QSizePolicy.Policy.Minimum,
                             QSizePolicy.Policy.Preferred)
        widget.setProperty("insightRole", role)
        if tip:
            widget.setToolTip(tip)
        return widget

    def _card(self, title):
        frame = QFrame()
        frame.setProperty("insightCard", True)
        frame.setProperty("sd", "nowRow")
        body = QVBoxLayout(frame)
        body.setContentsMargins(6, 4, 6, 4)
        body.setSpacing(6)
        body.addWidget(self._label(title, role="title"))
        self.body.addWidget(frame)
        return body

    def _t(self, ko, en):
        return ko if self.language == "ko" else en

    def _note(self, body, short, detail):
        body.addWidget(self._label(short, role="muted", tip=detail))

    def _expand(self, body, title, widget):
        button = QPushButton()
        button.setProperty("sd", "link")
        button.setProperty("qg_literal", True)
        button.setText(title)
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setIcon(chevron("right", self.dark))
        button.setIconSize(QSize(14, 14))
        widget.hide()
        def toggle(checked):
            widget.setVisible(checked)
            button.setIcon(chevron("down" if checked else "right", self.dark))
        button.toggled.connect(toggle)
        body.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
        body.addWidget(widget)

    def _provenance(self, value):
        source = value.get("source") or self._t("출처 미제공", "Source unavailable")
        received = value.get("received_at") or self._t("수신 시각 미제공", "Receipt time unavailable")
        return self._t(f"{source} · 앱 수신 {received}", f"{source} · received {received}")

    def set_profile(self, profile, *, language="ko", dark=False, comparison=None):
        """Public integration entry. None clears; all other calls only render input."""
        self.language, self.dark = ("ko" if language == "ko" else "en"), bool(dark)
        while self.body.count():
            item = self.body.takeAt(0)
            widget = item.widget()
            if widget is not None:
                # Hide first: addWidget queued a show for a visible panel, and a card
                # detached before it runs would open as its own top-level window.
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self.model = build_insights(profile, comparison=comparison) if profile is not None else None
        self.covered_key_figures = frozenset()
        self.covered_sections = frozenset()
        self.setVisible(self.model is not None)
        if self.model is None:
            return
        palette = DARK if self.dark else LIGHT
        # A closer, partial stylesheet previously bypassed the page's sd roles.
        # Reuse its source of truth, including N3 sizes/weights and link controls.
        self.setStyleSheet(sheet(palette, self.dark))
        self._valuation()
        self._flows()
        self._shorts()
        self._book()
        self._executions()
        self.covered_key_figures = frozenset(m["key"] for m in self.model["metrics"] if m["value"] is not None)
        covered = set()
        if any(row["net_qty"] is not None or row["buy_fraction"] is not None
               for rows in self.model["flow_windows"].values() for row in rows):
            covered.add("flows")
        short = self.model["shorts"]
        if any(number(value) is not None for value in (short["ratio_pct"], short["qty"],
                                                     short["average"].get("short_ratio_pct"), short["average"].get("short_qty"))):
            covered.add("short_selling")
        self.covered_sections = frozenset(covered)

    def _valuation(self):
        from .metric_help import financial_help, valuation_reference
        body = self._card(self._t("기업 가치 한눈에", "Valuation at a glance"))
        missing = []
        for item in self.model["metrics"]:
            help_text = financial_help(item["key"], self.language)
            peer = self.model["comparisons"].get(item["key"])
            if item["value"] is None and item["key"] in ("roe", "psr") and not peer:
                missing.append((item["key"], help_text))
                continue
            box = QWidget()
            layout = QVBoxLayout(box)
            layout.setContentsMargins(0, 0, 0, 6)
            layout.setSpacing(4)
            # Name on the left, the supplied value on the right of one line; the
            # full-width strip below it (owner, 2026-11-24: PER·PBR 가독성).
            head = QHBoxLayout()
            head.setContentsMargins(0, 0, 0, 0)
            head.setSpacing(8)
            head.addWidget(self._label(item["key"].upper() + " · " + help_text.label, tip=help_text.hover), 1)
            shown = _fmt(item["value"]) + self._t("배", "x") if item["value"] is not None else self._t("미제공", "Unavailable")
            value = self._label(shown, role="value", wrap=False,
                                tip=help_text.hover + "\n" + self._provenance(item))
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            head.addWidget(value, 0)
            layout.addLayout(head)
            if item['key'] in ('per', 'pbr'):
                reference = valuation_reference(item['key'], item['value'], self.language)
                if item["value"] is not None and item["value"] > 0:
                    basis = self._t("주당순이익(EPS)", "earnings per share") if item["key"] == "per" else \
                        self._t("주당순자산(BPS)", "book value per share")
                    times = _fmt(item["value"])   # same digits as the value above, so a band edge reads alike
                    layout.addWidget(self._label(self._t(f"주가가 {basis}의 {times}배예요",
                                                         f"The price is {times} times {basis}"),
                                                 role="muted", tip=help_text.hover))
                strip = ValuationReferenceStrip(item['key'], reference, self.dark, box)
                layout.addWidget(strip)
                # The tinted middle segment already says "10–20"; the outer bands and a
                # missing value carry a caution worth a line of its own.
                if reference.band_index != 1:
                    layout.addWidget(self._label(reference.reading, role='muted', tip=reference.hover))
            if peer:
                group = self._t("테마", "Theme") if peer["kind"] == "theme" else self._t("업종", "Industry")
                unit = "%" if peer["unit"] == "%" else self._t("배", "x")
                mean = f"{_fmt(peer['mean'])}{unit}"
                sample = f"{peer['included']}/{peer['total']}"
                reading = self._t(f"{group} 평균 {mean} · {sample}개사", f"{group} average {mean} · {sample} companies")
                tip = self._t(f"{group} {peer['group_id']} · 산술평균 · 기준일 {peer['as_of']}",
                              f"{group} {peer['group_id']} · arithmetic mean · as of {peer['as_of']}")
                membership_source = self._t("구성 출처", "Membership source")
                tip += f"\n{peer['period']} · {peer['basis']}\n{membership_source} · {peer['source']}"
                if peer["excluded"]:
                    reasons = {"nonpositive_multiple": self._t("0 이하 배수", "Nonpositive multiple"),
                               "missing_value": self._t("값 미제공", "Value unavailable"),
                               "source_missing": self._t("출처 없음", "Source unavailable"),
                               "basis_mismatch": self._t("산정 기준 불일치", "Incompatible reporting basis")}
                    tip += "\n" + self._t("평균에서 제외한 종목", "Excluded from the average")
                    for symbol, reason in peer["excluded"]:
                        tip += f"\n{symbol} · {reasons[reason]}"
                self._note(layout, reading, tip)
            body.addWidget(box)
        if missing:
            names = "·".join(key.upper() for key, _ in missing)
            topic = "은" if missing[-1][0] == "psr" else "는"   # 피에스알은 · 알오이는
            body.addWidget(self._label(self._t(f"{names}{topic} 아직 연결되지 않았어요", f"{names} not connected yet"),
                                       role="muted", tip="\n\n".join(h.hover for _, h in missing)))
        detail = self._t('같은 업종·기간·회계 기준에서 이익의 지속성, ROE, 부채를 함께 살펴요. 성장주·경기민감주·금융업은 해석이 달라요.',
                         'Compare consistent industry, period and accounting bases, earnings durability, ROE and debt. Growth, cyclical and financial businesses differ.')
        detail += "\n" + self._t("PER·PBR은 공급자 제공값이에요. 회계 기준·기준일은 확인되지 않았어요. ROE·PSR 수치는 아직 연결되지 않았어요.",
                                 "PER/PBR are provider values with unconfirmed accounting/reference basis. ROE/PSR values are not connected.")
        if self.model["comparisons"]:
            as_of = next(iter(self.model["comparisons"].values()))["as_of"]
            detail += "\n" + self._t(f"집단 평균 기준일 {as_of}", f"Peer averages as of {as_of}")
        else:
            detail += "\n" + self._t("비교 평균은 미제공이에요. 확인된 비교 집합과 같은 기간·단위의 지표가 필요해요.",
                                     "Peer average unavailable: verified membership and matching period/unit data are needed.")
        self._note(body, self._t('구간은 설명용 예시예요 · 낮은 배수만으로 우량 판단은 어려워요',
                                 'Illustrative ranges · low multiples alone do not mean quality'), detail)
        guide = self._label(self._t(
            "PER은 같은 업종 기업의 같은 기간 이익으로 비교해요. 이번에만 큰 이익이 나면 PER이 낮아 보여요. "
            "적자이거나 이익이 0이면 이 배수로 싼지 판단하기 어려워요.\n\n"
            "PBR 1배는 주가와 장부상 주당 순자산이 같다는 뜻이에요. 1배 아래라면 회사가 자기 자본으로 "
            "이익을 얼마나 내는지(ROE), 손실이 이어지는지 함께 보세요.",
            "For PER, compare companies in the same industry using earnings from the same period. A one-off "
            "profit can make PER look low. With a loss or zero earnings, PER is not a useful price comparison.\n\n"
            "At 1x PBR, price equals book value per share. Below 1x, check how much profit the company earns "
            "on its own equity (ROE) and whether losses persist."), role="muted")
        self._expand(body, self._t("PER·PBR 읽는 법", "Reading PER and PBR"), guide)

    def _flow_daily_rows(self, body, days):
        """Owner, 2026-11-24: 외국인·개인 일별 순매수 막대 (one column per session)."""
        labels = {"individual": self._t("개인", "Individuals"), "foreign": self._t("외국인", "Foreign"),
                  "institution": self._t("기관", "Institutions")}
        windows = self.model["flow_windows"]
        sums = {length: {row["group"]: row for row in rows} for length, rows in windows.items()}
        scale = max((abs(day[group]) for day in days for group in labels if day[group] is not None), default=0.)
        self.flow_bars = {}
        for group in ("individual", "foreign", "institution"):
            head = QHBoxLayout()
            head.setContentsMargins(0, 0, 0, 0)
            head.setSpacing(6)
            head.addWidget(self._label(labels[group], wrap=False), 1)
            row = sums[max(sums)].get(group) if sums else None
            tip = self._t("순매수 = 매수 수량 − 매도 수량 (주)", "Net = bought − sold (shares)")
            if row is not None and row["buy_fraction"] is not None:
                buy_text, sell_text = display_split(row["buy_fraction"])
                tip += self._t(f"\n매수·매도 양쪽 자료가 있는 {row['reported_pairs']}/{row['sessions']}일 기준 · 이 투자자 거래량 중 매수 {buy_text} · 매도 {sell_text}",
                               f"\nOver the {row['reported_pairs']}/{row['sessions']} days with both sides: buy {buy_text} · sell {sell_text} of this group's volume")
            if row is not None:
                tip += "\n" + self._provenance(row)
            shown = False
            # Each window's sum in its own tone: 20 days can be net buying while 5 days are net selling.
            for length in sorted(sums, reverse=True):
                net = sums[length].get(group, {}).get("net_qty")
                if net is None:
                    continue
                if shown:
                    head.addSpacing(4)          # with the layout's 6 px: a clear gap, no separator glyph
                reported = sums[length][group]["net_reported"]
                exact = self._t(f"{length}일 순매수 {net:+,.0f}주 · 자료 {reported}/{length}일",
                                f"{length}-day net {net:+,.0f} shares · reported {reported}/{length} days")
                value = self._label(self._t(f"{length}일 {_shares(net, 'ko')}", f"{length}d {_shares(net, 'en')}"),
                                    role="value", wrap=False, tip=exact + "\n" + tip)
                value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if net:
                    value.setProperty("tone", "up" if net > 0 else "down")
                head.addWidget(value, 0)
                shown = True
            if not shown:
                head.addWidget(self._label(self._t("자료 미제공", "Data unavailable"), role="muted", wrap=False), 0)
            body.addLayout(head)

            def describe(day, value, name=labels[group]):
                if value is None:
                    return self._t(f"{day} · {name} 자료 없음", f"{day} · {name} no data")
                verb = self._t("순매수" if value >= 0 else "순매도", "net buy" if value >= 0 else "net sell")
                return self._t(f"{day} · {name} {verb} {abs(value):,.0f}주", f"{day} · {name} {verb} {abs(value):,.0f} shares")
            bars = DailyNetBars(((day["date"], day[group]) for day in days), scale, self.dark, describe)
            ups = sum(1 for day in days if day[group] is not None and day[group] > 0)
            downs = sum(1 for day in days if day[group] is not None and day[group] < 0)
            bars.setAccessibleName(self._t(f"{labels[group]} 일별 순매수 막대", f"{labels[group]} daily net buying"))
            bars.setAccessibleDescription(self._t(f"{len(days)}일 중 순매수 {ups}일 · 순매도 {downs}일",
                                                  f"{ups} net-buy and {downs} net-sell days of {len(days)}"))
            self.flow_bars[group] = bars
            body.addWidget(bars)
        axis = QHBoxLayout()
        axis.setContentsMargins(0, 0, 0, 0)
        first, last = self._label(days[0]["date"], role="muted", wrap=False), self._label(days[-1]["date"], role="muted", wrap=False)
        last.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        axis.addWidget(first, 1)
        axis.addWidget(last, 1)
        body.addLayout(axis)

    def _flow_rows(self, body, rows):
        scale = max((abs(row["net_qty"]) for row in rows if row["net_qty"] is not None), default=1.0)
        labels = {"individual": self._t("개인", "Individuals"), "foreign": self._t("외국인", "Foreign"), "institution": self._t("기관", "Institutions")}
        for row in rows:
            if row["buy_fraction"] is not None:
                buy_text, sell_text = display_split(row["buy_fraction"])
                reading = self._t(f"매수 {buy_text} · 매도 {sell_text}",
                                  f"Buy {buy_text} · sell {sell_text}")
                reading += self._t(f" · {row['reported_pairs']}/{row['sessions']}일", f" · {row['reported_pairs']}/{row['sessions']} days")
            elif row["net_qty"] is not None:
                reading = self._t(f"순매수 {row['net_qty']:+,.0f}주 · 매수/매도 비율 미제공",
                                  f"Net {row['net_qty']:+,.0f} shares · gross split unavailable")
            else:
                reading = self._t("자료 미제공", "Data unavailable")
            body.addWidget(self._label(labels[row["group"]] + " · " + reading))
            bar = FlowBar()
            bar.set_reading(row["buy_fraction"], row["net_qty"], scale, self.dark)
            hint = self._t(f"매수 {_fmt(row['buy_qty'], 0)}주 / 매도 {_fmt(row['sell_qty'], 0)}주\n동일 날짜 양쪽 자료 {row['reported_pairs']}/{row['sessions']}거래일",
                           f"Buy {_fmt(row['buy_qty'], 0)} / sell {_fmt(row['sell_qty'], 0)} shares\nMatched daily pairs {row['reported_pairs']}/{row['sessions']}")
            hint += self._t(f"\n순매수 {_fmt(row['net_qty'], 0)}주 · 보고 {row['net_reported']}/{row['sessions']}거래일",
                            f"\nNet {_fmt(row['net_qty'], 0)} shares · reported {row['net_reported']}/{row['sessions']} sessions")
            bar.setToolTip(hint + f"\n{row['first_date']} – {row['last_date']}\n" + self._provenance(row))
            body.addWidget(bar)
        dated = next((r for r in rows if r["first_date"]), None)
        if dated:
            body.addWidget(self._label(f"{dated['first_date']} – {dated['last_date']}", role="muted"))

    def _flows(self):
        body = self._card(self._t("누가 사고팔았나요?", "Who bought and sold?"))
        days = self.model.get("flow_daily") or ()
        self.flow_bars = {}
        if days:
            self._flow_daily_rows(body, days)
            self._note(body, self._t("막대 하나가 하루 · 위 빨강 순매수 · 아래 파랑 순매도",
                                     "One column per day · up red net buying · down blue net selling"),
                       self._t("순매수는 그날 매수 수량에서 매도 수량을 뺀 값(주)이에요. 세 투자자 막대는 같은 눈금이라 길이를 서로 비교할 수 있어요. "
                               "점은 그날 자료가 없다는 뜻이에요. 막대에 마우스를 올리면 날짜와 수량이 보여요. 순매수가 많아도 주가 상승이 보장되지는 않아요.",
                               "Net buying is the day's bought minus sold shares. All three groups share one scale, so lengths compare across groups. "
                               "A dot means no data that day. Hover a column for its date and quantity. Net buying does not guarantee a price rise."))
            return
        self._flow_rows(body, self.model["flows"])
        windows = self.model["flow_windows"]
        for length in sorted(windows):
            if length == max(windows):
                continue
            extra = QWidget()
            layout = QVBoxLayout(extra)
            layout.setContentsMargins(0, 0, 0, 0)
            self._flow_rows(layout, windows[length])
            self._expand(body, self._t(f"최근 {length}거래일도 보기", f"Also show last {length} sessions"), extra)
        self._note(body, self._t("각 투자자 거래량 안의 비중 · 순매수와 달라요", "Within-group split · different from net buying"),
                   self._t("비율은 각 투자자 거래량 안의 매수·매도 비중이에요. 양쪽 수량이 없으면 순매수만 보여요. 순매수와 매수비중은 다르며, 매수가 많아도 주가 상승이 보장되지는 않아요.",
                           "Each split is within that group's trading quantity. Missing gross pairs show net shares instead. Net buying and buy share differ; neither guarantees a price rise."))

    def _shorts(self):
        body = self._card(self._t("공매도는 거래 흐름과 함께", "Read short sales in context"))
        row = self.model["shorts"]
        if row["ratio_pct"] is None and row["qty"] is None:
            body.addWidget(self._label(self._t("일별 공매도 자료 미제공", "Daily short-sale data unavailable")))
        else:
            parts = []
            if row["ratio_pct"] is not None:
                parts.append(self._t(f"비중 {_fmt(row['ratio_pct'])}%", f"Share {_fmt(row['ratio_pct'])}%"))
            if row["qty"] is not None:
                parts.append(self._t(f"수량 {_fmt(row['qty'], 0)}주", f"Volume {_fmt(row['qty'], 0)} shares"))
            body.addWidget(self._label(" · ".join(parts), role="value"))
            body.addWidget(self._label(row["date"], role="muted", tip=self._provenance(row)))
        avg = row["average"]
        if row["ratio_pct"] is not None or avg.get("short_ratio_pct") is not None:
            reading = self._label(self._short_comparison(row), role="muted")
            reading.setObjectName("shortShareComparison")
            body.addWidget(reading)
        if number(avg.get("short_ratio_pct")) is not None or number(avg.get("short_qty")) is not None:
            detail = QWidget()
            layout = QVBoxLayout(detail)
            layout.setContentsMargins(0, 0, 0, 0)
            if number(avg.get("short_ratio_pct")) is not None:
                layout.addWidget(self._label(self._t(f"평균 비중 {_fmt(avg['short_ratio_pct'])}% · 보고 {avg.get('reported_ratio', 0)}일",
                                                    f"Mean share {_fmt(avg['short_ratio_pct'])}% · {avg.get('reported_ratio', 0)} reported days")))
            if number(avg.get("short_qty")) is not None:
                layout.addWidget(self._label(self._t(f"평균 수량 {_fmt(avg['short_qty'], 0)}주 · 보고 {avg.get('reported_qty', 0)}일",
                                                    f"Mean volume {_fmt(avg['short_qty'], 0)} shares · {avg.get('reported_qty', 0)} reported days")))
            layout.addWidget(self._label(f"{avg.get('first_date', '')} – {avg.get('last_date', '')}", role="muted", tip=self._provenance(row)))
            self._expand(body, self._t(f"최근 {avg.get('sessions', 0)}거래일 단순평균", f"Arithmetic average · {avg.get('sessions', 0)} sessions"), detail)
        self._note(body, self._t("거래량 중 빌린 주식을 판 비중이에요. 평소보다 높으면 주가와 전체 거래량도 함께 보세요.",
                                "This is the share of trading volume sold short. If it rises above its usual level, check the price and total volume too."),
                   self._t("그날 거래 중 공매도 비중이에요. 공매도 잔고·대차 잔고와 달라요. 가격 하락·거래량 변화와 같이 살피되, 헤지·차익거래도 있어 하락 신호로 단정하지 마세요.",
                           "This is the day's short-sale trading share, not outstanding short or borrowed positions. Compare price/volume context; hedging and arbitrage mean it is not a certain bearish signal."))

    def _short_comparison(self, row):
        avg = row["average"]
        sessions, reported = avg.get("sessions"), avg.get("reported_ratio")
        latest, mean = row["ratio_pct"], avg.get("short_ratio_pct")
        try:
            first = date.fromisoformat(avg.get("first_date"))
            last = date.fromisoformat(avg.get("last_date"))
        except (TypeError, ValueError):
            first = last = None
        if (latest is None or mean is None or type(reported) is not int or type(sessions) is not int
                or not 2 <= reported <= sessions or first is None or first >= last
                or row["date"] != last.isoformat()):
            return self._t("같은 기간에 보고된 비중이 충분해야 평균과 비교할 수 있어요.",
                           "A comparison needs reported shares from the same period.")
        baseline = self._t(f"최근 {sessions}거래일 중 {reported}일 평균 {_fmt(mean)}%",
                           f"{_fmt(mean)}% average over {reported} reported days in {sessions} sessions")
        diff = round(latest, 2) - round(mean, 2)
        if diff == 0:
            return self._t(f"{baseline}와 같아요.", f"Matches the {baseline}.")
        delta = _fmt(abs(diff))
        if diff > 0:
            return self._t(f"{baseline}보다 {delta}%p 높아요.", f"{delta} pp above the {baseline}.")
        return self._t(f"{baseline}보다 {delta}%p 낮아요.", f"{delta} pp below the {baseline}.")

    def _book(self):
        body = self._card(self._t("호가 · 조회 스냅숏", "Order book · REST snapshot"))
        book = self.model["orderbook"]
        self.depth_ladder = self.depth_toggle = self.depth_totals = self.depth_share = None
        if book is None:
            body.addWidget(self._label(self._t("호가 자료 미제공", "Depth unavailable")))
        else:
            ladder = DepthLadder(book['levels'], self.language, self.dark,
                                 last_price=self.model.get('last_price'),
                                 price_basis=self.model.get('price_basis', ''))
            self.depth_ladder = ladder
            body.addWidget(ladder)
            best = book["levels"][0]
            ask, bid = best["ask_price"], best["bid_price"]
            if (ask is not None and bid is not None and ask >= bid
                    and best["ask_qty"] > 0 and best["bid_qty"] > 0):
                spread = ask - bid
                gap = _fmt(spread, 0 if spread.is_integer() else 2)
                spread_text = self._t(f"최우선 매도·매수 가격 차이 {gap}원", f"Best ask–bid spread: KRW {gap}")
            else:
                spread_text = self._t("최우선 호가 차이 확인 불가", "Best ask–bid spread unavailable")
            reading = self._label(spread_text, role="muted",
                                  tip=self._t("가장 낮은 매도 가격에서 가장 높은 매수 가격을 뺀 값이에요.",
                                              "The lowest sell price minus the highest buy price."))
            reading.setObjectName("orderBookSpread")
            body.addWidget(reading)
            self._depth_totals(body, book)
            toggle = QPushButton()
            toggle.setProperty('sd', 'link')
            toggle.setProperty('qg_literal', True)
            toggle.setCheckable(True)
            toggle.setCursor(Qt.CursorShape.PointingHandCursor)
            toggle.setIconSize(QSize(14, 14))
            self.depth_toggle = toggle
            def expand(checked):
                ladder.set_expanded(checked)
                toggle.setText(self._t('3단계로 접기' if checked else '10단계 펼치기',
                                       'Show 3 levels' if checked else 'Show 10 levels'))
                toggle.setIcon(chevron('down' if checked else 'right', self.dark))
            toggle.toggled.connect(expand)
            expand(False)
            body.addWidget(toggle, 0, Qt.AlignmentFlag.AlignLeft)
            self._note(body, self._t('위 파란 막대 매도 대기 · 아래 빨간 막대 매수 대기',
                                    'Blue above: waiting sells · red below: waiting buys'),
                       self._t('모든 10단계의 같은 최대 수량으로 막대 길이를 비교해요. 펼쳐도 기준은 바뀌지 않아요. 0은 관측된 빈 잔량이며 —는 자료가 없는 값이에요. 색과 위치는 매수·매도 측 구분이지 전망이 아니에요.',
                               'Every bar uses the same maximum across the supplied 10 levels on both sides. Expanding keeps that scale. Zero is observed empty quantity; — means missing. Colours and positions identify sides, not forecasts.'))
            body.addWidget(self._label(self._t("가격 원 · 잔량 주", "Prices KRW · sizes shares"), role="muted"))
            body.addWidget(self._label(self._t(f"공급자 시각 {book['provider_time'] or '미제공'} · 날짜 미제공",
                                              f"Provider clock {book['provider_time'] or 'unavailable'} · date unavailable"), role="muted", tip=self._provenance(book)))
        self._note(body, self._t("같은 종목에서 호가 차이가 클수록 즉시 사고팔 때 가격 부담이 커져요. 대기 주문은 취소될 수 있어 실제 체결도 함께 보세요.",
                                "A wider spread in the same stock makes an immediate round trip more costly. Waiting orders can be cancelled. Check actual trades too."),
                   self._t("잔량은 아직 체결되지 않은 주문이라 취소·이동할 수 있어요. 큰 매수벽을 확정 지지로 보지 말고, 가격 간격과 실제 체결을 함께 보세요. 예상체결가는 실제 체결과 달라요.",
                           "Depth is unfilled orders that can move or be cancelled. A large bid wall is not confirmed support: compare the spread and actual trades. Indicative auction prices are not executions."))

    def _depth_totals(self, body, book):
        """Waiting sell size against waiting buy size. Provider totals when supplied;
        otherwise the sum of the supplied levels, labelled as such."""
        ask, bid = book.get('total_ask_qty'), book.get('total_bid_qty')
        provided = ask is not None and bid is not None
        if not provided:
            asks = [r['ask_qty'] for r in book['levels'] if r['ask_qty'] is not None]
            bids = [r['bid_qty'] for r in book['levels'] if r['bid_qty'] is not None]
            if not asks or not bids:
                self.depth_totals = None
                return
            ask, bid = float(sum(asks)), float(sum(bids))
        self.depth_totals = (ask, bid, provided)
        name = self._t('총잔량' if provided else '10단계 잔량 합', 'Total depth' if provided else 'Sum of 10 levels')
        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(8)
        sell = self._label(self._t(f'매도 {_fmt(ask, 0)}', f'Sell {_fmt(ask, 0)}'), role='value', wrap=False)
        sell.setProperty('tone', 'down')
        buy = self._label(self._t(f'매수 {_fmt(bid, 0)}', f'Buy {_fmt(bid, 0)}'), role='value', wrap=False)
        buy.setProperty('tone', 'up')
        buy.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        middle = self._label(name, role='muted', wrap=False)
        middle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # On a narrow column the name gives way; the two totals keep their full digits.
        middle.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        middle.setToolTip(name)
        head.addWidget(sell, 0)
        head.addWidget(middle, 1)
        head.addWidget(buy, 0)
        body.addLayout(head)
        bar = SideShareBar(ask, bid, self.dark)
        total = ask + bid
        if total > 0:
            ask_text, bid_text = display_split(ask / total)   # complementary tenths: always 100.0% together
            bar.setToolTip(self._t(f'{name} 중 매도 {ask_text} · 매수 {bid_text}\n대기 주문이라 취소·이동할 수 있어요.',
                                   f'{name}: sell {ask_text} · buy {bid_text}\nWaiting orders can be cancelled or moved.'))
            for widget in (sell, buy):
                widget.setToolTip(bar.toolTip())
        self.depth_share = bar
        body.addWidget(bar)

    def _executions(self):
        body = self._card(self._t("체결강도 · 조회 스냅숏", "Execution strength · REST snapshot"))
        snapshot = self.model["executions"]
        reading = next((r for r in snapshot["rows"] if r["strength"] is not None), None) if snapshot else None
        if reading is None:
            body.addWidget(self._label(self._t("체결강도 자료 미제공", "Execution strength unavailable")))
        else:
            body.addWidget(self._label(_fmt(reading["strength"]), role="value", tip=self._provenance(snapshot)))
            body.addWidget(self._label(self._t(f"공급자 시각 {reading['provider_time'] or '미제공'} · 날짜 미제공",
                                              f"Provider clock {reading['provider_time'] or 'unavailable'} · date unavailable"), role="muted"))
        self._note(body, self._t("제공값 · 산식·단위 미확인 · 자동으로 새로 고치지 않아요", "Provider value · formula/unit unconfirmed · not streamed"),
                   self._t("공급자가 제공한 체결강도 값이에요. 이 연결의 산식·단위는 확인되지 않았으므로 특정 숫자를 매수·매도 기준으로 쓰지 않아요. 주가가 실제로 전진하는지와 거래량을 같이 보세요. 자동 실시간 갱신은 아니에요.",
                           "This is the provider's strength value; its formula/unit is unconfirmed here, so no fixed number is a trading trigger. Compare actual price progress and volume. This is not an automatically streamed reading."))
