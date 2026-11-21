"""Copy an explicit runtime allowlist; never traverse research or secret stores.

python tools/packaging/stage.py --output /tmp/quantgen-build
python tools/packaging/stage.py --profile mobile --output /tmp/quantgen-mobile
The destination must be new. This is an install smoke stage, not a research archive.

Profile `mobile` (OS-P0-b, Flet Android trial): the Flet app (main.py, ui/, core/, data/) without Qt. Of
quantgen_desktop it keeps only the modules the Flet side imports (and what they import), and refuses to stage
if any of them imports a Qt binding. mobile/pyproject.toml replaces the root pyproject.toml.
"""
from pathlib import Path, PurePosixPath
import argparse
import ast
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FILES = {"pyproject.toml", "README.md", "main.py", "config.py", "tools/__init__.py",
         "qa/research_status.json", "qa/acceptance_results.json", "assets/manifest.json"}
DATA_PREFIXES = ("core/calendars/data/", "core/ficc/schemas/", "core/skills/macro_workflows/",
                 "data/calendars/", "core/market/data/")
DATA_FILES = {"data/macro/series_registry.yaml", "data/macro/rules_v2.0.0.json", "core/research/display_rights.json",
              "core/gateway/routes.json"}


def allowed(name: str) -> bool:
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or any(x.startswith(".env") for x in p.parts):
        return False
    if any(x in p.parts for x in ("cache", "holdout", "frozen", "paper_live", "grokteam", "_backup", "techfund")):
        return False
    if name in FILES or name in DATA_FILES:
        return True
    if p.suffix == ".py" and p.parts[0] in ("core", "data", "ui", "quantgen_desktop"):
        return True
    if name.startswith("tools/status/") and p.suffix == ".py":
        return True
    if name in {'core/education/samples/usdeur_daily.csv',
                'core/education/samples/usdeur_provenance.json'}:
        return True
    if name.startswith(DATA_PREFIXES) and p.suffix in (".yaml", ".json"):
        return True
    if name.startswith("assets/") and p.suffix in (".png", ".ico", ".svg", ".otf", ".ttf", ".txt"):
        return True
    return False


QT_BINDINGS = tuple("PyQt6 PySide6 shiboken6 sip".split())  # one string: the port tool leaves it as is


def _module_level(tree):
    """Statements that run on import: the module body and class bodies, not function bodies; a Qt import
    guarded by `except ImportError` is optional and does not count."""
    stack = list(tree.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if isinstance(node, ast.Try) and any(
                isinstance(h.type, ast.Name) and h.type.id in ("ImportError", "ModuleNotFoundError") for h in node.handlers):
            stack.extend(node.finalbody + node.orelse)
            continue
        yield node
        for field in ("body", "orelse", "finalbody", "handlers"):
            stack.extend(getattr(node, field, []) or [])


def _imported_modules(source: str, package: str = "", module_level_only: bool = False) -> set:
    tree = ast.parse(source)
    nodes = _module_level(tree) if module_level_only else ast.walk(tree)
    found = set()
    for node in nodes:
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parent = package.split(".")[: len(package.split(".")) - node.level + 1]
                base = ".".join(parent + ([base] if base else []))
            if base:
                found.add(base)
                found.update(f"{base}.{alias.name}" for alias in node.names)
    return found


def mobile_desktop_modules(root: Path, names) -> set:
    """quantgen_desktop files the Flet app needs: what main.py and ui/ import (anywhere in the file), then
    what those modules import when they are imported (module level), transitively."""
    present = {n for n in names if n.startswith("quantgen_desktop/") and n.endswith(".py")}
    def path_of(module):
        stem = module.replace(".", "/")
        return next((c for c in (stem + ".py", stem + "/__init__.py") if c in present), None)
    def package_of(name):
        parts = name[:-3].split("/")
        return ".".join(parts[:-1] if parts[-1] != "__init__" else parts[:-1])
    flet = [n for n in names if n == "main.py" or (n.startswith("ui/") and n.endswith(".py"))]
    queue, needed = [], set()
    def want(module):
        for target in (path_of("quantgen_desktop"), path_of(module)):
            if target and target not in needed:
                needed.add(target); queue.append(target)
                if target.endswith("/__init__.py") and target != "quantgen_desktop/__init__.py":
                    # a sub-package (owner_ui_language) loads its parts with import_module: take it whole
                    for part in sorted(n for n in present if n.startswith(target[:-len("__init__.py")])):
                        if part not in needed:
                            needed.add(part); queue.append(part)
    for name in flet:
        for module in _imported_modules((root / name).read_text(encoding="utf-8")):
            if module.startswith("quantgen_desktop"):
                want(module)
    while queue:
        name = queue.pop()
        for module in _imported_modules((root / name).read_text(encoding="utf-8"), package_of(name), True):
            if module.startswith("quantgen_desktop"):
                want(module)
    for name in sorted(needed):
        qt = sorted(m for m in _imported_modules((root / name).read_text(encoding="utf-8"), package_of(name), True)
                    if m.split(".")[0] in QT_BINDINGS)
        if qt:
            raise ValueError(f"mobile profile refused: {name} imports {qt[0]} on import")
    return needed


def allowed_mobile(name: str, desktop_modules) -> bool:
    if name == "pyproject.toml":
        return False  # replaced by mobile/pyproject.toml
    if name.startswith("quantgen_desktop/"):
        return name in desktop_modules
    return allowed(name)


def stage(root: Path, destination: Path, profile: str = "desktop") -> int:
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    names = [n for n in names if n]
    if profile == "mobile":
        desktop_modules = mobile_desktop_modules(root, names)
        selected = [n for n in names if allowed_mobile(n, desktop_modules)]
    else:
        selected = [n for n in names if allowed(n)]
    destination.mkdir(parents=True, exist_ok=False)
    for name in selected:
        source = root / name
        if source.is_symlink() or source.resolve() != source.absolute():
            raise ValueError("Symlinked build input refused: " + name)
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    if profile == "mobile":
        shutil.copyfile(root / "mobile" / "pyproject.toml", destination / "pyproject.toml")
        selected = selected + ["mobile/pyproject.toml -> pyproject.toml"]
    (destination / "STAGE_MANIFEST.json").write_text(json.dumps(selected, indent=2) + "\n")
    return len(selected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--profile", choices=("desktop", "mobile"), default="desktop")
    args = parser.parse_args()
    print("Staged", stage(ROOT, args.output.resolve(), args.profile), "allowlisted files", f"({args.profile})")
