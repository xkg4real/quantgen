"""Compact educational valuation, investor-flow and REST microstructure cards.

The parent supplies an already-loaded profile. This widget never starts a worker,
timer, provider, credential lookup or network request.
"""
from __future__ import annotations

import math

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QSizePolicy, QToolButton, QVBoxLayout, QWidget

from core.market.detail_insights import build_insights, number
from core.theme import DARK, LIGHT, RADII
from .typography import mix, tone_colors


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

    def _label(self, text, *, role="", tip=""):
        widget = QLabel(text)
        widget.setWordWrap(True)
        widget.setMinimumWidth(0)
        widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        widget.setTextFormat(Qt.TextFormat.PlainText)
        widget.setProperty("insightRole", role)
        if tip:
            widget.setToolTip(tip)
        return widget

    def _card(self, title):
        frame = QFrame()
        frame.setProperty("insightCard", True)
        body = QVBoxLayout(frame)
        body.setContentsMargins(10, 10, 10, 10)
        body.setSpacing(7)
        body.addWidget(self._label(title, role="title"))
        self.body.addWidget(frame)
        return body

    def _t(self, ko, en):
        return ko if self.language == "ko" else en

    def _note(self, body, short, detail):
        body.addWidget(self._label(short, role="muted", tip=detail))

    def _expand(self, body, title, widget):
        button = QToolButton()
        button.setText(title)
        button.setCheckable(True)
        button.setArrowType(Qt.ArrowType.RightArrow)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        widget.hide()
        def toggle(checked):
            widget.setVisible(checked)
            button.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
        button.toggled.connect(toggle)
        body.addWidget(button)
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
        text, muted = palette.text, palette.muted
        line, background = mix(palette.border, palette.bg, 0.5), palette.surface
        self.setStyleSheet(f"""
            QFrame#stockInsights QFrame[insightCard="true"] {{ background:{background}; border:1px solid {line}; border-radius:{RADII['sm']}px; }}
            QFrame#stockInsights QLabel {{ color:{text}; background:transparent; border:0; }}
            QFrame#stockInsights QLabel[insightRole="muted"] {{ color:{muted}; }}
            QFrame#stockInsights QLabel[insightRole="title"] {{ font-weight:600; }}
            QFrame#stockInsights QLabel[insightRole="value"] {{ font-size:16px; font-weight:600; }}
        """)
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
        from .metric_help import financial_help
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
            grid.addWidget(box, index // 2, index % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        body.addLayout(grid)
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
        if book is None:
            body.addWidget(self._label(self._t("호가 자료 미제공", "Depth unavailable")))
        else:
            grid = QGridLayout()
            headers = self._t(("매도 잔량", "매도 호가", "매수 호가", "매수 잔량"), ("Ask size", "Ask", "Bid", "Bid size"))
            for c, title in enumerate(headers):
                grid.addWidget(self._label(title, role="muted"), 0, c)
                grid.setColumnStretch(c, 1)
            extra = QWidget()
            more = QGridLayout(extra)
            more.setContentsMargins(0, 0, 0, 0)
            for c in range(4):
                more.setColumnStretch(c, 1)
            for n, row in enumerate(book["levels"], 1):
                for c, key in enumerate(("ask_qty", "ask_price", "bid_price", "bid_qty")):
                    digits = 2 if key.endswith("price") and row[key] is not None and row[key] % 1 else 0
                    (grid if n <= 3 else more).addWidget(self._label(_fmt(row[key], digits)), n if n <= 3 else n - 4, c)
            body.addLayout(grid)
            self._expand(body, self._t("호가 10단계 펼치기", "Expand10 depth levels"), extra)
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
