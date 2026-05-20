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
