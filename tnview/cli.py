"""Command-line interface for TNView."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from time import sleep
from typing import Iterable, TextIO

from tnview.commands import diagnose_run_log
from tnview.compare import (
    render_comparison,
    render_comparison_csv,
    render_run_log_comparison,
    render_run_log_comparison_csv,
    sort_run_log_summaries,
    sort_summaries,
    summarize_run,
    summarize_run_log,
)
from tnview.cli_output import CliError, error_payload, render_error, result_payload, write_json, write_text
from tnview.events import EventParseError, TelemetryEvent, parse_jsonl_line
from tnview.examples import list_examples, render_examples
from tnview.export import export_manifest_json, export_records_csv, export_replay_csv, export_replay_jsonl
from tnview.fixtures import generate_chain_fixture
from tnview.focus import choose_focus, choose_focus_for_bond
from tnview.interactive import run_interactive
from tnview.preview import complexity_preview, render_preview
from tnview.render import RenderOptions, render_run
from tnview.runreplay import render_run_log_replay, run_interactive_run_log
from tnview.runlog import RUN_LOG_EVENTS, read_jsonl_records
from tnview.search import is_tensor_query, render_search, render_tensor_search, search_bonds, search_tensors
from tnview.snapshot import snapshot_json
from tnview.state import RunState
from tnview.tail import render_run_log_tail
from tnview.validate import render_validation, validate_lines, validation_payload


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "replay":
            return _replay(args)
        if args.command == "replay-runlog":
            return _replay_runlog(args)
        if args.command == "live":
            return _live(args)
        if args.command == "tail":
            return _tail(args)
        if args.command == "demo":
            return _demo(args)
        if args.command == "compare":
            return _compare(args)
        if args.command == "preview":
            return _preview(args)
        if args.command == "inspect":
            return _inspect(args)
        if args.command == "search":
            return _search(args)
        if args.command == "validate":
            return _validate(args)
        if args.command == "diagnose":
            return _diagnose(args)
        if args.command == "export":
            return _export(args)
        if args.command == "examples":
            return _examples(args)
        if args.command == "fixture":
            return _fixture(args)
    except CliError as exc:
        if getattr(args, "json", False):
            write_json(error_payload(exc), stream=sys.stderr)
        else:
            write_text(render_error(exc), stream=sys.stderr)
        return exc.exit_code
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
        description="Terminal-native viewer for tensor-network dynamics and complexity telemetry.",
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
    replay.add_argument(
        "--focus",
        choices=["none", "bottleneck", "entropy", "front", "compute", "center"],
        default="none",
        help="select an interesting bond automatically",
    )
    _render_args(replay)

    replay_runlog = subparsers.add_parser("replay-runlog", help="replay a run-log JSONL file by event index")
    replay_runlog.add_argument("path", help="JSONL run log, or '-' for stdin")
    replay_runlog.add_argument("--index", default="latest", help="event index to render, or 'latest' (default)")
    replay_runlog.add_argument("--interactive", action="store_true", help="open an interactive run-log replay shell")
    replay_runlog.add_argument("--ascii", action="store_true", help="use ASCII sparklines")
    replay_runlog.add_argument("--width", type=int, default=100, help="render width in columns")

    live = subparsers.add_parser("live", help="stream JSONL telemetry and refresh on checkpoints")
    live.add_argument("path", nargs="?", default="-", help="JSONL source, default stdin")
    live.add_argument("--no-clear", action="store_true", help="do not clear the terminal between frames")
    _render_args(live)

    tail = subparsers.add_parser("tail", help="tail a TNView replay or run-log JSONL file")
    tail.add_argument("path", nargs="?", default="-", help="JSONL source, default stdin")
    tail.add_argument("--follow", "-f", action="store_true", help="keep refreshing as new JSONL events are appended")
    tail.add_argument("--interval", type=float, default=1.0, help="refresh interval in seconds for --follow")
    tail.add_argument("--max-refreshes", type=int, help="stop after N refreshes, useful for scripted checks")
    tail.add_argument("--no-clear", action="store_true", help="do not clear the terminal between frames")
    _render_args(tail)

    demo = subparsers.add_parser("demo", help="render a generated tensor-network dynamics demo")
    demo.add_argument("--sites", type=int, default=32, help="number of sites in the generated chain")
    demo.add_argument("--checkpoints", type=int, default=10, help="number of generated checkpoints")
    demo.add_argument("--chi-max", type=int, default=128, help="maximum bond dimension")
    demo.add_argument("--profile", choices=["easy", "hard"], default="hard", help="demo complexity profile")
    demo.add_argument("--interactive", action="store_true", help="open the generated replay in the interactive shell")
    demo.add_argument("--ascii", action="store_true", help="use ASCII heatmap glyphs")
    demo.add_argument("--width", type=int, help="render width in columns")
    demo.add_argument("--window", type=int, default=16, help="number of bonds to show around the bottleneck")

    compare = subparsers.add_parser("compare", help="compare multiple JSONL telemetry replays")
    compare.add_argument("paths", nargs="+", help="JSONL replay files")
    compare.add_argument("--width", type=int, default=160, help="render width in columns")
    compare.add_argument(
        "--sort",
        choices=["input", "name", "risk", "max-entropy", "trunc", "chi"],
        default="input",
        help="sort comparison rows",
    )
    compare.add_argument(
        "--metric",
        choices=["energy", "delta-energy", "loss", "trunc", "chi", "entropy", "rss", "wall"],
        help="sort run-log comparisons by a specific metric",
    )
    compare.add_argument("--csv", action="store_true", help="write comparison as CSV")

    preview = subparsers.add_parser("preview", help="preview model/ansatz complexity from setup telemetry")
    preview.add_argument("path", help="JSONL replay or setup metadata file")
    preview.add_argument("--width", type=int, default=100, help="render width in columns")

    inspect = subparsers.add_parser("inspect", help="render a focused bottleneck view of a replay")
    inspect.add_argument("path", help="JSONL replay file")
    inspect.add_argument("--checkpoint", default="latest", help="checkpoint index to inspect, or 'latest'")
    inspect.add_argument(
        "--focus",
        choices=["bottleneck", "entropy", "front", "compute", "center"],
        default="bottleneck",
        help="focus strategy",
    )
    inspect.add_argument("--window", type=int, default=12, help="number of bonds to show around focus")
    inspect.add_argument("--ascii", action="store_true", help="use ASCII heatmap glyphs")
    inspect.add_argument("--width", type=int, help="render width in columns")

    search = subparsers.add_parser("search", help="search bonds by bond, site, tag, or status")
    search.add_argument("path", help="JSONL replay file")
    search.add_argument("query", help="query such as bond:14, site:15, tag:chi_saturated, status:limited")
    search.add_argument("--checkpoint", default="latest", help="checkpoint index to search, or 'latest'")
    search.add_argument("--width", type=int, default=100, help="render width in columns")

    validate = subparsers.add_parser("validate", help="validate a JSONL telemetry replay")
    validate.add_argument("path", help="JSONL replay file, or '-' for stdin")
    validate.add_argument("--strict", action="store_true", help="require run-log metadata fields")
    validate.add_argument("--json", action="store_true", help="write stable machine-readable validation JSON")

    diagnose = subparsers.add_parser("diagnose", help="print run-log diagnostics")
    diagnose.add_argument("path", help="JSONL run log, or '-' for stdin")
    diagnose.add_argument("--json", action="store_true", help="write stable machine-readable diagnostics JSON")

    export = subparsers.add_parser("export", help="export normalized replay JSONL or manifest JSON")
    export.add_argument("path", help="JSONL replay file, or '-' for stdin")
    export.add_argument(
        "--format",
        choices=["jsonl", "manifest", "csv"],
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
    parser.add_argument("--window", type=int, help="number of bonds to show around selected/focused bond")
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
    _apply_focus_and_selection(state, args)
    output = snapshot_json(state) if args.snapshot else render_run(state, _options(args))
    _write_output(output, args.output)
    return 0


def _replay_runlog(args: argparse.Namespace) -> int:
    report = read_jsonl_records(_iter_lines(args.path))
    if report.errors:
        raise EventParseError("; ".join(report.errors))
    records = [record for record in report.records if record.get("event") in RUN_LOG_EVENTS]
    if not records:
        raise EventParseError("no run-log events found")
    if args.interactive:
        run_interactive_run_log(records, ascii_mode=args.ascii)
        return 0
    index = _run_log_index(args.index, len(records))
    print(render_run_log_replay(records, index=index, width=args.width, unicode=not args.ascii))
    return 0


def _live(args: argparse.Namespace) -> int:
    return _render_live_lines(_iter_lines(args.path), args)


def _tail(args: argparse.Namespace) -> int:
    if args.follow:
        return _tail_follow(args)
    lines = list(_iter_lines(args.path))
    report = read_jsonl_records(lines)
    run_records = [record for record in report.records if record.get("event") in RUN_LOG_EVENTS]
    if run_records:
        print(render_run_log_tail(run_records, width=args.width or 100, unicode=not args.ascii))
        return 0 if not report.errors else 2
    return _render_live_lines(lines, args)


def _tail_follow(args: argparse.Namespace) -> int:
    if args.path == "-":
        raise EventParseError("tail --follow requires a file path")
    if args.interval <= 0:
        raise EventParseError("--interval must be positive")
    if args.max_refreshes is not None and args.max_refreshes <= 0:
        raise EventParseError("--max-refreshes must be positive")

    refreshes = 0
    status = 0
    try:
        while args.max_refreshes is None or refreshes < args.max_refreshes:
            output, status = _tail_snapshot(args)
            if not args.no_clear and sys.stdout.isatty():
                print("\033[2J\033[H", end="")
            print(output)
            print(flush=True)
            refreshes += 1
            if args.max_refreshes is not None and refreshes >= args.max_refreshes:
                break
            sleep(args.interval)
    except KeyboardInterrupt:
        return status
    return status


def _tail_snapshot(args: argparse.Namespace) -> tuple[str, int]:
    lines = list(_iter_lines(args.path))
    report = read_jsonl_records(lines)
    run_records = [record for record in report.records if record.get("event") in RUN_LOG_EVENTS]
    if run_records:
        return render_run_log_tail(run_records, width=args.width or 100, unicode=not args.ascii), 0 if not report.errors else 2

    events = _read_events(lines)
    state = _state_at_checkpoint(events, "latest")
    _apply_focus_and_selection(state, args)
    return render_run(state, _options(args)), 0


def _render_live_lines(lines: Iterable[str], args: argparse.Namespace) -> int:
    state = RunState()
    rendered = False

    for line_number, line in enumerate(lines, start=1):
        event = parse_jsonl_line(line, line_number=line_number)
        if event is None:
            continue
        state.apply(event)
        _apply_focus_and_selection(state, args)
        if event.__class__.__name__ == "Checkpoint":
            _print_frame(state, args)
            rendered = True

    if not rendered:
        _print_frame(state, args)
    return 0


def _demo(args: argparse.Namespace) -> int:
    replay = generate_chain_fixture(
        sites=args.sites,
        checkpoints=args.checkpoints,
        chi_max=args.chi_max,
        profile=args.profile,
        run_id="tnview-demo",
    )
    events = _read_events(replay.splitlines())
    if args.interactive:
        run_interactive(events, ascii_mode=args.ascii)
        return 0

    state = _state_at_checkpoint(events, "latest")
    focus = choose_focus(state, strategy="bottleneck", window=args.window)
    if focus.bond is not None:
        state.select_bond(focus.bond)
    print(f"TNView demo | generated {args.profile} MPS/TEBD replay")
    print("Tip: run `tnview demo --interactive` for keyboard navigation.")
    print()
    print(
        render_run(
            state,
            RenderOptions(
                width=args.width,
                unicode=not args.ascii,
                bond_start=focus.bond_start,
                bond_limit=focus.bond_limit,
            ),
        )
    )
    return 0


def _compare(args: argparse.Namespace) -> int:
    sources = [(path, list(_iter_lines(path))) for path in args.paths]
    raw_reports = [(path, read_jsonl_records(lines)) for path, lines in sources]
    run_log_inputs = [
        (path, [record for record in report.records if record.get("event") in RUN_LOG_EVENTS])
        for path, report in raw_reports
    ]
    has_run_logs = [bool(records) for _, records in run_log_inputs]
    if any(has_run_logs):
        if not all(has_run_logs):
            raise EventParseError("compare cannot mix replay telemetry and run-log telemetry")
        errors = [f"{path}: {error}" for path, report in raw_reports for error in report.errors]
        if errors:
            raise EventParseError("; ".join(errors))
        summaries = [summarize_run_log(path, records) for path, records in run_log_inputs]
        summaries = sort_run_log_summaries(summaries, args.sort, metric=args.metric)
        print(
            render_run_log_comparison_csv(summaries)
            if args.csv
            else render_run_log_comparison(summaries, width=args.width)
        )
        return 0
    if args.metric:
        raise EventParseError("--metric is only supported for run-log comparisons")
    summaries = []
    for path, lines in sources:
        events = _read_events(lines)
        state = _state_at_checkpoint(events, "latest")
        summaries.append(summarize_run(path, state))
    summaries = sort_summaries(summaries, args.sort)
    print(render_comparison_csv(summaries) if args.csv else render_comparison(summaries, width=args.width))
    return 0


def _preview(args: argparse.Namespace) -> int:
    events = _read_events(_iter_lines(args.path))
    state = _state_for_preview(events)
    print(render_preview(complexity_preview(state), width=args.width))
    return 0


def _inspect(args: argparse.Namespace) -> int:
    events = _read_events(_iter_lines(args.path))
    state = _state_at_checkpoint(events, args.checkpoint)
    focus = choose_focus(state, strategy=args.focus, window=args.window)
    if focus.bond is not None:
        state.select_bond(focus.bond)
    options = RenderOptions(
        width=args.width,
        unicode=not args.ascii,
        bond_start=focus.bond_start,
        bond_limit=focus.bond_limit,
    )
    print(f"Focus: {focus.reason}" + (f" at b{focus.bond}" if focus.bond is not None else ""))
    print()
    print(render_run(state, options))
    return 0


def _search(args: argparse.Namespace) -> int:
    events = _read_events(_iter_lines(args.path))
    state = _state_at_checkpoint(events, args.checkpoint)
    if is_tensor_query(args.query):
        matches = search_tensors(state, args.query)
        print(render_tensor_search(matches, query=args.query, width=args.width))
        return 0
    matches = search_bonds(state, args.query)
    print(render_search(matches, query=args.query, width=args.width))
    return 0


def _validate(args: argparse.Namespace) -> int:
    lines = list(_iter_lines(args.path))
    report = validate_lines(lines, strict=args.strict)
    if args.json:
        write_json(validation_payload(report))
    else:
        print(render_validation(report))
    return 0 if report.valid else 2


def _diagnose(args: argparse.Namespace) -> int:
    result = diagnose_run_log(_iter_lines(args.path), path=args.path)
    if args.json:
        write_json(result_payload(result))
    else:
        write_text(result.text)
    return result.exit_code


def _export(args: argparse.Namespace) -> int:
    lines = list(_iter_lines(args.path))
    if args.format == "csv":
        report = read_jsonl_records(lines)
        if report.errors:
            raise EventParseError("; ".join(report.errors))
        if any(record.get("event") in RUN_LOG_EVENTS for record in report.records):
            output = export_records_csv(report.records)
        else:
            output = export_replay_csv(_read_events(lines))
        _write_output(output, args.output)
        return 0
    events = _read_events(lines)
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


def _state_for_preview(events: list[TelemetryEvent]) -> RunState:
    state = RunState()
    for event in events:
        if event.__class__.__name__ in {"BondUpdated", "Checkpoint", "ObservableUpdated", "TdvpSweep"}:
            break
        state.apply(event)
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


def _run_log_index(index: str, count: int) -> int | None:
    if index == "latest":
        return None
    try:
        target = int(index)
    except ValueError as exc:
        raise EventParseError("--index must be an integer index or 'latest'") from exc
    if target < 0:
        raise EventParseError("--index must be non-negative")
    if target >= count:
        raise EventParseError(f"--index {target} out of range; run log has {count} events")
    return target


def _select_requested_bond(state: RunState, bond: int | None) -> None:
    if bond is not None:
        state.select_bond(bond)


def _apply_focus_and_selection(state: RunState, args: argparse.Namespace) -> None:
    explicit_bond_start = args.bond_start
    if getattr(args, "focus", "none") != "none":
        focus = choose_focus(state, strategy=args.focus, window=args.window or args.bond_limit)
        if focus.bond is not None:
            state.select_bond(focus.bond)
        if args.bond_start is None:
            args.bond_start = focus.bond_start
        if args.bond_limit is None:
            args.bond_limit = focus.bond_limit
    _select_requested_bond(state, args.bond)
    if args.window is not None and explicit_bond_start is None:
        focused = state.selected_bond
        if focused is not None:
            focus = choose_focus_for_bond(state, focused, args.window)
            args.bond_start = focus.bond_start
            args.bond_limit = focus.bond_limit


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
        bond_limit=args.bond_limit or args.window,
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
