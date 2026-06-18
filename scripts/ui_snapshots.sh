#!/usr/bin/env sh
set -eu

TNVIEW=${TNVIEW:-tnview}
OUT_DIR=${1:-.artifacts/ui}

mkdir -p "$OUT_DIR"

snapshot() {
	name=$1
	shift
	path="$OUT_DIR/$name"
	{
		printf '$'
		printf ' %s' "$@"
		printf '\n\n'
		"$@"
	} > "$path"
	printf 'wrote %s\n' "$path"
}

snapshot instrument.txt \
	"$TNVIEW" animate examples/tebd_run.jsonl \
	--style instrument --frames 3 --window 1 --interval 0 --no-clear --width 100

snapshot instrument-ascii-80.txt \
	"$TNVIEW" animate examples/tebd_run.jsonl \
	--style instrument --frames 1 --window 0.3 --interval 0 --no-clear --ascii --width 80

snapshot replay-focus.txt \
	"$TNVIEW" replay examples/tebd_run.jsonl \
	--focus bottleneck --width 100 --no-color

snapshot runlog-watch.txt \
	"$TNVIEW" watch examples/quimb_tnoptimizer_run.jsonl \
	--max-refreshes 1 --no-clear --width 100 --no-color

snapshot runlog-tail.txt \
	"$TNVIEW" tail examples/quimb_tnoptimizer_run.jsonl \
	--width 100 --no-color

printf '\nUI snapshots are local artifacts under %s\n' "$OUT_DIR"
