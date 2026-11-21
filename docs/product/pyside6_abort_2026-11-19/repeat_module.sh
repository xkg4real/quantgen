#!/bin/bash
# Run one test module (or test ID) many times under PySide6, a few at once, and count fatal signals.
# usage: repeat_module.sh <work dir from setup_copy.sh> <module or test id> <runs> [parallel=4]
# Logs: <work dir>/runs/<n>.log. Prints one line per non-zero exit and a summary.
# 2026-11-19 reference: tests.desktop_market_tabs_acceptance aborted 2 times in 66 runs (4 at once, 4-CPU Linux);
# the single test SearchZoomTests.test_choosing_a_name_loads_and_connects_without_a_button alone: 0 in 60.
set -uo pipefail
WORK=${1:?work dir}; TARGET=${2:?module or test id}; RUNS=${3:?runs}; PAR=${4:-4}
mkdir -p "$WORK/runs"
one() {
  ( cd "$WORK/copy" && QT_QPA_PLATFORM=offscreen HOME="$WORK/home" PYTHONPATH="$WORK/block" PYTHONFAULTHANDLER=1 \
      timeout 1800 "$WORK/venv/bin/python" -m unittest "$TARGET" > "$WORK/runs/$1.log" 2>&1 )
  rc=$?
  [ $rc -ne 0 ] && echo "run $1 rc=$rc $(grep -m1 -E 'malloc|Fatal Python|Segmentation' "$WORK/runs/$1.log")"
}
n=0
while [ $n -lt "$RUNS" ]; do
  for _ in $(seq 1 "$PAR"); do
    [ $n -ge "$RUNS" ] && break
    n=$((n+1)); one "$n" &
  done
  wait
done
fatal=$(grep -l -E 'malloc_consolidate|Fatal Python error|Segmentation fault' "$WORK"/runs/*.log 2>/dev/null | wc -l)
echo "runs=$RUNS fatal=$fatal"
