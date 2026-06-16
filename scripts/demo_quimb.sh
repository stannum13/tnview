#!/usr/bin/env sh
set -eu

PYTHON="${PYTHON:-python}"
TNVIEW="${TNVIEW:-tnview}"

if ! "$PYTHON" - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("quimb") else 1)
PY
then
  printf '%s\n' "quimb is not installed. Install with: python -m pip install -e '.[quimb]'"
  exit 0
fi

printf '%s\n' "$PYTHON examples/quimb_mps_snapshot_example.py"
"$PYTHON" examples/quimb_mps_snapshot_example.py

printf '\n%s\n' "$TNVIEW tail runs/quimb_mps_snapshots.jsonl --width 100"
"$TNVIEW" tail runs/quimb_mps_snapshots.jsonl --width 100

printf '\n%s\n' "$TNVIEW diagnose runs/quimb_mps_snapshots.jsonl"
"$TNVIEW" diagnose runs/quimb_mps_snapshots.jsonl

printf '\n%s\n' "$PYTHON examples/quimb_tnoptimizer_example.py"
"$PYTHON" examples/quimb_tnoptimizer_example.py

printf '\n%s\n' "$TNVIEW tail runs/quimb_tnoptimizer.jsonl --width 100"
"$TNVIEW" tail runs/quimb_tnoptimizer.jsonl --width 100
