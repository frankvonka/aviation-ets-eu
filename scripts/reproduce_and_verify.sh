#!/usr/bin/env bash
# reproduce_and_verify.sh — clean-environment reproduction driver.
# Usage: PY=/root/venvs/doall/bin/python bash scripts/reproduce_and_verify.sh
set -euo pipefail
PY="${PY:-/root/venvs/doall/bin/python}"
BASE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BASE"
export PYTHONPATH="$BASE"
echo "=== Reproduce & verify ==="
echo "Python: $("$PY" --version)"
echo "Commit: $(git rev-parse HEAD)"
"$PY" src/config_loader.py
"$PY" src/split_manager.py
"$PY" run_all.py
"$PY" tests/test_smoke.py
echo "=== ALL GREEN ==="
