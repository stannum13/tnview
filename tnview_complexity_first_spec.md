# TNView: A Complexity-First TUI for Tensor-Network Research

## One-line description

**TNView is a terminal-native complexity microscope for tensor-network research, designed to make entanglement geometry, ansatz pressure, truncation, and computational cost visible while toy models are still being designed.**

---

## Core thesis

Most tensor-network tooling helps after the model is already chosen. The larger opportunity is earlier: help researchers **see the complexity geometry of a toy model before they overcommit to it**.

A good terminal TUI for tensor networks should answer:

```text
Is this toy model too trivial, too hard, or structurally wrong for the phenomenon I care about?
Where is the entanglement living?
Where is computational complexity accumulating?
Which part of the ansatz is doing real work?
Which simplification destroyed the interesting physics?
```

The tool should not merely draw tensor networks. It should make the **geometry of state complexity** visible.

This is motivated by the geometric view of quantum states: quantum states live in structured, high-dimensional spaces with convexity, distinguishability, entropy, separability, and entanglement geometry as central objects. This framing is closely aligned with work such as:

- Bengtsson and Życzkowski, *Geometry of Quantum States*
- Horodecki et al., *Quantum entanglement*, Reviews of Modern Physics 81, 865

In this spirit, TNView should expose not only the state representation but also where the state sits, moves, compresses, and fails within the computational geometry induced by a tensor-network ansatz.

---

## Product reframing

### Original framing

```text
A TUI visualizer for tensor-network structures and entanglement dynamics.
```

### Stronger framing

```text
A terminal-native complexity microscope for tensor-network research.

It helps researchers choose, debug, and compare toy models by visualizing the geometry of entanglement, ansatz pressure, truncation, and computational cost in real time.
```

---

## Biggest pain points this could solve

## 1. Choosing the wrong toy model early

### Pain

A researcher often starts with a toy Hamiltonian, ansatz, circuit, or interaction graph because it is analytically clean or easy to simulate. Only later do they discover that it is:

```text
too simple      → no meaningful entanglement growth
too hard        → immediate χ explosion / contraction blowup
wrong geometry  → complexity accumulates in the wrong place
wrong ansatz    → the tensor network fights the physics
```

This is especially painful in early-stage research because the toy model is supposed to be a thinking aid. Instead, it can silently mislead.

### What TNView should do

TNView should show a **complexity preview** and a **complexity trajectory**.

```text
Toy model complexity preview
----------------------------
sites:              32
geometry:           1D open chain
interaction range:  nearest-neighbor
expected lightcone: linear
initial entropy:    low
early χ pressure:   mild
contraction risk:   low
recommended ansatz: MPS / TEBD
```

During simulation:

```text
Complexity trajectory
---------------------
max S_vN:        0.8 → 1.7 → 2.9 → 4.1
max χ:           16  → 64  → 128 → 256
χ saturation:    none → b14 → b13,b14,b15
trunc error:     1e-12 → 1e-9 → 1e-7
diagnosis:       toy model is becoming χ-limited near the center
```

### Product value

The tool helps users ask:

```text
Did I choose the simplest model that still contains the phenomenon?
Did I accidentally choose a model whose complexity overwhelms the effect?
Is the geometry of the ansatz aligned with the geometry of the state?
```

This is probably the most important pain point.

---

## 2. Invisible entanglement geometry

### Pain

Entanglement is often reduced to a scalar plot after the run:

```text
S(t)
```

But for tensor-network work, the important object is usually richer:

```text
S(bond, t)
Schmidt spectrum(bond, t)
truncation error(bond, t)
χ pressure(bond, t)
```

A scalar plot can hide the spatial geometry of complexity.

### What TNView should do

TNView should make entanglement spatially and temporally visible:

```text
Entanglement heatmap

time ↓ / bond →
t=0.0   ▁▁▁▁▁▁▁▁▁▁▁
t=0.5   ▁▁▂▃▄▃▂▁▁▁▁
t=1.0   ▁▂▃▅▇▅▃▂▁▁▁
t=1.5   ▂▃▅▇█▇▅▃▂▁▁
t=2.0   ▃▄▆████▆▄▃▂
```

For a selected bond:

