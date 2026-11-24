"""Self-check of a packaged desktop app: `QUANTGEN --selfcheck <report.json>` (OS-P0-b/2).

Runs inside the frozen app, before any window, and answers the questions a build on a CI runner cannot
answer by looking at files: does the bundled code import, do the bundled fonts load, does provenance record
the calculation hash, is exactly one Qt binding inside. It writes a JSON report (the Windows app has no
console) and exits 0 when every check passes, 1 otherwise. It reads only the app's own folder, computes
the user data folder without creating it, and opens no network connection and no window.
"""
import hashlib
import importlib
import json
import os
import re
from pathlib import Path
import sys
import traceback

BINDINGS = tuple("PyQt6 PySide6".split())  # one string: the port tool leaves it as is
FONT_FILES = ("qg-interface.otf", "qg-interface-medium.otf", "qg-interface-semibold.otf",
              "qg-symbols.otf", "qg-symbols-medium.otf", "qg-symbols-semibold.otf")
CALCULATION_SOURCES = ("montecarlo.py", "garch.py", "history.py")
# Never in a bundle (tools/packaging/stage.py allowlist): checked by name, nothing is opened. Anywhere in a
# path for the first group; only as the bundle's own top folder for the second (libraries ship their own tests).
FORBIDDEN_ANYWHERE = (".env", ".nextgen", "asset_expansion")
FORBIDDEN_TOP = ("_legacy", "tests", "qa", "docs", "papers")
# The two recorded-status files the System screen verifies (tools/packaging/stage.py FILES).
ALLOWED_PROTECTED = ("qa/research_status.json", "qa/acceptance_results.json")


def _check(results, name, fn):
    try:
        ok, detail = fn()
    except Exception as exc:  # a broken bundle shows up here; the report must still be written
        ok, detail = False, "".join(traceback.format_exception_only(type(exc), exc)).strip()
    results.append({"check": name, "ok": bool(ok), "detail": detail})


def expected_calculation_sha256(quant_dir: Path):
    """The same digest as core.research.provenance.code_evidence(), from the given folder."""
    digest = hashlib.sha256()
    for name in CALCULATION_SOURCES:
        digest.update(name.encode() + b"\0" + (quant_dir / name).read_bytes() + b"\0")
    return digest.hexdigest()


