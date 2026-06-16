# TNView Integration Guide

TNView records compact run telemetry. It does not own tensor objects, serialize
tensors, or replace simulation libraries.

## Plain Python

Use `RunLogger` when your code already has sweep, step, optimizer, or observable
metrics.

```python
from tnview import RunLogger

with RunLogger("runs/dmrg.jsonl", run_id="dmrg-001") as log:
    log.start(library="my-code", algorithm="dmrg")
    for sweep in range(8):
        log.sweep(
            sweep=sweep,
            energy=-1.0 - 0.01 * sweep,
            delta_energy=1e-5 / (sweep + 1),
            max_chi=128,
            chi_max=256,
            max_trunc_err=1e-9,
        )
    log.end(status="complete")
```

Inspect it:

```bash
tnview watch runs/dmrg.jsonl
tnview diagnose runs/dmrg.jsonl
```

## quimb MPS Snapshots

The quimb adapter is dependency-optional and duck-typed. It reads MPS-like
attributes such as site count, bond dimensions, and singular values when
available.

```python
from tnview import RunLogger
from tnview.adapters.quimb import emit_mps_snapshot

with RunLogger("runs/quimb_mps.jsonl", run_id="quimb-mps") as log:
    log.start(library="quimb", algorithm="mps_snapshot")
    for step, psi in enumerate(states):
        emit_mps_snapshot(log, psi, step=step, chi_max=64)
    log.end(status="complete")
```

Inspect it:

```bash
tnview tail runs/quimb_mps.jsonl
tnview compare runs/*.jsonl --metric chi
```

## quimb TNOptimizer

`TNOptimizerObserver(log)` is a callable object compatible with quimb's
`TNOptimizer(callback=...)` shape. It emits one `optimizer_step` event per new
evaluation using attributes such as `nevals`, `loss`, `loss_best`, `losses`, and
`grad_norm` when present. The older `tnoptimizer_callback(log)` helper returns
the same observer.

```python
import quimb.tensor as qtn

from tnview import RunLogger
from tnview.adapters.quimb import TNOptimizerObserver

with RunLogger("runs/quimb_opt.jsonl", run_id="quimb-opt") as log:
    log.start(library="quimb", algorithm="tnoptimizer")
    opt = qtn.TNOptimizer(tn, loss_fn, callback=TNOptimizerObserver(log))
    opt.optimize(100)
    log.end(status="complete")
```

Inspect it:

```bash
tnview watch runs/quimb_opt.jsonl
tnview compare runs/*.jsonl --metric loss
```

## TeNPy DMRG

The TeNPy adapter reads `engine.sweep_stats` and emits one `sweep_end` event per
new sweep row. Repeated calls suppress rows already emitted by the same
observer. It accepts common aliases such as `energy`, `delta_energy`, and
`max_entropy`, and infers `chi_max_configured` from nested truncation options
when available.

```python
from tnview import RunLogger
from tnview.adapters.tenpy import DMRGObserver

with RunLogger("runs/tenpy_dmrg.jsonl", run_id="tenpy-dmrg") as log:
    log.start(library="tenpy", algorithm="dmrg")
    observer = DMRGObserver(log)
    energy, psi = engine.run()
    observer.emit_new_sweeps(engine, chi_max_configured=chi_max)
    log.observable("final_energy", energy, library="tenpy", algorithm="dmrg")
    log.end(status="complete")
```

Inspect it:

```bash
tnview tail runs/tenpy_dmrg.jsonl
tnview diagnose runs/tenpy_dmrg.jsonl
```

## Schema Contract

Use the CLI to inspect the current supported event names and common fields:

```bash
tnview schema
tnview schema --json
```

The package version and telemetry schema version are separate. Package releases
use semantic versions. The current run-log schema is `0.1`.
