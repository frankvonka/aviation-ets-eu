#!/usr/bin/env bash
# run_each_script.sh — run every code/ script one at a time; print exit code + duration + last line.
# Usage: bash scripts/run_each_script.sh
set -euo pipefail
PY="/root/venvs/doall/bin/python"
BASE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BASE"

for s in code/02_clean_build.py code/03_wb_extra.py code/04_did_models.py \
         code/05_models_fixed.py code/05_reconcile.py code/06_ml_suite.py \
         code/07_scm_suite.py code/08_simulation_suite.py code/09_optimization_suite.py \
         code/10_tables_figures.py code/11_null_precision.py code/12_mechanism_pass_through.py \
         code/14_fuel_crosscheck.py code/15_dose_response.py code/build_manuscript.py; do
    echo "======================================================================"
    echo "RUNNING $s"
    start=$(date +%s)
    if output=$("$PY" "$s" 2>&1); then
        rc=0
    else
        rc=$?
    fi
    dur=$(( $(date +%s) - start ))
    last=$(echo "$output" | tail -1)
    echo "exit=$rc  duration=${dur}s  last_line=$last"
    if [ $rc -ne 0 ]; then
        echo "FAILED: $s (exit $rc)"
        exit $rc
    fi
done
echo "ALL STAGES EXITED 0"
