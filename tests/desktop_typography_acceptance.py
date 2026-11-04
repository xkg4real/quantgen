"""Type scale, bundled-font glyph coverage and the thinner sidebar (owner request 2026-11-04).

Offline: provider requests raise, dotenv loading is patched off, no jobs run.
"""
import ast
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import dotenv
with patch.object(dotenv, "load_dotenv", return_value=False):
    from quantgen_desktop import app as desktop
    from quantgen_desktop.app import ResearchWindow, label

from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPalette, QRawFont
from PyQt6.QtWidgets import QApplication, QFrame, QLabel, QMessageBox, QVBoxLayout, QWidget

from core.market.models import Candle, ChartRequest, MarketSnapshot
from core.market.presentation import card_svg, chart_svg
from core.theme import DARK, LIGHT
from quantgen_desktop.typography import (NAV_PADDING, SIDEBAR_WIDTH_RANGE, TONE_COLORS, scaled_font,
                                         set_tone, tone_colors, tone_for, window_stylesheet)

ROOT = Path(__file__).resolve().parents[1]
FONT_FILES = ("qg-interface.otf", "qg-interface-medium.otf", "qg-interface-semibold.otf")
SVG = "{http://www.w3.org/2000/svg}"

# Modules whose string literals the native window shows: its own widgets plus the
# catalogues, report builders and chart renderers it displays.
UI_SOURCES = (sorted((ROOT / "quantgen_desktop").glob("*.py"))
              + sorted((ROOT / "core/research").glob("*.py"))
              + sorted((ROOT / "core/education").glob("*.py"))
              + sorted((ROOT / "core/market").glob("*.py"))
              + [ROOT / name for name in ("core/ui_messages.py", "core/ui_legacy_messages.py", "core/i18n.py",
                                          "core/ficc/insights.py", "core/quant/insights.py")])


