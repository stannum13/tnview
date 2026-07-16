# E001 Preregistration: Early Tensor-Network Diagnostics

**Status:** preregistered, not yet canonically run
**Date:** 2026-07-17
**Harness branch:** `refocus/upstream-e001-public`
**Upstream pins:** see `UPSTREAM.md`

## Question

Can telemetry from the early portion of a DMRG or TEBD run identify capacity-limited or truncation-limited runs early enough to avoid wasted compute while keeping false stops on healthy runs low?

## Hypothesis

A compact diagnostic rule using only telemetry available by a predeclared fraction of the run can save measurable compute on capacity-limited or truncation-limited Quimb runs while maintaining a false-stop rate at or below the configured limit.

## Primary Substrate

Canonical evidence targets Quimb at the pinned commit in `UPSTREAM.md`. TNView should remain an external telemetry adapter unless a generic Quimb callback hook is genuinely missing. TeNPy remains optional compatibility evidence, not a blocker for the first canonical Quimb result.

## Baselines

- No early warning.
- Current fixed TNView diagnostic thresholds.
- A recent-trend baseline that uses only the last few telemetry points.
- An oracle label derived from the completed paired higher-accuracy run.

## Treatment

A declared TNView diagnostic policy using only metrics available at early fractions of each run. It may use energy/loss deltas, truncation error, chi saturation, runtime, and memory telemetry, but it must not inspect final labels or paired-reference outcomes at decision time.

## Corpus Plan

- Model families: transverse-field Ising chain and Heisenberg-like spin chain.
- Geometries/orderings: at least one simple chain and one ordering or geometry that changes entanglement pressure.
- Sizes: at least three system sizes around the smoke/canonical budget.
- Accuracy axis: multiple `chi_max` values and truncation tolerances.
- Paired references: each candidate run must have a higher-accuracy paired reference for labeling.
- Seeds: at least three repeated seeds or deterministic equivalent variants where stochasticity is absent.

## Labels

Capacity-limited labels must come from paired higher-chi or higher-accuracy references, not from subjective inspection. A run is a false stop if the early policy would stop it but the completed paired-reference comparison marks it healthy under the preregistered final-error tolerance.

## Primary Metrics

- Early-warning precision and recall.
- False-stop rate.
- Detection fraction of the run.
- Compute saved under the declared stopping policy.
- Final energy or observable error relative to the paired reference.
- Telemetry write overhead.
- Parser throughput on canonical JSONL files.

## Required Controls

- Held-out model family or geometry.
- Held-out system size.
- Time-shuffled telemetry.
- Feature set excluding energy/loss.
- Feature set excluding memory and runtime telemetry.

## Promotion Rule

Promote the diagnostic result only if the treatment saves measurable compute while keeping false stops at or below the predeclared threshold and beating transparent fixed-threshold baselines. If it cannot beat thresholds, publish the threshold result and do not add a learned predictor.

## Falsification Rule

Falsify or demote the claim if the rule only works on synthetic fixtures, if paired-reference labels are unavailable, if false stops exceed the declared limit, or if the signal disappears under the held-out family/size controls.

## Artifact Contract

Canonical results must be traceable through:

```text
configuration -> raw run records -> deterministic summary -> table/figure -> README statement
```

Required artifacts after canonical execution:

- `results/e001/manifest.json`
- `results/e001/summary.csv` or `results/e001/summary.json`
- `results/e001/figure.*`
- one manifest row per Quimb run and paired reference
- confusion matrix by model family
- compute-saved versus false-stop curve
- one correct-diagnosis and one incorrect-diagnosis raw telemetry example

## Reproduction Commands

Local fixture and logger-overhead smoke:

```bash
./scripts/reproduce_e001.sh smoke
```

Canonical plan dry-run:

```bash
./scripts/reproduce_e001.sh canonical --dry-run
```

Canonical execution is intentionally blocked until the Quimb corpus runner and paired-reference artifact writer are implemented.
