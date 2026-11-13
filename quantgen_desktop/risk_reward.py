"""Editable chart price scenarios, with native text and keyboard alternatives to dragging."""
from dataclasses import replace
import math

from PyQt6.QtCore import QObject, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFrame, QGridLayout,
                            QHBoxLayout, QPushButton, QVBoxLayout)

from core.market.risk_reward import RiskRewardPlan
from .stock_detail_style import label


class RiskRewardTool(QObject):
    def __init__(self, view):
        super().__init__(view)
        self.view, self.chart = view, view.chart.chart
        self.plan = None
        self.scale_levels = ()
        self._instrument = None
        self._drag = None
        self.panel = QFrame()
        self.panel.setProperty("sd", "notesBox")
        self.panel.setObjectName("riskRewardPanel")
        box = QVBoxLayout(self.panel)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(8)
        head = QHBoxLayout()
        self.title = label("cardTitle")
        self.close = QPushButton("×")
        self.close.setProperty("sd", "mini")
        self.close.clicked.connect(self.panel.hide)
        head.addWidget(self.title, 1)
        head.addWidget(self.close)
        box.addLayout(head)
        self.toggle = QCheckBox()
        self.toggle.toggled.connect(self._toggle)
        box.addWidget(self.toggle)
        self.direction = QComboBox()
        self.direction.addItem("", "long")
        self.direction.addItem("", "short")
        self.direction.currentIndexChanged.connect(self._direction)
        box.addWidget(self.direction)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        self.fields, self.labels = {}, {}
        for row, key in enumerate(("entry", "stop", "target")):
            title, edit = label("muted"), QDoubleSpinBox()
            edit.setObjectName("riskReward" + key.title())
            edit.setDecimals(4)
            edit.setRange(0.0001, 1e12)
            edit.setGroupSeparatorShown(True)
            edit.setKeyboardTracking(False)
            edit.valueChanged.connect(self._edited)
            grid.addWidget(title, row, 0)
            grid.addWidget(edit, row, 1)
            self.labels[key], self.fields[key] = title, edit
        grid.setColumnStretch(1, 1)
        box.addLayout(grid)
        self.result = label("body", wrap=True, selectable=True)
        self.result.setObjectName("riskRewardResult")
        box.addWidget(self.result)
        self.hint = label("muted", wrap=True)
        box.addWidget(self.hint)
        actions = QHBoxLayout()
        self.reset, self.remove = QPushButton(), QPushButton()
        self.reset.clicked.connect(self.seed)
        self.remove.clicked.connect(self.clear)
        for button in (self.reset, self.remove):
            button.setProperty("sd", "text")
            actions.addWidget(button)
        box.addLayout(actions)
        for widget in (self.panel, self.title, self.toggle, self.direction, self.result, self.hint,
                       self.close, self.reset, self.remove, *self.labels.values()):
            widget.setProperty("qg_literal", True)
        self.panel.hide()
        self.chart.risk_tool = self
        canvas = self.chart
        view.destroyed.connect(lambda: setattr(canvas, "risk_tool", None))
        self.chart.layout_changed.connect(self.sync)
        self.translate()

    def words(self, ko, en):
        return ko if self.view.ctx.language == "ko" else en

    @property
    def available(self):
        snapshot = self.chart.snapshot
        return bool(snapshot and snapshot.candles and self.chart.detail
                    and snapshot.request.instrument == self.view.instrument
                    and math.isfinite(snapshot.candles[-1].close) and snapshot.candles[-1].close > 0)

    @property
    def active(self):
        return self.available and self.plan is not None and self.toggle.isChecked()

    @property
    def price_levels(self):
        return self.scale_levels if self.active else ()

    def sync(self, *_):
        instrument = self.view.instrument
        if instrument != self._instrument:
            self._instrument = instrument
            self.plan, self.scale_levels, self._drag = None, (), None
            self.toggle.blockSignals(True)
            self.toggle.setChecked(False)
            self.toggle.blockSignals(False)
        available = self.available
        self.reset.setEnabled(available)
        self.toggle.setEnabled(available and self.plan is not None)
        self.remove.setEnabled(self.plan is not None)
        for widget in (self.direction, *self.fields.values()):
            widget.setEnabled(available and self.plan is not None)
        self._result()
        self.chart.update()

    def open(self):
        self.sync()
        self.panel.show()
        if self.plan is None and self.available:
            self.seed()
        self.fields["entry"].setFocus(Qt.FocusReason.OtherFocusReason)

    def seed(self):
        if not self.available:
            return
        entry = self.chart.snapshot.candles[-1].close
        domestic = self.view.instrument.asset == "domestic_stock"
        decimals = 0 if domestic else (8 if entry < 1 else 4)
        minimum = 10 ** -decimals
        for edit in self.fields.values():
            edit.blockSignals(True)
            edit.setDecimals(decimals)
            edit.setMinimum(minimum)
            edit.setSingleStep(max(minimum, round(entry * .001, decimals)))
            edit.blockSignals(False)
        # These are editable starting distances, never model targets or recommendations.
        risk = min(entry * .25, max(minimum, entry * .01))
        sign = 1 if self.direction.currentData() == "long" else -1
        self.toggle.blockSignals(True)
        self.toggle.setChecked(True)
        self.toggle.blockSignals(False)
        self.set_plan(RiskRewardPlan(self.direction.currentData(), entry, entry - sign * risk,
                                    entry + sign * risk * 2), fit=True)

    def set_plan(self, plan, *, fit=False):
        decimals = self.fields["entry"].decimals()
        plan = replace(plan, **{key: round(getattr(plan, key), decimals) for key in self.fields})
        if any(not math.isfinite(getattr(plan, k)) or not 0 < getattr(plan, k) <= edit.maximum()
               for k, edit in self.fields.items()):
            return
        self.plan = plan
        for key, edit in self.fields.items():
            edit.blockSignals(True)
            edit.setValue(getattr(plan, key))
            edit.blockSignals(False)
        if fit:
            self.scale_levels = (plan.entry, plan.stop, plan.target)
            self.chart.redraw()
        self.sync()

    def _edited(self, *_):
        if self.plan is not None:
            self.set_plan(RiskRewardPlan(self.direction.currentData(),
                          **{k: v.value() for k, v in self.fields.items()}), fit=True)

    def _direction(self, *_):
        if self.plan is None:
            return
        p = self.plan
        sign = 1 if self.direction.currentData() == "long" else -1
        minimum = self.fields["entry"].minimum()
        mirrored = RiskRewardPlan(self.direction.currentData(), p.entry,
                                  p.entry - sign * max(minimum, abs(p.entry - p.stop)),
                                  p.entry + sign * max(minimum, abs(p.target - p.entry)))
        if min(mirrored.stop, mirrored.target) <= 0 or max(mirrored.stop, mirrored.target) > self.fields["entry"].maximum():
            mirrored = replace(p, direction=self.direction.currentData())
        self.set_plan(mirrored, fit=True)

    def _toggle(self, *_):
        self._drag = None
        self.chart.redraw()

    def clear(self):
        self.plan, self.scale_levels, self._drag = None, (), None
        self.toggle.setChecked(False)
        self.chart.redraw()
        self.sync()

    def translate(self):
        name = self.words("손익비", "Risk / reward")
        self.title.setText(name)
        self.view.risk_button.setText(name)
        self.view.risk_button.setAccessibleName(name)
        self.view.more_risk.setText(name)
        self.close.setAccessibleName(self.words("손익비 설정 닫기", "Close risk / reward settings"))
        self.toggle.setText(self.words("차트에 표시", "Show on chart"))
        self.direction.setItemText(0, self.words("매수 관점 · 롱", "Long · price rises"))
        self.direction.setItemText(1, self.words("매도 관점 · 숏", "Short · price falls"))
        self.direction.setAccessibleName(self.words("손익비 방향", "Scenario direction"))
        for key, ko, en in (("entry", "진입가", "Entry"), ("stop", "손절가", "Stop"),
                            ("target", "목표가", "Target")):
            self.labels[key].setText(self.words(ko, en))
            self.fields[key].setAccessibleName(self.words(ko, en))
            self.labels[key].setBuddy(self.fields[key])
        self.reset.setText(self.words("현재가로 초기화", "Reset at latest price"))
        self.remove.setText(self.words("삭제", "Remove"))
        self.hint.setText(self.words(
            "선을 끌거나 가격을 입력하세요. 진입선을 끌면 세 선이 함께 이동합니다.\n"
            "초기선은 편집용 예시입니다. 가격 기준 손익이며 수수료·세금·슬리피지는 제외합니다. 주문은 실행하지 않습니다.",
            "Drag a line or enter a price. Dragging entry moves all three levels.\n"
            "Initial levels are editable examples. Price-based returns exclude fees, tax and slippage. No orders are placed."))
        self._result()
        self.chart.update()

    def _result(self):
        if not self.available:
            message = self.words("실제 차트를 조회한 뒤 손익비를 설정할 수 있습니다.",
                                 "Load a chart before setting a price scenario.")
        elif self.plan is None:
            message = self.words("현재가로 초기화하여 시작하세요.", "Reset at the latest price to start.")
        elif self.plan.error:
            message = self.words("매수: 손절가 < 진입가 < 목표가", "Long: stop < entry < target") if \
                self.plan.direction == "long" else self.words("매도: 목표가 < 진입가 < 손절가", "Short: target < entry < stop")
            message = "—\n" + message
        else:
            m, n = self.plan.metrics, self.view.ctx.number
            message = self.words("손익비", "Risk / reward") + "  1 : " + n(m["ratio"], 2)
            message += "\n" + self.words("예상 이익", "Potential gain") + "  +" + n(m["reward_pct"], 2) + "%"
            message += "\n" + self.words("예상 손실", "Potential loss") + "  −" + n(m["risk_pct"], 2) + "%"
        if self.result.text() != message:
            self.result.setText(message)

    def region(self):
        layout = self.chart.layout_info
        if layout is None:
            return QRectF()
        width = layout.plot_right - layout.plot_left
        return QRectF(layout.plot_left + width * .42, layout.price[0], width * .53,
                      layout.price[1] - layout.price[0])

    def hit(self, point):
        if not self.active or not self.region().contains(point):
            return None
        layout = self.chart.layout_info
        key = min(self.fields, key=lambda k: abs(point.y() - layout.y_of_price(getattr(self.plan, k))))
        return key if abs(point.y() - layout.y_of_price(getattr(self.plan, key))) <= 8 else None

    def press(self, event):
        key = self.hit(event.position())
        if event.button() != Qt.MouseButton.LeftButton or key is None:
            return False
        self._drag = (key, self.plan, self.chart.layout_info.price_at(event.position().y()))
        return True

    def move(self, event):
        if self._drag is None:
            return False
        if not event.buttons() & Qt.MouseButton.LeftButton:
            self.release()
            return False
        key, original, grabbed = self._drag
        layout = self.chart.layout_info
        if layout is not None:
            y = min(max(event.position().y(), layout.price[0]), layout.price[1])
            value = getattr(original, key) + layout.price_at(y) - grabbed
            self.set_plan(original.moved(key, value))
        self.chart.setCursor(Qt.CursorShape.SizeVerCursor)
        return True

    def release(self):
        if self._drag is None:
            return False
        self._drag = None
        if self.plan:
            self.set_plan(self.plan, fit=True)
        return True

    def paint(self):
        if not self.active or self.chart.layout_info is None:
            return
        p, layout, area = self.plan, self.chart.layout_info, self.region()
        painter = QPainter(self.chart)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setClipRect(area)
        ys = {key: layout.y_of_price(getattr(p, key)) for key in self.fields}
        dark = getattr(self.view, "dark", self.chart.dark)
        colors = {"target": QColor("#288575" if not dark else "#5CCBB2"),
                  "stop": QColor("#C34D59" if not dark else "#F17B86"),
                  "entry": QColor(self.view.palette.text)}
        if p.metrics:
            for key in ("target", "stop"):
                tint = QColor(colors[key]); tint.setAlpha(32)
                painter.fillRect(QRectF(area.left(), min(ys[key], ys["entry"]), area.width(),
                                       abs(ys[key] - ys["entry"])), tint)
        font = self.chart.font()
        font.setPixelSize(13)
        painter.setFont(font)
        positions, previous = {}, area.top() - 23
        for key in sorted(ys, key=ys.get):
            positions[key] = max(area.top(), ys[key] - 23, previous + 23)
            previous = positions[key]
        overflow = max(0, previous - (area.bottom() - 21))
        if overflow:
            positions = {key: value - overflow for key, value in positions.items()}
        for key in ("target", "stop", "entry"):
            y = ys[key]
            painter.setPen(QPen(colors[key], 1.5, Qt.PenStyle.DashLine if key == "entry" else Qt.PenStyle.SolidLine))
            painter.drawLine(QPointF(area.left(), y), QPointF(area.right(), y))
            painter.setBrush(QColor(self.view.palette.bg))
            painter.drawEllipse(QPointF(area.right() - 6, y), 4, 4)
            caption = self.labels[key].text() + "  " + self.view.price_text(getattr(p, key))
            if key == "entry" and p.metrics:
                caption += "  ·  1 : " + self.view.ctx.number(p.metrics["ratio"], 2)
            caption = painter.fontMetrics().elidedText(caption, Qt.TextElideMode.ElideRight,
                                                       max(10, int(area.width()) - 28))
            rect = QRectF(area.left() + 5, positions[key],
                          painter.fontMetrics().horizontalAdvance(caption) + 10, 21)
            painter.fillRect(rect, QColor(self.view.palette.bg))
            painter.setPen(colors[key])
            painter.drawText(rect.adjusted(5, 0, -5, 0), Qt.AlignmentFlag.AlignVCenter, caption)
        painter.end()