```text
Bond b14 = sites 14|15
----------------------
S_vN:              3.82
Renyi-2:           3.11
χ:                 256 / 256
saturated:         yes
truncation error:  4.2e-8
Schmidt λ²:        ███████▆▅▄▃▂▁
diagnosis:         central bond is the dominant complexity bottleneck
```

### Product value

The user gets a geometric feel for:

```text
where correlations are forming
where the ansatz is strained
where information is being discarded
whether the state is chain-like, tree-like, area-law-like, or volume-law-like
```

This makes tensor networks feel less like opaque numerical containers and more like coordinates on the state manifold.

---

## 3. No immediate feedback on ansatz/model mismatch

### Pain

A tensor network is a choice of geometry. An MPS, PEPS, TTN, MERA, circuit ansatz, or generic TN each expresses a different hypothesis about the state.

Most simulation workflows do not clearly say:

```text
your state wants a tree, but you gave it a chain
your state wants a 2D geometry, but you projected it onto 1D
your circuit creates long-range structure faster than your ansatz can absorb
your bond dimension is compensating for the wrong topology
```

### What TNView should do

Add an **ansatz mismatch panel**.

```text
Ansatz mismatch
---------------
current ansatz:        MPS
model geometry:        2D ladder flattened to 1D
long-range edges:      18
high-pressure bonds:   7, 8, 9, 10
entropy front:         anisotropic
diagnosis:             MPS ordering is likely poor

suggestions:
  - try snake ordering variant B
  - try blocking rungs
  - try tree layout
  - try PEPS-like geometry for this toy model
```

For 2D-to-1D mappings:

```text
Flattening stress map
---------------------
physical edge distance in MPS ordering:

low stress:    nearest in model and nearest in MPS
high stress:   nearest in model but far in MPS

edge stress:
(3,4)-(4,4):  MPS distance 1     ok
(3,4)-(3,5):  MPS distance 16    bad
```

### Product value

This helps researchers construct better toy models by making the **cost of geometry choices** explicit.

---

## 4. Complexity is discovered too late

### Pain

A run may look fine for many steps and then suddenly become useless:

```text
χ saturates everywhere
truncation error spikes
energy drift grows
entanglement becomes volume-law
contraction intermediates explode
```

Usually this is discovered after the expensive part has already happened.

### What TNView should do

Show early-warning diagnostics.

```text
Early warning
-------------
χ saturation trend:       rising
truncation trend:         rising exponentially
entropy front velocity:   1.8 bonds / unit time
estimated χ need:         ~512 by t=4.0
current χmax:             256
risk:                     high

recommendation:
  this toy model will likely become χ-limited before the target time
```

### Product value

The visualizer becomes a **complexity weather forecast** for simulations.

---

## 5. Truncation error is hard to localize

### Pain

A global truncation number does not tell you where the simulation lost information.

```text
total truncation error = 1e-6
```

This is much less useful than:

```text
bond 14 caused 60% of the loss
bond 15 caused 20%
the rest of the network was fine
```

### What TNView should do

Show truncation as a spatial process.

```text
Truncation heatmap

time ↓ / bond →
t=1.0   . . . . . . . . .
t=1.5   . . . : + # + : .
t=2.0   . . : + @ @ # + .
t=2.5   . : + # @ @ @ # +
```

And in diagnostics:

```text
Error localization
------------------
max truncation:        4.2e-7 at b14
top error bonds:       b14, b15, b13
error concentration:   82% in 3 bonds
diagnosis:             local bottleneck, not global failure
```

### Product value

This tells the researcher whether the model is fundamentally hard or just badly represented.

---

## 6. TEBD/TDVP updates are algorithmically opaque

### Pain

The state changes after every update, but the researcher often only sees checkpoints.

For TEBD, it is not enough to know:

```text
S increased
```

You want to know:

```text
which gate increased S?
which layer caused truncation?
did the even or odd sweep produce the bottleneck?
did one local interaction dominate the complexity?
```

### What TNView should do

Show the update process itself.

```text
TEBD brick-wall view

sites:  0   1   2   3   4   5   6   7
        │ ╔═·═╗ │ ╔═+═╗ │ ╔═█═╗ │
          b1      b3      b5

legend:
·  small ΔS
+  moderate ΔS
█  large ΔS
!  high truncation
```

Selected update:

