"""Non-interactive focus reports for replay telemetry."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from tnview.focus import FocusSelection, choose_focus
from tnview.render import RenderOptions, render_run
from tnview.snapshot import snapshot_dict
from tnview.state import RunState


FOCUS_STRATEGIES: dict[str, str] = {
    "bottleneck": "highest truncation/chi pressure",
    "entropy": "highest entanglement entropy",
    "front": "center of the current entanglement front",
    "compute": "slowest observed bond update",
    "center": "middle bond in the visible chain",
}


def focus_payload(state: RunState, selection: FocusSelection) -> dict[str, Any]:
    return {
        "strategy": selection.reason,
        "selection": asdict(selection),
        "snapshot": snapshot_dict(state),
    }


def render_focus_view(
    state: RunState,
    selection: FocusSelection,
    *,
    width: int | None = None,
    unicode: bool = True,
) -> str:
    header = "Focus: " + selection.reason
    if selection.bond is not None:
        header += f" at b{selection.bond}"
    return "\n\n".join(
        [
            header,
            render_run(
                state,
                RenderOptions(
                    width=width,
                    unicode=unicode,
                    bond_start=selection.bond_start,
                    bond_limit=selection.bond_limit,
                ),
            ),
        ]
    )


def render_focus_strategies() -> str:
    lines = ["Focus strategies"]
    for name, description in FOCUS_STRATEGIES.items():
        lines.append(f"  {name:<10} {description}")
    return "\n".join(lines)


def focus_strategies_payload() -> dict[str, Any]:
    """Return stable machine-readable focus strategy metadata."""

    return {
        "kind": "focus-strategies",
        "strategies": [
            {"name": name, "description": description}
            for name, description in FOCUS_STRATEGIES.items()
        ],
    }


def apply_focus(state: RunState, *, strategy: str, window: int | None) -> FocusSelection:
    selection = choose_focus(state, strategy=strategy, window=window)
    if selection.bond is not None:
        state.select_bond(selection.bond)
    return selection
