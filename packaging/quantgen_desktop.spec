# PyInstaller spec for the native desktop app (OS-P0-b), binding-neutral.
#
#   QG_QT_BINDING=PyQt6|PySide6   Qt binding to bundle (default PyQt6 until the OS-F1 switch). The other
#                                 binding is excluded: PyInstaller's Qt hooks refuse a build that collects
#                                 two Qt binding packages.
#   QG_BUILD_CHANNEL=public|beta|dev   build channel baked in (default public; see core/app_identity.py)
#
#   pyinstaller --noconfirm --clean packaging/quantgen_desktop.spec      (from the repository root)
#
# Data files come from the same allowlist as the wheel (tools/packaging/stage.py), read from `git ls-files`,
# so research stores, caches and .env files can never be bundled. Output: dist/QUANTGEN/ (onedir).
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent
sys.path.insert(0, str(ROOT))
from tools.packaging.stage import allowed  # noqa: E402

BINDINGS = ("PyQt6", "PySide6")
BINDING = os.environ.get("QG_QT_BINDING", "PyQt6")
if BINDING not in BINDINGS:
    raise SystemExit(f"QG_QT_BINDING must be one of {BINDINGS}, not {BINDING!r}")
OTHER = [b for b in BINDINGS if b != BINDING]
if BINDING == "PyQt6":
    OTHER.append("shiboken6")   # PySide6's runtime; PyQt6 uses its own sip module
CHANNEL = os.environ.get("QG_BUILD_CHANNEL", "public")
if CHANNEL not in ("public", "beta", "dev"):
    raise SystemExit("QG_BUILD_CHANNEL must be public, beta or dev")

names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
datas = [(str(ROOT / n), str(Path(n).parent)) for n in names
         if n and allowed(n) and not n.endswith(".py") and n not in ("pyproject.toml",)]
# qa/research_status.json and qa/acceptance_results.json are in on purpose: the System screen's project
# status (quantgen_desktop/app.py -> tools.status.snapshot.verify(application_root())) reads them.
# core/research/provenance.py code_evidence() hashes these sources from disk; ship them as files so a packaged
# app records the same calculation_sha256 as a checkout instead of None.
datas += [(str(ROOT / "core" / "quant" / n), "core/quant") for n in ("montecarlo.py", "garch.py", "history.py")]
try:
    commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
except Exception:
    commit = "unknown"
sys.path.insert(0, str(ROOT / "packaging"))
from selfcheck import expected_calculation_sha256  # noqa: E402
calc_sha256 = expected_calculation_sha256(ROOT / "core" / "quant")
hook_dir = Path(workpath) / "qg_hooks"
hook_dir.mkdir(parents=True, exist_ok=True)
hook = hook_dir / "rthook_build_info.py"
hook.write_text((ROOT / "packaging" / "rthook_build_info.py.in").read_text(encoding="utf-8")
                .replace("@CHANNEL@", CHANNEL).replace("@BINDING@", BINDING).replace("@COMMIT@", commit)
                .replace("@CALC_SHA256@", calc_sha256),
                encoding="utf-8")

# Item 15-7 (sale build): packages only the flet-cli build tool needs (flet[all] -> flet-cli -> cookiecutter ->
# python-slugify -> text-unidecode [Artistic], binaryornot/flet-cli -> chardet [LGPL]). The app never uses them;
# requests falls back to charset-normalizer (MIT). Excluded so they are not shipped or licensed.
FLET_CLI_ONLY = ["flet_cli", "cookiecutter", "slugify", "text_unidecode", "binaryornot", "chardet"]
# LGPL pure-Python packages that are shipped stay plain .py files (below). chardet was the only one (found by
# tools/packaging/third_party_notices.py, 2026-11-17) and is excluded above, so the list is empty today.
LGPL_PURE_PYTHON = ()

# Every allowlisted module of the app packages, so lazily imported screens are bundled too.
hidden = sorted({n[:-3].replace("/", ".").removesuffix(".__init__") for n in names
                 if n.endswith(".py") and allowed(n) and n.split("/")[0] in ("core", "data", "ui", "quantgen_desktop")})

a = Analysis(
    [str(ROOT / "packaging" / "launch_desktop.py")],
    pathex=[str(ROOT), str(ROOT / "packaging")],
    datas=datas,
    hiddenimports=hidden,
    runtime_hooks=[str(hook)],
    excludes=OTHER + FLET_CLI_ONLY + ["tkinter", "tests", "qa", "_legacy"],
    noarchive=False,
    # LGPL pure-Python packages stay plain .py files next to the app (not inside the PYZ archive), so a user
    # can replace them like the Qt shared libraries (docs/platform/LICENSE_COMPLIANCE_PREP.md).
    module_collection_mode={name: "py" for name in LGPL_PURE_PYTHON},
)
# Third-party notices for what is actually inside (tools/packaging/third_party_notices.py), at licenses/.
from tools.packaging.third_party_notices import notices_text  # noqa: E402
collected = {name.split(".")[0] for name, *_ in a.pure} | {Path(dest).parts[0] for dest, *_ in a.binaries}
# Packages kept as plain .py files (module_collection_mode "py") leave a.pure; list them too. Measured 2026-11-24:
# main de32ea1 shipped chardet's 43 files with no chardet entry in the notices.
collected |= set(LGPL_PURE_PYTHON)
notice_text, notice_dists = notices_text(sorted(collected))
notice_file = hook_dir / "THIRD_PARTY_NOTICES.txt"
notice_file.write_text(notice_text, encoding="utf-8")
a.datas += [("licenses/THIRD_PARTY_NOTICES.txt", str(notice_file), "DATA")]
print(f"QUANTGEN: third-party notices for {len(notice_dists)} distributions")

pyz = PYZ(a.pure)
icon = ROOT / "assets" / ("icon.ico" if sys.platform == "win32" else "icon.png")
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="QUANTGEN",
    console=False,
    icon=str(icon) if icon.exists() else None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="QUANTGEN")
if sys.platform == "darwin":
    import tomllib
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    png = ROOT / "assets" / "icon.png"
    app = BUNDLE(
        coll,
        name="QUANTGEN.app",
        # PyInstaller turns the PNG into the .icns the Dock and Finder show (needs Pillow: matplotlib brings it).
        icon=str(png) if png.exists() else None,
        bundle_identifier=None,  # set from core/app_identity.BUNDLE_ID once the owner confirms it
        info_plist={
            "CFBundleName": "QUANTGEN",
            "CFBundleDisplayName": "QUANTGEN",
            "CFBundleShortVersionString": version,  # pyproject.toml, not a second copy of the number
            "CFBundleVersion": version,
            "LSMinimumSystemVersion": "14.0",  # PySide6 / PyQt6 6.12 wheels need macOS 14 (LICENSE_COMPLIANCE_PREP)
            "NSHighResolutionCapable": True,
        },
    )