```text
Gate update
-----------
layer:             odd
bond:              b5
gate:              exp(-i dt h_5,6)
S before:          2.41
S after:           2.88
ΔS:                +0.47
χ before:          128
χ after:           256
truncation error:  8.1e-8
diagnosis:         this local gate is driving the bottleneck
```

### Product value

The tool becomes a debugger for **algorithms**, not just states.

---

## 7. Hard to compare toy models

### Pain

Researchers often compare:

```text
different interaction graphs
different boundary conditions
different system sizes
different initial states
different ansatz geometries
different χmax values
different dt values
```

But the comparison is usually scattered across plots, logs, notebooks, and intuition.

### What TNView should do

Provide side-by-side complexity comparison.

```text
Toy model comparison at t=2.0

model                 max S    max χ    trunc err    diagnosis
1D NN chain            2.1      96       1e-10        easy, maybe too simple
1D long-range          5.8      256      1e-6         χ-limited
2D ladder snake        4.2      256      1e-7         ordering stress
blocked ladder         3.1      160      1e-9         better toy model
TTN geometry           2.9      128      1e-10        promising
```

Visual comparison:

```text
max entropy over bonds

1D NN chain       ▁▂▃▃▂▁
long-range        ▁▃▆██▇
ladder snake      ▁▃▅██▆
blocked ladder    ▁▂▄▅▄▂
TTN               ▁▂▃▄▃▂
```

### Product value

This directly supports early toy-model design.

The tool should help answer:

```text
Which toy model gives me the phenomenon with the least unnecessary complexity?
```

---

## 8. The connection between physics and compute cost is hidden

### Pain

Tensor-network complexity is both physical and computational.

The same event can appear as:

```text
entanglement growth
larger Schmidt rank
larger χ
higher SVD cost
more truncation
larger memory pressure
slower wall time
```

But existing workflows often separate these into different places.

### What TNView should do

Unify physics and compute metrics.

```text
Bond complexity panel
---------------------
bond:               b14
S_vN:               3.82
χ:                  256 / 256
trunc error:        4.2e-8
SVD walltime:       31 ms
estimated memory:   210 MB
local diagnosis:    physics complexity is now compute complexity
```

Global compute view:

```text
Compute complexity
------------------
slowest bond:         b14
slowest operation:    SVD
largest tensor:       A14
largest intermediate: 256 × 2 × 256
UI diagnosis:         runtime dominated by central high-entropy region
```

### Product value

The researcher learns which parts of the physics are causing computational pressure.

---

## 9. Poor visibility into separability, witnesses, and mixed-state structure

### Pain

For pure-state MPS simulations, Schmidt spectra are often enough. But for mixed states, channels, MPOs, and bipartite/multipartite diagnostics, the geometry is subtler.

The Horodecki program around entanglement detection, positive maps, separability criteria, witnesses, and quantification suggests a broader direction: the visualizer should eventually expose not only “how much entropy,” but also **which region of state space the object appears to occupy**.

### What TNView should do eventually

Add a **state-space diagnostics panel**.

```text
State-space diagnostics
-----------------------
object:                 ρ_AB
partial transpose min:  -0.031
PPT status:             non-PPT
negativity:             0.044
witness W expectation:  -0.012
separability status:    likely entangled
```

For toy models:

```text
Bipartite cut scan
------------------
cut       PPT min eig    negativity    witness
A|B       -0.031         0.044         violated
A|C       +0.004         0.000         inconclusive
B|C       -0.008         0.011         violated
```

### Product value

This extends the tool from tensor-network complexity into **operational entanglement geometry**.

---

## 10. Debugging happens after leaving the terminal

### Pain

A lot of tensor-network work happens over SSH, tmux, cluster jobs, and logs. But rich visualization usually requires leaving the remote environment:

```text
download logs
open notebook
plot after the run
discover issue too late
rerun
```

### What TNView should do

The terminal itself should show:

```text
topology
entropy heatmaps
χ pressure
truncation warnings
update events
compute bottlenecks
run comparisons
```

The visualization should be good enough to steer the experiment live.

### Product value

The TUI becomes a real-time research cockpit.

---

## Target users

```text
- tensor-network researchers
- quantum many-body simulation developers
- numerical physicists
- quantum information researchers
- people designing toy Hamiltonians or ansatz geometries
- people debugging TEBD, TDVP, DMRG, PEPS, MERA, TTN, or circuit-TN simulations
```

