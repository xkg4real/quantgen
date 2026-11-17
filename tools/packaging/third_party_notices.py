"""Third-party notices for a packaged app (OS-P0-b/3). Not legal advice (법률 자문이 아닙니다).

    python tools/packaging/third_party_notices.py --modules numpy PySide6 ... --output NOTICES.txt

Lists, for every installed distribution that provides one of the given top-level modules, its name,
version and declared licence, followed by the full text of each licence file the distribution ships.
packaging/quantgen_desktop.spec calls notices_text() with the modules PyInstaller collected, so the list
matches what is inside the build. When the Qt for Python binding (PySide6, shiboken6) is inside, the
LGPL-3.0 and GPL-3.0 texts (packaging/licenses/) and a note on replacing the Qt libraries are added,
because the PySide6 wheels themselves ship no LGPL text. Whether this meets the LGPL for a sold app is for
a lawyer to confirm (docs/platform/LICENSE_COMPLIANCE_PREP.md).
"""
import argparse
import importlib.metadata as md
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
LICENCE_FILE = re.compile(r"(^|/)(LICEN[CS]E|COPYING|NOTICE|AUTHORS)[^/]*$", re.I)
QT_FOR_PYTHON = {"pyside6", "pyside6-essentials", "pyside6-addons", "shiboken6"}
OWN = {"quantgen", "quantgen-mobile"}

QT_NOTE = """\
Qt for Python (PySide6, shiboken6) and the Qt libraries it loads are used under the GNU Lesser General
Public License v3.0 (texts below). They are kept as separate shared libraries in the application folder
(Windows: _internal\\PySide6\\Qt6*.dll; macOS: Contents/Frameworks/PySide6/Qt/lib/*.framework;
Linux: _internal/PySide6/Qt/lib/libQt6*.so*), so they can be replaced with a compatible modified version.
Qt source code: https://download.qt.io/official_releases/qt/ ; Qt for Python source:
https://download.qt.io/official_releases/QtForPython/ (the same versions as listed above).
"""


def distributions_for(modules):
    """Installed distributions providing the given top-level module names, by normalised name."""
    owners = md.packages_distributions()
    names = set()
    for module in modules:
        for dist in owners.get(module.split(".")[0], ()):
            names.add(dist)
    found = {}
    for name in names:
        try:
            dist = md.distribution(name)
        except md.PackageNotFoundError:
            continue
        key = re.sub(r"[-_.]+", "-", dist.metadata["Name"]).lower()
        if key not in OWN:
            found[key] = dist
    return dict(sorted(found.items()))


def declared_licence(dist):
    meta = dist.metadata
    expression = meta.get("License-Expression")
    if expression:
        return expression
    text = (meta.get("License") or "").strip()
    if text and "\n" not in text and len(text) < 120:
        return text
    classifiers = [c.split("::")[-1].strip() for c in meta.get_all("Classifier") or [] if c.startswith("License ::")]
    return "; ".join(classifiers) or "see licence text below (not declared in metadata)"


def licence_texts(dist):
    out = []
    for f in dist.files or ():
        if LICENCE_FILE.search(str(f)):
            try:
                out.append((str(f), Path(dist.locate_file(f)).read_text(encoding="utf-8", errors="replace")))
            except OSError:
                pass
    return out


def notices_text(modules, *, product="QUANTGEN"):
    dists = distributions_for(modules)
    lines = [f"{product} third-party notices", "", "Generated at build time from the installed packages "
             "that are inside this build.", ""]
    for key, dist in dists.items():
        lines.append(f"- {dist.metadata['Name']} {dist.version}: {declared_licence(dist)}")
    qt = sorted(QT_FOR_PYTHON & set(dists))
    if qt:
        lines += ["", "=" * 78, "Qt for Python", "=" * 78, QT_NOTE]
    for key, dist in dists.items():
        for name, text in licence_texts(dist):
            lines += ["", "=" * 78, f"{dist.metadata['Name']} {dist.version} — {name}", "=" * 78, text.rstrip()]
    if qt:
        for name in ("LGPL-3.0.txt", "GPL-3.0.txt"):
            lines += ["", "=" * 78, f"{name[:-4]} (Qt for Python, Qt)", "=" * 78,
                      (ROOT / "packaging" / "licenses" / name).read_text(encoding="utf-8").rstrip()]
    return "\n".join(lines) + "\n", sorted(dists)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--modules", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    text, names = notices_text(args.modules)
    Path(args.output).write_text(text, encoding="utf-8")
    print(f"{len(names)} distributions -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
