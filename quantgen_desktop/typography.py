"""Type scale and rise/fall tones for the native window (owner request 2026-11-04).

Only the bundled QG Interface weights 400, 500 and 600 are used; asking Qt for 700
draws a synthetic bold from the SemiBold face. Tone colours stay here, next to the
stylesheet that uses them, instead of becoming Palette fields: `core.theme.Palette`
keeps `warning` as its last positional field.

Korean market convention: a rise is red and a fall is blue. Each colour meets WCAG AA
4.5:1 for 13px text on the window surfaces and on its own tinted pill
(docs/compliance/14-contrast.md).
"""
from __future__ import annotations

from PyQt6.QtGui import QColor, QFont

TONES = ("up", "down", "flat")

# Text colour and pill tint per theme. Light values are checked against #FFFEFB,
# #F7F5F0 and #F1F2EB; dark values against #17231D, #101915 and #1E2D25.
TONE_COLORS = {
    False: {"up": "#C8343D", "down": "#2F6DB5", "flat": "#646E68",
            "up_tint": "#FDF0F0", "down_tint": "#EEF4FB", "flat_tint": "#F3F4EE"},
    True: {"up": "#F0868C", "down": "#7FB0E8", "flat": "#A7B8AC",
           "up_tint": "#3A2427", "down_tint": "#1E2F44", "flat_tint": "#26342C"},
}

# Raised-panel depth: a subtle vertical gradient with a lighter top edge and a 2px
# bottom edge. No QGraphicsDropShadowEffect: it re-renders children offscreen on
# every live quote and can blur text at fractional scaling.
PANEL_DEPTH = {
    False: {"top": "#FFFFFF", "bottom": "#FAF9F4", "edge_top": "#ECEDE6", "edge_bottom": "#D2D5C9"},
    True: {"top": "#1B2A23", "bottom": "#15201B", "edge_top": "#3F5649", "edge_bottom": "#0A110E"},
}

# Sidebar geometry: rail margins (left, top, right, bottom), nav padding and limits.
RAIL_MARGINS = (12, 22, 12, 16)
RAIL_SPACING = 5
NAV_PADDING = (9, 14)        # vertical, horizontal
NAV_SLACK = 20               # breathing room beyond the widest label
SIDEBAR_WIDTH_RANGE = (168, 208)
# Owner 2026-11-11 (UI-D7 points 2-3): the rail hides to a thin strip, and Markets opens an indented
# sub-menu. Brand row = symbol + wordmark + the hide toggle; the strip keeps only the show toggle.
RAIL_COLLAPSED_WIDTH = 48
RAIL_TOGGLE_SIZE = 26
BRAND_SYMBOL_SIZE = 32
BRAND_SPACING = 6
SUBNAV_INDENT = 14           # from the nav buttons' left edge to the sub-menu guide line
SUBNAV_PADDING = (7, 12)     # vertical, horizontal (after the 2px guide line): airy rows


def is_dark(palette) -> bool:
    """A palette is dark when its background is darker than mid grey."""
    color = QColor(palette.bg)
    return color.lightnessF() < 0.5


def tone_colors(palette_or_dark) -> dict:
    """Rise/fall/flat colours for a Palette (or a bool meaning dark)."""
    dark = palette_or_dark if isinstance(palette_or_dark, bool) else is_dark(palette_or_dark)
    return dict(TONE_COLORS[dark])


def tone_for(change) -> str:
    """'up', 'down' or 'flat' for a signed change; unknown values are flat."""
    try:
        value = float(change)
    except (TypeError, ValueError):
        return "flat"
    if value != value:  # NaN
        return "flat"
    return "up" if value > 0 else "down" if value < 0 else "flat"


def set_tone(widget, tone: str) -> None:
    """Set the `tone` dynamic property (up/down/flat) and re-polish the widget.

    Stylesheet selectors such as QLabel[role='delta'][tone='up'] are only
    re-evaluated after unpolish/polish, so a changing quote needs both calls.
    """
    if tone not in TONES:
        raise ValueError(f"Unsupported tone: {tone!r}")
    if widget.property("tone") == tone:
        return
    widget.setProperty("tone", tone)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def scaled_font(base: QFont, pixel_size: int, weight: int) -> QFont:
    """A copy of `base` (family and features kept) at a pixel size and weight."""
    if weight not in (400, 500, 600):
        raise ValueError("Only the bundled 400/500/600 weights are allowed")
    font = QFont(base)
    font.setPixelSize(int(pixel_size))
    font.setWeight(QFont.Weight(weight))
    return font


