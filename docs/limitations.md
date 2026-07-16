# Limitations

This document is the current public evidence boundary for TNView.

## Current Status

E001 is preregistered but has not been canonically run on a real Quimb corpus.
The repository currently supports local fixture smoke checks, run-log
validation, deterministic diagnostics, comparison commands, and optional
duck-typed adapters.

## Diagnostic Limits

- Current diagnostics are deterministic threshold rules, not a validated
  scientific failure classifier.
- Fixture logs demonstrate CLI behavior but do not provide precision, recall,
  false-stop rate, or compute-saved evidence.
- Capacity-limited labels for E001 must come from paired higher-accuracy runs,
  not subjective inspection.
- A future learned predictor should not be added unless transparent thresholds
  fail under the preregistered controls.

## Integration Limits

- Quimb and TeNPy are optional dependencies.
- Adapter tests use fake library-shaped objects unless an optional integration
  environment installs the real libraries.
- No Quimb or TeNPy source is vendored here.
- TNView records telemetry summaries and does not serialize full tensor-network
  objects.

## Measurement Limits

- Logger-overhead numbers from `./scripts/reproduce_e001.sh smoke` are smoke
  measurements for the local environment, not canonical benchmark results.
- Parser throughput, memory scaling, and logger overhead still need canonical
  corpus measurements.
- Terminal rendering is optimized for operator inspection, not for preserving
  every raw event field in the visual output.
