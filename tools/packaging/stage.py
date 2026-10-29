"""Copy an explicit runtime allowlist; never traverse research or secret stores.

python tools/packaging/stage.py --output /tmp/quantgen-build
The destination must be new. This is an install smoke stage, not a research archive.
"""
from pathlib import Path, PurePosixPath
import argparse
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FILES = {"pyproject.toml", "README.md", "main.py", "config.py", "tools/__init__.py",
         "qa/research_status.json", "qa/acceptance_results.json"}
DATA_PREFIXES = ("core/calendars/data/", "core/ficc/schemas/", "core/skills/macro_workflows/",
                 "data/calendars/")
DATA_FILES = {"data/macro/series_registry.yaml", "data/macro/rules_v2.0.0.json"}


def allowed(name: str) -> bool:
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or any(x.startswith(".env") for x in p.parts):
        return False
    if any(x in p.parts for x in ("cache", "holdout", "frozen", "paper_live", "grokteam", "_backup", "techfund")):
        return False
    if name in FILES or name in DATA_FILES:
        return True
    if p.suffix == ".py" and p.parts[0] in ("core", "data", "ui"):
        return True
    if name.startswith("tools/status/") and p.suffix == ".py":
        return True
    if name.startswith(DATA_PREFIXES) and p.suffix in (".yaml", ".json"):
        return True
    if name.startswith("assets/") and p.suffix in (".png", ".ico", ".svg", ".otf", ".txt"):
        return True
    return False


def stage(root: Path, destination: Path) -> int:
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    selected = [n for n in names if n and allowed(n)]
    destination.mkdir(parents=True, exist_ok=False)
    for name in selected:
        source = root / name
        if source.is_symlink() or source.resolve() != source.absolute():
            raise ValueError("Symlinked build input refused: " + name)
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (destination / "STAGE_MANIFEST.json").write_text(json.dumps(selected, indent=2) + "\n")
    return len(selected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print("Staged", stage(ROOT, args.output.resolve()), "allowlisted files")
