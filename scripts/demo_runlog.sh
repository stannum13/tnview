#!/usr/bin/env sh
set -eu

TNVIEW="${TNVIEW:-python -m tnview.cli}"

echo "$TNVIEW examples"
$TNVIEW examples

echo
echo "$TNVIEW watch examples/quimb_tnoptimizer_run.jsonl --max-refreshes 1 --no-clear --width 100"
$TNVIEW watch examples/quimb_tnoptimizer_run.jsonl --max-refreshes 1 --no-clear --width 100

echo
echo "$TNVIEW replay-runlog examples/quimb_tnoptimizer_run.jsonl --index 2 --ascii --width 100"
$TNVIEW replay-runlog examples/quimb_tnoptimizer_run.jsonl --index 2 --ascii --width 100

echo
echo "$TNVIEW diagnose examples/dmrg_bad_run.jsonl"
$TNVIEW diagnose examples/dmrg_bad_run.jsonl

echo
echo "$TNVIEW compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --sort risk --width 140"
$TNVIEW compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --sort risk --width 140
