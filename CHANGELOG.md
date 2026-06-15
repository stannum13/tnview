# Changelog

## 0.1.0 - 2026-06-15

Initial public development release.

- Added `RunLogger` for append-only JSONL telemetry.
- Added run-log commands: `tail`, `tail --follow`, `diagnose`, `compare`,
  `replay-runlog`, and CSV export.
- Added visual replay commands for MPS/TEBD-style telemetry.
- Added quimb integration helpers for MPS snapshots and `TNOptimizer`
  callbacks.
- Added TeNPy DMRG sweep-stat adapter scaffold.
- Added deterministic diagnostics for convergence, chi saturation,
  truncation floors, runtime regressions, memory growth, optimizer
  stagnation, non-finite metrics, canonical-form drift, and entropy growth.
- Added built-in replay and run-log fixtures plus `make runlog-demo`.
