"""Owner items of 2026-11-24 on the stock insight cards, with real Qt widgets.

"외국인·개인 그거 캔들로" -> one up/down column per session for each investor group;
"호가 캔들로" -> filled depth bars, the quote's last price between the sides and a
sell/buy total bar; "PBR·PER 등 재무지표 가독성" -> name and value on one line, a
full-width strip with the band tinted. Synthetic, supplied profiles only: no
window, provider, worker or network request.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import unittest


def _days(count=24, missing=()):
    rows = []
    for i in range(count):
        day = f"2026-10-{i + 1:02d}" if i < 31 else f"2026-11-{i - 30:02d}"
        row = {"date": day}
        for k, group in enumerate(("foreign", "institution", "individual")):
            net = (i - 12) * (k + 1) * 1000.0
            row[group] = None if (i, group) in missing else net
            row[group + "_buy"], row[group + "_sell"] = 50000.0 + net, 50000.0
        rows.append(row)
    return rows


def _profile(*, rows=None, last_price=71050.0, totals=False, per=13.2, pbr=1.1, basis="quote", sizes=None):
    from core.research.stock_profile import _flows
    raw = {"aspr_acpt_hour": "151230"}
    for level in range(1, 11):
        raw[f"askp{level}"] = str(71000 + level * 100)
        raw[f"bidp{level}"] = str(71000 - (level - 1) * 100)
        raw[f"askp_rsqn{level}"] = str(1000 * level if sizes is None else sizes[0])
        raw[f"bidp_rsqn{level}"] = str(700 * level if sizes is None else sizes[1])
    if totals:
        raw["total_askp_rsqn"], raw["total_bidp_rsqn"] = totals if isinstance(totals, tuple) else ("900000", "300000")
    values = {"key_figures": {"per": per, "pbr": pbr}, "orderbook": {"output1": raw}}
    if rows is not None:
        values["flows"] = _flows(rows)
    return SimpleNamespace(values=values, reasons={}, sources={"quote": "KIS", "flows": "KIS"},
                           fetched={"quote": "2026-11-24T15:12:30+09:00", "flows": "2026-11-24T15:12:30+09:00"},
                           last_price=last_price, price_basis=basis)


class OwnerItemsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        from quantgen_desktop.font_policy import configure_interface_font
        cls.app = QApplication.instance() or QApplication([])
        configure_interface_font(cls.app, Path(__file__).resolve().parents[1] / "assets/fonts")

    def settle(self):
        for _ in range(6):
            self.app.processEvents()

    def panel(self, profile, *, language="ko", dark=False, width=360):
        from PyQt6.QtWidgets import QVBoxLayout, QWidget
        from quantgen_desktop.stock_insights import StockInsightsPanel
        host = QWidget()
        box = QVBoxLayout(host)
        box.setContentsMargins(0, 0, 0, 0)        # `width` is the panel's own width
        panel = StockInsightsPanel(host)
        box.addWidget(panel)
        host.resize(width, 1600)
        host.show()
        panel.set_profile(profile, language=language, dark=dark)
        self.settle()
        self.addCleanup(lambda: (host.close(), host.deleteLater(), self.settle()))
        return host, panel

    # ------------------------------------------------------------------ flows
    def test_model_keeps_the_last_window_of_dated_daily_rows(self):
        from core.market.detail_insights import build_insights
        rows = _days(24, missing={(23, "foreign")})
        model = build_insights(_profile(rows=rows))
        daily = model["flow_daily"]
        self.assertEqual(len(daily), 20)                       # the longest summed window
        self.assertEqual([d["date"] for d in daily], [r["date"] for r in rows[-20:]])
        self.assertIsNone(daily[-1]["foreign"])                # blank stays missing, never 0
        self.assertEqual(daily[-1]["individual"], rows[-1]["individual"])
        # The 20 columns add up to the window's own net sum.
        for group in ("foreign", "institution", "individual"):
            window = next(r for r in model["flows"] if r["group"] == group)
            self.assertEqual(sum(d[group] for d in daily if d[group] is not None), window["net_qty"])
        bad = _profile(rows=rows)
        bad.values["flows"]["daily"] = (("not a date", 1, 2, 3), ("2026-11-02", "x", None, 4.0))
        self.assertEqual([d["date"] for d in build_insights(bad)["flow_daily"]], ["2026-11-02"])
        self.assertEqual(build_insights(_profile())["flow_daily"], ())

    def test_each_group_gets_one_column_per_session_on_a_shared_scale(self):
        from PyQt6.QtCore import QPointF, Qt
        from PyQt6.QtGui import QMouseEvent
        from PyQt6.QtWidgets import QLabel
        rows = _days(20, missing={(5, "individual")})
        host, panel = self.panel(_profile(rows=rows))
        self.assertEqual(set(panel.flow_bars), {"individual", "foreign", "institution"})
        expected_scale = max(abs(r[g]) for r in rows for g in ("foreign", "institution", "individual")
                             if r[g] is not None)
        for group, bars in panel.flow_bars.items():
            self.assertEqual([v for _, v in bars.days], [r[group] for r in rows])
            self.assertEqual(bars.scale, expected_scale)
            self.assertFalse(bars.isHidden())
            self.assertGreater(bars.width(), 200)
        self.assertIsNone(panel.flow_bars["individual"].days[5][1])
        # Hover names the date and the side.
        bars = panel.flow_bars["foreign"]
        x = bars.width() * (19.5 / 20)
        event = QMouseEvent(QMouseEvent.Type.MouseMove, QPointF(x, 10), bars.mapToGlobal(QPointF(x, 10)),
                            Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
        bars.mouseMoveEvent(event)
        self.assertEqual(bars.hover, 19)
        self.assertEqual(bars.describe(*bars.days[19]), f"{rows[19]['date']} · 외국인 순매수 7,000주")
        self.assertEqual(bars.describe(*bars.days[0]), f"{rows[0]['date']} · 외국인 순매도 12,000주")
        self.assertIn("자료 없음", panel.flow_bars["individual"].describe(*panel.flow_bars["individual"].days[5]))
        # Window sums: each in its own tone, short Korean units, exact figure on hover.
        sums = [w for w in panel.findChildren(QLabel) if w.text().startswith(("20일 ", "5일 "))]
        self.assertEqual(len(sums), 6)
        for widget in sums:
            sign = widget.text().split()[1][0]
            self.assertEqual(widget.property("tone"), {"+": "up", "−": "down"}.get(sign))
            self.assertIn("순매수", widget.toolTip())
        from PyQt6.QtWidgets import QPushButton
        self.assertFalse([w for w in panel.findChildren(QPushButton) if "거래일도 보기" in w.text()])
        # The sums' hover says how many days the figures rest on and what the split is a share of.
        individual = next(w for w in sums if w.text().startswith("20일 ") and "개인" not in w.text()
                          and w.parent() is panel.flow_bars["individual"].parent()
                          and w.y() < panel.flow_bars["individual"].y())
        self.assertIn("자료 19/20일", individual.toolTip())         # one missing individual day
        self.assertIn("양쪽 자료가 있는 20/20일 기준 · 이 투자자 거래량 중 매수", individual.toolTip())

    def test_profile_without_daily_rows_keeps_the_previous_split_bars(self):
        from quantgen_desktop.stock_insights import FlowBar
        profile = _profile(rows=_days(20))
        profile.values["flows"].pop("daily")
        host, panel = self.panel(profile)
        self.assertEqual(panel.flow_bars, {})
        self.assertEqual(len(panel.findChildren(FlowBar)), 6)   # 20-day rows + folded 5-day rows

    def test_short_share_units(self):
        from quantgen_desktop.stock_insights import _shares
        self.assertEqual(_shares(55123, "ko"), "+5.5만주")
        self.assertEqual(_shares(-9999, "ko"), "−9,999주")
        self.assertEqual(_shares(0, "ko"), "0주")
        self.assertEqual(_shares(-2_345_678, "en"), "−2.3M")
        self.assertEqual(_shares(12_300, "en"), "+12.3K")

    # ------------------------------------------------------------- order book
    def test_last_price_sits_between_the_sides_and_totals_compare_them(self):
        from PyQt6.QtCore import QPoint
        host, panel = self.panel(_profile())
        ladder = panel.depth_ladder
        self.assertEqual(ladder.current_label.text(), "현재가 71,050")
        y = lambda w: w.mapTo(ladder.viewport(), QPoint()).y()
        best_ask = next(r for r in ladder.rows if r.side == "ask" and r.level == 1)
        best_bid = next(r for r in ladder.rows if r.side == "bid" and r.level == 1)
        self.assertLess(y(best_ask.price_label), y(ladder.current_label))
        self.assertLess(y(ladder.current_label), y(best_bid.price_label))
        # Without provider totals: the sum of the supplied ten levels, named as such.
        self.assertEqual(panel.depth_totals, (55000.0, 38500.0, False))
        self.assertIn("10단계 잔량 합", panel.depth_share.toolTip())
        host2, panel2 = self.panel(_profile(totals=True))
        self.assertEqual(panel2.depth_totals, (900000.0, 300000.0, True))
        self.assertIn("총잔량", panel2.depth_share.toolTip())
        host3, panel3 = self.panel(_profile(last_price=None))
        self.assertIsNone(panel3.depth_ladder.current_label)
        # Without a quote the profile falls back to the last daily close: never call that the current price.
        host4, panel4 = self.panel(_profile(basis="daily_close"))
        self.assertEqual(panel4.depth_ladder.current_label.text(), "마지막 거래일 종가 71,050")
        self.assertNotIn("현재가", panel4.depth_ladder.current_label.toolTip())
        host5, panel5 = self.panel(_profile(basis=""))
        self.assertIsNone(panel5.depth_ladder.current_label)
        host6, panel6 = self.panel(_profile(basis="daily_close"), language="en")
        self.assertEqual(panel6.depth_ladder.current_label.text(), "Last daily close 71,050")
        # Shares always add up to 100.0%: complementary tenths, as display_split does elsewhere.
        host7, panel7 = self.panel(_profile(totals=("207", "1793")))
        self.assertIn("매도 10.4% · 매수 89.6%", panel7.depth_share.toolTip())   # 10.35 -> 10.4, 89.6

    # -------------------------------------------------------------- valuation
    def test_value_shares_the_name_line_and_the_band_is_marked(self):
        from PyQt6.QtCore import QPoint
        from PyQt6.QtWidgets import QLabel
        from quantgen_desktop.stock_insights import ValuationReferenceStrip
        host, panel = self.panel(_profile(per=13.2, pbr=0.8))
        labels = panel.findChildren(QLabel)
        for name, value in (("PER · ", "13.20배"), ("PBR · ", "0.80배")):
            title = next(w for w in labels if w.text().startswith(name))
            shown = next(w for w in labels if w.text() == value)
            self.assertEqual(title.mapTo(host, QPoint()).y(), shown.mapTo(host, QPoint()).y())
            self.assertGreater(shown.mapTo(host, QPoint()).x(), title.mapTo(host, QPoint()).x())
        strips = {s.metric: s for s in panel.findChildren(ValuationReferenceStrip)}
        self.assertEqual((strips["per"].reference.band_index, strips["pbr"].reference.band_index), (1, 0))
        for strip in strips.values():
            self.assertGreater(strip.width(), 250)               # full width, not half a column
        texts = [w.text() for w in labels]
        self.assertIn("주가가 주당순이익(EPS)의 13.20배예요", texts)
        self.assertIn("주가가 주당순자산(BPS)의 0.80배예요", texts)
        self.assertNotIn(strips["per"].reference.reading, texts)  # the tinted middle band says it
        self.assertIn(strips["pbr"].reference.reading, texts)     # an outer band keeps its caution
        self.assertIn("ROE·PSR은 아직 연결되지 않았어요", texts)
        self.assertNotIn("미제공", texts)
        self.assertTrue(any("회계 기준·기준일은 확인되지" in w.toolTip() for w in labels))


    # ------------------------------------------------------------ what is painted
    def grab_image(self, widget):
        widget.repaint()
        self.settle()
        return widget.grab().toImage()

    def test_columns_paint_net_buying_up_in_red_and_net_selling_down_in_blue(self):
        from PyQt6.QtGui import QColor
        from quantgen_desktop.stock_insights import DailyNetBars
        from quantgen_desktop.typography import tone_colors
        for dark in (False, True):
            bars = DailyNetBars((("2026-11-19", 1000.0), ("2026-11-20", -1000.0), ("2026-11-21", None)),
                                1000.0, dark, lambda d, v: d)
            bars.resize(300, bars.height())
            bars.show()
            self.addCleanup(bars.deleteLater)
            image = self.grab_image(bars)
            ratio = image.width() / bars.width()
            px = lambda x, y: QColor(image.pixel(int(x * ratio), int(y * ratio))).name()
            mid, slot = bars.height() / 2, bars.width() / 3
            tones = tone_colors(dark)
            self.assertEqual(px(slot * .5, mid - 8), QColor(tones["up"]).name())      # day 1 rises, red
            self.assertNotEqual(px(slot * .5, mid + 8), QColor(tones["up"]).name())
            self.assertEqual(px(slot * 1.5, mid + 8), QColor(tones["down"]).name())   # day 2 falls, blue
            self.assertNotEqual(px(slot * 1.5, mid - 8), QColor(tones["down"]).name())
            for y in (mid - 8, mid + 8):                                             # day 3: no column
                self.assertNotIn(px(slot * 2.5, y), {QColor(tones["up"]).name(), QColor(tones["down"]).name()})
            bars.close()

    def test_depth_bars_are_filled_and_the_valuation_band_is_tinted(self):
        from PyQt6.QtGui import QColor
        from quantgen_desktop.stock_insights import DepthQuantityBar, ValuationReferenceStrip
        from quantgen_desktop.metric_help import valuation_reference
        bar = DepthQuantityBar("bid", 1000.0, 1000.0, False)
        bar.resize(200, 24)
        bar.show()
        self.addCleanup(bar.deleteLater)
        image = self.grab_image(bar)
        ratio = image.width() / bar.width()
        fill = QColor(image.pixel(int(190 * ratio), int(12 * ratio)))
        # A clearly filled bar: well away from the background, not a faint wash (alpha 48 before).
        background = bar.palette().color(bar.backgroundRole())
        self.assertGreater(abs(fill.red() - background.red()) + abs(fill.green() - background.green())
                           + abs(fill.blue() - background.blue()), 120)
        strip = ValuationReferenceStrip("per", valuation_reference("per", 15, "ko"), False)
        strip.resize(300, strip.height())
        strip.show()
        self.addCleanup(strip.deleteLater)
        image = self.grab_image(strip)
        ratio = image.width() / strip.width()
        y = (strip.TRACK_TOP + strip.TRACK_HEIGHT / 2) * ratio
        segment = lambda i: QColor(image.pixel(int((i * 100 + 20) * ratio), int(y))).name()
        self.assertEqual(segment(0), segment(2))          # the two other bands look alike
        self.assertNotEqual(segment(1), segment(0))       # the band holding 15 is tinted

    def test_totals_row_shows_full_figures_at_the_real_sidebar_width(self):
        from PyQt6.QtWidgets import QLabel
        from quantgen_desktop.stock_insights import SideShareBar
        cases = (dict(sizes=(123456, 123456)), dict(totals=("15234000", "19876500")))
        for language in ("ko", "en"):
            for case in cases:
                for width in (264, 282):
                    with self.subTest(language=language, width=width, **{k: str(v) for k, v in case.items()}):
                        host, panel = self.panel(_profile(**case), language=language, width=width)
                        word = ("매도 ", "매수 ") if language == "ko" else ("Sell ", "Buy ")
                        values = [w for w in panel.findChildren(QLabel) if w.property("insightRole") == "value"]
                        sell = next(w for w in values if w.text().startswith(word[0]))
                        buy = next(w for w in values if w.text().startswith(word[1]))
                        self.assertEqual((sell.property("tone"), buy.property("tone")), ("down", "up"))
                        for widget in (sell, buy):
                            self.assertTrue(widget.isVisible())
                            self.assertGreaterEqual(widget.width(), widget.sizeHint().width(), widget.text())
                        self.assertIs(panel.findChild(SideShareBar), panel.depth_share)
                        self.assertTrue(panel.depth_share.isVisible())
                        self.assertGreater(panel.depth_share.width(), width - 40)

    def test_large_investor_sums_fit_on_the_header_line(self):
        from PyQt6.QtWidgets import QLabel
        rows = _days(20)
        for row in rows:
            row["foreign"], row["institution"], row["individual"] = -1_234_567.0, 987_654.0, -999_999.0
        for language in ("ko", "en"):
            for width in (264, 282):
                with self.subTest(language=language, width=width):
                    host, panel = self.panel(_profile(rows=rows), language=language, width=width)
                    for widget in panel.findChildren(QLabel):
                        if widget.isVisible() and not widget.wordWrap() \
                                and widget.sizePolicy().horizontalPolicy().name != "Ignored":
                            self.assertGreaterEqual(widget.width(), widget.sizeHint().width(), widget.text())

    # ---------------------------------------------------------- window life
    def test_rerendering_a_visible_panel_opens_no_top_level_window(self):
        from PyQt6.QtWidgets import QApplication
        before = {id(w) for w in QApplication.topLevelWidgets() if w.isVisible()}
        host, panel = self.panel(_profile(rows=_days(20)))
        # Render again before the layout's queued show of the first cards runs.
        for dark in (True, False, True):
            panel.set_profile(_profile(rows=_days(20)), language="ko", dark=dark)
        self.settle()
        opened = [w for w in QApplication.topLevelWidgets()
                  if w.isVisible() and id(w) not in before and w is not host]
        self.assertEqual(opened, [])


if __name__ == "__main__":
    unittest.main()
