# TNView

TNView is a terminal-first telemetry and diagnostics tool for tensor-network
runs.

Long-running DMRG, TEBD, and tensor-network optimization jobs can emit
append-only JSONL through `RunLogger` or a small adapter. TNView then lets you
watch the run over SSH, diagnose convergence problems, replay visual telemetry,
and compare variants without a browser dashboard.

The core workflow is deliberately small:

```text
RunLogger -> tnview watch -> tnview diagnose -> tnview compare
```

It is built for tmux, batch jobs, and crash recovery: record observable run
state, attach from a terminal while the job is alive, then inspect the same log
afterward.

## Install

From this repo:

```bash
make setup
source .venv/bin/activate
```

Or install into an active environment:

```bash
python -m pip install -e .
```

Optional integration extras:

```bash
python -m pip install -e ".[quimb]"
python -m pip install -e ".[tenpy]"
```

## 30-Second Demo

Run the terminal diagnostics tour:

```bash
make runlog-demo
```

The script lists built-in examples, tails a healthy optimizer run, replays a
specific historical event, diagnoses a stalled DMRG-style run, and compares the
two run logs. It is intentionally plain terminal output so it works over SSH and
is easy to record with tools such as `script` or `asciinema`. A checked-in
transcript is available at [docs/demo/runlog-demo.txt](docs/demo/runlog-demo.txt).

Try individual commands:

```bash
tnview watch examples/quimb_tnoptimizer_run.jsonl --max-refreshes 1 --no-clear
tnview tail examples/quimb_tnoptimizer_run.jsonl
tnview replay-runlog examples/quimb_tnoptimizer_run.jsonl --index 2 --ascii
tnview diagnose examples/dmrg_bad_run.jsonl
tnview compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --sort risk
```

The demo output is intentionally plain terminal text:

```text
TNView run tail | run_id=quimb-opt library=quimb algorithm=tnoptimizer
events=6 updated=2026-06-10T01:00:11.000Z

Current:
    step          4
    loss          0.07
    wall time     2.3
    rss           526

Diagnostics:
  no warnings
```

## Record a Run

Record a run:

```python
from tnview import RunLogger

with RunLogger("runs/dmrg.jsonl", run_id="dmrg-001") as log:
    log.emit("run_start", library="my-code", algorithm="dmrg")
    for sweep in range(4):
        log.emit(
            "sweep_end",
            sweep=sweep,
            energy=-1.0 - sweep * 0.01,
            delta_energy=1e-9,
            max_chi=128,
            chi_max_configured=128,
            max_trunc_err=2e-7,
        )
    log.emit("run_end", status="complete")
```

Inspect it from the terminal:

```bash
tnview watch runs/dmrg.jsonl
tnview tail runs/dmrg.jsonl
tnview diagnose runs/dmrg.jsonl
```

For a visual MPS/TEBD replay demo:

```bash
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

## Stability

The stable public surface is:

- `RunLogger` append-only JSONL logging
- run-log commands: `watch`, `tail`, `diagnose`, `compare`, `validate`,
  `schema`, and `init`
- stable JSON modes for `diagnose`, `compare`, `validate`, and `schema`
- the documented run-log event names and common metric fields

The visual replay surface is useful and tested, but its richer rendering details
are allowed to evolve. quimb and TeNPy adapters are dependency-optional and
duck-typed; they are integration helpers, not replacements for those libraries.

Non-goals for this release:

- tensor serialization
- full quantum-object inspection
- full QuTiP/Qiskit support
- browser dashboards
- replacing quimb or TeNPy optimizers/engines

Package releases use semantic versions. The telemetry schema is versioned
separately; the current run-log schema is `0.1`, and schema changes should be
additive when practical.

## Common Commands

```bash
tnview demo
tnview demo --interactive
tnview examples
tnview schema
tnview schema --json
tnview init emit_tnview.py
tnview init emit_quimb.py --kind quimb

tnview watch examples/dmrg_bad_run.jsonl --max-refreshes 1 --no-clear
tnview tail examples/dmrg_bad_run.jsonl
tnview tail examples/dmrg_bad_run.jsonl --follow
tnview replay-runlog examples/dmrg_bad_run.jsonl --interactive
tnview diagnose examples/dmrg_bad_run.jsonl
tnview diagnose examples/dmrg_bad_run.jsonl --json
tnview compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --sort risk
tnview compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --json
tnview export examples/quimb_tnoptimizer_run.jsonl --format csv

