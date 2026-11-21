#!/bin/bash
# Repeat a test module under gdb (4 at once) until one run gets SIGABRT/SIGSEGV, then keep its log with every
# thread's backtrace. usage: gdb_until_abort.sh <work dir from setup_copy.sh> <module> [max batches=25] [debug-malloc]
# With a 4th argument "debug-malloc" the runs use glibc's checking allocator (LD_PRELOAD libc_malloc_debug.so.0,
# MALLOC_CHECK_=3, MALLOC_PERTURB_=165). 2026-11-19: plain gdb caught the abort in 1 of 8 runs; with the checking
# allocator 0 of 121 (it changes allocation and timing).
set -uo pipefail
WORK=${1:?work dir}; TARGET=${2:?module}; MAX=${3:-25}; MODE=${4:-plain}
mkdir -p "$WORK/gdb"
extra=()
if [ "$MODE" = debug-malloc ]; then
  extra=(-ex "set environment LD_PRELOAD /lib/x86_64-linux-gnu/libc_malloc_debug.so.0"
         -ex "set environment MALLOC_CHECK_ 3" -ex "set environment MALLOC_PERTURB_ 165")
fi
one() {
  ( cd "$WORK/copy" && QT_QPA_PLATFORM=offscreen HOME="$WORK/home" PYTHONPATH="$WORK/block" PYTHONFAULTHANDLER=1 \
      timeout 2400 gdb -q -batch -ex "set pagination off" -ex "handle SIGPIPE nostop noprint" "${extra[@]}" \
      -ex run -ex "info threads" -ex "thread apply all bt 50" \
      --args "$WORK/venv/bin/python" -m unittest "$TARGET" > "$WORK/gdb/$1_$2.log" 2>&1 )
}
for b in $(seq 1 "$MAX"); do
  for s in 1 2 3 4; do one "$b" "$s" & done
  wait
  hit=$(grep -l "received signal SIG" "$WORK"/gdb/*.log 2>/dev/null | head -1)
  if [ -n "$hit" ]; then echo "fatal signal after batch $b: $hit"; exit 0; fi
done
echo "no fatal signal in $((MAX*4)) runs"
