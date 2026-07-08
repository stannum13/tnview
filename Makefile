.PHONY: setup install test compile check smoke validate replay replay-interactive runlog-demo quimb-demo compare demo-assets ui-snapshots ui-review ui-worktrees clean

PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python; fi)
PIP ?= $(PYTHON) -m pip
TNVIEW ?= $(shell if [ -x .venv/bin/tnview ]; then echo .venv/bin/tnview; else echo tnview; fi)
BASE_DIR ?=

setup install:
	./scripts/setup_env.sh

test:
	$(PYTHON) -m unittest discover -s tests

compile:
	$(PYTHON) -m compileall tnview tests

check: test compile

smoke:
	TNVIEW="$(TNVIEW)" ./scripts/smoke_cli.sh

validate:
	$(TNVIEW) validate examples/tebd_run.jsonl

replay:
	$(TNVIEW) replay examples/tebd_run.jsonl --ascii --width 120 -b 1

replay-interactive:
	$(TNVIEW) replay examples/tebd_run.jsonl --interactive

runlog-demo:
	TNVIEW="$(TNVIEW)" ./scripts/demo_runlog.sh

quimb-demo:
	PYTHON="$(PYTHON)" TNVIEW="$(TNVIEW)" ./scripts/demo_quimb.sh

compare:
	$(TNVIEW) compare examples/easy_chain.jsonl examples/long_range_chi_limited.jsonl examples/ladder_snake_mismatch.jsonl examples/blocked_ladder.jsonl

demo-assets:
	$(PYTHON) ./scripts/render_demo_svgs.py

ui-snapshots:
	PYTHON="$(PYTHON)" ./scripts/ui_snapshots.sh

ui-review: ui-snapshots
	$(PYTHON) ./scripts/ui_review.py

ui-worktrees:
	./scripts/setup_ui_worktrees.sh $(BASE_DIR)

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache .artifacts build dist *.egg-info