def shown_strings(path):
    """String constants except docstrings and other bare string statements (never shown)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    skipped = {id(node.value) for node in ast.walk(tree)
               if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skipped:
            yield node.lineno, node.value


def directory_names():
    """Instrument names bundled for search and display (core/market/data/*.json)."""
    for path in sorted((ROOT / "core/market/data").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data.get("symbols", []) if isinstance(data, dict) else data
        for row in rows:
            for key, value in row.items():
                if key.startswith("name") and isinstance(value, str):
                    yield f"{path.name}:{row.get('code')}", value


def history(n=60, stamp="2026-10-{:02d}"):
    return MarketSnapshot(ChartRequest(), tuple(Candle(stamp.format(i % 28 + 1), 100 + i, 102 + i, 99 + i, 101 + i, 1000 + i)
                                                for i in range(n)))


class BundledFontCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.faces = {name: QRawFont(str(ROOT / "assets/fonts" / name), 16) for name in FONT_FILES}
        for name, face in cls.faces.items():
            assert face.isValid(), name

    @staticmethod
    def noncharacter(ch):
        # Sort sentinels such as U+10FFFF are never shown; Unicode reserves them as noncharacters.
        code = ord(ch)
        return 0xFDD0 <= code <= 0xFDEF or code & 0xFFFE == 0xFFFE

    def missing(self, text):
        return sorted({ch for ch in text if ord(ch) >= 0x20 and not self.noncharacter(ch)
                       for face in self.faces.values() if not face.supportsCharacter(ord(ch))})

    def test_every_shown_string_literal_is_in_the_bundled_font(self):
        problems = []
        for path in UI_SOURCES:
            for line, text in shown_strings(path):
                missing = self.missing(text)
                if missing:
                    problems.append(f"{path.relative_to(ROOT)}:{line} " + " ".join(f"U+{ord(c):04X}" for c in missing))
        self.assertEqual(problems, [], "Characters without a glyph fall back to another font")

    def test_bundled_instrument_names_are_in_the_bundled_font(self):
        names = list(directory_names())
        self.assertTrue(names)
        self.assertEqual([(where, self.missing(text)) for where, text in names if self.missing(text)], [])

    def test_indicator_chip_remove_uses_a_bundled_multiplication_sign(self):
        times, heavy_x = chr(0x00D7), chr(0x2715)  # multiplication sign; heavy multiplication X
        self.assertTrue(all(face.supportsCharacter(times) for face in self.faces.values()))
        self.assertFalse(any(face.supportsCharacter(heavy_x) for face in self.faces.values()))
        source = (ROOT / "quantgen_desktop/indicator_guide.py").read_text(encoding="utf-8")
        self.assertTrue("QPushButton('" + times + "')" in source, "the chip remove button must use U+00D7")
        self.assertFalse(heavy_x in source, "U+2715 has no glyph in the bundled font")


class SvgTypographyTests(unittest.TestCase):
    def assert_text(self, svg):
        root = ElementTree.fromstring(svg)
        texts = root.findall(SVG + "text")
        self.assertTrue(texts)
        for text in texts:
            # QtSvg reads "QG Interface, sans-serif" as one family that does not exist.
            self.assertEqual(text.attrib["font-family"], "QG Interface", text.text)
            self.assertGreaterEqual(float(text.attrib["font-size"]), 12, text.text)
        return root

    def test_price_chart_labels_use_the_registered_family_at_12px_or_more(self):
        intraday = history(80, "2026-11-04T09:{:02d}:00+09:00")
        for snapshot in (history(), intraday):
            for width in (320, 420, 1000):
                for dark in (False, True):
                    for language in ("ko", "en"):
                        with self.subTest(width=width, dark=dark, language=language):
                            root = self.assert_text(chart_svg(snapshot, width=width, dark=dark, language=language,
                                                              indicators=("sma", "ema", "bollinger", "rsi", "macd")))
                            # Drawn 1:1 down to 320px, so 12px labels are not scaled below 12px.
                            self.assertEqual(root.attrib["width"], str(width))
                            for text in root.findall(SVG + "text"):
                                if text.attrib.get("text-anchor") == "middle":
                                    half = len(text.text) * 3.3
                                    self.assertGreaterEqual(float(text.attrib["x"]) - half, 0, text.text)
                                    self.assertLessEqual(float(text.attrib["x"]) + half, width, text.text)
        self.assert_text(chart_svg(MarketSnapshot(ChartRequest(), ())))

    def test_card_labels_use_the_registered_family_at_12px_or_more(self):
        dates = [f"2026-10-{i:02d}" for i in range(1, 29)]
        for width in (220, 360, 900):
            for values in ([2500 + i for i in range(28)], [98765.43 + i for i in range(28)]):
                with self.subTest(width=width, last=values[-1]):
                    root = self.assert_text(card_svg(dates, values, width=width, decimals=2))
                    labels = [t for t in root.findall(SVG + "text") if "," in (t.text or "")]
                    for text in labels:  # right-hand value labels keep about 6.4px per character
                        self.assertLessEqual(float(text.attrib["x"]) + len(text.text) * 6.4, width + 1, text.text)
        self.assert_text(card_svg((), ()))


class ToneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_korean_rise_fall_tokens_meet_aa_on_surfaces_and_pills(self):
        def luminance(value):
            channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
            return sum(c * w for c, w in zip(linear, (.2126, .7152, .0722)))

        def ratio(a, b):
            low, high = sorted((luminance(a), luminance(b)))
            return (high + .05) / (low + .05)
        for palette, dark in ((LIGHT, False), (DARK, True)):
            tones = tone_colors(palette)
            self.assertEqual(tones, TONE_COLORS[dark])
            self.assertEqual(tone_colors(dark), tones)
            for tone in ("up", "down", "flat"):
                for background in (palette.bg, palette.surface, palette.surface_2, tones[tone + "_tint"]):
                    with self.subTest(dark=dark, tone=tone, background=background):
                        self.assertGreaterEqual(ratio(tones[tone], background), 4.5)
        self.assertEqual((TONE_COLORS[False]["up"], TONE_COLORS[False]["down"]), ("#C8343D", "#2F6DB5"))
        self.assertEqual((TONE_COLORS[True]["up"], TONE_COLORS[True]["down"]), ("#F0868C", "#7FB0E8"))
        self.assertEqual([tone_for(v) for v in (1.2, -0.1, 0, None, "x", float("nan"))],
                         ["up", "down", "flat", "flat", "flat", "flat"])

    def test_set_tone_repolishes_a_delta_pill(self):
        host = QLabel()
        host.setStyleSheet(window_stylesheet(LIGHT, False))
        pill = label("+1.20%", "delta")
        pill.setParent(host)
        pill.ensurePolished()
        colour = lambda: pill.palette().color(QPalette.ColorRole.WindowText).name().upper()
        self.assertEqual(colour(), TONE_COLORS[False]["flat"])
        self.assertEqual((pill.font().pixelSize(), pill.font().weight()), (13, 600))
        set_tone(pill, "up")
        self.assertEqual(colour(), "#C8343D")
        set_tone(pill, "down")
        self.assertEqual(colour(), "#2F6DB5")
        with self.assertRaises(ValueError):
            set_tone(pill, "bold")
        with self.assertRaises(ValueError):
            scaled_font(QFont(), 14, 700)  # no real Bold face is bundled

    def test_delta_pill_keeps_its_tint_inside_a_panel(self):
        # Cards are QFrame#panel; `QFrame#panel QLabel { background: transparent }`
        # carries an ID selector and must not strip the pill tint.
        for palette, dark in ((LIGHT, False), (DARK, True)):
            tones = TONE_COLORS[dark]
            root = QWidget()
            root.setStyleSheet(window_stylesheet(palette, dark))
            layout = QVBoxLayout(root)
            box = QFrame()
            box.setObjectName("panel")
            QVBoxLayout(box).addWidget(label("+1.20%", "delta"))
            layout.addWidget(box)
            layout.addWidget(label("+1.20%", "delta"))
            pills = {"inside panel": box.findChild(QLabel), "outside panel": root.findChildren(QLabel)[-1]}
            self.assertIsNot(pills["inside panel"], pills["outside panel"])
            root.resize(300, 200)
            root.show()
            self.app.processEvents()
            try:
                for tone in ("up", "down", "flat"):
                    for where, pill in pills.items():
                        set_tone(pill, tone)
                        self.app.processEvents()
                        image = pill.grab().toImage()
                        tint = {QColor(image.pixel(x, image.height() // 2)).name().upper() for x in range(2, 6)}
                        text = pill.palette().color(QPalette.ColorRole.WindowText).name().upper()
                        with self.subTest(dark=dark, tone=tone, where=where):
                            self.assertEqual(tint, {tones[tone + "_tint"]})
                            self.assertEqual(text, tones[tone])
            finally:
                root.close()
                root.deleteLater()
                self.app.processEvents()


class WindowTypographyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.original_font = cls.app.font()
        cls.family = desktop.load_interface_fonts(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.app.setFont(cls.original_font)

    def setUp(self):
        network = patch("requests.sessions.Session.request", side_effect=AssertionError("network forbidden"))
        self.http = network.start()
        self.addCleanup(network.stop)
        jobs = patch("quantgen_desktop.jobs.Jobs.start", side_effect=AssertionError("no research job"))
        self.jobs = jobs.start()
        self.addCleanup(jobs.stop)
        self.window = ResearchWindow(auto_refresh=False, language="en")
        self.window.resize(1360, 900)
        self.window.show()
        self.drain()
        self.addCleanup(self.close_window)

    def close_window(self):
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            self.window.close()
        self.window.deleteLater()
        self.drain()
        self.http.assert_not_called()
        self.jobs.assert_not_called()

    def drain(self):
        for _ in range(5):
            self.app.processEvents()

    def test_bundled_family_is_registered(self):
        self.assertEqual(self.family, "QG Interface")

    def test_sidebar_is_thinner_and_every_nav_label_fits_in_both_languages(self):
        w = self.window
        low, high = SIDEBAR_WIDTH_RANGE
        for language in ("en", "ko", "en"):
            w.sidebar.setFixedWidth(300)  # proves the language change recomputes the width
            w.set_language(language)
            self.drain()
            with self.subTest(language=language):
                width = w.sidebar.width()
                self.assertLess(width, 222)
                self.assertTrue(low <= width <= high, width)
                font = scaled_font(w.nav["home"].font(), 14, 600)  # the checked (widest) nav font
                for route, button in w.nav.items():
                    text = button.text().replace("&&", "&")
                    self.assertLessEqual(QFontMetrics(font).horizontalAdvance(text) + 2 * NAV_PADDING[1],
                                         button.width(), (route, text))
                for widget in (w.paper_halt, w.theme, w.language):
                    self.assertLessEqual(widget.sizeHint().width(), widget.width(), widget)
                rail_text = [v.text() for v in w.sidebar.findChildren(QLabel)]
                self.assertNotIn("PERSONAL RESEARCH", rail_text)
                self.assertFalse([t for t in rail_text if "Flet" in t or "미리보기" in t or "개인 연구" in t])
        self.assertEqual(w.nav["guide"].text(), "Indicator guide")
        self.assertEqual(w.guide_subtitle.parentWidget().layout().itemAt(0).widget().text(), "Technical indicator guide")
        w.set_language("ko")
        self.drain()
        self.assertEqual(w.nav["guide"].text(), "기술지표 가이드")
        w.set_language("en")
        self.drain()
        self.assertFalse([b.text() for b in w.nav.values() if re.search("[가-힣]", b.text())])

    def test_heading_accent_bar_stays_at_text_height_on_every_page(self):
        # The 3px heading bar is as tall as its label: a heading added to a row
        # beside a taller button without an alignment stretches it to the row height.
        w = self.window
        for language, size in (("en", (1000, 700)), ("ko", (1360, 900))):
            w.set_language(language)
            w.resize(*size)
            for route in w.nav:
                w.navigate(route)
                self.drain()
                page = w.stack.currentWidget()
                for heading in page.findChildren(QLabel):
                    if heading.property("role") != "heading" or not heading.isVisible():
                        continue
                    needed = (heading.heightForWidth(heading.width()) if heading.wordWrap()
                              else heading.sizeHint().height())
                    with self.subTest(language=language, size=size, route=route, text=heading.text()[:30]):
                        self.assertLessEqual(heading.height(), needed + 6)

    def test_type_scale_uses_only_real_weights(self):
        w = self.window
        sheet = w.styleSheet()
        self.assertNotRegex(sheet, r"font-weight:\s*(700|800|900|bold)")
        self.assertFalse("QGraphicsDropShadowEffect" in Path(desktop.__file__).read_text(encoding="utf-8"))
        expected = {"title": (30, 600), "heading": (18, 600), "caption": (12, 400), "number": (32, 600),
                    "brand": (17, 600), "": (14, 400)}
        seen = {}
        for widget in w.findChildren(QLabel):
            role = widget.property("role")
            if role in expected and role not in seen:
                widget.ensurePolished()
                seen[role] = (widget.font().pixelSize(), widget.font().weight())
        self.assertEqual(seen, expected)
        for role, size in (("cardTitle", 15), ("price", 15), ("eyebrow", 12), ("delta", 13)):
            probe = label("MARKETS", role)
            probe.setParent(w.stack.currentWidget().widget())
            probe.ensurePolished()
            self.assertEqual((probe.font().pixelSize(), probe.font().weight()), (size, 600), role)
        for button in w.nav.values():
            button.ensurePolished()
            self.assertEqual(button.font().pixelSize(), 14)
        self.assertIn("QPushButton[nav='true']:checked { font-weight: 600; }", sheet)
        self.assertIn("font-size: 12px; font-weight: 600; }", sheet.split("QHeaderView::section")[1].split("\n")[0])
        self.assertIn("qlineargradient", sheet.split("QFrame#panel {")[1].split("}")[0])
        self.assertIn("border-bottom: 2px solid #D2D5C9", sheet)
        w.theme.setCurrentIndex(1)
        self.assertIn("border-bottom: 2px solid #0A110E", w.styleSheet())

    def test_watchlist_score_header_uses_header_font_and_korean_tones(self):
        from tests.desktop_watchlist_acceptance import sample_rows
        w = self.window
        w.watchlist.set_rows(sample_rows())
        self.drain()
        header = w.watchlist.table.horizontalHeader()
        font = header.title_font()
        self.assertEqual((font.pixelSize(), font.weight()), (12, 600))
        left, title_width = header._group_geometry()
        self.assertGreaterEqual(title_width, QFontMetrics(font).horizontalAdvance("Q-SCORE"))
        self.assertGreaterEqual(w.watchlist.score_help.x(), left + title_width)
        self.assertIn("font-size: 12px; font-weight: 600;", w.watchlist.styleSheet().split("QHeaderView::section")[1])
        badge = next(v for v in w.watchlist.findChildren(QLabel) if v.objectName() == "watchlistTicker")
        badge.ensurePolished()
        self.assertEqual((badge.font().pixelSize(), badge.font().weight()), (12, 600))
        self.assertEqual(w.watchlist.table.item(6, 2).foreground().color().name(), "#c8343d")
        self.assertEqual(w.watchlist.table.item(3, 2).foreground().color().name(), "#2f6db5")
        for language in ("en", "ko"):
            w.set_language(language)
            self.drain()
            for row in range(w.watchlist.table.rowCount()):
                details = w.watchlist.table.cellWidget(row, w.watchlist.detail_column)
                # "Details" used to be clipped on both sides in the 70px column.
                self.assertLessEqual(details.sizeHint().width(), details.width(), (language, details.text()))


class FontLoadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_missing_font_files_are_logged_and_keep_the_platform_font(self):
        before = self.app.font()
        with tempfile.TemporaryDirectory() as empty, \
                patch.object(desktop, "application_root", return_value=Path(empty)), \
                self.assertLogs("quantgen_desktop.app", level="WARNING") as logs:
            self.assertIsNone(desktop.load_interface_fonts(self.app))
        self.assertEqual(self.app.font(), before)
        self.assertTrue(any("qg-interface.otf" in line for line in logs.output))
        self.assertTrue(any("platform font" in line for line in logs.output))


if __name__ == "__main__":
    unittest.main()
