"""Compute-cost diagnostics derived from bond telemetry."""

from __future__ import annotations

from dataclasses import dataclass

from tnview.events import ContractionPathEvent
from tnview.state import BondState, RunState


@dataclass(frozen=True)
class ComputeCost:
    slowest_bond: BondState | None
    largest_chi_bond: BondState | None
    estimated_largest_tensor: str | None
    estimated_memory_mb: float | None
    contraction_path: ContractionPathEvent | None
    diagnosis: str


def compute_cost(state: RunState, *, physical_dim: int = 2) -> ComputeCost:
    bonds = state.ordered_bonds
    if not bonds:
        return ComputeCost(
            slowest_bond=None,
            largest_chi_bond=None,
            estimated_largest_tensor=None,
            estimated_memory_mb=None,
            contraction_path=_latest_path(state),
            diagnosis="waiting for compute telemetry",
        )

    slowest = max(bonds, key=lambda bond: bond.walltime_ms or 0.0)
    largest = max(bonds, key=lambda bond: bond.chi)
    path = _latest_path(state)
    tensor_shape = f"{largest.chi} x {physical_dim} x {largest.chi}"
    memory_mb = path.estimated_memory_mb if path and path.estimated_memory_mb is not None else largest.chi * physical_dim * largest.chi * 16 / 1_000_000
    return ComputeCost(
        slowest_bond=slowest if slowest.walltime_ms is not None else None,
        largest_chi_bond=largest,
        estimated_largest_tensor=tensor_shape,
        estimated_memory_mb=memory_mb,
        contraction_path=path,
        diagnosis=_diagnosis(slowest, largest),
    )


def _latest_path(state: RunState) -> ContractionPathEvent | None:
    if not state.contraction_paths:
        return None
    return state.contraction_paths[-1]


def _diagnosis(slowest: BondState, largest: BondState) -> str:
    if slowest.bond == largest.bond and largest.saturated:
        return "runtime dominated by saturated high-entropy region"
    if slowest.bond == largest.bond:
        return "runtime follows local chi pressure"
    return "compute hotspot differs from largest chi bond"
