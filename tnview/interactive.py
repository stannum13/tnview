"""Interactive replay controller and curses shell."""

from __future__ import annotations

import curses
from dataclasses import dataclass

from tnview.events import Checkpoint, TelemetryEvent
from tnview.render import RenderOptions, render_run
from tnview.state import RunState


@dataclass
class ReplayController:
    events: list[TelemetryEvent]
    checkpoint_index: int | None = None
    selected_bond: int | None = None
    show_updates: bool = True
    show_entropy: bool = True
    show_pressure: bool = True
    show_inspector: bool = True
    show_diagnostics: bool = True

    def __post_init__(self) -> None:
        count = self.checkpoint_count
        if self.checkpoint_index is None:
            self.checkpoint_index = count - 1 if count else None

    @property
    def checkpoint_count(self) -> int:
        return sum(1 for event in self.events if isinstance(event, Checkpoint))

    def state(self) -> RunState:
        state = RunState()
        target = self.checkpoint_index
        seen = 0
        for event in self.events:
            state.apply(event)
            if isinstance(event, Checkpoint):
                if seen == target:
                    break
                seen += 1
        if self.selected_bond is not None:
            state.select_bond(self.selected_bond)
        elif state.selected_bond is not None:
            self.selected_bond = state.selected_bond
        return state

    def render(self, *, width: int, unicode: bool = True) -> str:
        return render_run(
            self.state(),
            RenderOptions(
                width=width,
                unicode=unicode,
                show_updates=self.show_updates,
                show_entropy=self.show_entropy,
                show_pressure=self.show_pressure,
                show_inspector=self.show_inspector,
                show_diagnostics=self.show_diagnostics,
            ),
        )

    def handle_key(self, key: str) -> bool:
        if key in {"q", "Q"}:
            return False
        if key in {"n", "l", "KEY_RIGHT"}:
            self.next_checkpoint()
        elif key in {"p", "h", "KEY_LEFT"}:
            self.previous_checkpoint()
        elif key in {"j", "KEY_DOWN"}:
            self.next_bond()
        elif key in {"k", "KEY_UP"}:
            self.previous_bond()
        elif key == "u":
            self.show_updates = not self.show_updates
        elif key == "e":
            self.show_entropy = not self.show_entropy
        elif key == "c":
            self.show_pressure = not self.show_pressure
        elif key == "i":
            self.show_inspector = not self.show_inspector
        elif key == "d":
            self.show_diagnostics = not self.show_diagnostics
        return True

    def next_checkpoint(self) -> None:
        count = self.checkpoint_count
        if not count:
            return
        current = self.checkpoint_index or 0
        self.checkpoint_index = min(count - 1, current + 1)

    def previous_checkpoint(self) -> None:
        if self.checkpoint_index is None:
            return
        self.checkpoint_index = max(0, self.checkpoint_index - 1)

    def next_bond(self) -> None:
        bonds = [bond.bond for bond in self.state().ordered_bonds]
        if not bonds:
            return
        if self.selected_bond not in bonds:
            self.selected_bond = bonds[0]
            return
        index = bonds.index(self.selected_bond)
        self.selected_bond = bonds[min(len(bonds) - 1, index + 1)]

    def previous_bond(self) -> None:
        bonds = [bond.bond for bond in self.state().ordered_bonds]
        if not bonds:
            return
        if self.selected_bond not in bonds:
            self.selected_bond = bonds[0]
            return
        index = bonds.index(self.selected_bond)
        self.selected_bond = bonds[max(0, index - 1)]


def run_interactive(events: list[TelemetryEvent], *, ascii_mode: bool = False) -> None:
    controller = ReplayController(events)
    curses.wrapper(_main, controller, ascii_mode)


def _main(stdscr: object, controller: ReplayController, ascii_mode: bool) -> None:
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


def _footer(controller: ReplayController) -> str:
    checkpoint = "n/a" if controller.checkpoint_index is None else str(controller.checkpoint_index)
    bond = "n/a" if controller.selected_bond is None else f"b{controller.selected_bond}"
    return (
        f"checkpoint {checkpoint}/{max(0, controller.checkpoint_count - 1)}  "
        f"bond {bond}  n/p checkpoint  j/k bond  "
        "u/e/c/i/d toggle  q quit"
    )
