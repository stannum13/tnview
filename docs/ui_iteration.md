# UI Iteration Workflow

TNView's terminal UI is easiest to improve when every change can be compared
against the same small set of replay and run-log experiences. The commands below
create local artifacts only; `.artifacts/` is ignored by git.

## Snapshot Review

Render the canonical UI set and run basic readability checks:

```bash
make ui-review
```

This writes:

```text
.artifacts/ui/instrument.txt
.artifacts/ui/instrument-ascii-80.txt
.artifacts/ui/instrument-ascii-72.txt
.artifacts/ui/replay-focus.txt
.artifacts/ui/demo.txt
.artifacts/ui/runlog-watch.txt
.artifacts/ui/runlog-tail.txt
.artifacts/ui/review.txt
```

The review report checks for missing landmarks, excessive body width, likely
truncation markers, duplicate focus details, and long blank runs. It is a guardrail,
not a replacement for qualitative inspection.

## Public Demo Assets

Generate committed README-safe SVG cards from real CLI output:

```bash
make demo-assets
```

This writes:

```text
docs/demo/demo-instrument.svg
docs/demo/watch-dashboard.svg
docs/demo/diagnostics.svg
docs/demo/compare-runs.svg
```

These cards should avoid fitted `~` truncation and should show current command
output rather than mocked UI. Regenerate them after changing the public terminal
presentation.

## Variant Worktrees

Create isolated UI experiment branches:

```bash
make ui-worktrees
```

This creates sibling worktrees:

```text
../tnview-ui-panels        ui/panels
../tnview-ui-motion        ui/motion
../tnview-ui-accessibility ui/accessibility
../tnview-ui-demo          ui/demo
```

Use those branches for divergent experiments, then integrate the best small slice
back into `main` with normal tests and an atomic commit.

If a sibling path already exists but is not a registered git worktree, the setup
script stops rather than silently skipping that workstream. Choose another base
directory when needed:

```bash
make ui-worktrees BASE_DIR=/tmp/tnview-ui
```

## Review Loop

1. Pick one worktree and one UX question.
2. Make a small visual change.
3. Run `make ui-review`.
4. Inspect `.artifacts/ui/*.txt` and `.artifacts/ui/review.txt`.
5. Keep, revise, or discard the experiment.
6. Integrate the smallest successful slice into `main`.
