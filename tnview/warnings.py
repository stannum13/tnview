"""Early-warning diagnostics for TNView run state."""

from __future__ import annotations

from dataclasses import dataclass

from tnview.state import RunState, entanglement_front


@dataclass(frozen=True)
class EarlyWarning:
    chi_saturation_trend: str
    truncation_trend: str
    entropy_front_velocity: float | None
    estimated_chi_need: int | None
    risk: str
    recommendation: str


def early_warning(state: RunState) -> EarlyWarning:
    saturated_counts = _saturated_counts(state)
    truncation_totals = [sum(row.trunc_by_bond.values()) for row in state.history]
    front = entanglement_front(state)
    chi_need = _estimated_chi_need(state)
    chi_trend = _trend(saturated_counts)
    trunc_trend = _trend(truncation_totals, exponential=True)
    risk = _risk(state, chi_trend, trunc_trend)
    return EarlyWarning(
        chi_saturation_trend=chi_trend,
        truncation_trend=trunc_trend,
        entropy_front_velocity=front.velocity_bonds_per_time if front is not None else None,
        estimated_chi_need=chi_need,
        risk=risk,
        recommendation=_recommendation(risk),
    )


def _saturated_counts(state: RunState) -> list[int]:
    counts = []
    for row in state.history:
        count = 0
        for bond, chi in row.chi_by_bond.items():
            bond_state = state.bonds.get(bond)
            if bond_state is not None and bond_state.chi_max > 0 and chi >= bond_state.chi_max:
                count += 1
        counts.append(count)
    return counts


def _estimated_chi_need(state: RunState) -> int | None:
    bonds = state.ordered_bonds
    if not bonds:
        return None

    max_pressure = max((bond.chi_pressure for bond in bonds), default=0.0)
    max_chi = max((bond.chi_max for bond in bonds), default=0)
    if max_chi <= 0:
        return None
    if max_pressure >= 0.98:
        return _next_power_of_two(max_chi * 2)
    if max_pressure >= 0.75:
        return _next_power_of_two(int(max_chi * 1.5))
    return max_chi


def _trend(values: list[float | int], *, exponential: bool = False) -> str:
    if len(values) < 2:
        return "unknown"
    previous = float(values[-2])
    current = float(values[-1])
    if current <= previous:
        return "stable"
    if exponential and previous > 0 and current / previous >= 10:
        return "rising exponentially"
    if current > previous:
        return "rising"
    return "stable"


def _risk(state: RunState, chi_trend: str, trunc_trend: str) -> str:
    saturated = any(bond.saturated for bond in state.ordered_bonds)
    high_trunc = any(bond.trunc_error >= 1e-7 for bond in state.ordered_bonds)
    if saturated and (high_trunc or chi_trend == "rising"):
        return "high"
    if saturated or high_trunc or trunc_trend != "stable":
        return "medium"
    return "low"


def _recommendation(risk: str) -> str:
    if risk == "high":
        return "increase chi_max or change ansatz geometry before extending target time"
    if risk == "medium":
        return "watch central bonds and compare against a larger chi replay"
    return "continue; current complexity growth is controlled"


def _next_power_of_two(value: int) -> int:
    if value <= 1:
        return 1
    return 1 << (value - 1).bit_length()
