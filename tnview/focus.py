"""Focus helpers for selecting interesting replay regions."""

from __future__ import annotations

from dataclasses import dataclass

from tnview.state import RunState, entanglement_front


@dataclass(frozen=True)
class FocusSelection:
    bond: int | None
    bond_start: int | None
    bond_limit: int | None
    reason: str


def choose_focus(state: RunState, *, strategy: str, window: int | None = None) -> FocusSelection:
    bonds = state.ordered_bonds
    if not bonds:
        return FocusSelection(bond=None, bond_start=None, bond_limit=window, reason="no bonds")

    if strategy == "center":
        bond = bonds[len(bonds) // 2].bond
        reason = "center bond"
    elif strategy == "entropy":
        selected = max(bonds, key=lambda item: item.entropy)
        bond = selected.bond
        reason = "max entropy"
    elif strategy == "compute":
        selected = max(bonds, key=lambda item: item.walltime_ms or 0.0)
        bond = selected.bond
        reason = "slowest update"
    elif strategy == "front":
        front = entanglement_front(state)
        if front is not None and front.active_bonds:
            bond = front.active_bonds[len(front.active_bonds) // 2]
            reason = "entropy front"
        else:
            selected = max(bonds, key=lambda item: item.entropy)
            bond = selected.bond
            reason = "max entropy fallback"
    elif strategy == "bottleneck":
        selected = max(bonds, key=lambda item: (item.trunc_error, item.saturated, item.entropy, item.chi_pressure))
        bond = selected.bond
        reason = "truncation/chi bottleneck"
    else:
        raise ValueError(f"unknown focus strategy {strategy!r}")

    return FocusSelection(
        bond=bond,
        bond_start=_window_start([item.bond for item in bonds], bond, window),
        bond_limit=window,
        reason=reason,
    )


def choose_focus_for_bond(
    state: RunState,
    bond: int,
    window: int | None,
    *,
    reason: str = "selected bond",
) -> FocusSelection:
    bonds = [item.bond for item in state.ordered_bonds]
    if bond not in bonds:
        return FocusSelection(bond=None, bond_start=None, bond_limit=window, reason="bond not found")
    return FocusSelection(
        bond=bond,
        bond_start=_window_start(bonds, bond, window),
        bond_limit=window,
        reason=reason,
    )


def _window_start(bonds: list[int], bond: int, window: int | None) -> int | None:
    if window is None or window <= 0:
        return None
    if bond not in bonds:
        return None
    index = bonds.index(bond)
    first_index = max(0, index - window // 2)
    first_index = min(first_index, max(0, len(bonds) - window))
    return bonds[first_index]
