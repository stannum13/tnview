#!/usr/bin/env sh
set -eu

PYTHON=${PYTHON:-python}
TNVIEW_EXE=${TNVIEW_EXE:-}
OUT_DIR=${1:-.artifacts/ui}

mkdir -p "$OUT_DIR"

run_tnview() {
	if [ -n "$TNVIEW_EXE" ]; then
		"$TNVIEW_EXE" "$@"
	else
		PYTHONPATH="${PWD}${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON" -m tnview.cli "$@"
	fi
}

snapshot() {
	name=$1
	shift
	path="$OUT_DIR/$name"
	{
		if [ -n "$TNVIEW_EXE" ]; then
			printf '$ %s' "$TNVIEW_EXE"
		else
			printf '$ %s -m tnview.cli' "$PYTHON"
		fi
		printf ' %s' "$@"
		printf '\n\n'
		run_tnview "$@"
	} > "$path"
	printf 'wrote %s\n' "$path"
}

snapshot instrument.txt \
	animate examples/tebd_run.jsonl \
	--style instrument --frames 3 --window 1 --interval 0 --no-clear --width 100

snapshot instrument-ascii-80.txt \
	animate examples/tebd_run.jsonl \
	--style instrument --frames 1 --window 0.3 --interval 0 --no-clear --ascii --width 80

snapshot instrument-ascii-72.txt \
	animate examples/tebd_run.jsonl \
	--style instrument --frames 1 --window 1 --interval 0 --no-clear --ascii --no-color --width 72

snapshot replay-focus.txt \
	replay examples/tebd_run.jsonl \
	--focus bottleneck --width 100 --no-color

snapshot demo.txt \
	demo --sites 8 --checkpoints 3 --chi-max 64 \
	--profile hard --width 100 --no-color

snapshot runlog-watch.txt \
	watch examples/quimb_tnoptimizer_run.jsonl \
	--max-refreshes 1 --no-clear --width 100 --no-color

snapshot runlog-tail.txt \
	tail examples/quimb_tnoptimizer_run.jsonl \
	--width 100 --no-color

printf '\nUI snapshots are local artifacts under %s\n' "$OUT_DIR"