def run(report_path: str) -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    results = []
    info = sys.modules.get("core._build_info")
    binding = getattr(info, "QT_BINDING", None)

    _check(results, "frozen", lambda: (bool(getattr(sys, "frozen", False)), getattr(sys, "_MEIPASS", None)))
    _check(results, "build_info", lambda: (info is not None and binding in BINDINGS, {
        k: getattr(info, k, None) for k in ("CHANNEL", "QT_BINDING", "SOURCE_COMMIT", "CALCULATION_SHA256")}))

    def one_binding():
        found = [b for b in BINDINGS if importlib.util.find_spec(b) is not None]
        return found == [binding], found
    _check(results, "single_qt_binding", one_binding)

    def root_and_assets():
        from core.app_paths import application_root
        root = application_root()
        need = ["README.md", "assets/branding/f1-symbol.svg"] + [f"assets/fonts/{f}" for f in FONT_FILES]
        missing = [n for n in need if not (root / n).is_file()]
        return not missing, {"root": str(root), "missing": missing}
    _check(results, "application_root_assets", root_and_assets)

    def provenance():
        from core.research.provenance import code_evidence
        got = code_evidence().get("calculation_sha256")
        want = getattr(info, "CALCULATION_SHA256", None)
        return got is not None and got == want, {"recorded": got, "built_from": want}
    _check(results, "code_evidence_hash", provenance)

    def data_dir():
        from core.app_paths import user_data_dir
        path = user_data_dir()
        return True, {"user_data_dir": str(path), "exists": path.is_dir()}
    _check(results, "user_data_dir", data_dir)

    def credential_store():
        # Keys live in the OS store (core/credentials): Windows Credential Manager, macOS Keychain. Only asks keyring
        # which backend it would use; nothing is read or written. Linux build machines often have none: reported only.
        from core import credentials
        available = credentials.keyring_available()
        required = sys.platform in ("win32", "darwin")
        return available or not required, {"available": available, "required_on_this_platform": required}
    _check(results, "os_credential_store", credential_store)
    def sale_build_contents():
        # Item 15-7: no flet-cli-only package and no retired NEXTGEN logo inside; the data-source profile is reported.
        root = Path(getattr(sys, "_MEIPASS", "."))
        cli_only = ("flet_cli", "cookiecutter", "slugify", "text_unidecode", "binaryornot", "chardet")
        found = sorted({p.relative_to(root).parts[0] for p in root.iterdir()
                        if p.name.split(".")[0].split("-")[0] in cli_only})
        found += [m for m in cli_only if importlib.util.find_spec(m) is not None and m not in found]
        logos = sorted(str(p.relative_to(root)) for p in (root / "assets").glob("nextgen_logo_*"))
        from core import app_identity
        return not found and not logos, {"flet_cli_only": found, "retired_logos": logos,
                                         "gateway_profile": getattr(app_identity, "GATEWAY_PROFILE", None)}
    _check(results, "sale_build_contents", sale_build_contents)

    def bundle_names():
        root = Path(getattr(sys, "_MEIPASS", "."))
        bad = []
        for p in root.rglob("*"):
            parts = p.relative_to(root).parts
            name = "/".join(parts)
            if name in ALLOWED_PROTECTED or (parts == ("qa",) and p.is_dir()):
                continue
            if parts[0] in FORBIDDEN_TOP or any(x in FORBIDDEN_ANYWHERE for x in parts):
                bad.append(str(p.relative_to(root)))
        return not bad, sorted(bad)[:20]
    _check(results, "no_protected_files", bundle_names)

    def notices_and_qt_libraries():
        root = Path(getattr(sys, "_MEIPASS", "."))
        notices = root / "licenses" / "THIRD_PARTY_NOTICES.txt"
        text = notices.read_text(encoding="utf-8") if notices.is_file() else ""
        lgpl_needed = binding == "PySide6"
        has_lgpl = "GNU LESSER GENERAL PUBLIC LICENSE" in text
        # LGPL relinking: the Qt core library must be a separate file a user can replace, not inside the archive.
        qt_core = sorted(str(p.relative_to(root)) for p in root.rglob("*")
                         if p.is_file() and re.fullmatch(r"(lib)?Qt6?Core(\.dll|\.so(\.\d+)*)?", p.name))
        ok = bool(text) and (has_lgpl or not lgpl_needed) and bool(qt_core)
        return ok, {"notices_bytes": len(text.encode()), "lgpl_text": has_lgpl, "qt_core_files": qt_core[:4]}
    _check(results, "licence_notices_and_separate_qt", notices_and_qt_libraries)

    def recorded_status():
        # The System screen's "project status": the same call as quantgen_desktop/app.py.
        from core.app_paths import application_root
        from tools.status.snapshot import verify
        status = verify(application_root())
        return isinstance(status, dict), sorted(status)[:6]
    _check(results, "recorded_project_status", recorded_status)

    app = None

    def qt_and_fonts():
        nonlocal app
        widgets = importlib.import_module(f"{binding}.QtWidgets")
        gui = importlib.import_module(f"{binding}.QtGui")
        app = widgets.QApplication.instance() or widgets.QApplication([sys.argv[0]])
        from core.app_paths import assets_directory
        loaded = {}
        for name in FONT_FILES:
            fid = gui.QFontDatabase.addApplicationFont(str(Path(assets_directory()) / "fonts" / name))
            loaded[name] = list(gui.QFontDatabase.applicationFontFamilies(fid)) if fid >= 0 else []
        ok = all(any(f.startswith(("QG Interface", "QG Symbols")) for f in fams) for fams in loaded.values())
        return ok, loaded
    _check(results, "qt_offscreen_fonts", qt_and_fonts)

    def app_imports():
        importlib.import_module("quantgen_desktop.app")
        return True, "quantgen_desktop.app imported"
    _check(results, "app_module_imports", app_imports)

    report = {"ok": all(r["ok"] for r in results), "platform": sys.platform, "results": results}
    Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report["ok"] else 1
