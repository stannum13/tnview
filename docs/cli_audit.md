# CLI Audit

## Current Structure

Entrypoints:

- `pyproject.toml`: `tnview = "tnview.cli:main"`
- `python -m tnview.cli`

Commands:

- `replay`: render visual replay telemetry, optionally interactive or snapshot JSON.
- `replay-runlog`: step through run-log events by event index.
- `live`: stream replay telemetry and refresh on checkpoints.
- `tail`: render replay or run-log state; supports `--follow`.
- `demo`: generate and render synthetic MPS/TEBD replay telemetry.
- `compare`: compare replay logs or run logs.
- `preview`: inspect setup telemetry for complexity risk.
- `inspect`: choose and render a focused replay view.
- `search`: search replay bonds/sites/tags/tensors.
- `validate`: validate replay and run-log JSONL.
- `diagnose`: run deterministic diagnostics over run-log JSONL.
- `export`: export normalized JSONL, manifest JSON, or CSV.
- `examples`: list built-in example logs.
- `fixture`: generate synthetic replay fixtures.

Shared utilities:

- Event parsing: `tnview.events`, `tnview.runlog`
- Rendering: `tnview.render`, `tnview.tail`, `tnview.compare`, `tnview.preview`, `tnview.search`
- State: `tnview.state`
- Diagnostics: `tnview.diagnose`
- Export: `tnview.export`
- Adapters: `tnview.adapters.quimb`, `tnview.adapters.tenpy`

Config and packaging:

- `pyproject.toml`
- `requirements.txt`, `requirements-dev.txt`
- `Makefile`
- No runtime config file yet.

Output paths:

- Most commands write directly to stdout with `print`.
- Error handling is centralized only at the top-level `main`, and prints compact `tnview: ...` messages to stderr for `EventParseError` and `OSError`.
- `RunLogger` writes JSONL telemetry to user-selected files.

## UX Diagnosis

- Command model is broad but mostly coherent. The biggest naming risk is that `replay` and `replay-runlog` are related but operate on different schemas.
- Many commands have useful output, but there is no shared section/table/error vocabulary.
- Errors usually say what failed, but rarely include a clear `Path`, `Reason`, and `Try` section.
- Machine-readable output exists in places (`--snapshot`, `--csv`, `export --format ...`) but is inconsistent. `diagnose` is a natural first target for `--json`.
- `tail --follow` gives useful status and trends, but long-running command output still lives directly in command handlers.
- There is no global `--verbose` yet; stack traces are not dumped by default because only expected exceptions are caught.

## Code Diagnosis

- `tnview/cli.py` is the main knot: argument parsing, command orchestration, user-facing rendering, printing, and error handling are mixed.
- Print calls are scattered through command handlers.
- `diagnose`, `tail`, `compare`, and `export` duplicate run-log reading and error handling patterns.
- Return codes are mostly stable (`0`, `1`, `2`) but not named or documented in code.
- Tests cover command behavior well, but not a reusable output contract.
- Adding `--json` command by command is feasible, but should not be implemented as ad hoc print logic each time.

## Target Architecture

Incremental target shape for this Python project:

```text
tnview/
  cli.py                 # argparse and command routing
  cli_output.py          # human/json output and CLI errors
  commands/              # future home for larger command handlers
  render.py              # replay rendering
  tail.py                # run-log tail rendering
  diagnose.py            # core diagnostics
  runlog.py              # raw run-log event IO
  events.py              # replay event schema
  adapters/
```

The first useful seam is not a command-package rewrite. It is:

```text
command -> core action -> command result -> human renderer / json renderer -> tests
```

Use `diagnose` as the reference slice because it has:

- clear core logic
- high value for scripts
- natural success and error JSON
- existing tests
- minimal blast radius

Future command migrations should move one command at a time through this seam.