---

## User stories

## Toy-model design

```text
As a researcher,
I want to see how entanglement and χ pressure emerge in the first few timesteps,
so that I can decide whether my toy model is too simple, too hard, or geometrically mismatched.
```

## Ansatz selection

```text
As a tensor-network user,
I want to compare MPS, TTN, PEPS-like, and circuit-inspired layouts,
so that I can choose an ansatz geometry aligned with the state geometry.
```

## Entanglement debugging

```text
As a numerical physicist,
I want to inspect S(bond, t), Schmidt spectra, and truncation error locally,
so that I can identify which part of the state is causing failure.
```

## Algorithm debugging

```text
As a TEBD/TDVP developer,
I want to see which gate or sweep caused each entropy/truncation spike,
so that I can debug the algorithm rather than only the final state.
```

## Convergence testing

```text
As a simulation user,
I want to compare runs with different χmax, dt, cutoffs, and ansatz geometries,
so that I can tell whether my result is physically meaningful or numerically constrained.
```

---

# Complexity-first feature spec

## P0 features

These are the core features that directly solve the pain points.

```text
1. MPS topology view
2. Entanglement heatmap: S(bond, t)
3. Bond-dimension overlay: χ(bond, t)
4. Truncation-error overlay
5. Selected-bond inspector
6. Schmidt spectrum sparkline
7. TEBD brick-wall update view
8. χ saturation warnings
9. JSONL event stream
10. Replay mode
```

## P1 features

These make the tool meaningfully better for research.

```text
1. Toy-model comparison mode
2. Ansatz mismatch diagnostics
3. Complexity preview before full run
4. Entanglement-front tracker
5. TDVP sweep view
6. Energy/norm drift panel
7. Compute-cost overlay
8. Contraction-path cost view
9. Search by site, bond, tensor, tag
10. Export snapshots and replay files
```

## P2 features

These connect the tool more deeply to the geometry of quantum states.

```text
1. State-space diagnostics for mixed states
2. PPT / negativity / witness panels
3. Sector-resolved entanglement
4. Charge-sector visualization
5. Multipartite entanglement summaries
6. Causal-cone overlays
7. Distance-to-baseline run metrics
8. Geometry-aware ansatz recommendation
9. Entanglement class / orbit-inspired diagnostics
10. Interactive reduced-state inspection
```

---

# Key visualization concepts

## 1. Complexity heatmap

```text
time ↓ / bond →
t=0.0   ▁▁▁▁▁▁▁▁▁
t=0.5   ▁▁▂▃▄▃▂▁▁
t=1.0   ▁▂▃▅▇▅▃▂▁
t=1.5   ▂▃▅▇█▇▅▃▂
```

Shows where entanglement lives.

## 2. χ pressure map

```text
bond:       0 1 2 3 4 5 6 7 8
χ/χmax:     ▁ ▁ ▃ ▅ █ █ ▆ ▃ ▁
saturated:  . . . + ! ! + . .
```

Shows where the ansatz is under strain.

## 3. Error localization map

```text
bond:       0 1 2 3 4 5 6 7 8
trunc ε:    . . : + # @ # + :
```

Shows where information is discarded.

## 4. Geometry stress map

```text
Physical geometry edge  →  ansatz distance

edge          ansatz distance    stress
(0,1)          1                 ok
(1,2)          1                 ok
(2,10)         8                 high
(3,11)         8                 high
```

Shows whether the tensor-network layout is fighting the model geometry.

## 5. Complexity trajectory

```text
t       max S      max χ      trunc ε      diagnosis
0.0     0.0        1          0            product state
0.5     1.1        32         1e-12        easy
1.0     2.3        96         1e-10        healthy
1.5     3.8        256        1e-8         χ pressure
2.0     4.4        256        1e-6         χ-limited
```

Shows whether the toy model remains useful.

---

# Scientific diagnosis vocabulary

TNView should not only show numbers. It should name common situations.

```text
trivial dynamics
  Entropy remains near zero; toy model may be too simple.

localized complexity
  Entanglement and truncation are concentrated around a few bonds.

geometry mismatch
  High χ pressure caused by poor ansatz ordering or layout.

χ-limited run
  Important bonds repeatedly saturate χmax.

truncation-dominated run
  Physical behavior may be contaminated by discarded weight.

healthy growth
  Entanglement grows but χ and truncation remain controlled.

volume-law onset
  Entanglement grows broadly across many bonds; MPS may become unsuitable.

contraction blowup
  Generic TN contraction path creates large intermediates.

algorithmic hotspot
  Specific gate, sweep, or local update causes disproportionate complexity.
```

