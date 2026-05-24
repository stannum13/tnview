# TNView

TNView is a terminal-native complexity microscope for tensor-network research.

The MVP reads JSONL telemetry from TEBD/MPS-style simulations and renders:

- MPS topology
- recent TEBD updates
- entanglement heatmap
- bond-dimension pressure
- truncation localization
- selected-bond diagnostics
- run-level complexity status
- contraction-path cost diagnostics

```bash
tnview replay examples/tebd_run.jsonl
tnview inspect examples/ladder_snake_mismatch.jsonl
python run_tebd.py | tnview live -
```

Telemetry producers should emit the JSONL events documented in
[docs/telemetry.md](docs/telemetry.md).

Current implementation status is tracked in [docs/status.md](docs/status.md).

## Setup

From the repo root, install the editable package into your active Python
environment. This creates the `tnview` command.

Recommended:

```bash
make setup
```

If a conda or virtualenv environment is active, `make setup` installs into that
environment. Otherwise it creates a local `.venv`.

Manual install into the active environment:

```bash
python -m pip install -r requirements.txt
```

If `make setup` created `.venv`, activate it before running `tnview` directly:

```bash
source .venv/bin/activate
tnview replay examples/tebd_run.jsonl --interactive
```

If you are using a named conda/venv environment, activate it first, then run the
same command:

```bash
conda activate p310
make setup
```

## Common commands

```bash
tnview validate examples/tebd_run.jsonl
tnview inspect examples/ladder_snake_mismatch.jsonl
tnview replay examples/ladder_snake_mismatch.jsonl --focus bottleneck --window 12
tnview replay examples/tebd_run.jsonl --ascii --width 120 -b 1
tnview replay examples/tebd_run.jsonl --interactive
tnview examples
tnview fixture chain --sites 64 --checkpoints 8 --profile hard --output generated.jsonl
tnview compare examples/tebd_run.jsonl examples/tebd_run.jsonl
tnview compare examples/easy_chain.jsonl examples/long_range_chi_limited.jsonl examples/ladder_snake_mismatch.jsonl examples/blocked_ladder.jsonl
tnview compare examples/*.jsonl --sort risk --csv
```

Use `inspect` when you want TNView to choose a useful starting point. It
defaults to the truncation/chi bottleneck, selects that bond, and shows a
smaller bond window around it. `replay --focus` supports the same targeting
inside the regular replay view: `bottleneck`, `entropy`, `front`, `compute`, or
`center`.

Makefile shortcuts:

```bash
make test
make validate
make replay
make replay-interactive
make compare
```

If `tnview` is not found, the package has not been installed into the currently
active environment. Re-run one of:

```bash
make setup
python -m pip install -r requirements.txt
```

You can also run without activating an environment:

```bash
python -m tnview.cli replay examples/tebd_run.jsonl --interactive
```

Interactive replay keys:

```text
n/p       next/previous checkpoint
j/k       next/previous bond
g         jump to checkpoint
b         jump to bond
[ / ]     previous/next bond viewport
u/e/c/i/d toggle updates, entropy, chi rows, inspector, diagnostics
?         help
q         quit
```
