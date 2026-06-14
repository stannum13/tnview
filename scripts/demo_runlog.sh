#!/usr/bin/env sh
set -eu

TNVIEW="${TNVIEW:-python -m tnview.cli}"

echo "$TNVIEW examples"
$TNVIEW examples

echo
echo "$TNVIEW tail examples/quimb_tnoptimizer_run.jsonl --width 100"
$TNVIEW tail examples/quimb_tnoptimizer_run.jsonl --width 100

echo
echo "$TNVIEW replay-runlog examples/quimb_tnoptimizer_run.jsonl --index 2 --ascii --width 100"
$TNVIEW replay-runlog examples/quimb_tnoptimizer_run.jsonl --index 2 --ascii --width 100

echo
echo "$TNVIEW diagnose examples/dmrg_bad_run.jsonl"
$TNVIEW diagnose examples/dmrg_bad_run.jsonl

echo
echo "$TNVIEW compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --sort risk --width 140"
$TNVIEW compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --sort risk --width 140