def icon_dir() -> str:
    """Forward-slash path to the bundled chevrons (Qt stylesheet url() needs '/' on Windows too)."""
    from core.app_paths import application_root
    return (application_root() / "assets" / "ui").as_posix()


def controls_stylesheet(p, dark: bool) -> str:
    """Owner, 2026-11-04: no native arrow boxes anywhere ("저 화살표와 네모박스는 어디에서도 보고싶지않다").

    Drop-downs show a thin chevron (up while open) with no box, their lists are rounded, spin boxes
    use the same chevrons, scroll bars are thin with no arrow buttons, and an overflowing tab bar
    scrolls with chevrons instead of boxed arrows.
    """
    icons, theme = icon_dir(), "dark" if dark else "light"
    down, up = f"{icons}/chevron-down-{theme}.svg", f"{icons}/chevron-up-{theme}.svg"
    left, right = f"{icons}/chevron-left-{theme}.svg", f"{icons}/chevron-right-{theme}.svg"
    line = mix(p.border, p.bg, 0.5)  # owner 2026-11-11: light section lines ("구획 선을 연하게")
    return f"""
          QComboBox {{ padding: 5px 30px 5px 10px; }}
          QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: center right; width: 28px; border: 0; background: transparent; }}
          QComboBox::down-arrow {{ image: url({down}); width: 12px; height: 12px; }}
          QComboBox::down-arrow:on {{ image: url({up}); }}
          QComboBox QAbstractItemView {{ background: {p.surface}; color: {p.text}; border: 1px solid {line}; border-radius: 10px; padding: 4px; outline: 0; selection-background-color: {p.accent_soft}; selection-color: {p.text}; }}
          QComboBox QAbstractItemView::item {{ min-height: 26px; padding: 3px 8px; border-radius: 6px; }}
          QAbstractSpinBox {{ padding-right: 26px; }}
          QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{ subcontrol-origin: border; width: 24px; border: 0; background: transparent; }}
          QAbstractSpinBox::up-button {{ subcontrol-position: top right; }}
          QAbstractSpinBox::down-button {{ subcontrol-position: bottom right; }}
          QAbstractSpinBox::up-button:hover, QAbstractSpinBox::down-button:hover {{ background: {p.accent_soft}; border-radius: 4px; }}
          QAbstractSpinBox::up-arrow {{ image: url({up}); width: 10px; height: 10px; }}
          QAbstractSpinBox::down-arrow {{ image: url({down}); width: 10px; height: 10px; }}
          QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px 1px; border: 0; }}
          QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 1px 2px; border: 0; }}
          QScrollBar::handle:vertical {{ background: {p.border}; border-radius: 4px; min-height: 32px; }}
          QScrollBar::handle:horizontal {{ background: {p.border}; border-radius: 4px; min-width: 32px; }}
          QScrollBar::handle:hover {{ background: {p.muted}; }}
          QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; border: 0; background: transparent; }}
          QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
          QPushButton[flat='true'] {{ padding: 0; border: 0; border-radius: 14px; background: transparent; color: {p.muted}; font-size: 18px; font-weight: 400; }}
          QPushButton[flat='true']:hover {{ background: {p.accent_soft}; color: {p.text}; }}
          QTabBar QToolButton {{ border: 0; background: {p.bg}; width: 22px; }}
          QTabBar QToolButton::left-arrow {{ image: url({left}); width: 12px; height: 12px; }}
          QTabBar QToolButton::right-arrow {{ image: url({right}); width: 12px; height: 12px; }}
        """


def popup_stylesheet(p, dark: bool) -> str:
    """Applied directly to a completer popup: a parentless top-level list window that the window
    stylesheet never reaches (markets_view.SymbolCompleter.set_theme)."""
    line = mix(p.border, p.bg, 0.5)  # owner 2026-11-11: light section lines ("구획 선을 연하게")
    return f"""
          QListView {{ background: {p.surface}; color: {p.text}; border: 1px solid {line}; border-radius: 12px;
                       padding: 0; outline: 0; font-size: 13px; }}
          QListView::item {{ min-height: 28px; padding: 3px 10px; border-radius: 8px; color: {p.text}; }}
          QListView::item:selected, QListView::item:hover {{ background: {p.accent_soft}; color: {p.text}; }}
          QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px 1px; border: 0; }}
          QScrollBar::handle:vertical {{ background: {p.border}; border-radius: 4px; min-height: 32px; }}
          QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; border: 0; background: transparent; }}
          QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
        """


