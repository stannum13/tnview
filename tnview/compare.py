"""Comparison rendering for multiple TNView replay files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tnview.drift import drift_diagnostics
from tnview.geometry import geometry_diagnostics
from tnview.state import RunState, diagnose_run


@dataclass(frozen=True)
class RunSummary:
    name: str
    status: str
    step: int | None
    time: float | None
    max_entropy: float
    max_chi: int
    saturated_bonds: int
    total_trunc_error: float
    bottleneck_bond: int | None
    drift_risk: str
    geometry_diagnosis: str


def summarize_run(name: str, state: RunState) -> RunSummary:
    bonds = state.ordered_bonds
    checkpoint = state.latest_checkpoint
    max_entropy = max((bond.entropy for bond in bonds), default=0.0)
    max_chi = max((bond.chi for bond in bonds), default=0)
    saturated_bonds = sum(1 for bond in bonds if bond.saturated)
    total_trunc_error = sum(bond.trunc_error for bond in bonds)
    bottleneck = max(bonds, key=lambda bond: (bond.trunc_error, bond.entropy), default=None)
    drift = drift_diagnostics(state)
    geometry = geometry_diagnostics(state)

    return RunSummary(
        name=Path(name).name,
        status=diagnose_run(state),
        step=checkpoint.step if checkpoint is not None else None,
        time=checkpoint.time if checkpoint is not None else None,
        max_entropy=max_entropy,
        max_chi=max_chi,
        saturated_bonds=saturated_bonds,
        total_trunc_error=total_trunc_error,
        bottleneck_bond=bottleneck.bond if bottleneck is not None else None,
        drift_risk=drift.risk,
        geometry_diagnosis=geometry.mismatch.diagnosis,
    )


def render_comparison(summaries: list[RunSummary], *, width: int = 160) -> str:
    columns = [
        ("model", 24),
        ("step", 6),
        ("time", 8),
        ("max S", 8),
        ("max chi", 8),
        ("sat", 5),
        ("trunc err", 11),
        ("hot bond", 8),
        ("drift", 8),
        ("geometry", 28),
        ("diagnosis", 24),
    ]
    header = "  ".join(label.ljust(size) for label, size in columns)
    divider = "  ".join("-" * size for _, size in columns)
    lines = ["Toy model comparison", _fit(header, width), _fit(divider, width)]
    for summary in summaries:
        row = [
            _clip(summary.name, 24).ljust(24),
            _maybe_int(summary.step).ljust(6),
            _maybe_float(summary.time).ljust(8),
            f"{summary.max_entropy:.3g}".ljust(8),
            str(summary.max_chi).ljust(8),
            str(summary.saturated_bonds).ljust(5),
            f"{summary.total_trunc_error:.2e}".ljust(11),
            _maybe_bond(summary.bottleneck_bond).ljust(8),
            _clip(summary.drift_risk, 8).ljust(8),
            _clip(summary.geometry_diagnosis, 28).ljust(28),
            _clip(summary.status, 24).ljust(24),
        ]
        lines.append(_fit("  ".join(row), width))
    return "\n".join(lines)


def _maybe_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return str(value)


def _maybe_float(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:g}"


def _maybe_bond(value: int | None) -> str:
    if value is None:
        return "n/a"
    return f"b{value}"


def _clip(value: str, size: int) -> str:
    if len(value) <= size:
        return value
    if size <= 1:
        return value[:size]
    return value[: size - 1] + "~"


def _fit(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 1:
        return text[:width]
    return text[: width - 1] + "~"
