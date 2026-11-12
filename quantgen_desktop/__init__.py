"""Native PyQt6 QUANTGEN desktop; the Flet browser entry point remains main.py."""


def use_fusion_style():
    """Draw every widget with Qt's Fusion style, on every platform.

    The window's style sheets (typography.py) and every capture and layout test of the native app were made under
    Fusion, which is what Qt picks on Linux. On Windows (the owner's PC) Qt picks its native "windows11" style, which
    gives header sections, table cells, combo boxes and buttons other margins: CI on Windows showed column titles
    4 px off their figures, a macro table 72 px wider than its page and the Markets page scrolling sideways at
    1000 px. Called on import (before or after the QApplication exists) and again when a window is built, so a style
    chosen in between (QT_STYLE_OVERRIDE, a test's own QApplication) cannot leave the app in another style.
    """
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:  # the Flet entry point imports nothing from Qt
        return
    app = QApplication.instance()
    if app is None or app.style() is None or app.style().name().lower() != "fusion":
        QApplication.setStyle("Fusion")


use_fusion_style()