def mix(base, other, amount: float) -> str:
    """`amount` of the way from colour `base` toward `other` (0 = base, 1 = other), as #rrggbb."""
    a, b = QColor(base), QColor(other)
    channels = (round(x + (y - x) * amount) for x, y in ((a.red(), b.red()), (a.green(), b.green()), (a.blue(), b.blue())))
    return "#{:02x}{:02x}{:02x}".format(*channels)


def rail_stylesheet(p, dark: bool) -> str:
    """The left rail's own sheet, set on QFrame#sidebar (owner 2026-11-11, UI-D7 points 2-3).

    A widget's own sheet wins over the window sheet, so the rail is styled here without touching
    window_stylesheet. Owner, same day: "모든 화면들의 구획 선을 연하게 ... 한칸한칸 공간을 넓게": the
    rail's right edge is a near-surface line (the surface/background difference does the separating),
    and the Markets sub-items are airy text rows on a faint guide line, with no boxes: the selected one
    turns accent (text and its piece of the guide line).

    The rail's containers are transparent so the sidebar surface shows through. Focus follows the
    `focusRing` property (shell_rail.RailKeys: keyboard focus only), not :focus, so nothing lingers after
    a mouse click or when the window opens. Nav buttons keep their size: a 2px transparent border with
    2px less padding equals the window rule's NAV_PADDING, and only its colour changes for focus.
    """
    nav_v, nav_h = NAV_PADDING
    sub_v, sub_h = SUBNAV_PADDING
    edge, guide = mix(p.surface, p.border, 0.45), mix(p.surface, p.border, 0.8)
    return f"""
          QFrame#sidebar {{ background: {p.surface}; border: 0; border-right: 1px solid {edge}; }}
          QWidget#railPanel, QWidget#railStrip, QWidget#railNav, QWidget#marketSubmenu, QScrollArea#railScroll,
          QScrollArea#railScroll > QWidget {{ background: transparent; }}
          QPushButton[nav='true'] {{ border: 2px solid transparent; padding: {nav_v - 2}px {nav_h - 2}px; }}
          QPushButton[nav='true'][focusRing='true'] {{ border-color: {p.accent}; }}
          QPushButton[nav='true'][focusRing='true']:checked {{ border-color: {p.accent_soft}; }}
          QPushButton[railIcon='true'] {{ padding: 0; border: 1px solid transparent; border-radius: 8px; background: transparent; }}
          QPushButton[railIcon='true']:hover {{ background: {p.accent_soft}; }}
          QPushButton[railIcon='true'][focusRing='true'] {{ border-color: {p.accent}; background: {p.accent_soft}; }}
          QPushButton[subnav='true'] {{ text-align: left; padding: {sub_v}px {sub_h}px; min-height: 18px; border: 0;
                                       border-left: 2px solid {guide}; border-radius: 0; background: transparent;
                                       color: {p.muted}; font-size: 13px; font-weight: 400; letter-spacing: -0.1px; }}
          QPushButton[subnav='true']:hover {{ color: {p.text}; }}
          QPushButton[subnav='true']:checked {{ color: {p.accent}; border-left-color: {p.accent}; font-weight: 600; }}
          QPushButton[subnav='true'][focusRing='true'] {{ color: {p.text}; background: {p.accent_soft}; border-left-color: {p.accent};
                                                         border-top-right-radius: 6px; border-bottom-right-radius: 6px; }}
          QPushButton[subnav='true'][focusRing='true']:checked {{ color: {p.accent}; }}
        """


