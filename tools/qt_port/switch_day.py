"""OS-F1 switch day: the edits outside Python files that move the project from PyQt6 to PySide6.

    python tools/qt_port/switch_day.py --check  [ROOT]   # what is still to do (exit 1 if anything is)
    python tools/qt_port/switch_day.py --apply  [ROOT]   # make the edits (idempotent)

Python files (app, tests, tools/packaging/smoke_desktop.py) are rewritten by
`tools/qt_port/pyqt6_to_pyside6.py --apply`; this tool covers the rest: the dependency pin, the CI install
line, the Windows launcher's import check, the build defaults and the README sentence. Each edit is an
exact text replacement, so a file that changed since this list was written shows up as "missing" instead
of being edited blindly. Run both tools on the switch branch, after the UI session's fixes are merged
(docs/platform/PYSIDE6_UI_CHECKLIST.md); main is merged by the main session.
"""
import argparse
from pathlib import Path
import sys

OLD = "Py" + "Qt6"       # spelled in two pieces so the port tool leaves this file alone
NEW = "Py" + "Side6"
PIN_OLD = f'"{OLD}==6.12.0"'
PIN_NEW = f'"{NEW}-Essentials==6.12.0"'

# (file, text today, text after the switch, why)
EDITS = (
    ("pyproject.toml", f"desktop = [{PIN_OLD}]", f"desktop = [{PIN_NEW}]",
     "the desktop extra installs the binding"),
    (".github/workflows/runtime-smoke.yml", f"run: python -m pip install {PIN_OLD}",
     f"run: python -m pip install {PIN_NEW}", "CI installs the pinned Qt runtime"),
    ("Start-QUANTGEN-Desktop.cmd", f'-c "import {OLD}"', f'-c "import {NEW}"',
     "the Windows launcher checks the desktop extra is installed"),
    ("packaging/quantgen_desktop.spec", f'os.environ.get("QG_QT_BINDING", "{OLD}")',
     f'os.environ.get("QG_QT_BINDING", "{NEW}")', "packaged builds default to the new binding"),
    (".github/workflows/platform-build.yml", f"        default: {OLD}\n", f"        default: {NEW}\n",
     "manual platform builds default to the new binding"),
    (".github/workflows/platform-build.yml", f"QG_QT_BINDING: ${{{{ inputs.qt_binding || '{OLD}' }}}}",
     f"QG_QT_BINDING: ${{{{ inputs.qt_binding || '{NEW}' }}}}", "tag builds use the new binding"),
    ("README.md", f"the optional {OLD} research workspace", f"the optional {NEW} (Qt for Python) research workspace",
     "user-facing install note"),
)

# Left to the UI session on the same day (screen text, owned by it): the System screen line that names the
# binding, kept in step in three places so the translation still matches.
UI_TEXT = ("quantgen_desktop/app.py", "quantgen_desktop/translations.py", "core/ui_legacy_messages.py")


def state(root: Path, path: str, old: str, new: str) -> str:
    p = root / path
    if not p.is_file():
        return "missing file"
    text = p.read_text(encoding="utf-8")
    if new in text and old not in text:
        return "done"
    if text.count(old) == 1:
        return "to do"
    return "missing" if old not in text else "ambiguous"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    ap.add_argument("root", nargs="?", default=".")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    problems = pending = 0
    for path, old, new, why in EDITS:
        st = state(root, path, old, new)
        if args.apply and st == "to do":
            p = root / path
            p.write_text(p.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8")
            st = "applied"
        pending += st == "to do"
        problems += st in ("missing", "missing file", "ambiguous")
        print(f"{st:13s} {path}: {why}")
    leftover = [f for f in UI_TEXT if (root / f).is_file() and f"{OLD} " in (root / f).read_text(encoding="utf-8")]
    if leftover:
        print(f"note          screen text still says {OLD} (UI session, same day): {', '.join(leftover)}")
    if problems:
        print(f"{problems} edit(s) no longer match the file: update EDITS in tools/qt_port/switch_day.py", file=sys.stderr)
        return 2
    return 1 if (args.check and pending) else 0


if __name__ == "__main__":
    raise SystemExit(main())
