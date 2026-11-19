"""Count what survives after a ResearchWindow is deleted the way the tests delete it (OS-P0-f, D9 group 9).

Run from the root of a scratch copy (git archive), never from the repository checkout; the app code is
imported, not changed:
    cd <scratch copy> && QT_QPA_PLATFORM=offscreen python <repo>/tools/qt_port/repro/window_survivors.py PyQt6|PySide6
2026-11-17 Linux offscreen, main 5888d05: PyQt6 keeps 6 hidden top-level widgets after each window (constant),
PySide6 keeps 6 more per window (6, then 12): the old window's MarketChartPane, BondsPane QComboBox and QFrames,
still referenced from the old ResearchWindow Python object.
"""
import gc
import importlib
import os
import sys

sys.path.insert(0, os.getcwd())
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
BINDING = sys.argv[1] if len(sys.argv) > 1 else "PySide6"
ROUNDS = int(sys.argv[2]) if len(sys.argv) > 2 else 2
W = importlib.import_module(BINDING + ".QtWidgets")
from unittest.mock import patch  # noqa: E402
import dotenv  # noqa: E402
with patch.object(dotenv, "load_dotenv", return_value=False):
    from quantgen_desktop.app import ResearchWindow, load_interface_fonts  # noqa: E402
from tests.qt_fixture_cleanup import delete_owned_widget  # noqa: E402


def census(tag):
    tops = W.QApplication.topLevelWidgets()
    tables = [w for w in W.QApplication.allWidgets() if isinstance(w, W.QTableView)]
    print(f"{BINDING} {tag}: widgets={len(W.QApplication.allWidgets())} tables={len(tables)} top-level={len(tops)}", flush=True)
    return tops


def owners(widget):
    found = []
    for ref in gc.get_referrers(widget):
        if isinstance(ref, dict):
            for obj in gc.get_referrers(ref):
                if getattr(obj, "__dict__", None) is ref:
                    found.append(type(obj).__name__ + "." + next((k for k, v in ref.items() if v is widget), "?"))
    return sorted(set(found))


app = W.QApplication.instance() or W.QApplication([])
app.setStyle("Fusion")
load_interface_fonts(app)
for n in range(ROUNDS):
    window = ResearchWindow(auto_refresh=False, market_loader=lambda: [])
    window.resize(1360, 820)
    window.show()
    for _ in range(6):
        app.processEvents()
    census(f"window {n} shown")
    delete_owned_widget(window)
    del window
    gc.collect()
    for _ in range(6):
        app.processEvents()
    survivors = census(f"window {n} deleted")
for widget in survivors:
    print(f"  survivor {type(widget).__name__} {widget.objectName()!r} held by {owners(widget)}")
