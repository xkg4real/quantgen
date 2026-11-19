#!/bin/bash
# Reproduce the PySide6 segmentation fault seen in the D9 trial (OS-P0-f), on a scratch copy only.
# usage: shell_window_segfault.sh <converted scratch copy> <python of a PySide6 venv> [tries]
# The scratch copy is `git archive` of a ref (with README.md) after
#   python tools/qt_port/pyqt6_to_pyside6.py --apply <copy>   and the trial font shim.
# 2026-11-17, main 5888d05, Linux offscreen, PySide6-Essentials 6.12.0, Python 3.12: rc=139 in 2 of 3 tries
# (and 3 of 3 with the full CI step 2); PyQt6 6.12.0 on the same tests: rc=0.
set -u
COPY=$1; PY=$2; TRIES=${3:-3}
H=$(mktemp -d); mkdir -p "$H/run"; chmod 700 "$H/run"
export QT_QPA_PLATFORM=offscreen PYTHONFAULTHANDLER=1 HOME=$H XDG_CONFIG_HOME=$H/.config XDG_CACHE_HOME=$H/.cache XDG_DATA_HOME=$H/.local/share XDG_RUNTIME_DIR=$H/run
M=tests.desktop_home_markets_shell_acceptance.ShellRailTests
cd "$COPY" || exit 2
for i in $(seq "$TRIES"); do
  timeout 600 "$PY" -m unittest $M.test_window_mouse_click_on_hovered_country_opens_that_market \
    $M.test_single_destination_mouse_click_needs_no_submenu $M.test_outside_window_click_dismisses_without_navigating \
    tests.desktop_workspace_readability_acceptance > "$H/try$i.log" 2>&1
  echo "try$i rc=$? segfault=$(grep -c 'Fatal Python error: Segmentation fault' "$H/try$i.log")"
done
echo "logs: $H"
