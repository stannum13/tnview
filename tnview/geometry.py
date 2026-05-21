"""Geometry and ansatz diagnostics derived from run telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from tnview.state import BondState, RunState


@dataclass(frozen=True)
class GeometryEdge:
    site_a: int
    site_b: int
    label: str | None = None
    weight: float | None = None

    @property
    def sites(self) -> tuple[int, int]:
        return (self.site_a, self.site_b)


@dataclass(frozen=True)
class ModelGeometry:
    name: str = "unknown geometry"
    ansatz: str = "MPS"
    edges: tuple[GeometryEdge, ...] = field(default_factory=tuple)
    ansatz_order: tuple[int, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EdgeStress:
    edge: GeometryEdge
    ansatz_distance: int | None
    crossed_bonds: tuple[int, ...]
    max_chi_pressure: float
    max_trunc_error: float
    stress: float | None
    severity: str


@dataclass(frozen=True)
class FlatteningStressSummary:
    model_geometry: str
    ansatz: str
    total_edges: int
    long_range_edges: int
    high_stress_edges: tuple[EdgeStress, ...]
    max_stress: float
    mean_stress: float
    edge_stress: tuple[EdgeStress, ...]
    diagnosis: str


@dataclass(frozen=True)
class AnsatzMismatchSummary:
    current_ansatz: str
    model_geometry: str
    high_pressure_bonds: tuple[int, ...]
    long_range_edges: int
    high_stress_edges: tuple[GeometryEdge, ...]
    mismatch_score: float
    diagnosis: str
    suggestions: tuple[str, ...]


@dataclass(frozen=True)
class GeometryDiagnostics:
    flattening: FlatteningStressSummary
    mismatch: AnsatzMismatchSummary


GeometryMetadata = ModelGeometry | Mapping[str, Any] | None


def geometry_diagnostics(state: RunState, model_geometry: GeometryMetadata = None) -> GeometryDiagnostics:
    """Compute geometry-aware flattening and ansatz mismatch diagnostics.

    ``model_geometry`` may be a ``ModelGeometry`` or a telemetry-derived mapping
    with keys such as ``name``, ``ansatz``, ``edges``, and ``ansatz_order``.
    Edges may be ``GeometryEdge`` instances, ``(site_a, site_b)`` pairs, or
    mappings containing ``site_a``/``site_b`` or ``source``/``target``.
    """

    geometry = _coerce_geometry(model_geometry or _metadata_from_state(state))
    order = geometry.ansatz_order or _infer_ansatz_order(state)
    edges = geometry.edges or _infer_local_edges(state)
    edge_stress = tuple(_edge_stress(edge, state, order) for edge in edges)
    flattening = _flattening_summary(geometry, edge_stress)
    mismatch = _mismatch_summary(state, geometry, flattening)
    return GeometryDiagnostics(flattening=flattening, mismatch=mismatch)


def flattening_stress(state: RunState, model_geometry: GeometryMetadata = None) -> FlatteningStressSummary:
    return geometry_diagnostics(state, model_geometry).flattening


def ansatz_mismatch(state: RunState, model_geometry: GeometryMetadata = None) -> AnsatzMismatchSummary:
    return geometry_diagnostics(state, model_geometry).mismatch


def _coerce_geometry(model_geometry: GeometryMetadata) -> ModelGeometry:
    if model_geometry is None:
        return ModelGeometry(name="inferred 1D chain")
    if isinstance(model_geometry, ModelGeometry):
        return model_geometry

    name = str(model_geometry.get("name") or model_geometry.get("geometry") or "unknown geometry")
    ansatz = str(model_geometry.get("ansatz") or model_geometry.get("current_ansatz") or "MPS")
    order = tuple(_coerce_ints(model_geometry.get("ansatz_order") or model_geometry.get("ordering") or ()))
    raw_edges = model_geometry.get("edges") or model_geometry.get("physical_edges") or ()
    return ModelGeometry(
        name=name,
        ansatz=ansatz,
        edges=tuple(_coerce_edge(edge) for edge in raw_edges),
        ansatz_order=order,
    )


def _metadata_from_state(state: RunState) -> dict[str, Any] | None:
    if state.model_geometry is None and state.ansatz_layout is None:
        return None
    metadata: dict[str, Any] = {}
    if state.model_geometry is not None:
        metadata["name"] = state.model_geometry.name
        metadata["edges"] = state.model_geometry.edges
    if state.ansatz_layout is not None:
        metadata["ansatz"] = state.ansatz_layout.ansatz
        metadata["ansatz_order"] = state.ansatz_layout.ordering
    return metadata


def _coerce_edge(edge: Any) -> GeometryEdge:
    if isinstance(edge, GeometryEdge):
        return edge
    if isinstance(edge, Mapping):
        site_a = edge.get("site_a", edge.get("source", edge.get("u")))
        site_b = edge.get("site_b", edge.get("target", edge.get("v")))
        return GeometryEdge(
            site_a=_coerce_int(site_a),
            site_b=_coerce_int(site_b),
            label=str(edge["label"]) if edge.get("label") is not None else None,
            weight=float(edge["weight"]) if edge.get("weight") is not None else None,
        )
    if isinstance(edge, tuple | list) and len(edge) >= 2:
        return GeometryEdge(site_a=_coerce_int(edge[0]), site_b=_coerce_int(edge[1]))
    raise ValueError(f"unsupported geometry edge {edge!r}")


def _coerce_ints(values: Any) -> tuple[int, ...]:
    if values is None:
        return ()
    return tuple(_coerce_int(value) for value in values)


def _coerce_int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"geometry site ids must be integers, got {value!r}")
    return value


def _infer_ansatz_order(state: RunState) -> tuple[int, ...]:
    sites: set[int] = set()
    for bond in state.ordered_bonds:
        sites.add(bond.site_left)
        sites.add(bond.site_right)
    return tuple(sorted(sites))


def _infer_local_edges(state: RunState) -> tuple[GeometryEdge, ...]:
    return tuple(GeometryEdge(bond.site_left, bond.site_right) for bond in state.ordered_bonds)


def _edge_stress(edge: GeometryEdge, state: RunState, order: tuple[int, ...]) -> EdgeStress:
    positions = {site: index for index, site in enumerate(order)}
    left = positions.get(edge.site_a)
    right = positions.get(edge.site_b)
    if left is None or right is None:
        return EdgeStress(
            edge=edge,
            ansatz_distance=None,
            crossed_bonds=(),
            max_chi_pressure=0.0,
            max_trunc_error=0.0,
            stress=None,
            severity="unknown",
        )

    ansatz_distance = abs(right - left)
    crossed = _crossed_bonds(state, order, min(left, right), max(left, right))
    max_pressure = max((bond.chi_pressure for bond in crossed), default=0.0)
    max_trunc = max((bond.trunc_error for bond in crossed), default=0.0)
    distance_stress = max(0, ansatz_distance - 1)
    weighted_stress = float(distance_stress) * (edge.weight if edge.weight is not None else 1.0)
    return EdgeStress(
        edge=edge,
        ansatz_distance=ansatz_distance,
        crossed_bonds=tuple(bond.bond for bond in crossed),
        max_chi_pressure=max_pressure,
        max_trunc_error=max_trunc,
        stress=weighted_stress,
        severity=_stress_severity(ansatz_distance, max_pressure, max_trunc),
    )


def _crossed_bonds(state: RunState, order: tuple[int, ...], start: int, stop: int) -> tuple[BondState, ...]:
    if start == stop:
        return ()

    by_sites = {
        frozenset((bond.site_left, bond.site_right)): bond
        for bond in state.ordered_bonds
    }
    crossed: list[BondState] = []
    for index in range(start, stop):
        bond = by_sites.get(frozenset((order[index], order[index + 1])))
        if bond is not None:
            crossed.append(bond)
    return tuple(crossed)


def _stress_severity(ansatz_distance: int, max_pressure: float, max_trunc: float) -> str:
    if ansatz_distance >= 4 or (ansatz_distance > 1 and max_pressure >= 0.9):
        return "high"
    if ansatz_distance > 1 or max_pressure >= 0.8 or max_trunc >= 1e-7:
        return "medium"
    return "ok"


def _flattening_summary(
    geometry: ModelGeometry,
    edge_stress: tuple[EdgeStress, ...],
) -> FlatteningStressSummary:
    known = tuple(row for row in edge_stress if row.stress is not None)
    stress_values = tuple(row.stress for row in known if row.stress is not None)
    high = tuple(row for row in edge_stress if row.severity == "high")
    long_range = sum(1 for row in known if row.ansatz_distance is not None and row.ansatz_distance > 1)
    max_stress = max(stress_values, default=0.0)
    mean_stress = sum(stress_values) / len(stress_values) if stress_values else 0.0
    return FlatteningStressSummary(
        model_geometry=geometry.name,
        ansatz=geometry.ansatz,
        total_edges=len(edge_stress),
        long_range_edges=long_range,
        high_stress_edges=high,
        max_stress=max_stress,
        mean_stress=mean_stress,
        edge_stress=edge_stress,
        diagnosis=_flattening_diagnosis(edge_stress, long_range, high),
    )


def _flattening_diagnosis(
    edge_stress: tuple[EdgeStress, ...],
    long_range: int,
    high: tuple[EdgeStress, ...],
) -> str:
    if not edge_stress:
        return "waiting for geometry telemetry"
    if high:
        return "high flattening stress"
    if long_range:
        return "mild flattening stress"
    if any(row.severity == "unknown" for row in edge_stress):
        return "incomplete geometry telemetry"
    return "geometry aligned"


def _mismatch_summary(
    state: RunState,
    geometry: ModelGeometry,
    flattening: FlatteningStressSummary,
) -> AnsatzMismatchSummary:
    high_pressure = tuple(
        bond.bond
        for bond in state.ordered_bonds
        if bond.chi_pressure >= 0.9 or (bond.saturated and bond.trunc_error >= 1e-7)
    )
    high_edges = tuple(row.edge for row in flattening.high_stress_edges)
    score = _mismatch_score(flattening, len(high_pressure), len(state.bonds))
    diagnosis = _mismatch_diagnosis(score, high_pressure, flattening)
    return AnsatzMismatchSummary(
        current_ansatz=geometry.ansatz,
        model_geometry=geometry.name,
        high_pressure_bonds=high_pressure,
        long_range_edges=flattening.long_range_edges,
        high_stress_edges=high_edges,
        mismatch_score=score,
        diagnosis=diagnosis,
        suggestions=_suggestions(diagnosis, geometry.ansatz, flattening.long_range_edges),
    )


def _mismatch_score(flattening: FlatteningStressSummary, pressure_count: int, bond_count: int) -> float:
    if flattening.total_edges == 0 and bond_count == 0:
        return 0.0

    edge_score = flattening.long_range_edges / flattening.total_edges if flattening.total_edges else 0.0
    high_score = len(flattening.high_stress_edges) / flattening.total_edges if flattening.total_edges else 0.0
    pressure_score = pressure_count / bond_count if bond_count else 0.0
    return min(1.0, 0.45 * edge_score + 0.35 * high_score + 0.20 * pressure_score)


def _mismatch_diagnosis(
    score: float,
    high_pressure: tuple[int, ...],
    flattening: FlatteningStressSummary,
) -> str:
    if flattening.total_edges == 0 and not high_pressure:
        return "waiting for geometry telemetry"
    if flattening.high_stress_edges and high_pressure:
        return "geometry mismatch with chi pressure"
    if flattening.high_stress_edges:
        return "geometry mismatch"
    if score >= 0.5 and high_pressure:
        return "geometry mismatch with chi pressure"
    if score >= 0.5:
        return "geometry mismatch"
    if high_pressure:
        return "ansatz pressure without clear geometry mismatch"
    return "ansatz geometry aligned"


def _suggestions(diagnosis: str, ansatz: str, long_range_edges: int) -> tuple[str, ...]:
    suggestions: list[str] = []
    if "geometry mismatch" in diagnosis and long_range_edges:
        suggestions.append("try a different site ordering")
        suggestions.append("block strongly coupled distant sites")
    if ansatz.upper() == "MPS" and long_range_edges:
        suggestions.append("try a PEPS-like or tree layout for this model")
    if "chi pressure" in diagnosis:
        suggestions.append("increase chi_max only after checking layout")
    return tuple(suggestions)
