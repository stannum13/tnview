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
    show_help: bool = False
    input_mode: str | None = None
    input_buffer: str = ""
    bond_start: int = 0
    bond_limit: int = 24

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
        if self.show_help:
            return _help_text()
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
                bond_start=self.bond_start,
                bond_limit=self.bond_limit,
            ),
        )

    def handle_key(self, key: str) -> bool:
        if self.input_mode is not None:
            self._handle_input_key(key)
            return True
        if key in {"q", "Q"}:
            return False
        if key in {"?", "H"}:
            self.show_help = not self.show_help
        if key in {"n", "l", "KEY_RIGHT"}:
            self.next_checkpoint()
        elif key in {"p", "h", "KEY_LEFT"}:
            self.previous_checkpoint()
        elif key in {"j", "KEY_DOWN"}:
            self.next_bond()
        elif key in {"k", "KEY_UP"}:
            self.previous_bond()
        elif key in {"]", "KEY_NPAGE"}:
            self.next_bond_window()
        elif key in {"[", "KEY_PPAGE"}:
            self.previous_bond_window()
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
        elif key == "g":
            self.input_mode = "checkpoint"
            self.input_buffer = ""
        elif key == "b":
            self.input_mode = "bond"
            self.input_buffer = ""
        return True

    def jump_checkpoint(self, index: int) -> None:
        count = self.checkpoint_count
        if not count:
            return
        self.checkpoint_index = min(count - 1, max(0, index))

    def jump_bond(self, bond: int) -> None:
        bonds = {bond_state.bond for bond_state in self.state().ordered_bonds}
        if bond in bonds:
            self.selected_bond = bond

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

    def next_bond_window(self) -> None:
        bonds = [bond.bond for bond in self.state().ordered_bonds]
        if not bonds:
            return
        max_start = max(0, bonds[-1] - self.bond_limit + 1)
        self.bond_start = min(max_start, self.bond_start + self.bond_limit)

    def previous_bond_window(self) -> None:
        self.bond_start = max(0, self.bond_start - self.bond_limit)

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
            value = int(self.input_buffer)
            if self.input_mode == "checkpoint":
                self.jump_checkpoint(value)
            elif self.input_mode == "bond":
                self.jump_bond(value)
        self.input_mode = None
        self.input_buffer = ""


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
    if controller.input_mode is not None:
        label = "checkpoint" if controller.input_mode == "checkpoint" else "bond"
        return f"jump {label}: {controller.input_buffer}_  enter accept  esc cancel"
    checkpoint = "n/a" if controller.checkpoint_index is None else str(controller.checkpoint_index)
    bond = "n/a" if controller.selected_bond is None else f"b{controller.selected_bond}"
    toggles = (
        f"U:{_on(controller.show_updates)} "
        f"E:{_on(controller.show_entropy)} "
        f"C:{_on(controller.show_pressure)} "
        f"I:{_on(controller.show_inspector)} "
        f"D:{_on(controller.show_diagnostics)}"
    )
    return (
        f"checkpoint {checkpoint}/{max(0, controller.checkpoint_count - 1)}  "
        f"bond {bond}  window b{controller.bond_start}+{controller.bond_limit}  "
        f"{toggles}  ? help  q quit"
    )


def _on(value: bool) -> str:
    return "on" if value else "off"


def _help_text() -> str:
    return "\n".join(
        [
            "TNView interactive replay help",
            "",
            "navigation",
            "  n, l, right     next checkpoint",
            "  p, h, left      previous checkpoint",
            "  j, down         next bond",
            "  k, up           previous bond",
            "  g               jump to checkpoint index",
            "  b               jump to bond index",
            "  [, ]            previous/next bond viewport",
            "",
            "toggles",
            "  u               TEBD/TDVP updates",
            "  e               entropy heatmap",
            "  c               chi/truncation rows",
            "  i               selected-bond inspector",
            "  d               diagnostics",
            "",
            "other",
            "  ?               toggle this help",
            "  q               quit",
        ]
    )
