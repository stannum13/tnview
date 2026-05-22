# TNView Telemetry Schema

TNView reads newline-delimited JSON. Each line is one event object with an
`event` field.

```bash
python run_tebd.py | tnview live -
tnview replay run.jsonl
tnview validate run.jsonl
```

## Event Ordering

A useful replay usually emits metadata first, then update/checkpoint events:

```text
run_started
model_geometry
ansatz_layout
bond_updated ...
observable_updated ...
tdvp_sweep ...
checkpoint
```

Only `bond_updated` events are required for a basic render. Checkpoints create
history rows for the heatmap and enable checkpoint navigation.

## Common Types

- `step`: integer simulation step.
- `time`: numeric simulation time.
- `diagnostic_tags`: optional string array used by search and diagnostics.
- `edges`: object array. TNView accepts `source`/`target`, `site_a`/`site_b`,
  or `u`/`v` integer endpoints.

## `run_started`

Declares run-level metadata.

Required:
- `run_id`: string
- `time`: number

Optional:
- `name`: string or null
- `simulator`: string or null
- `algorithm`: string or null
- `parameters`: object

Example:

```json
{"event":"run_started","run_id":"r1","time":0.0,"name":"Ladder test","simulator":"my-code","algorithm":"TEBD","parameters":{"dt":0.01,"chi_max":256}}
```

## `model_geometry`

Declares the physical model graph.

Required:
- `step`: integer
- `time`: number
- `name`: string

Optional:
- `sites`: integer or null
- `dimensions`: integer array
- `boundary`: string or null
- `edges`: object array

Example:

```json
{"event":"model_geometry","step":0,"time":0.0,"name":"2D ladder","sites":8,"dimensions":[2,4],"boundary":"open","edges":[{"source":0,"target":1},{"source":0,"target":4}]}
```

## `ansatz_layout`

Declares the tensor-network layout used to represent the state.

Required:
- `step`: integer
- `time`: number
- `ansatz`: string

Optional:
- `ordering`: integer array for MPS-style linear order
- `tensors`: object array
- `parameters`: object

Example:

```json
{"event":"ansatz_layout","step":0,"time":0.0,"ansatz":"MPS","ordering":[0,1,2,3,4,5,6,7],"parameters":{"physical_dim":2}}
```

## `bond_updated`

Reports local bond complexity after an update.

Required:
- `step`: integer
- `time`: number
- `layer`: string
- `bond`: integer
- `site_left`: integer
- `site_right`: integer
- `entropy_before`: number
- `entropy_after`: number
- `chi_before`: integer
- `chi_after`: integer
- `chi_max`: integer
- `trunc_error`: number

Optional:
- `renyi2_before`: number or null
- `renyi2_after`: number or null
- `discarded_weight`: number or null
- `walltime_ms`: number or null
- `schmidt_values`: number array, interpreted as a compact Schmidt spectrum
- `diagnostic_tags`: string array

Example:

```json
{"event":"bond_updated","step":120,"time":1.2,"layer":"odd","bond":14,"site_left":14,"site_right":15,"entropy_before":2.71,"entropy_after":2.94,"renyi2_before":2.10,"renyi2_after":2.25,"chi_before":192,"chi_after":256,"chi_max":256,"trunc_error":4.2e-8,"discarded_weight":4.2e-8,"walltime_ms":31.4,"schmidt_values":[0.42,0.31,0.18,0.08],"diagnostic_tags":["chi_saturated","local_bottleneck"]}
```

## `checkpoint`

Captures run-level state at a step. Checkpoints create heatmap history rows.

Required:
- `step`: integer
- `time`: number

Optional:
- `max_entropy`: number or null
- `mean_entropy`: number or null
- `max_chi`: integer or null
- `num_saturated_bonds`: integer or null
- `total_trunc_error`: number or null
- `energy`: number or null
- `energy_drift`: number or null
- `norm`: number or null
- `complexity_status`: string or null

Example:

```json
{"event":"checkpoint","step":120,"time":1.2,"max_entropy":2.94,"mean_entropy":1.33,"max_chi":256,"num_saturated_bonds":3,"total_trunc_error":1.1e-6,"energy":-12.381,"energy_drift":2.3e-7,"norm":0.999999991,"complexity_status":"chi_limited"}
```

## `tdvp_sweep`

Reports a TDVP sweep summary.

Required:
- `step`: integer
- `time`: number
- `direction`: string
- `start_site`: integer
- `end_site`: integer

Optional:
- `max_residual`: number or null
- `max_entropy_delta`: number or null
- `max_trunc_error`: number or null
- `walltime_ms`: number or null
- `diagnostic_tags`: string array

Example:

```json
{"event":"tdvp_sweep","step":120,"time":1.2,"direction":"right","start_site":0,"end_site":31,"max_residual":3e-6,"max_entropy_delta":0.47,"max_trunc_error":4.2e-8,"walltime_ms":58.3,"diagnostic_tags":["entropy_spike"]}
```

## `observable_updated`

Reports scalar observable telemetry.

Required:
- `step`: integer
- `time`: number
- `name`: string
- `value`: number

Optional:
- `site`: integer or null
- `bond`: integer or null
- `error`: number or null
- `diagnostic_tags`: string array

Example:

```json
{"event":"observable_updated","step":120,"time":1.2,"name":"magnetization","site":14,"value":0.73,"error":1e-8,"diagnostic_tags":["local"]}
```

## Minimal Python Emitter

```python
import json
import sys


def emit(event):
    print(json.dumps(event, separators=(",", ":")), flush=True)


emit({
    "event": "bond_updated",
    "step": 1,
    "time": 0.01,
    "layer": "odd",
    "bond": 0,
    "site_left": 0,
    "site_right": 1,
    "entropy_before": 0.0,
    "entropy_after": 0.12,
    "renyi2_before": None,
    "renyi2_after": None,
    "chi_before": 1,
    "chi_after": 4,
    "chi_max": 128,
    "trunc_error": 0.0,
    "discarded_weight": 0.0,
    "walltime_ms": 1.7,
    "diagnostic_tags": [],
})
```

Validate a generated stream:

```bash
python run_tebd.py > run.jsonl
tnview validate run.jsonl
tnview replay run.jsonl --interactive
```
