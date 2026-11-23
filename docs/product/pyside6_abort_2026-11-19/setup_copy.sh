#!/bin/bash
# Build a PySide6 scratch copy of a UI commit, the way the 2026-11-19 verification did.
# usage: setup_copy.sh <repo checkout> <ref> <work dir> <qt_port tool dir>
#   <repo checkout>     a quantgen checkout that has <ref> (read only: only `git archive` runs there)
#   <ref>               e.g. origin/claude/friendly-bardeen-r6xe8f or 5025c6f
#   <work dir>          a new, empty folder for the copy, the venv and the PyQt6 blocker
#   <qt_port tool dir>  folder holding pyqt6_to_pyside6.py (tools/qt_port on claude/os-prep-20261117)
# Afterwards: <work dir>/copy is the converted tree, <work dir>/venv has PySide6-Essentials 6.12.0 (system site packages
# visible for numpy, pandas, ...), and <work dir>/block holds a PyQt6 package that refuses to import, so the two
# bindings never load in one process. Never touches .env, docs/asset_expansion/cache/ or tools/nautilus/.
set -euo pipefail
REPO=${1:?repo checkout}; REF=${2:?ref}; WORK=${3:?work dir}; TOOL=${4:?qt_port tool dir}
mkdir -p "$WORK/copy" "$WORK/block/PyQt6" "$WORK/home"
if [ -n "$(ls -A "$WORK/copy")" ]; then echo "copy folder is not empty: $WORK/copy" >&2; exit 2; fi
git -C "$REPO" archive "$REF" -- quantgen_desktop core data ui tests tools assets config.py main.py pyproject.toml \
    requirements.txt README.md docs results ':!**/*.jsonl' ':!**/holdout/**' ':!**/frozen/**' ':!**/.env*' \
    ':!docs/asset_expansion/cache/**' ':!tools/nautilus/**' | tar -x -C "$WORK/copy"
touch "$WORK/copy/.qt_port_scratch"
(cd "$WORK/copy" && python3 "$TOOL/pyqt6_to_pyside6.py" --apply "$WORK/copy")
printf 'raise ImportError("PyQt6 is blocked in the PySide6 run")\n' > "$WORK/block/PyQt6/__init__.py"
if [ ! -x "$WORK/venv/bin/python" ]; then
  python3 -m venv --system-site-packages "$WORK/venv"
  "$WORK/venv/bin/python" -m pip install -q "PySide6-Essentials==6.12.0"
fi
"$WORK/venv/bin/python" -c "import PySide6; print('PySide6', PySide6.__version__)"
echo "ready: $WORK/copy"
