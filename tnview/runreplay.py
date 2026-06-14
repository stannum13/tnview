"""Replay controls for run-log telemetry."""

from __future__ import annotations

import curses
from dataclasses import dataclass
from typing import Any

from tnview.tail import render_run_log_tail


def render_run_log_replay(
    records: list[dict[str, Any]],
    *,
    index: int | None = None,
    width: int = 100,
    unicode: bool = True,
) -> str:
    controller = RunLogReplayController(records, index=index)
    return controller.render(width=width, unicode=unicode)


@dataclass
class RunLogReplayController:
    records: list[dict[str, Any]]
    index: int | None = None
    show_help: bool = False
    input_mode: str | None = None
    input_buffer: str = ""

    def __post_init__(self) -> None:
        if not self.records:
            self.index = None
        elif self.index is None:
            self.index = len(self.records) - 1
        else:
            self.index = _clamp(self.index, 0, len(self.records) - 1)

    @property
    def event_count(self) -> int:
        return len(self.records)

    def current_records(self) -> list[dict[str, Any]]:
        if self.index is None:
            return []
        return self.records[: self.index + 1]

    def render(self, *, width: int, unicode: bool = True) -> str:
        if self.show_help:
            return _help_text()
        position = "n/a" if self.index is None else str(self.index)
        header = f"Run-log replay event {position}/{max(0, self.event_count - 1)}"
        body = render_run_log_tail(self.current_records(), width=width, unicode=unicode)
        return header + "\n" + body

    def handle_key(self, key: str) -> bool:
        if self.input_mode is not None:
            self._handle_input_key(key)
            return True
        if key in {"q", "Q"}:
            return False
        if key in {"?", "H"}:
            self.show_help = not self.show_help
        elif key in {"n", "l", "KEY_RIGHT"}:
            self.next_event()
        elif key in {"p", "h", "KEY_LEFT"}:
            self.previous_event()
        elif key in {"0", "KEY_HOME"}:
            self.first_event()
        elif key in {"$", "KEY_END"}:
            self.last_event()
        elif key == "g":
            self.input_mode = "event"
            self.input_buffer = ""
        return True

    def jump_event(self, index: int) -> None:
        if not self.records:
            return
        self.index = _clamp(index, 0, len(self.records) - 1)

    def next_event(self) -> None:
        if self.index is None:
            return
        self.jump_event(self.index + 1)

    def previous_event(self) -> None:
        if self.index is None:
            return
        self.jump_event(self.index - 1)

    def first_event(self) -> None:
        self.jump_event(0)

    def last_event(self) -> None:
        self.jump_event(len(self.records) - 1)

    def _handle_input_key(self, key: str) -> None:
        if key in {"\n", "\r", "KEY_ENTER"}:
            self._commit_input()
            return
        if key in {"\x1b", "ESC"}:
            self.input_mode = None
            self.input_buffer = ""
            return
        if key in {"KEY_BACKSPACE", "\b", "\x7f"}:
            self.input_buffer = self.input_buffer[:-1]
            return
        if key.isdigit():
            self.input_buffer += key

    def _commit_input(self) -> None:
        if self.input_buffer:
            self.jump_event(int(self.input_buffer))
        self.input_mode = None
        self.input_buffer = ""


def run_interactive_run_log(records: list[dict[str, Any]], *, ascii_mode: bool = False) -> None:
    controller = RunLogReplayController(records)
    curses.wrapper(_main, controller, ascii_mode)


def _main(stdscr: object, controller: RunLogReplayController, ascii_mode: bool) -> None:
    curses.curs_set(0)
    stdscr.keypad(True)
    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        content = controller.render(width=max(60, width), unicode=not ascii_mode)
        footer = _footer(controller)
        for row, line in enumerate(content.splitlines()[: max(0, height - 2)]):
            stdscr.addnstr(row, 0, line, max(0, width - 1))
        stdscr.addnstr(max(0, height - 1), 0, footer, max(0, width - 1), curses.A_REVERSE)
        stdscr.refresh()
        key = stdscr.getkey()
        if not controller.handle_key(key):
            break


def _footer(controller: RunLogReplayController) -> str:
    if controller.input_mode is not None:
        return f"jump event: {controller.input_buffer}_  enter accept  esc cancel"
    index = "n/a" if controller.index is None else str(controller.index)
    return f"event {index}/{max(0, controller.event_count - 1)}  n/p step  0/$ ends  g jump  ? help  q quit"


def _help_text() -> str:
    return "\n".join(
        [
            "Run-log replay keys",
            "",
            "n / right     next event",
            "p / left      previous event",
            "0 / home      first event",
            "$ / end       last event",
            "g             jump to event index",
            "?             toggle help",
            "q             quit",
        ]
    )


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))