def window_stylesheet(p, dark: bool) -> str:
    """The research window stylesheet.

    Controls, tables and tabs stay at 13px so dense forms do not clip at 1000x700;
    body labels are 15px; explanatory captions use the real Medium face at
    14px instead of thin 12px text. Table/axis labels keep their own dense scale.
    Each delta rule is repeated under QFrame#panel: the ID selector in
    `QFrame#panel QLabel { background: transparent }` outranks a bare
    QLabel[role='delta'], and cards (MarketCard and the like) are panels.
    """
    t, d = TONE_COLORS[dark], PANEL_DEPTH[dark]
    controls = controls_stylesheet(p, dark)
    nav_v, nav_h = NAV_PADDING
    line = mix(p.border, p.bg, 0.5)  # owner 2026-11-11: light section lines ("구획 선을 연하게")
    return f"""
          QWidget {{ background: {p.bg}; color: {p.text}; font-size: 13px; font-weight: 400; }}
          QFrame#sidebar {{ background: {p.surface}; border-right: 1px solid {p.border}; }}
          QFrame#panel {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {d['top']}, stop:1 {d['bottom']});
                          border: 1px solid {line}; border-radius: 16px; }}
          QFrame#panel QLabel {{ background: transparent; }}
          QLabel {{ background: transparent; font-size: 15px; }}
          QLabel[role='title'] {{ font-size: 30px; font-weight: 600; letter-spacing: -0.6px; }}
          QLabel[role='heading'] {{ font-size: 18px; font-weight: 600; border: 0; border-left: 3px solid {p.accent}; padding-left: 8px; }}
          QLabel[role='cardTitle'] {{ font-size: 15px; font-weight: 600; }}
          QLabel[role='price'] {{ font-size: 15px; font-weight: 600; font-family: "QG Interface"; }}
          QLabel[role='eyebrow'] {{ font-size: 12px; font-weight: 600; letter-spacing: 1px; color: {p.accent}; }}
          QLabel[role='delta'], QFrame#panel QLabel[role='delta'] {{ font-size: 13px; font-weight: 600; font-family: "QG Interface"; padding: 2px 7px; border-radius: 6px; color: {t['flat']}; background: {t['flat_tint']}; }}
          QLabel[role='delta'][tone='up'], QFrame#panel QLabel[role='delta'][tone='up'] {{ color: {t['up']}; background: {t['up_tint']}; }}
          QLabel[role='delta'][tone='down'], QFrame#panel QLabel[role='delta'][tone='down'] {{ color: {t['down']}; background: {t['down_tint']}; }}
          QLabel[role='brand'] {{ font-size: 17px; font-weight: 600; letter-spacing: 0.15px; color: {p.accent}; }}
          QLabel[role='number'] {{ font-size: 32px; font-weight: 600; letter-spacing: -0.6px; font-family: "QG Interface"; }}
          QLabel[role='muted'], QLabel[role='caption'] {{ color: {p.muted}; }}
          QLabel[role='caption'] {{ font-size: 14px; font-weight: 500; }}
          QToolTip {{ background: {p.surface}; color: {p.text}; border: 1px solid {line}; padding: 7px 10px; font-size: 14px; font-weight: 400; }}
          QPushButton {{ padding: 7px 12px; border: 1px solid {line}; border-radius: 8px; background: {p.surface}; font-weight: 500; }}
          QPushButton:hover {{ background: {p.accent_soft}; }}
          QPushButton:focus, QLineEdit:focus, QComboBox:focus {{ border: 2px solid {p.accent}; }}
          QPushButton[primary='true'], QPushButton:checked {{ background: {p.accent}; color: {p.on_accent}; }}
          QPushButton[primary='true'] {{ font-weight: 600; }}
          QPushButton[nav='true'] {{ text-align: left; border: 0; padding: {nav_v}px {nav_h}px; min-height: 20px; font-size: 14px; font-weight: 500; }}
          QPushButton[tool='true'] {{ padding: 7px 12px; border: 0; border-bottom: 2px solid transparent; border-radius: 5px; font-size: 14px; }}
          QPushButton[tool='true']:checked {{ background: {p.accent_soft}; color: {p.accent}; border-bottom: 2px solid {p.accent}; font-weight: 600; }}
          QPushButton[tool='true']:focus {{ border: 2px solid {p.accent}; }}
          QPushButton[nav='true']:checked {{ font-weight: 600; }}
          QPushButton:disabled {{ color: {p.muted}; background: {p.surface_2}; }}
          QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{ min-height: 24px; padding: 5px; border: 1px solid {line}; border-radius: 6px; background: {p.surface}; }}
          QTableWidget {{ font-size: 14px; background: {p.surface}; alternate-background-color: {p.surface_2}; gridline-color: {line}; border: 0; selection-background-color: {p.accent_soft}; selection-color: {p.text}; }}
          QTableWidget::item {{ padding: 4px 8px; }}
          QHeaderView::section {{ padding: 6px 8px; border: 0; background: {p.surface_2}; color: {p.muted}; font-size: 12px; font-weight: 600; }}
          QScrollArea {{ border: 0; }}
          QTabWidget::pane {{ border: 0; }}
          QTabBar::tab {{ background: {p.surface_2}; color: {p.muted}; padding: 7px 12px; margin-right: 4px; border-top-left-radius: 7px; border-top-right-radius: 7px; font-size: 13px; font-weight: 500; }}
          QTabBar::tab:selected {{ background: {p.accent}; color: {p.on_accent}; font-weight: 600; }}
          QTabWidget#marketInnerTabs QTabBar::tab {{ background: transparent; color: {p.muted}; padding: 7px 14px; margin-right: 6px; border: 0; border-bottom: 2px solid transparent; border-radius: 0; }}
          QTabWidget#marketInnerTabs QTabBar::tab:selected {{ background: transparent; color: {p.accent}; border-bottom: 2px solid {p.accent}; font-weight: 600; }}
          QLineEdit#guideSearch {{ min-height: 34px; padding: 6px 12px; border-radius: 20px; font-size: 14px; }}
          QListWidget#guideSuggestions {{ background: {p.surface}; border: 1px solid {line}; border-radius: 14px; padding: 4px; outline: 0; }}
          QListWidget#guideSuggestions::item {{ border-radius: 9px; color: transparent; }}
          QListWidget#guideSuggestions::item:selected, QListWidget#guideSuggestions::item:hover {{ background: {p.accent_soft}; }}
          QPushButton[chip='true'] {{ padding: 6px 12px; border-radius: 15px; font-weight: 500; }}
{controls}          /* Owner UI-D6 (2026-11-11, font mockup N3 "Pretendard 차분"): tighter tracking and every text
             weight one step lighter. Kept last: later rules of equal specificity override the ones above. */
          QLabel {{ letter-spacing: -0.2px; }}
          QLabel[role='title'] {{ letter-spacing: -0.9px; }}
          QLabel[role='heading'], QLabel#watchlistTitle {{ font-weight: 500; letter-spacing: -0.36px; }}
          QLabel[role='cardTitle'], QLabel#watchlistDetailTitle {{ font-weight: 500; letter-spacing: -0.2px; }}
          QLabel[qgRole='verdictTitle'] {{ letter-spacing: -0.4px; }}
          QLabel[role='caption'], QLabel[role='muted'], QLabel[role='eyebrow'] {{ letter-spacing: -0.14px; }}
          QLabel[role='caption'] {{ font-weight: 400; }}
          QTableWidget, QHeaderView, QHeaderView::section {{ letter-spacing: -0.1px; }}
          QHeaderView::section {{ font-weight: 500; }}
          QPushButton, QTabBar::tab, QLineEdit, QComboBox {{ font-weight: 400; letter-spacing: -0.1px; }}
          QPushButton[nav='true'] {{ font-weight: 400; }}
          QPushButton[nav='true']:checked, QPushButton[tool='true']:checked {{ font-weight: 600; }}
          QPushButton[primary='true'] {{ font-weight: 500; }}
          QLabel[role='price'], QLabel[role='delta'], QFrame#panel QLabel[role='delta'] {{ letter-spacing: 0px; }}
          QTabBar::tab {{ font-weight: 400; }}
        """


__all__ = ["TONES", "TONE_COLORS", "PANEL_DEPTH", "RAIL_MARGINS", "RAIL_SPACING", "NAV_PADDING",
           "NAV_SLACK", "SIDEBAR_WIDTH_RANGE", "RAIL_COLLAPSED_WIDTH", "RAIL_TOGGLE_SIZE", "BRAND_SYMBOL_SIZE",
           "BRAND_SPACING", "SUBNAV_INDENT", "SUBNAV_PADDING", "is_dark", "tone_colors", "tone_for", "set_tone",
           "scaled_font", "mix", "window_stylesheet", "rail_stylesheet", "controls_stylesheet",
           "popup_stylesheet", "icon_dir"]
