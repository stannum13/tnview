# TNView

TNView is an experimental terminal-native viewer for tensor-network dynamics.

It is built around lightweight JSONL telemetry: simulations emit events, and
TNView turns them into compact terminal views for entropy growth, bond-dimension
pressure, truncation hotspots, update history, and run-level diagnostics.

The immediate goal is a lively TUI that makes MPS/TEBD-style runs easy to watch
without opening a heavier GUI. The longer-term research direction is to make the
same telemetry useful for comparing toy models, spotting ansatz pressure, and
debugging complexity growth.

## Quick Start

```bash
make setup
tnview demo
tnview demo --interactive
```

If `tnview` is not on your shell path, run the module directly:

```bash
python -m tnview.cli demo
```

## What It Shows

- MPS topology and bond viewporting
- recent TEBD/TDVP-style updates
- entanglement heatmaps over time
- chi pressure and saturation rows
- truncation-error localization
- selected-bond inspection
- entropy-front and early-warning signals
- contraction-path and compute-cost telemetry
- geometry/ansatz mismatch hints
- run comparison tables and CSV export

## Common Commands

```bash
tnview demo
tnview demo --interactive
tnview examples

tnview validate examples/tebd_run.jsonl
tnview replay examples/tebd_run.jsonl --ascii --width 120
tnview replay examples/tebd_run.jsonl --interactive

tnview preview examples/ladder_snake_mismatch.jsonl
tnview inspect examples/ladder_snake_mismatch.jsonl
tnview replay examples/ladder_snake_mismatch.jsonl --focus bottleneck --window 12

tnview search examples/tebd_run.jsonl tensor:A2
tnview compare examples/*.jsonl --sort risk
tnview fixture chain --sites 64 --checkpoints 8 --profile hard --output generated.jsonl
```

## Command Guide

`demo` generates an in-memory MPS/TEBD-style replay and renders it immediately.
Use this first to see the terminal view without preparing data.

`replay` renders JSONL telemetry from disk. Add `--interactive` for keyboard
navigation, or use `--focus bottleneck --window N` to frame the interesting
region automatically.

`live` streams JSONL telemetry from a file or stdin and refreshes on checkpoint
events.

`preview` reads setup telemetry such as `model_geometry` and `ansatz_layout` and
reports interaction range, expected lightcone, early chi-pressure risk,
contraction risk, and ansatz suggestions.

`inspect` chooses a useful starting point, selects that bond, and shows a
smaller window around it. Focus strategies include `bottleneck`, `entropy`,
`front`, `compute`, and `center`.

`search` locates bonds by `bond:`, `site:`, `tag:`, or `status:`. Tensor-name
search also works with `tensor:A2`; it scans `ansatz_layout.tensors` and
contraction-path step operands.

`compare` summarizes multiple runs side by side.

## Setup

From the repo root:

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
tnview demo --interactive
```

## Interactive Keys

```text
n/p       next/previous checkpoint
j/k       next/previous bond
g         jump to checkpoint
b         jump to bond
[ / ]     previous/next bond viewport
f/m/x     focus bottleneck / max entropy / slowest compute
u/e/c/i/d toggle updates, entropy, chi rows, inspector, diagnostics
?         help
q         quit
```

## Telemetry

Telemetry producers should emit the JSONL events documented in
[docs/telemetry.md](docs/telemetry.md). The core event types are:

- `run_started`
- `model_geometry`
- `ansatz_layout`
- `bond_updated`
- `checkpoint`
- `tdvp_sweep`
- `observable_updated`
- `contraction_path`
