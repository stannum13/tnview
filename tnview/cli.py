"""Command-line interface for TNView."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Iterable, TextIO

from tnview.compare import render_comparison, render_comparison_csv, sort_summaries, summarize_run
from tnview.events import EventParseError, TelemetryEvent, parse_jsonl_line
from tnview.examples import list_examples, render_examples
from tnview.export import export_manifest_json, export_replay_jsonl
from tnview.fixtures import generate_chain_fixture
from tnview.interactive import run_interactive
from tnview.render import RenderOptions, render_run
from tnview.search import render_search, search_bonds
from tnview.snapshot import snapshot_json
from tnview.state import RunState
from tnview.validate import render_validation, validate_lines


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "replay":
            return _replay(args)
        if args.command == "live":
            return _live(args)
        if args.command == "compare":
            return _compare(args)
        if args.command == "search":
            return _search(args)
        if args.command == "validate":
            return _validate(args)
        if args.command == "export":
            return _export(args)
        if args.command == "examples":
            return _examples(args)
        if args.command == "fixture":
            return _fixture(args)
    except EventParseError as exc:
        print(f"tnview: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"tnview: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tnview",
        description="Terminal-native complexity microscope for tensor-network JSONL telemetry.",
    )
    subparsers = parser.add_subparsers(dest="command")

    replay = subparsers.add_parser("replay", help="render a JSONL telemetry replay")
    replay.add_argument("path", help="JSONL replay file, or '-' for stdin")
    replay.add_argument(
        "--checkpoint",
        default="latest",
        help="checkpoint index to render, or 'latest' (default)",
    )
    replay.add_argument("--snapshot", action="store_true", help="write a JSON snapshot instead of terminal view")
    replay.add_argument("--output", "-o", help="write snapshot or rendered output to a file")
    replay.add_argument("--interactive", action="store_true", help="open an interactive replay shell")
    _render_args(replay)

    live = subparsers.add_parser("live", help="stream JSONL telemetry and refresh on checkpoints")
    live.add_argument("path", nargs="?", default="-", help="JSONL source, default stdin")
    live.add_argument("--no-clear", action="store_true", help="do not clear the terminal between frames")
    _render_args(live)

    compare = subparsers.add_parser("compare", help="compare multiple JSONL telemetry replays")
    compare.add_argument("paths", nargs="+", help="JSONL replay files")
    compare.add_argument("--width", type=int, default=160, help="render width in columns")
    compare.add_argument(
        "--sort",
        choices=["input", "name", "risk", "max-entropy", "trunc", "chi"],
        default="input",
        help="sort comparison rows",
    )
    compare.add_argument("--csv", action="store_true", help="write comparison as CSV")

    search = subparsers.add_parser("search", help="search bonds by bond, site, tag, or status")
    search.add_argument("path", help="JSONL replay file")
    search.add_argument("query", help="query such as bond:14, site:15, tag:chi_saturated, status:limited")
    search.add_argument("--checkpoint", default="latest", help="checkpoint index to search, or 'latest'")
    search.add_argument("--width", type=int, default=100, help="render width in columns")

    validate = subparsers.add_parser("validate", help="validate a JSONL telemetry replay")
    validate.add_argument("path", help="JSONL replay file, or '-' for stdin")

    export = subparsers.add_parser("export", help="export normalized replay JSONL or manifest JSON")
    export.add_argument("path", help="JSONL replay file, or '-' for stdin")
    export.add_argument(
        "--format",
        choices=["jsonl", "manifest"],
        default="jsonl",
        help="export format",
    )
    export.add_argument("--output", "-o", help="write exported output to a file")

    examples = subparsers.add_parser("examples", help="list built-in replay examples")
    examples.add_argument("--root", default="examples", help="examples directory")

    fixture = subparsers.add_parser("fixture", help="generate synthetic JSONL replay fixtures")
    fixture.add_argument("kind", choices=["chain"], help="fixture kind")
    fixture.add_argument("--sites", type=int, default=32, help="number of sites")
    fixture.add_argument("--checkpoints", type=int, default=8, help="number of checkpoints")
    fixture.add_argument("--chi-max", type=int, default=256, help="maximum bond dimension")
    fixture.add_argument("--profile", choices=["easy", "hard"], default="hard", help="complexity profile")
    fixture.add_argument("--output", "-o", help="write generated JSONL to a file")

    return parser


def _render_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-b", "--bond", type=int, help="select a bond for the inspector")
    parser.add_argument("--ascii", action="store_true", help="use ASCII heatmap glyphs")
    parser.add_argument("--width", type=int, help="render width in columns")
    parser.add_argument("--history", type=int, default=12, help="number of checkpoint rows to show")
    parser.add_argument("--bond-start", type=int, help="first bond index to show in topology and heatmaps")
    parser.add_argument("--bond-limit", type=int, help="number of bonds to show in topology and heatmaps")
    parser.add_argument("--no-updates", action="store_true", help="hide TEBD update rows")
    parser.add_argument("--no-entropy", action="store_true", help="hide the entropy heatmap")
    parser.add_argument("--no-pressure", action="store_true", help="hide chi/truncation pressure rows")
    parser.add_argument("--no-inspector", action="store_true", help="hide the selected-bond inspector")
    parser.add_argument("--no-diagnostics", action="store_true", help="hide the diagnostics panel")


def _replay(args: argparse.Namespace) -> int:
    events = _read_events(_iter_lines(args.path))
    if args.interactive:
        run_interactive(events, ascii_mode=args.ascii)
        return 0
    state = _state_at_checkpoint(events, args.checkpoint)
    _select_requested_bond(state, args.bond)
    output = snapshot_json(state) if args.snapshot else render_run(state, _options(args))
    _write_output(output, args.output)
    return 0


def _live(args: argparse.Namespace) -> int:
    state = RunState()
    source = _iter_lines(args.path)
    rendered = False

    for line_number, line in enumerate(source, start=1):
        event = parse_jsonl_line(line, line_number=line_number)
        if event is None:
            continue
        state.apply(event)
        _select_requested_bond(state, args.bond)
        if event.__class__.__name__ == "Checkpoint":
            _print_frame(state, args)
            rendered = True

    if not rendered:
        _print_frame(state, args)
    return 0


def _compare(args: argparse.Namespace) -> int:
    summaries = []
    for path in args.paths:
        events = _read_events(_iter_lines(path))
        state = _state_at_checkpoint(events, "latest")
        summaries.append(summarize_run(path, state))
    summaries = sort_summaries(summaries, args.sort)
    print(render_comparison_csv(summaries) if args.csv else render_comparison(summaries, width=args.width))
    return 0


def _search(args: argparse.Namespace) -> int:
    events = _read_events(_iter_lines(args.path))
    state = _state_at_checkpoint(events, args.checkpoint)
    matches = search_bonds(state, args.query)
    print(render_search(matches, query=args.query, width=args.width))
    return 0


def _validate(args: argparse.Namespace) -> int:
    lines = list(_iter_lines(args.path))
    report = validate_lines(lines)
    print(render_validation(report))
    return 0 if report.valid else 2


def _export(args: argparse.Namespace) -> int:
    events = _read_events(_iter_lines(args.path))
    if args.format == "manifest":
        output = export_manifest_json(events)
    else:
        output = export_replay_jsonl(events).rstrip("\n")
    _write_output(output, args.output)
    return 0


def _examples(args: argparse.Namespace) -> int:
    print(render_examples(list_examples(Path(args.root))))
    return 0


def _fixture(args: argparse.Namespace) -> int:
    if args.kind == "chain":
        output = generate_chain_fixture(
            sites=args.sites,
            checkpoints=args.checkpoints,
            chi_max=args.chi_max,
            profile=args.profile,
        )
        _write_output(output.rstrip("\n"), args.output)
        return 0
    raise EventParseError(f"unsupported fixture kind {args.kind!r}")


def _read_events(lines: Iterable[str]) -> list[TelemetryEvent]:
    events: list[TelemetryEvent] = []
    for line_number, line in enumerate(lines, start=1):
        event = parse_jsonl_line(line, line_number=line_number)
        if event is not None:
            events.append(event)
    return events


def _state_at_checkpoint(events: list[TelemetryEvent], checkpoint: str) -> RunState:
    state = RunState()
    checkpoint_count = sum(1 for event in events if event.__class__.__name__ == "Checkpoint")
    target = _checkpoint_target(checkpoint, checkpoint_count)

    seen = 0
    for event in events:
        state.apply(event)
        if event.__class__.__name__ == "Checkpoint":
            if seen == target:
                break
            seen += 1
    return state


def _checkpoint_target(checkpoint: str, checkpoint_count: int) -> int | None:
    if checkpoint == "latest":
        return None if checkpoint_count == 0 else checkpoint_count - 1
    try:
        target = int(checkpoint)
    except ValueError as exc:
        raise EventParseError("--checkpoint must be an integer index or 'latest'") from exc
    if target < 0:
        raise EventParseError("--checkpoint must be non-negative")
    if checkpoint_count and target >= checkpoint_count:
        raise EventParseError(f"--checkpoint {target} out of range; replay has {checkpoint_count} checkpoints")
    return target


def _select_requested_bond(state: RunState, bond: int | None) -> None:
    if bond is not None:
        state.select_bond(bond)


def _print_frame(state: RunState, args: argparse.Namespace) -> None:
    if not args.no_clear and sys.stdout.isatty():
        print("\033[2J\033[H", end="")
    print(render_run(state, _options(args)))
    print(flush=True)


def _options(args: argparse.Namespace) -> RenderOptions:
    return RenderOptions(
        width=args.width,
        unicode=not args.ascii,
        history_limit=max(1, args.history),
        bond_start=args.bond_start,
        bond_limit=args.bond_limit,
        show_updates=not args.no_updates,
        show_entropy=not args.no_entropy,
        show_pressure=not args.no_pressure,
        show_inspector=not args.no_inspector,
        show_diagnostics=not args.no_diagnostics,
    )


def _iter_lines(path: str) -> Iterable[str]:
    if path == "-":
        yield from sys.stdin
        return

    with _open_path(path) as handle:
        yield from handle


def _open_path(path: str) -> TextIO:
    return Path(path).open("r", encoding="utf-8")


def _write_output(output: str, path: str | None) -> None:
    if path is None:
        print(output)
        return
    Path(path).write_text(output + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