---

# Data model implications

Telemetry should treat complexity as a first-class object.

## Required event fields for `bond_updated`

```json
{
  "event": "bond_updated",
  "step": 120,
  "time": 1.2,
  "layer": "odd",
  "bond": 14,
  "site_left": 14,
  "site_right": 15,

  "entropy_before": 2.71,
  "entropy_after": 2.94,
  "renyi2_before": 2.10,
  "renyi2_after": 2.25,

  "chi_before": 192,
  "chi_after": 256,
  "chi_max": 256,

  "trunc_error": 4.2e-8,
  "discarded_weight": 4.2e-8,

  "walltime_ms": 31.4,
  "diagnostic_tags": ["chi_saturated", "local_bottleneck"]
}
```

## Required event fields for `checkpoint`

```json
{
  "event": "checkpoint",
  "step": 120,
  "time": 1.2,

  "max_entropy": 2.94,
  "mean_entropy": 1.33,
  "max_chi": 256,
  "num_saturated_bonds": 3,
  "total_trunc_error": 1.1e-6,

  "energy": -12.381,
  "energy_drift": 2.3e-7,
  "norm": 0.999999991,

  "complexity_status": "chi_limited"
}
```

---

# System design principles

## 1. Stream events, not tensors

The simulation owns tensors. The TUI owns observability.

```text
simulation backend
    ↓
JSONL / MessagePack telemetry
    ↓
TNView reducer
    ↓
terminal visualization
```

Do not stream full tensors by default. Stream:

```text
bond entropy
Schmidt summaries
χ values
truncation errors
update events
contraction costs
selected local observables
```

## 2. Prefer structure-aware layouts

Use layouts that match tensor-network semantics:

```text
MPS       → horizontal chain
MPO       → horizontal chain with operator legs
TEBD      → brick-wall spacetime view
TDVP      → sweep view
PEPS      → 2D grid
TTN       → rooted tree
MERA      → layered scale structure
generic   → bipartite tensor-index graph
```

## 3. Make warnings local

Global metrics are useful, but local metrics are actionable.

Bad:

```text
total truncation error = 1e-6
```

Better:

```text
b14 caused 60% of truncation error
b15 caused 20%
all other bonds are low-risk
```

## 4. Keep the terminal useful over SSH

The tool should work in:

```text
SSH
tmux
cluster jobs
narrow terminals
no-color terminals
Unicode and ASCII modes
```

## 5. Make replay a first-class mode

Live visualization is useful. Replayable telemetry is more useful.

```bash
python run_tebd.py | tnview live -
tnview replay run.jsonl
tnview compare run_chi64.jsonl run_chi128.jsonl run_chi256.jsonl
```

---

# Minimum viable product

## MVP scope

```text
Mode:      evolution
Network:   MPS
Algorithm: TEBD
Input:     JSONL event stream
Output:    terminal TUI
```

## MVP views

```text
1. MPS topology row
2. TEBD brick-wall update row
3. S(bond, t) entropy heatmap
4. χ pressure row
5. truncation-error row
6. selected-bond inspector
7. diagnostics panel
```

## MVP metrics

```text
S_vN
Renyi-2 entropy
χ
χmax saturation
truncation error
discarded weight
energy drift
norm drift
walltime per update
```

## MVP interactions

```text
pause / resume
select bond
previous / next checkpoint
toggle entropy overlay
toggle χ overlay
toggle truncation overlay
search by site or bond
export replay
```

---

# Success criteria

TNView is successful if, within one terminal screen, the user can tell:

```text
1. whether the toy model contains nontrivial entanglement,
2. whether the ansatz geometry matches the state geometry,
3. where complexity is accumulating,
4. where information is being discarded,
5. which update caused the problem,
6. whether the run is physically meaningful or numerically constrained,
7. which simpler or better toy model to try next.
```

The highest-value outcome is not prettier tensor-network diagrams. It is faster scientific iteration.

---

# Possible project tagline

```text
See the complexity before it eats the simulation.
```

