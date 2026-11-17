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
try:
    commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
except Exception:
    commit = "unknown"
hook_dir = Path(workpath) / "qg_hooks"
hook_dir.mkdir(parents=True, exist_ok=True)
hook = hook_dir / "rthook_build_info.py"
hook.write_text((ROOT / "packaging" / "rthook_build_info.py.in").read_text(encoding="utf-8")
                .replace("@CHANNEL@", CHANNEL).replace("@BINDING@", BINDING).replace("@COMMIT@", commit),
                encoding="utf-8")

# Every allowlisted module of the app packages, so lazily imported screens are bundled too.
hidden = sorted({n[:-3].replace("/", ".").removesuffix(".__init__") for n in names
                 if n.endswith(".py") and allowed(n) and n.split("/")[0] in ("core", "data", "ui", "quantgen_desktop")})

a = Analysis(
    [str(ROOT / "packaging" / "launch_desktop.py")],
    pathex=[str(ROOT)],
    datas=datas,
    hiddenimports=hidden,
    runtime_hooks=[str(hook)],
    excludes=OTHER + ["tkinter", "tests", "qa", "_legacy"],
    noarchive=False,
)
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
    app = BUNDLE(
        coll,
        name="QUANTGEN.app",
        icon=None,
        bundle_identifier=None,  # set from core/app_identity.BUNDLE_ID once the owner confirms it
        info_plist={"NSHighResolutionCapable": True, "CFBundleShortVersionString": "2.0.0"},
    )
