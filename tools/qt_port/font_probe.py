"""Font fallback probe for the PySide6 port (OS-P0-f, D9 group 8). Reads quantgen_desktop/font_policy.py
only as a reference; it never imports or changes it.

PySide6 has neither QChar nor the four QFontDatabase application-fallback functions that
quantgen_desktop/font_policy.py uses today. This probe draws the same Korean, figure, Greek and symbol
lines with each way of choosing fonts and records, character by character, which font family Qt really
used, so the alternatives can be compared with today's PyQt6 result.

Methods (`--method`):
  fallback       today's way: app font families + addApplicationFallbackFontFamily per script (PyQt6 only)
  families       QFont.setFamilies([...]) only
  substitutions  QFont.insertSubstitutions(interface, [symbols]) only
  both           setFamilies + insertSubstitutions
  none           no fallback set up (control)

Each method is measured on two kinds of font, because they behave differently:
  app     the application font (setFamilies list, what most widgets inherit)
  single  a font naming only the interface family (what a style sheet `font-family:` or QFont(name) gives)
  other   a font naming a platform family without Hangul (DejaVu Sans; Segoe UI on Windows)

Usage (run each binding in its own virtual environment):
  python -m tools.qt_port.font_probe --binding PyQt6 --method fallback --out OUT
  python -m tools.qt_port.font_probe --binding PySide6 --method families --out OUT
  python -m tools.qt_port.font_probe --compare OUT     # writes OUT/FONT_PROBE.md from the JSON files
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import platform
import sys

INTERFACE = "QG Interface"
SYMBOLS = "QG Symbols"
FONT_FILES = ("qg-interface.otf", "qg-interface-medium.otf", "qg-interface-semibold.otf",
              "qg-symbols.otf", "qg-symbols-medium.otf", "qg-symbols-semibold.otf")
LINES = (
    ("hangul", "가격 상승 하락 거래대금 한글 원화"),
    ("figures", "0123456789 1,255,000 -3.25% +12.5%"),
    ("greek", "α β γ δ σ μ Δ Σ"),
    ("symbols", "× ÷ ± − · … → ← ↑ ↓ ▲ ▼ ● ○ ≈ ≤ ≥ ₩ ‰ ①"),
    ("outside", "✕ ★ 株"),  # not in the bundled fonts: the platform decides
)
METHODS = ("fallback", "families", "substitutions", "both", "none")
FONT_KINDS = ("app", "single", "other")
# A platform family without Hangul, as a widget would get from a style sheet naming another font.
OTHER = "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"
DEFAULT_FONTS = Path(__file__).resolve().parents[2] / "assets" / "fonts"


def _qt(binding):
    core = importlib.import_module(f"{binding}.QtCore")
    gui = importlib.import_module(f"{binding}.QtGui")
    widgets = importlib.import_module(f"{binding}.QtWidgets")
    return core, gui, widgets


def _setup(binding, method, gui, core):
    db = gui.QFontDatabase
    if method in ("fallback",):
        qchar = getattr(core, "QChar", None)
        if qchar is None or not hasattr(db, "addApplicationFallbackFontFamily"):
            return f"unsupported in {binding}: QChar or addApplicationFallbackFontFamily is missing"
        for script in (qchar.Script.Script_Common, qchar.Script.Script_Greek, qchar.Script.Script_Hangul):
            for family in (INTERFACE, SYMBOLS):
                if family not in db.applicationFallbackFontFamilies(script):
                    db.addApplicationFallbackFontFamily(script, family)
    if method in ("substitutions", "both"):
        gui.QFont.insertSubstitutions(INTERFACE, [SYMBOLS])
        gui.QFont.insertSubstitutions(OTHER, [INTERFACE, SYMBOLS])
    return None


def _font(kind, method, gui):
    font = gui.QFont(OTHER if kind == "other" else INTERFACE)
    font.setPixelSize(20)
    if kind == "app" and method in ("fallback", "families", "both"):
        font.setFamilies([INTERFACE, SYMBOLS])
    return font


def _family_of(ch, font, gui):
    layout = gui.QTextLayout(ch, font)
    layout.beginLayout()
    layout.createLine()
    layout.endLayout()
    runs = layout.glyphRuns()
    if not runs:
        return "(no glyph run)"
    raw = runs[0].rawFont()
    indexes = list(runs[0].glyphIndexes())
    family = raw.familyName()
    return family + (" [missing glyph]" if not indexes or indexes[0] == 0 else "")


def probe(binding, method, out: Path, fonts: Path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    core, gui, widgets = _qt(binding)
    app = widgets.QApplication.instance() or widgets.QApplication([])
    loaded = []
    for name in FONT_FILES:
        fid = gui.QFontDatabase.addApplicationFont(str(fonts / name))
        loaded.append({"file": name, "id": fid, "families": list(gui.QFontDatabase.applicationFontFamilies(fid)) if fid >= 0 else []})
    note = _setup(binding, method, gui, core)
    result = {"binding": binding, "binding_version": getattr(importlib.import_module(binding), "__version__", None)
              or getattr(core, "PYQT_VERSION_STR", None), "qt_version": core.qVersion(), "method": method,
              "platform": f"{platform.system()} {platform.release()} QPA={os.environ.get('QT_QPA_PLATFORM')}",
              "python": sys.version.split()[0], "fonts_loaded": loaded, "note": note, "chars": {}}
    if note is None:
        for kind in FONT_KINDS:
            font = _font(kind, method, gui)
            result["chars"][kind] = {ch: _family_of(ch, font, gui)
                                     for _, text in LINES for ch in dict.fromkeys(text) if not ch.isspace()}
        _png(out / f"{binding}_{method}.png", binding, method, gui, core)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{binding}_{method}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{binding} {method}: {'written' if note is None else note}")
    del app


def _png(path: Path, binding, method, gui, core):
    width, row = 980, 34
    image = gui.QImage(width, row * (len(LINES) * len(FONT_KINDS) + 1) + 12, gui.QImage.Format.Format_ARGB32)
    image.fill(gui.QColor("white"))
    painter = gui.QPainter(image)
    painter.setRenderHint(gui.QPainter.RenderHint.TextAntialiasing)
    label = gui.QFont("DejaVu Sans")
    label.setPixelSize(13)
    painter.setFont(label)
    painter.setPen(gui.QColor("#444444"))
    painter.drawText(10, 22, f"{binding} / {method} (Qt {core.qVersion()}, offscreen)")
    y = row
    for kind in FONT_KINDS:
        font = _font(kind, method, gui)
        for name, text in LINES:
            y += row
            painter.setFont(label)
            painter.setPen(gui.QColor("#666666"))
            painter.drawText(10, y, f"{kind}/{name}")
            painter.setFont(font)
            painter.setPen(gui.QColor("black"))
            painter.drawText(150, y, text)
    painter.end()
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(path))


def compare(out: Path):
    runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(out.glob("*.json"))]
    base = next((r for r in runs if r["binding"] == "PyQt6" and r["method"] == "fallback" and r["chars"]), None)
    lines = ["# Font fallback probe", "", "Generated by `python -m tools.qt_port.font_probe --compare`. "
             "Each cell is the font family Qt used for that character; [missing glyph] means a blank box.", ""]
    lines += ["| run | Qt | platform | note |", "|---|---|---|---|"]
    for r in runs:
        lines.append(f"| {r['binding']} {r['binding_version']} / {r['method']} | {r['qt_version']} | {r['platform']} | {r['note'] or ''} |")
    verdicts = []
    for kind in FONT_KINDS:
        cols = [r for r in runs if r["chars"]]
        lines += ["", f"## Font kind: {kind}", "", "| char | " + " | ".join(f"{r['binding']}/{r['method']}" for r in cols) + " |",
                  "|---|" + "---|" * len(cols)]
        chars = list(dict.fromkeys(ch for r in cols for ch in r["chars"].get(kind, {})))
        for ch in chars:
            lines.append(f"| {ch} | " + " | ".join(r["chars"][kind].get(ch, "") for r in cols) + " |")
    if base:
        lines += ["", "## Same as today (PyQt6 / fallback) for every character?", "",
                  "| run | app font | single-family font | other-family font |", "|---|---|---|---|"]
        for r in runs:
            if not r["chars"] or r is base:
                continue
            same = [all(r["chars"][k].get(ch) == v for ch, v in base["chars"][k].items()) for k in FONT_KINDS]
            diff = {k: [ch for ch, v in base["chars"][k].items() if r["chars"][k].get(ch) != v] for k in FONT_KINDS}
            cell = lambda ok, k: "yes" if ok else "no: " + " ".join(diff[k])
            lines.append(f"| {r['binding']}/{r['method']} | " + " | ".join(cell(ok, k) for ok, k in zip(same, FONT_KINDS)) + " |")
            verdicts.append((r["binding"], r["method"], same))
    (out / "FONT_PROBE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out / 'FONT_PROBE.md'}")
    return verdicts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--binding", choices=("PyQt6", "PySide6"))
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--fonts", type=Path, default=DEFAULT_FONTS)
    ap.add_argument("--compare", type=Path)
    args = ap.parse_args(argv)
    if args.compare:
        compare(args.compare)
        return 0
    if not (args.binding and args.method and args.out):
        ap.error("--binding, --method and --out are required (or use --compare OUT)")
    probe(args.binding, args.method, args.out, args.fonts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
