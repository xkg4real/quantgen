#!/bin/bash
# usage: run_steps.sh <tree> <logdir>
F2="${F2:?set F2 to your trial folder}"
TREE=$1; LOG=$2; mkdir -p $LOG
cd $TREE
export QT_QPA_PLATFORM=offscreen PYTHONUTF8=1 PYTHONFAULTHANDLER=1 HOME=$F2/home XDG_CONFIG_HOME=$F2/home/.config XDG_CACHE_HOME=$F2/home/.cache XDG_DATA_HOME=$F2/home/.local/share XDG_RUNTIME_DIR=$F2/home/run
mkdir -p $XDG_RUNTIME_DIR; chmod 700 $XDG_RUNTIME_DIR
i=0
while IFS= read -r cmd; do
  i=$((i+1))
  start=$(date +%s)
  timeout 1500 $F2/venv/bin/${cmd} > $LOG/step$i.log 2>&1
  rc=$?
  echo "step$i rc=$rc secs=$(( $(date +%s)-start ))" >> $LOG/summary.txt
done < $F2/tools/qt_steps.txt
echo DONE >> $LOG/summary.txt
