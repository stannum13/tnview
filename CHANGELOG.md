# Changelog

## 1.2.0 - 2026-06-16

- Added oscilloscope-style replay signals, marker ticks, `tnview scope`, and
  richer animation controls for time windows, selected bonds, and signal
  filtering.
- Added interactive replay command mode, jump-to-time support, and a toggleable
  scope panel.
- Added `RunLogger` DMRG/TEBD convenience helpers.
- Improved quimb `TNOptimizer` support with a stateful observer, deduplication,
  loss deltas, gradient norm capture, and alternate metric names.
- Improved TeNPy DMRG support with common sweep-stat aliases and inferred
  configured chi limits.
- Added diagnostic profiles, diagnostic categories, warning suppression, and
  baseline-vs-candidate diagnostic comparison.
- Added structured `tnview tour --json`, top-level CLI help examples, terminal
  severity theme helpers, and a release smoke script.
- Added dynamic `front` and `spike` sketch profiles plus `tnview sketch --json`.
- Added `tnview recipes` with human and JSON workflow examples.
- Added `tnview examples --json` for machine-readable example discovery.
- Added `tnview focus --list --json` for machine-readable focus strategy discovery.
- Added release-check hints to `tnview doctor` human and JSON output.

## 1.1.0 - 2026-06-15

Public release polish and live terminal UX.

- Added `tnview watch` as the primary live run-log dashboard command.
- Added semantic terminal primitives, pressure meters, a live status line, and
  compact event ticker output for run-log monitoring.
- Added pressure-aware replay topology glyphs and a selected-bond marker.
- Renamed public output headings from toy-focused language to neutral release
  language.
- Added a public integration guide for stdlib `RunLogger`, quimb snapshots,
  quimb `TNOptimizer`, and TeNPy DMRG observers.
- Clarified stable, experimental, and non-goal surfaces in the README.
- Added optional integration smoke jobs for quimb and TeNPy in CI.
- Reclassified package maturity as beta while keeping the core CLI/API contract
  documented and tested.

## 1.0.0 - 2026-06-15

Stable CLI and integration contract release.

- Added `tnview --version` and structured expected-error rendering across the
  CLI, with tracebacks behind `--verbose`.
- Added `tnview schema` with human and JSON output for supported run-log and
  visual replay event contracts.
- Added `tnview init` starter emitters for stdlib `RunLogger`, quimb snapshots,
  and TeNPy observer integration.
- Kept the v0.4 run-diagnostics surface stable: `tail`, `diagnose`, `compare`,
  `validate --strict --json`, configurable thresholds, quimb helpers, and TeNPy
  full sweep-history emission.
- Marked the package metadata as a stable console release.

## 0.4.0 - 2026-06-15

Run-diagnostics and integration readiness release.

- Added strict JSON validation output for replay and run-log files.
- Added stable JSON output for run-log and replay comparisons.
- Added configurable diagnostic thresholds for convergence, truncation,
  runtime, memory, canonical-form, and entropy checks.
- Hardened CLI parse and argument failures with structured recovery guidance.
- Added quimb run-log MPS snapshot helpers and an optional snapshot example.
- Expanded TeNPy DMRG support to emit full sweep histories without duplicates.

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
