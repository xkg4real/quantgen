"""Compact educational valuation, investor-flow and REST microstructure cards.

The parent supplies an already-loaded profile. This widget never starts a worker,
timer, provider, credential lookup or network request.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from PyQt6.QtCore import QEvent, QRect, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import (QFrame, QGridLayout, QLabel, QPushButton, QScrollArea,
                             QSizePolicy, QVBoxLayout, QWidget)

from core.market.detail_insights import build_insights, number
from core.theme import DARK, LIGHT
from .stock_detail_style import chevron, label, numbers, sheet
from .typography import tone_colors


def _fmt(value, digits=2):
    n = number(value)
    return "—" if n is None else f"{n:,.{digits}f}"


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
    """A neutral position guide, not a red/green investment rating."""
    def __init__(self, metric, reference, dark, parent=None):
        super().__init__(parent)
        self.metric, self.reference, self.dark = metric, reference, bool(dark)
        self.setFixedHeight(34)
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
        painter.setFont(number_font(scaled_font(self.font(), 12, 400)))
        width = max(0, self.width()-2)
        painter.setPen(QColor(palette.muted))
        for i, text in enumerate(self.reference.labels):
            painter.drawText(QRectF(1+i*width/3, 0, width/3, 18),
                             int(Qt.AlignmentFlag.AlignCenter), text)
        track = QRectF(1, 24, width, 4)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(palette.surface_2))
        painter.drawRoundedRect(track, 2, 2)
        painter.setPen(QColor(palette.border))
        for fraction in (1/3, 2/3):
            x = 1+width*fraction
            painter.drawLine(round(x), 23, round(x), 29)
        if self.reference.position is not None:
            x = 1+width*self.reference.position
            painter.setPen(QColor(palette.accent))
            painter.drawLine(round(x), 20, round(x), 31)
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
            width = self.width()*self.fraction
            start = self.width()-width if self.side == 'ask' else 0
            color = QColor(self.color)
            color.setAlpha(56 if self.dark else 48)
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
    def __init__(self, levels, language='ko', dark=False, parent=None):
        levels = tuple(levels)
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
                gap = QWidget()
                gap.setFixedHeight(6)
                grid.addWidget(gap, at, 0, 1, 3)
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
        grid = QGridLayout()
        grid.setSpacing(9)
        for index, item in enumerate(self.model["metrics"]):
            help_text = financial_help(item["key"], self.language)
            box = QWidget()
            layout = QVBoxLayout(box)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(3)
            layout.addWidget(self._label(item["key"].upper() + " · " + help_text.label, tip=help_text.hover))
            shown = _fmt(item["value"]) + self._t("배", "x") if item["value"] is not None else self._t("미제공", "Unavailable")
            layout.addWidget(self._label(shown, role="value", tip=help_text.hover + "\n" + self._provenance(item)))
            if item['key'] in ('per', 'pbr'):
                reference = valuation_reference(item['key'], item['value'], self.language)
                strip = ValuationReferenceStrip(item['key'], reference, self.dark, box)
                layout.addWidget(strip)
                layout.addWidget(self._label(reference.reading, role='muted', tip=reference.hover))
            grid.addWidget(box, index // 2, index % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        body.addLayout(grid)
        self._note(body, self._t('참고 구간 예시 · 낮은 배수만으로 우량 판단은 어려워요',
                                'Illustrative ranges · low multiples alone do not mean quality'),
                   self._t('같은 업종·기간·회계 기준에서 이익의 지속성, ROE, 부채를 함께 살펴요. 성장주·경기민감주·금융업은 해석이 달라요.',
                           'Compare consistent industry, period and accounting bases, earnings durability, ROE and debt. Growth, cyclical and financial businesses differ.'))
        self._note(body, self._t("PER·PBR 제공값 · ROE·PSR 수치 미연결", "Provider PER/PBR · ROE/PSR not connected"),
                   self._t("PER·PBR은 공급자 제공값이에요. 회계 기준·기준일은 확인되지 않았어요. ROE·PSR 수치는 아직 연결되지 않았어요.",
                           "PER/PBR are provider values with unconfirmed accounting/reference basis. ROE/PSR values are not connected."))
        peer = self.model["comparison"]
        if peer["status"] == "available":
            group = self._t("테마", "Theme") if peer["kind"] == "theme" else self._t("업종", "Industry")
            body.addWidget(self._label(f"{group} {peer['metric'].upper()} · {_fmt(peer['mean'])} {peer['unit']} · {peer['included']}/{peer['total']}",
                                      tip=f"{peer['method']} · {peer['period']} · {peer['basis']} · {peer['as_of']}\n{peer['source']}\n{peer['excluded']}"))
        else:
            body.addWidget(self._label(self._t("비교 평균은 미제공이에요. 확인된 비교 집합과 같은 기간·단위의 지표가 필요해요.",
                                             "Peer average unavailable: verified membership and matching period/unit data are needed."), role="muted"))

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
        self._note(body, self._t("거래 비중이며 잔고가 아니에요 · 자세히는 올려보세요", "Trading share, not outstanding positions · hover for context"),
                   self._t("그날 거래 중 공매도 비중이에요. 공매도 잔고·대차 잔고와 달라요. 가격 하락·거래량 변화와 같이 살피되, 헤지·차익거래도 있어 하락 신호로 단정하지 마세요.",
                           "This is the day's short-sale trading share, not outstanding short or borrowed positions. Compare price/volume context; hedging and arbitrage mean it is not a certain bearish signal."))

    def _book(self):
        body = self._card(self._t("호가 · 조회 스냅숏", "Order book · REST snapshot"))
        book = self.model["orderbook"]
        self.depth_ladder = self.depth_toggle = None
        if book is None:
            body.addWidget(self._label(self._t("호가 자료 미제공", "Depth unavailable")))
        else:
            ladder = DepthLadder(book['levels'], self.language, self.dark)
            self.depth_ladder = ladder
            body.addWidget(ladder)
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
            self._note(body, self._t('파란 막대는 매도 · 빨간 막대는 매수 대기 수량',
                                    'Blue: waiting sells · red: waiting buys'),
                       self._t('모든 10단계의 같은 최대 수량으로 막대 길이를 비교해요. 펼쳐도 기준은 바뀌지 않아요. 0은 관측된 빈 잔량이며 —는 자료가 없는 값이에요. 색과 위치는 매수·매도 측 구분이지 전망이 아니에요.',
                               'Every bar uses the same maximum across the supplied 10 levels on both sides. Expanding keeps that scale. Zero is observed empty quantity; — means missing. Colours and positions identify sides, not forecasts.'))
            body.addWidget(self._label(self._t("가격 원 · 잔량 주", "Prices KRW · sizes shares"), role="muted"))
            body.addWidget(self._label(self._t(f"공급자 시각 {book['provider_time'] or '미제공'} · 날짜 미제공",
                                              f"Provider clock {book['provider_time'] or 'unavailable'} · date unavailable"), role="muted", tip=self._provenance(book)))
        self._note(body, self._t("잔량은 체결 전 주문 · 취소될 수 있어요", "Depth is unfilled orders and may be cancelled"),
                   self._t("잔량은 아직 체결되지 않은 주문이라 취소·이동할 수 있어요. 큰 매수벽을 확정 지지로 보지 말고, 가격 간격과 실제 체결을 함께 보세요. 예상체결가는 실제 체결과 달라요.",
                           "Depth is unfilled orders that can move or be cancelled. A large bid wall is not confirmed support: compare the spread and actual trades. Indicative auction prices are not executions."))

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
        self._note(body, self._t("제공값 · 산식/단위 미확인 · 실시간 자동 갱신 아님", "Provider value · formula/unit unconfirmed · not streamed"),
                   self._t("공급자가 제공한 체결강도 값이에요. 이 연결의 산식·단위는 확인되지 않았으므로 특정 숫자를 매수·매도 기준으로 쓰지 않아요. 주가가 실제로 전진하는지와 거래량을 같이 보세요. 자동 실시간 갱신은 아니에요.",
                           "This is the provider's strength value; its formula/unit is unconfirmed here, so no fixed number is a trading trigger. Compare actual price progress and volume. This is not an automatically streamed reading."))
