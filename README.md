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

Start with the motivated CLI tour:

```bash
tnview tour
tnview recipes
```

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
tnview demo
tnview tour
tnview recipes
tnview sketch "mps sites=48 chi=128 profile=hard" --interactive
tnview watch examples/quimb_tnoptimizer_run.jsonl --max-refreshes 1 --no-clear
tnview tail examples/quimb_tnoptimizer_run.jsonl
tnview replay-runlog examples/quimb_tnoptimizer_run.jsonl --index 2 --ascii
tnview scope examples/tebd_run.jsonl --center-time 0.8 --window 0.3 --bond 1 --ascii
tnview animate examples/tebd_run.jsonl --style instrument
tnview animate examples/tebd_run.jsonl --center-time 0.8 --window 0.3 --signal trunc --no-clear --ascii
tnview scope examples/moving_front.jsonl --signal front --ascii
tnview animate examples/truncation_spike.jsonl --signal trunc --frames 5 --ascii
tnview diagnose examples/dmrg_bad_run.jsonl
tnview compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --sort risk
```

If quimb is installed, run the optional integration transcript:

```bash
make quimb-demo
```

`watch` is the live dashboard: a compact, lazygit-style terminal cockpit for
the latest run state, pressure signals, diagnostics, and recent events. `tail`
keeps the plainer one-shot summary for scripts and logs:

```text
* TNView watch  status=live  events=6  run=quimb-opt  lib=quimb  algo=tnoptimizer  step=4

