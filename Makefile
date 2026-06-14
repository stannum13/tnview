.PHONY: setup install test compile validate replay replay-interactive runlog-demo compare clean

PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python; fi)
PIP ?= $(PYTHON) -m pip
TNVIEW ?= $(shell if [ -x .venv/bin/tnview ]; then echo .venv/bin/tnview; else echo tnview; fi)

setup install:
	./scripts/setup_env.sh

test:
	$(PYTHON) -m unittest discover -s tests

compile:
	$(PYTHON) -m compileall tnview tests

validate:
	$(TNVIEW) validate examples/tebd_run.jsonl

replay:
	$(TNVIEW) replay examples/tebd_run.jsonl --ascii --width 120 -b 1

replay-interactive:
	$(TNVIEW) replay examples/tebd_run.jsonl --interactive

runlog-demo:
	TNVIEW="$(TNVIEW)" ./scripts/demo_runlog.sh

compare:
	$(TNVIEW) compare examples/easy_chain.jsonl examples/long_range_chi_limited.jsonl examples/ladder_snake_mismatch.jsonl examples/blocked_ladder.jsonl

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info