tnview validate examples/tebd_run.jsonl
tnview validate examples/dmrg_bad_run.jsonl --strict --json
tnview diagnose run.jsonl
tnview tail run.jsonl
tnview compare runs/*.jsonl --metric loss
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

`replay-runlog` steps through run-log events after a run has completed or
crashed. Use `--index N` for a static point-in-time view or `--interactive` for
keyboard navigation through the log.

`live` streams JSONL telemetry from a file or stdin and refreshes on checkpoint
events.

`watch` follows a run-log file with the live terminal dashboard: status line,
current metrics, pressure meters, trends, diagnostics, and recent event ticker.
It is the main command for attaching to a running batch job.

`tail` prints the same current-state summary once. Add `--follow` to keep
refreshing a file as a batch job appends events. For replay logs, it falls back
to the same frame rendering used by `live`.

`diagnose` prints deterministic warnings for run-log events such as energy
plateaus, chi saturation, truncation floors, runtime regressions, memory growth,
optimizer stagnation, non-finite metrics, canonical-form drift, and sustained
entropy growth. Add `--json` for stable machine-readable diagnostics. Thresholds
can be adjusted with flags such as `--energy-eps`, `--truncation-floor`,
`--memory-factor`, and `--canonical-error`.

`validate` checks replay and run-log JSONL syntax. Add `--strict` to require
run-log metadata such as `schema_version`, `run_id`, and timestamp fields. Add
`--json` for stable machine-readable validation output.

`preview` reads setup telemetry such as `model_geometry` and `ansatz_layout` and
reports interaction range, expected lightcone, early chi-pressure risk,
contraction risk, and ansatz suggestions.

`inspect` chooses a useful starting point, selects that bond, and shows a
smaller window around it. Focus strategies include `bottleneck`, `entropy`,
`front`, `compute`, and `center`.

`search` locates bonds by `bond:`, `site:`, `tag:`, or `status:`. Tensor-name
search also works with `tensor:A2`; it scans `ansatz_layout.tensors` and
contraction-path step operands.

`compare` summarizes multiple runs side by side. Replay logs show tensor-network
state summaries; run logs show latest energy, loss, chi, truncation, memory, and
diagnostic codes. Add `--metric loss` or another run-log metric to sort the
table. Add `--json` for stable machine-readable comparison output.

`schema` prints the supported replay and run-log telemetry schemas. Add `--json`
to feed schema metadata into emitters, tests, or integration tooling.

`init` writes a small starter emitter script. Use `--dry-run` to preview the
file, `--force` to overwrite, and `--kind quimb` or `--kind tenpy` for adapter
starter snippets.

## Python Object Interfaces

TNView can also adapt objects from existing quantum Python libraries. The first
adapter targets quimb-style matrix product states without making quimb a hard
dependency.

See [docs/integrations.md](docs/integrations.md) for copy-paste `RunLogger`,
quimb, and TeNPy examples.

```python
from pathlib import Path
import quimb.tensor as qtn
from tnview import view
from tnview.adapters.quimb import mps_to_jsonl

psi = qtn.MPS_rand_state(L=32, bond_dim=16, phys_dim=2)

print(view(psi, width=120))
Path("mps.jsonl").write_text(mps_to_jsonl(psi), encoding="utf-8")
```

The adapter reads MPS structure such as site count, bond dimensions, tensor
shapes, and singular values when the object exposes them.

To log quimb MPS snapshots into the diagnostics path:

```python
from tnview import RunLogger
from tnview.adapters.quimb import emit_mps_snapshot

with RunLogger("runs/quimb_mps.jsonl", run_id="quimb-mps") as log:
    log.emit("run_start", library="quimb", algorithm="mps_snapshot")
    for step, psi in enumerate(states):
        emit_mps_snapshot(log, psi, step=step, chi_max=64)
    log.emit("run_end", library="quimb", algorithm="mps_snapshot", status="complete")
```

For quimb `TNOptimizer`, use the callback helper:

```python
from tnview import RunLogger
from tnview.adapters.quimb import tnoptimizer_callback

with RunLogger("runs/quimb_opt.jsonl", run_id="quimb-opt") as log:
    optimizer = qtn.TNOptimizer(tn, loss_fn, callback=tnoptimizer_callback(log))
    optimizer.optimize(100)
```

For TeNPy DMRG runs, attach the observer to the engine sweep statistics:

```python
from tnview import RunLogger
from tnview.adapters.tenpy import DMRGObserver

with RunLogger("runs/tenpy_dmrg.jsonl", run_id="tenpy-dmrg") as log:
    log.emit("run_start", library="tenpy", algorithm="dmrg")
    observer = DMRGObserver(log)
    energy, psi = engine.run()
    observer.emit_new_sweeps(engine, chi_max_configured=32)
    log.emit("observable", library="tenpy", algorithm="dmrg", name="final_energy", value=energy)
    log.emit("run_end", library="tenpy", algorithm="dmrg", status="complete")
```

`emit_new_sweeps()` records every available row in TeNPy's `sweep_stats` and
suppresses duplicates on later calls.

## Development

Development and release checks:

```bash
make check
make runlog-demo
```

See [docs/release.md](docs/release.md) for the release checklist.

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

Python code can write TNView telemetry directly:

```python
from tnview import RunLogger

with RunLogger("run.jsonl") as log:
    log.run_started(run_id="ising-001", simulator="my-code", algorithm="TEBD")
    log.model_geometry(
        name="1D chain",
        sites=32,
        dimensions=[32],
        edges=[{"source": i, "target": i + 1} for i in range(31)],
    )
    log.ansatz_layout(ansatz="MPS", ordering=list(range(32)))
    log.bond_updated(
        step=10,
        time=0.1,
        layer="even",
        bond=15,
        site_left=15,
        site_right=16,
        entropy_before=0.4,
        entropy_after=0.8,
        chi_before=32,
        chi_after=64,
        chi_max=128,
        trunc_error=1e-10,
    )
    log.checkpoint(step=10, time=0.1, max_entropy=0.8, max_chi=64)
```

Then inspect it with:

```bash
tnview replay run.jsonl
tnview replay run.jsonl --interactive
tnview tail run.jsonl
tnview diagnose run.jsonl
```

For MPS-like objects, record snapshots directly inside an evolution loop:

```python
from tnview import RunLogger

with RunLogger("run.jsonl") as log:
    log.run_started(run_id="tebd-001", simulator="quimb", algorithm="TEBD")
    for step, time in enumerate(times):
        # update psi with your simulator here
        log.observe_mps(psi, step=step, time=time, chi_max=128, include_setup=(step == 0))
```

For quimb `TNOptimizer`, pass a TNView callback into the optimizer:

```python
from tnview import RunLogger
from tnview.adapters.quimb import tnoptimizer_callback

with RunLogger("runs/quimb_opt.jsonl", run_id="quimb-opt") as log:
    callback = tnoptimizer_callback(log)
    # qtn.TNOptimizer(..., callback=callback)
```

A tiny dependency-optional example script is included:

```bash
python -m pip install -e ".[quimb]"
python examples/quimb_tnoptimizer_example.py
tnview tail runs/quimb_tnoptimizer.jsonl
tnview replay-runlog runs/quimb_tnoptimizer.jsonl --interactive
```

For TeNPy DMRG-style runs, emit sweep summaries from the engine's
`sweep_stats` dictionary:

```python
from tnview import RunLogger
from tnview.adapters.tenpy import DMRGObserver

with RunLogger("runs/tenpy_dmrg.jsonl", run_id="tenpy-dmrg") as log:
    observer = DMRGObserver(log)
    # after each DMRG sweep:
    observer.sweep_end(engine)
```

The example script exits cleanly if TeNPy is not installed:

```bash
python examples/tenpy_dmrg_observer_example.py
tnview tail runs/tenpy_dmrg.jsonl
```

## Non-goals for v0

- full quantum object inspection across every library
- full QuTiP or Qiskit support
- tensor serialization or checkpoint storage
- browser dashboards