+ Run -----------------------------------+   + Signals ------------------------------------------+
| * loss       0.07 was 0.12             |   |   health    [###.......] ok                       |
| * wall s     2.3 was 1.9               |   |   progress  [###.......] ok                       |
| * rss MB     526 was 522               |   |   loss      #*+-.  latest=0.07 change=-0.05       |
+----------------------------------------+   +----------------------------------------------------+

+ Diagnostics --------------------------------------------------------------------------+
| no warnings                                                                            |
+---------------------------------------------------------------------------------------+
```

## Record a Run

Record a run:

```python
from tnview import RunLogger

with RunLogger("runs/dmrg.jsonl", run_id="dmrg-001") as log:
    log.start(library="my-code", algorithm="dmrg", model="ising", sites=128)
    for sweep in range(4):
        log.dmrg_sweep(
            sweep=sweep,
            library="my-code",
            energy=-1.0 - sweep * 0.01,
            delta_energy=1e-9,
            max_chi=128,
            chi_max=128,
            max_trunc_err=2e-7,
        )
    log.tebd_step(step=4, library="my-code", max_chi=96, max_trunc_err=1e-9)
    log.end(status="complete")
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
tnview demo --style report
tnview demo --interactive
tnview sketch --wizard
tnview sketch "mps sites=48 chi=128 profile=hard"
tnview sketch "mps sites=48 chi=128 profile=front" --json
tnview sketch "mps sites=48 chi=128 profile=hard" --output sketch.jsonl
```

For local terminal UI iteration, run `make ui-review` and inspect the ignored
snapshots under `.artifacts/ui/`. See [docs/ui_iteration.md](docs/ui_iteration.md)
for the worktree-based visual review loop.

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
tnview tour
tnview demo
tnview demo --interactive
tnview scope examples/tebd_run.jsonl --center-time 0.8 --window 0.3 --bond 1 --ascii
tnview scope examples/tebd_run.jsonl --bond 1 --json
tnview scope examples/moving_front.jsonl --signal front --ascii
tnview scope examples/truncation_spike.jsonl --signal trunc --ascii
tnview animate examples/tebd_run.jsonl --frames 3 --window 0.3 --no-clear --ascii
tnview animate examples/tebd_run.jsonl --start-time 0.1 --end-time 0.8 --signal selected --ascii
tnview sketch --list
tnview sketch --wizard
tnview recipes
tnview sketch "mps sites=48 chi=128 profile=hard"
tnview sketch "mps sites=48 chi=128 profile=spike" --json
tnview sketch "mps sites=48 chi=128 profile=hard" --interactive
tnview doctor
tnview doctor --json
tnview examples
tnview examples --json
tnview schema
tnview schema --json
tnview init emit_tnview.py
tnview init emit_quimb.py --kind quimb

tnview watch examples/dmrg_bad_run.jsonl --max-refreshes 1 --no-clear
tnview tail examples/dmrg_bad_run.jsonl
tnview tail examples/dmrg_bad_run.jsonl --json
tnview tail examples/dmrg_bad_run.jsonl --follow
tnview replay-runlog examples/dmrg_bad_run.jsonl --interactive
tnview diagnose examples/dmrg_bad_run.jsonl
tnview diagnose examples/dmrg_bad_run.jsonl --json
tnview compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --sort risk
tnview compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --json
tnview compare baseline.jsonl candidate.jsonl --diagnostics
tnview export examples/quimb_tnoptimizer_run.jsonl --format csv

tnview validate examples/tebd_run.jsonl
tnview validate examples/dmrg_bad_run.jsonl --strict --json
tnview diagnose run.jsonl
tnview tail run.jsonl
tnview compare runs/*.jsonl --metric loss
tnview compare baseline.jsonl candidate.jsonl --diagnostics --json
tnview replay examples/tebd_run.jsonl --ascii --width 120
tnview replay examples/tebd_run.jsonl --interactive
tnview scope examples/tebd_run.jsonl --signal selected --bond 1 --ascii
tnview animate examples/tebd_run.jsonl --style instrument
tnview animate examples/tebd_run.jsonl --frames 8 --window 0.4
tnview animate examples/tebd_run.jsonl --center-time 0.8 --window 0.2 --signal trunc --no-clear
tnview animate examples/tebd_run.jsonl --frames 3 --reverse --bounce --fps 8

tnview preview examples/ladder_snake_mismatch.jsonl
tnview inspect examples/ladder_snake_mismatch.jsonl
tnview focus --list
tnview focus --list --json
tnview focus examples/ladder_snake_mismatch.jsonl --strategy entropy --window 12
tnview replay examples/ladder_snake_mismatch.jsonl --focus bottleneck --window 12

tnview search examples/tebd_run.jsonl tensor:A2
tnview compare examples/*.jsonl --sort risk
tnview fixture chain --sites 64 --checkpoints 8 --profile hard --output generated.jsonl
```

## Command Guide

`demo` generates an in-memory MPS/TEBD-style replay and renders it immediately.
Use this first to see the terminal instrument without preparing data. The default
view is the denser instrument layout; add `--style report` for the full static
report or `--interactive` for keyboard navigation.

`recipes` prints runnable workflows for common tasks: watching a job, comparing
baseline/candidate logs, inspecting oscilloscope signals, and building a
synthetic sketch. Add `--json` for machine-readable recipe data.

`sketch` is the deterministic prompt-like builder for synthetic visual
telemetry. It currently supports MPS sketches such as
`tnview sketch "mps sites=48 chi=128 profile=hard"`. Profiles include `easy`,
`hard`, `front`, and `spike`; the last two are useful oscilloscope demos for
moving entanglement fronts and localized truncation bursts. Add `--interactive`
to pan around the generated replay, `--output sketch.jsonl` to save the JSONL,
or `--json` for machine-readable sketch metadata. Use `tnview sketch --wizard`
for a question-driven parameter flow that prints the equivalent prompt before
rendering or saving.

`replay` renders JSONL telemetry from disk. Add `--interactive` for keyboard
navigation, or use `--focus bottleneck --window N` to frame the interesting
region automatically.

`scope` renders a static oscilloscope summary for replay signals. Use
`--center-time T --window R` to inspect a local time window, `--signal selected
--bond N` to focus selected-bond rows, and `--json` for a stable signal payload
with event markers.

`animate` replays visual telemetry as an oscilloscope-style moving time window.
The active time `T` advances over checkpoint events while the heatmap is clipped
to `[T - window, T + window]`. Compact signal strips track entropy, max chi,
truncation, and front span so evolving bottlenecks are easier to see. Use
`--style instrument` for a denser status/focus/signal layout, or the default
`--style report` for the original replay transcript. Use `--frames N --no-clear`
when you want a transcript-friendly render. Add `--signal trunc`,
`--signal selected --bond N`, `--start-time/--end-time`, or
`--center-time T --window R` to keep the animation focused. Use `--reverse`,
`--bounce`, and `--fps` to control playback.

`replay-runlog` steps through run-log events after a run has completed or
crashed. Use `--index N` for a static point-in-time view or `--interactive` for
keyboard navigation through the log.

`live` streams JSONL telemetry from a file or stdin and refreshes on checkpoint
events.

`watch` follows a run-log file with the live terminal dashboard: status line,
current metrics, pressure meters, trends, diagnostics, and recent event ticker.
It is the main command for attaching to a running batch job.

`tail` prints the same current-state summary once. Add `--json` for a stable
machine-readable latest run-log state. Add `--follow` to keep refreshing a file
as a batch job appends events. For replay logs, it falls back to the same frame
rendering used by `live`.

`diagnose` prints deterministic warnings for run-log events such as energy
plateaus, chi saturation, truncation floors, runtime regressions, memory growth,
optimizer stagnation, non-finite metrics, canonical-form drift, and sustained
entropy growth. Add `--json` for stable machine-readable diagnostics. Thresholds
can be adjusted with `--profile strict|default|loose` or explicit flags such as
`--energy-eps`, `--truncation-floor`, `--memory-factor`, and
`--canonical-error`. Use repeatable `--suppress CODE` when a known warning is
expected for a particular run family.

`validate` checks replay and run-log JSONL syntax. Add `--strict` to require
run-log metadata such as `schema_version`, `run_id`, and timestamp fields. Add
`--json` for stable machine-readable validation output.

`preview` reads setup telemetry such as `model_geometry` and `ansatz_layout` and
reports interaction range, expected lightcone, early chi-pressure risk,
contraction risk, and ansatz suggestions.

`inspect` chooses a useful starting point, selects that bond, and shows a
smaller window around it. Focus strategies include `bottleneck`, `entropy`,
`front`, `compute`, and `center`.

`focus` exposes the same focus strategies without entering the interactive
keyboard UI. Use `focus --list` or `focus --list --json` to see strategies. Use
`focus PATH --json` to inspect the selected bond and rendered snapshot data from
scripts.

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

`doctor` checks the local TNView install, validates built-in examples, and
reports whether optional quimb and TeNPy integrations are importable. It also
prints the local release checks, including `make smoke`. Add `--json` for
support logs or CI checks.

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
    log.start(library="quimb", algorithm="mps_snapshot")
    for step, psi in enumerate(states):
        emit_mps_snapshot(log, psi, step=step, chi_max=64)
    log.end(status="complete")
```

For quimb `TNOptimizer`, use the callback helper:

```python
from tnview import RunLogger
from tnview.adapters.quimb import TNOptimizerObserver

with RunLogger("runs/quimb_opt.jsonl", run_id="quimb-opt") as log:
    callback = TNOptimizerObserver(log)
    optimizer = qtn.TNOptimizer(tn, loss_fn, callback=callback)
    optimizer.optimize(100)
```

For TeNPy DMRG runs, attach the observer to the engine sweep statistics:

```python
from tnview import RunLogger
from tnview.adapters.tenpy import DMRGObserver

with RunLogger("runs/tenpy_dmrg.jsonl", run_id="tenpy-dmrg") as log:
    log.start(library="tenpy", algorithm="dmrg")
    observer = DMRGObserver(log)
    energy, psi = engine.run()
    observer.emit_new_sweeps(engine, chi_max_configured=32)
    log.observable("final_energy", energy, library="tenpy", algorithm="dmrg")
    log.end(status="complete")
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
pgup/pgdn scroll up/down
shift-left/right or </> scroll left/right
home/end  top/bottom of view
[ / ]     previous/next bond viewport
f/m/x     focus bottleneck / max entropy / slowest compute
u/e/c/i/d toggle updates, entropy, chi rows, inspector, diagnostics
s         toggle oscilloscope scope panel
:time T   jump to nearest checkpoint time
:focus entropy, :toggle scope, :bond N
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
from tnview.adapters.quimb import TNOptimizerObserver

with RunLogger("runs/quimb_opt.jsonl", run_id="quimb-opt") as log:
    callback = TNOptimizerObserver(log)
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
