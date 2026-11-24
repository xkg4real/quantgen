"""What a packaged Linux desktop build needs from the machine it runs on (OS-F3, 2026-11-24).

    python tools/packaging/linux_runtime_report.py dist/QUANTGEN [--json report.json]

Reads only the built app folder (never the user's home or data folder) and reports:
  * glibc: the newest GLIBC_x.y symbol version any bundled ELF file asks for, and the files that ask for it.
    PyInstaller copies system libraries from the build machine, so a build made on a new distribution does
    not start on an older one (measured 2026-11-24: an Ubuntu 24.04 build needs GLIBC_2.38).
  * qt_platform_plugins: for libqxcb.so (X11) and libqwayland*.so (Wayland), the shared libraries `ldd` cannot
    find on this machine (for X11 Qt 6 needs, among others, libxcb-cursor0, which many desktops lack).
Needs `objdump` (binutils) and `ldd`; a missing tool is reported, not fatal. Exit code 0 always: it is a report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

GLIBC = re.compile(r"GLIBC_(\d+)\.(\d+)(?:\.(\d+))?")
PLATFORM_PLUGINS = ("libqxcb.so", "libqwayland")


def _is_elf(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            return fh.read(4) == b"\x7fELF"
    except OSError:
        return False


def newest_glibc(text: str):
    """The highest GLIBC_x.y[.z] in objdump -T output, as a tuple, or None."""
    found = [tuple(int(g or 0) for g in m.groups()) for m in GLIBC.finditer(text)]
    return max(found) if found else None


def _glibc_name(version):
    if version is None:
        return None
    major, minor, patch = version
    return f"GLIBC_{major}.{minor}" + (f".{patch}" if patch else "")


def missing_libraries(ldd_output: str) -> list[str]:
    """Library names `ldd` printed as `=> not found`, once each, in order."""
    out = []
    for line in ldd_output.splitlines():
        if "=> not found" in line:
            name = line.split("=>")[0].strip()
            if name not in out:
                out.append(name)
    return out


def _run(cmd) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def report(app_dir: Path) -> dict:
    app_dir = Path(app_dir)
    tools = {t: shutil.which(t) is not None for t in ("objdump", "ldd")}
    elves = sorted(p for p in app_dir.rglob("*") if p.is_file() and not p.is_symlink() and _is_elf(p))
    newest, holders = None, []
    if tools["objdump"]:
        for path in elves:
            v = newest_glibc(_run(["objdump", "-T", str(path)]))
            if v is None:
                continue
            if newest is None or v > newest:
                newest, holders = v, [path]
            elif v == newest:
                holders.append(path)
    plugins = {}
    if tools["ldd"]:
        for path in elves:
            if path.name.startswith(PLATFORM_PLUGINS):
                plugins[str(path.relative_to(app_dir))] = missing_libraries(_run(["ldd", str(path)]))
    return {
        "app_dir": str(app_dir),
        "tools": tools,
        "elf_files": len(elves),
        "glibc_required": _glibc_name(newest),
        "glibc_holders": [str(p.relative_to(app_dir)) for p in holders[:15]],
        "glibc_holders_total": len(holders),
        "qt_platform_plugins_missing": plugins,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("app_dir")
    ap.add_argument("--json", help="also write the report to this file")
    args = ap.parse_args(argv)
    result = report(Path(args.app_dir))
    text = json.dumps(result, indent=1, ensure_ascii=False)
    print(text)
    if args.json:
        Path(args.json).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
