#!/usr/bin/env sh
set -eu

TNVIEW="${TNVIEW:-tnview}"

"$TNVIEW" --help >/dev/null
"$TNVIEW" --version >/dev/null
"$TNVIEW" tour --json >/dev/null
"$TNVIEW" doctor --json >/dev/null
"$TNVIEW" schema --json >/dev/null
"$TNVIEW" validate examples/tebd_run.jsonl >/dev/null
"$TNVIEW" validate examples/dmrg_bad_run.jsonl --strict --json >/dev/null
"$TNVIEW" watch examples/quimb_tnoptimizer_run.jsonl --max-refreshes 1 --no-clear >/dev/null
"$TNVIEW" tail examples/quimb_tnoptimizer_run.jsonl --json >/dev/null
"$TNVIEW" diagnose examples/dmrg_bad_run.jsonl --profile default --json >/dev/null
"$TNVIEW" compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --diagnostics --json >/dev/null
"$TNVIEW" scope examples/tebd_run.jsonl --signal selected --bond 1 --ascii >/dev/null
"$TNVIEW" animate examples/tebd_run.jsonl --frames 2 --no-clear --ascii >/dev/null

printf '%s\n' "tnview smoke checks passed"
