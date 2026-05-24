# TNView Status

## Implemented

P0 coverage:
- MPS topology view
- Entanglement heatmap `S(bond, t)`
- Bond-dimension pressure rows
- Truncation-error rows
- Selected-bond inspector
- Schmidt spectrum sparkline from telemetry when available
- TEBD brick-wall update view
- Chi saturation warnings
- JSONL event stream
- Replay mode, live mode, validation, export, and snapshots

P1 coverage:
- Toy-model comparison mode
- Ansatz mismatch diagnostics
- Entanglement-front tracker
- TDVP sweep view
- Energy/norm drift diagnostics
- Compute-cost overlay
- Contraction-path cost telemetry
- Search by site, bond, tag, and diagnosis text
- Export snapshots, normalized replay JSONL, manifests, and CSV comparison

Operational support:
- Interactive replay shell
- Bond viewporting for larger systems
- Built-in replay examples
- Synthetic chain fixture generator
- Telemetry schema documentation
- Reproducible local setup via `make setup`

## Still Missing Or Thin

- Complexity preview before a run starts.
- Richer contraction-path visual layout beyond summary metrics.
- Search by tensor name.
- 2D PEPS, TTN, MERA, and generic graph layouts.
- P2 mixed-state/state-space diagnostics.
- Sector/charge-resolved entanglement.
- Distance-to-baseline run metrics.
- Reduced-state inspection.

## Recommended Next Steps

1. Add complexity preview from `model_geometry` + `ansatz_layout` before bond telemetry arrives.
2. Add tensor-name search using `ansatz_layout.tensors` and contraction path steps.
3. Add distance-to-baseline comparison metrics for P2-style run comparison.
4. Add richer graph/2D topology renderers for non-MPS layouts.
