# Upstream Pins

TNView is the telemetry layer. E001 must validate diagnostics on real tensor-network runs while keeping upstream simulation libraries outside this repository.

Pinned on 2026-07-17:

| Role | Repository | Pinned commit | Use in E001 |
| --- | --- | --- | --- |
| Primary experimental host | `https://github.com/jcmgray/quimb.git` | `3c89529fe0a3487133a3928201691161e110abdf` | Generate the canonical Quimb run corpus and validate the adapter against real Quimb objects/callbacks. |
| Optional compatibility host | `https://github.com/tenpy/tenpy.git` | `416043deb0145f22e97fd881fe469956279b99d2` | Optional compatibility smoke after Quimb evidence exists. TeNPy is not required for the first canonical result. |

## Current Integration Boundary

- No Quimb or TeNPy source is vendored here.
- The core package still has no required third-party runtime dependencies.
- The Quimb adapter uses public object attributes and callbacks by duck typing.
- Fork Quimb only if a generic event hook is missing and the smallest useful upstream-quality callback cannot be implemented downstream.

## Refresh Rule

Changing an upstream pin invalidates canonical E001 comparability unless `experiments/e001/experiment.md` and `experiments/e001/configs/canonical.json` are updated before the run.
