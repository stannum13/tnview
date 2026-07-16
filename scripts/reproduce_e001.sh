#!/usr/bin/env sh
set -eu

MODE="${1:-smoke}"
if [ "$#" -gt 0 ]; then
  shift
fi

PYTHON="${PYTHON:-python}"
TNVIEW="${TNVIEW:-python -m tnview.cli}"

case "$MODE" in
  smoke)
    $TNVIEW validate examples/quimb_tnoptimizer_run.jsonl --strict --json >/tmp/tnview-e001-validate-quimb.json
    $TNVIEW tail examples/quimb_tnoptimizer_run.jsonl --json >/tmp/tnview-e001-tail-quimb.json
    $TNVIEW validate examples/dmrg_bad_run.jsonl --strict --json >/tmp/tnview-e001-validate-dmrg.json
    $TNVIEW diagnose examples/dmrg_bad_run.jsonl --json >/tmp/tnview-e001-diagnose-dmrg.json
    $TNVIEW compare examples/quimb_tnoptimizer_run.jsonl examples/dmrg_bad_run.jsonl --diagnostics --json >/tmp/tnview-e001-compare.json
    "$PYTHON" scripts/measure_logger_overhead.py --events 1000 --output .artifacts/e001/logger-overhead-smoke.json
    ;;
  canonical)
    if [ "${1:-}" = "--dry-run" ]; then
      "$PYTHON" - <<'PY'
import json
from pathlib import Path

config = json.loads(Path("experiments/e001/configs/canonical.json").read_text())
planned = (
    len(config["model_families"])
    * len(config["geometries_or_orderings"])
    * len(config["system_sizes"])
    * len(config["chi_max_values"])
    * len(config["truncation_tolerances"])
    * len(config["seeds"])
)
print(
    f"canonical plan: {planned} candidate runs before paired-reference expansion; "
    f"false_stop_rate_max={config['false_stop_rate_max']}"
)
PY
      exit 0
    fi
    echo "canonical E001 requires the Quimb corpus runner and paired-reference artifact writer; use --dry-run for the preregistered plan" >&2
    exit 2
    ;;
  *)
    echo "usage: $0 [smoke|canonical] [--dry-run]" >&2
    exit 2
    ;;
esac
