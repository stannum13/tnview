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

```bash
tnview replay examples/tebd_run.jsonl
python run_tebd.py | tnview live -
```

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
tnview replay examples/tebd_run.jsonl --ascii --width 120 -b 1
tnview replay examples/tebd_run.jsonl --interactive
tnview compare examples/tebd_run.jsonl examples/tebd_run.jsonl
```

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
