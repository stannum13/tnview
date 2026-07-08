# CLI Audit

This is a current architecture snapshot for TNView 1.2.0. It should be treated
as a planning aid, not as a release promise.

## Current Structure

Entrypoints:

- `pyproject.toml`: `tnview = "tnview.cli:main"`
- `python -m tnview.cli`

Commands:

- `replay`: render visual replay telemetry, optionally interactive or snapshot JSON.
- `replay-runlog`: step through run-log events by event index.
- `animate`: render replay checkpoints as oscilloscope or instrument frames.
- `scope`: render a static oscilloscope view of replay signals.
- `live`: stream replay telemetry and refresh on checkpoints.
- `tail`: render replay or run-log state; supports `--follow` and run-log JSON.
- `watch`: live dashboard for append-only run-log telemetry.
- `demo`: generate and render synthetic MPS/TEBD replay telemetry.
- `sketch`: build deterministic synthetic replay telemetry from a prompt or wizard.
- `compare`: compare replay logs, run logs, metrics, or diagnostic regressions.
- `preview`: inspect setup telemetry for complexity risk.
- `inspect`: choose and render a focused replay view.
- `focus`: list focus strategies or render a non-interactive focus view.
- `search`: search replay bonds, sites, tags, tensors, or tensor metadata.
- `validate`: validate replay and run-log JSONL.
- `diagnose`: run deterministic diagnostics over run-log JSONL.
- `export`: export normalized JSONL, manifest JSON, or CSV.
- `examples`: list built-in example logs.
- `fixture`: generate synthetic replay fixtures.
- `schema`: show supported replay and run-log telemetry schemas.
- `init`: write starter telemetry emitter scripts.
- `doctor`: check install, examples, optional integrations, and release checks.
- `tour`: show the motivated first-run tour.
- `recipes`: show runnable workflow recipes.

Shared utilities:

- Event parsing: `tnview.events`, `tnview.runlog`
- Rendering: `tnview.render`, `tnview.terminal`, `tnview.tail`, `tnview.scope`, `tnview.compare`
- State and focus: `tnview.state`, `tnview.focus`, `tnview.focus_report`
- Diagnostics: `tnview.diagnose`, `tnview.commands`
- Output and errors: `tnview.cli_output`
- Export and schemas: `tnview.export`, `tnview.schema`
- Adapters: `tnview.adapters.quimb`, `tnview.adapters.tenpy`

Config and packaging:

- `pyproject.toml`
- `requirements.txt`, `requirements-dev.txt`
- `Makefile`
- `scripts/setup_env.sh`
- No runtime config file yet.

Output paths:

- Human command output writes to stdout.
- Expected errors are centralized through `CliError` / `EventParseError` handling
  in `tnview.cli.main`, with `Path`, `Reason`, and `Try` sections where useful.
- `--verbose` is global and prints tracebacks for expected CLI errors.
- Stable JSON output exists for command surfaces intended for scripts, including
  `tour`, `recipes`, `examples`, `focus --list`, `doctor`, `schema`, `scope`,
  `tail` for run logs, `diagnose`, `compare`, `validate`, `sketch`, and `export`
  formats.
- `RunLogger` writes append-only JSONL telemetry to user-selected files.

## UX Diagnosis

- The command model is broad but coherent around two schemas: visual replay
  telemetry and run-log telemetry.
- `demo`, `tour`, and `recipes` now provide a usable first-run path. The most
  useful command for a lively no-data demo is `tnview demo --animate`.
- `replay` and `replay-runlog` remain the most likely naming confusion because
  they operate on different schemas.
- Human output has a shared diagnostic/error vocabulary, but larger command
  handlers still mix orchestration and printing.
- Machine-readable output is much stronger than the first audit, but not every
  command should grow `--json`; add it only where scripting is a real workflow.
- Interactive replay has keyboard and command-mode navigation. Future TUI work
  should preserve non-key alternatives for accessibility and remote terminals.

## Code Diagnosis

- `tnview/cli.py` remains the main orchestration knot: parsing, dispatch,
  validation, and printing are still in one file.
- The most successful seam so far is:

  ```text
  command -> core action -> human renderer / json payload -> tests
  ```

- `cli_output.py` is the reusable error/output primitive.
- `diagnose`, `tail`, `compare`, `scope`, and `focus` are good examples of
  command surfaces with stable payload or renderer boundaries.
- Tests cover command behavior, output snippets, package metadata, and local UI
  snapshots, but the README command examples are not exhaustively executed.
- Release hygiene now depends on `make setup`, `make check`, `make smoke`,
  package build, and `twine check`.

## Target Architecture

Incremental target shape for this Python project:

```text
tnview/
  cli.py                 # argparse and command routing
  cli_output.py          # human/json output and CLI errors
  commands/              # future home for larger command handlers
  render.py              # replay rendering
  scope.py               # replay signal rendering
  tail.py                # run-log tail/watch rendering
  diagnose.py            # core diagnostics
  runlog.py              # raw run-log event IO
  events.py              # replay event schema
  adapters/
```

Do not rewrite the CLI wholesale. Migrate one command at a time only when the
move removes real duplication or makes a public contract easier to test.

Recommended next architecture slice:

1. Add curated public-doc command truth tests for the highest-visibility README
   commands.
2. Keep all generated UI snapshots and planning artifacts ignored.
3. Move a single large handler out of `cli.py` only after a test defines its
   output contract.
