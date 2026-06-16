#!/usr/bin/env sh
set -eu

TNVIEW="${TNVIEW:-tnview}"

"$TNVIEW" --help >/dev/null
"$TNVIEW" --version >/dev/null
"$TNVIEW" tour --json >/dev/null
"$TNVIEW" recipes --json >/dev/null
"$TNVIEW" examples --json >/dev/null
"$TNVIEW" focus --list --json >/dev/null
"$TNVIEW" doctor --json >/dev/null
"$TNVIEW" schema --json >/dev/null
"$TNVIEW" validate examples/tebd_run.jsonl >/dev/null
"$TNVIEW" validate examples/dmrg_bad_run.jsonl --strict --json >/dev/null
"$TNVIEW" watch examples/quimb_tnoptimizer_run.jsonl --max-refreshes 1 --no-clear >/dev/null
"$TNVIEW" tail examples/quimb_tnoptimizer_run.jsonl --json >/dev/null
"$TNVIEW" diagnose examples/dmrg_bad_run.jsonl --profile default --json >/dev/null
"$TNVIEW" compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --diagnostics --json >/dev/null
"$TNVIEW" sketch --list --json >/dev/null
"$TNVIEW" sketch "mps sites=16 chi=64 profile=front checkpoints=3" --json >/dev/null
"$TNVIEW" sketch --wizard --json >/dev/null 2>/dev/null <<'EOF'

16
64
3
front
8
n
n
EOF
"$TNVIEW" sketch "mps sites=16 chi=64 profile=front checkpoints=3" --ascii >/dev/null
"$TNVIEW" sketch "mps sites=16 chi=64 profile=spike checkpoints=3" --ascii >/dev/null
"$TNVIEW" scope examples/tebd_run.jsonl --signal selected --bond 1 --ascii >/dev/null
"$TNVIEW" animate examples/tebd_run.jsonl --frames 2 --no-clear --ascii >/dev/null
"$TNVIEW" animate examples/tebd_run.jsonl --frames 3 --reverse --bounce --fps 1000 --no-clear --ascii >/dev/null

printf '%s\n' "tnview smoke checks passed"
