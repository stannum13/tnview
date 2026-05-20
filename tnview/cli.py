"""Command-line interface for TNView."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Iterable, TextIO

from tnview.events import EventParseError, parse_jsonl_line
from tnview.render import RenderOptions, render_run
from tnview.state import RunState


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "replay":
            return _replay(args)
        if args.command == "live":
            return _live(args)
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
    _render_args(replay)

    live = subparsers.add_parser("live", help="stream JSONL telemetry and refresh on checkpoints")
    live.add_argument("path", nargs="?", default="-", help="JSONL source, default stdin")
    live.add_argument("--no-clear", action="store_true", help="do not clear the terminal between frames")
    _render_args(live)

    return parser


def _render_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-b", "--bond", type=int, help="select a bond for the inspector")
    parser.add_argument("--ascii", action="store_true", help="use ASCII heatmap glyphs")
    parser.add_argument("--width", type=int, help="render width in columns")
    parser.add_argument("--history", type=int, default=12, help="number of checkpoint rows to show")


def _replay(args: argparse.Namespace) -> int:
    state = _read_state(_iter_lines(args.path))
    _select_requested_bond(state, args.bond)
    print(render_run(state, _options(args)))
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


def _read_state(lines: Iterable[str]) -> RunState:
    state = RunState()
    for line_number, line in enumerate(lines, start=1):
        event = parse_jsonl_line(line, line_number=line_number)
        if event is not None:
            state.apply(event)
    return state


def _select_requested_bond(state: RunState, bond: int | None) -> None:
    if bond is not None:
        state.select_bond(bond)


def _print_frame(state: RunState, args: argparse.Namespace) -> None:
    if not args.no_clear and sys.stdout.isatty():
        print("\033[2J\033[H", end="")
    print(render_run(state, _options(args)))
    print(flush=True)


def _options(args: argparse.Namespace) -> RenderOptions:
    return RenderOptions(width=args.width, unicode=not args.ascii, history_limit=max(1, args.history))


def _iter_lines(path: str) -> Iterable[str]:
    if path == "-":
        yield from sys.stdin
        return

    with _open_path(path) as handle:
        yield from handle


def _open_path(path: str) -> TextIO:
    return Path(path).open("r", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
