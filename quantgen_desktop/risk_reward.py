"""Editable chart price scenarios, with native text and keyboard alternatives to dragging."""
from dataclasses import replace
import math

from PyQt6.QtCore import QObject, QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (QButtonGroup, QComboBox, QDoubleSpinBox, QFrame, QGridLayout,
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
        self.span = None
        self.selected = False
        self.panel = QFrame()
        self.panel.setProperty("sd", "guideCard")
        self.panel.setObjectName("riskRewardPanel")
        box = QVBoxLayout(self.panel)
        box.setContentsMargins(16, 14, 16, 16)
        box.setSpacing(12)
        head = QHBoxLayout()
        self.title = label("guideReading")
        self.close = QPushButton("×")
        self.close.setProperty("sd", "mini")
        self.close.clicked.connect(self.panel.hide)
        from .indicator_picker import Switch
        self.toggle = Switch()
        self.toggle.toggled.connect(self._toggle)
        head.addWidget(self.title, 1)
        head.addWidget(self.toggle)
        head.addWidget(self.close)
        box.addLayout(head)
        self.direction = QComboBox()
        self.direction.addItem("", "long")
        self.direction.addItem("", "short")
        self.direction.currentIndexChanged.connect(self._direction)
        box.addWidget(self.direction)
        self.direction.hide()
        choices = QHBoxLayout()
        choices.setSpacing(6)
        self.direction_group = QButtonGroup(self.panel)
        self.direction_buttons = []
        for i in range(2):
            button = QPushButton()
            button.setCheckable(True)
            button.setProperty('sd', 'chip')
            button.clicked.connect(lambda checked=False, i=i: self.direction.setCurrentIndex(i))
            self.direction_group.addButton(button, i)
            self.direction_buttons.append(button)
            choices.addWidget(button)
        self.direction_buttons[0].setChecked(True)
        box.addLayout(choices)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        self.fields, self.labels = {}, {}
        for row, key in enumerate(("entry", "stop", "target")):
            title, edit = label("guideOne"), QDoubleSpinBox()
            edit.setObjectName("riskReward" + key.title())
            edit.setDecimals(4)
            edit.setRange(0.0001, 1e12)
            edit.setGroupSeparatorShown(True)
            edit.setKeyboardTracking(False)
            # Qt 6.12 + themed spin subcontrols collapses the editor with NoButtons.
            # Hide subcontrols in the sheet while retaining the normal editor geometry.
            edit.lineEdit().setTextMargins(8, 0, 8, 0)
            edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            edit.setMinimumWidth(0)
            edit.valueChanged.connect(self._edited)
            grid.addWidget(title, row, 0)
            grid.addWidget(edit, row, 1)
            self.labels[key], self.fields[key] = title, edit
        grid.setColumnStretch(1, 1)
        box.addLayout(grid)
        self.result = label("rrRatio", wrap=True, selectable=True)
        self.result.setObjectName("riskRewardResult")
        box.addWidget(self.result)
        payoffs = QHBoxLayout()
        self.gain, self.loss = label('rrGain', wrap=True), label('rrLoss', wrap=True)
        payoffs.addWidget(self.gain, 1); payoffs.addWidget(self.loss, 1)
        box.addLayout(payoffs)
        self.instruction = label('guideCaution', wrap=True)
        box.addWidget(self.instruction)
        self.more = QPushButton()
        self.more.setProperty('sd', 'link'); self.more.setCheckable(True)
        box.addWidget(self.more, 0, Qt.AlignmentFlag.AlignLeft)
        self.hint = label("muted", wrap=True)
        self.hint.setProperty('sd', 'guideLong')
        box.addWidget(self.hint)
        self.hint.hide()
        self.more.toggled.connect(self._show_details)
        actions = QHBoxLayout()
        self.reset, self.remove = QPushButton(), QPushButton()
        self.reset.clicked.connect(self.seed)
        self.remove.clicked.connect(self.clear)
        for button in (self.reset, self.remove):
            button.setProperty("sd", "text")
            actions.addWidget(button)
        box.addLayout(actions)
        for widget in (self.panel, self.title, self.toggle, self.direction, self.result, self.hint,
                       self.close, self.reset, self.remove, self.gain, self.loss, self.instruction,
                       self.more, *self.direction_buttons, *self.labels.values()):
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
            self.span, self.selected = None, False
            self.toggle.blockSignals(True)
            self.toggle.setChecked(False)
            self.toggle.blockSignals(False)
        available = self.available
        self.reset.setEnabled(available)
        self.toggle.setEnabled(available and self.plan is not None)
        self.remove.setEnabled(self.plan is not None)
        for widget in (self.direction, *self.fields.values()):
            widget.setEnabled(available and self.plan is not None)
        for button in self.direction_buttons:
            button.setEnabled(available and self.plan is not None)
        self.direction_buttons[self.direction.currentIndex()].setChecked(True)
        self._style()
        self._result()
        self.chart.update()

    def open(self):
        self.sync()
        self.panel.show()
        if self.plan is None and self.available:
            self.seed()
        self.selected = self.plan is not None
        self.fields["entry"].setFocus(Qt.FocusReason.OtherFocusReason)

    def seed(self):
        if not self.available:
            return
        self.span = None
        self.selected = True
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
        self.span, self.selected = None, False
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
        self.toggle.setAccessibleName(self.toggle.text())
        self.direction.setItemText(0, self.words("매수 관점 · 롱", "Long · price rises"))
        self.direction.setItemText(1, self.words("매도 관점 · 숏", "Short · price falls"))
        for i, button in enumerate(self.direction_buttons):
            button.setText(self.words(('롱 · 상승', '숏 · 하락')[i], ('Long', 'Short')[i]))
        self.direction.setAccessibleName(self.words("손익비 방향", "Scenario direction"))
        for key, ko, en in (("entry", "진입가", "Entry"), ("stop", "손절가", "Stop"),
                            ("target", "목표가", "Target")):
            self.labels[key].setText(self.words(ko, en))
            self.fields[key].setAccessibleName(self.words(ko, en))
            self.labels[key].setBuddy(self.fields[key])
        self.reset.setText(self.words("현재가로 초기화", "Reset at latest price"))
        self.remove.setText(self.words("삭제", "Remove"))
        self.instruction.setText(self.words('영역을 끌어 이동 · 가장자리로 크기 조절 · 선택 후 Delete로 삭제',
                                           'Drag to move · resize at edges · select and press Delete to remove'))
        self.hint.setText(self.words(
            "진입선을 끌면 세 가격이 함께 이동합니다. 좌우 폭은 표시 범위이며 손익비를 바꾸지 않습니다.\n"
            "초기선은 편집용 예시입니다. 가격 기준 손익이며 수수료·세금·슬리피지는 제외합니다. 주문은 실행하지 않습니다.",
            "Dragging entry moves all three prices. Horizontal width changes the drawing only, not the ratio.\n"
            "Initial levels are editable examples. Price-based returns exclude fees, tax and slippage. No orders are placed."))
        self._show_details(self.more.isChecked())
        self._result()
        self.chart.update()

    def _result(self):
        valid = bool(self.available and self.plan and self.plan.metrics)
        self.gain.setVisible(valid); self.loss.setVisible(valid)
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
            message = "1 : " + n(m["ratio"], 2)
            self.gain.setText(self.words("목표 도달 시", "At target") + "\n+" + n(m["reward_pct"], 2) + "%")
            self.loss.setText(self.words("손절가 도달 시", "At stop") + "\n−" + n(m["risk_pct"], 2) + "%")
        if self.result.text() != message:
            self.result.setText(message)

    def _show_details(self, shown):
        self.hint.setVisible(shown)
        self.more.setText(self.words('안내 접기' if shown else '계산 기준 및 조작 안내',
                                    'Hide details' if shown else 'Calculation and controls'))

    def _style(self):
        p, dark = self.view.palette, getattr(self.view, 'dark', self.chart.dark)
        key = (p.bg, dark)
        if getattr(self, '_style_key', None) == key:
            return
        self._style_key = key
        self.toggle.colors = (p.accent, p.border, p.on_accent)
        self.panel.setStyleSheet(f'''
          QFrame#riskRewardPanel {{ background: {p.surface}; border: 1px solid {p.border}; border-radius: 14px; }}
          QLabel[sd='rrRatio'] {{ font-size: 24px; font-weight: 600; color: {p.text}; letter-spacing: 0px; }}
          QLabel[sd='rrGain'] {{ font-size: 13px; color: {'#5CCBB2' if dark else '#288575'}; }}
          QLabel[sd='rrLoss'] {{ font-size: 13px; color: {'#F17B86' if dark else '#C34D59'}; }}
          QDoubleSpinBox {{ min-width: 0px; padding: 7px 10px; border-radius: 8px; }}
          QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0px; height: 0px; }}
          QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {{ image: none; }}
          QDoubleSpinBox QLineEdit {{ border: 0; padding: 0; min-height: 0; background: transparent; }}
          QPushButton[sd='chip'] {{ padding: 6px 10px; border-radius: 8px; color: {p.muted}; background: {p.surface_2}; }}
          QPushButton[sd='chip']:checked {{ background: {p.accent_soft}; color: {p.accent}; }}
        ''')

    def region(self):
        layout = self.chart.layout_info
        if layout is None:
            return QRectF()
        if self.span is None:
            count = (layout.plot_right - layout.plot_left) / layout.step
            self.span = (layout.start - .5 + count * .42, layout.start - .5 + count * .95)
        left, right = (layout.x_of(index) for index in self.span)
        return QRectF(left, layout.price[0], right - left, layout.price[1] - layout.price[0])

    def plot(self):
        layout = self.chart.layout_info
        return QRectF(layout.plot_left, layout.price[0], layout.plot_right - layout.plot_left,
                      layout.price[1] - layout.price[0]) if layout else QRectF()

    def hit(self, point):
        if not self.active or not self.plot().contains(point):
            return None
        area = self.region()
        layout = self.chart.layout_info
        key = min(self.fields, key=lambda k: abs(point.y() - layout.y_of_price(getattr(self.plan, k))))
        near_line = abs(point.y() - layout.y_of_price(getattr(self.plan, key))) <= 8
        ys = [layout.y_of_price(getattr(self.plan, k)) for k in self.fields]
        for edge, x in (('left', area.left()), ('right', area.right())):
            if abs(point.x() - x) <= 7 and min(ys)-8 <= point.y() <= max(ys)+8:
                return edge + (':' + key if near_line and key != 'entry' else '')
        if area.left() <= point.x() <= area.right():
            if near_line:
                return key
            if self.plan.metrics and min(ys) <= point.y() <= max(ys):
                return 'body'
        return None

    def cursor(self, hit):
        if ':' in hit:
            edge, key = hit.split(':')
            top = getattr(self.plan, key) > self.plan.entry
            return Qt.CursorShape.SizeFDiagCursor if (edge == 'left') == top else Qt.CursorShape.SizeBDiagCursor
        if hit in ('left', 'right'):
            return Qt.CursorShape.SizeHorCursor
        return Qt.CursorShape.SizeAllCursor if hit in ('body', 'entry') else Qt.CursorShape.SizeVerCursor

    def press(self, event):
        key = self.hit(event.position())
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        self.selected = key is not None
        self.chart.update()
        if key is None:
            return False
        self._drag = (key, self.plan, self.span, QPointF(event.position()), self.chart.layout_info)
        return True

    def move(self, event):
        if self._drag is None:
            return False
        if not event.buttons() & Qt.MouseButton.LeftButton:
            self.release()
            return False
        hit, original, span, grabbed, layout = self._drag
        dx = (event.position().x() - grabbed.x()) / layout.step
        dy = layout.price_at(event.position().y()) - layout.price_at(grabbed.y())
        left, right = span
        edge, _, key = hit.partition(':')
        minimum = max(.5, 28 / layout.step)
        if edge == 'left':
            left = min(right - minimum, left + dx)
        elif edge == 'right':
            right = max(left + minimum, right + dx)
        elif hit in ('body', 'entry'):
            left, right = left + dx, right + dx
        self.span = (left, right)
        field = key or ('entry' if hit == 'body' else hit)
        if field in self.fields:
            if field == 'entry':
                dy = max(self.fields['entry'].minimum() - min(original.entry, original.stop, original.target), dy)
            self.set_plan(original.moved(field, getattr(original, field) + dy))
        self.chart.setCursor(self.cursor(hit))
        self.chart.update()
        return True

    def release(self):
        if self._drag is None:
            return False
        self._drag = None
        if self.plan:
            self.set_plan(self.plan, fit=True)
        return True

    def key_press(self, event):
        if event.key() == Qt.Key.Key_Delete and self.selected and self.active:
            self.clear()
            return True
        if event.key() == Qt.Key.Key_Escape and self.selected:
            self.selected = False
            self._drag = None
            self.chart.update()
            return True
        return False

    def paint(self):
        if not self.active or self.chart.layout_info is None:
            return
        p, layout, area = self.plan, self.chart.layout_info, self.region()
        if not area.intersects(self.plot()):
            return
        painter = QPainter(self.chart)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setClipRect(self.plot())
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
            painter.setPen(QPen(QColor(self.view.palette.muted), 1, Qt.PenStyle.DotLine))
            for x in (area.left(), area.right()):
                painter.drawLine(QPointF(x, min(ys.values())), QPointF(x, max(ys.values())))
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
            if self.selected:
                painter.setBrush(QColor(self.view.palette.surface))
                for x in (area.left(), area.right()):
                    painter.drawRect(QRectF(x - 3, y - 3, 6, 6))
            caption = self.labels[key].text() + "  " + self.view.price_text(getattr(p, key))
            if key == "entry" and p.metrics:
                caption += "  ·  1 : " + self.view.ctx.number(p.metrics["ratio"], 2)
            caption = painter.fontMetrics().elidedText(caption, Qt.TextElideMode.ElideRight,
                                                       max(10, int(area.width()) - 28))
            rect = QRectF(max(area.left(), layout.plot_left) + 5, positions[key],
                          painter.fontMetrics().horizontalAdvance(caption) + 10, 21)
            painter.fillRect(rect, QColor(self.view.palette.bg))
            painter.setPen(colors[key])
            painter.drawText(rect.adjusted(5, 0, -5, 0), Qt.AlignmentFlag.AlignVCenter, caption)
        painter.end()
