"""Complexity preview derived from geometry and ansatz metadata."""

from __future__ import annotations

from dataclasses import dataclass
import textwrap

from tnview.geometry import geometry_diagnostics
from tnview.state import RunState


@dataclass(frozen=True)
class ComplexityPreview:
    sites: int | None
    geometry: str
    dimensions: tuple[int, ...]
    boundary: str | None
    ansatz: str
    interaction_range: str
    expected_lightcone: str
    initial_entropy: str
    early_chi_pressure: str
    contraction_risk: str
    recommended_ansatz: str
    diagnosis: str
    suggestions: tuple[str, ...]


def complexity_preview(state: RunState) -> ComplexityPreview:
    geometry = state.model_geometry
    layout = state.ansatz_layout
    diagnostics = geometry_diagnostics(state)
    flattening = diagnostics.flattening
    mismatch = diagnostics.mismatch

    sites = _site_count(state)
    dimensions = geometry.dimensions if geometry is not None else ()
    ansatz = layout.ansatz if layout is not None else "unknown"
    long_range_edges = flattening.long_range_edges
    max_distance = max(
        (row.ansatz_distance or 0 for row in flattening.edge_stress),
        default=0,
    )
    high_stress_edges = len(flattening.high_stress_edges)

    return ComplexityPreview(
        sites=sites,
        geometry=geometry.name if geometry is not None else flattening.model_geometry,
        dimensions=dimensions,
        boundary=geometry.boundary if geometry is not None else None,
        ansatz=ansatz,
        interaction_range=_interaction_range(flattening.total_edges, long_range_edges, max_distance),
        expected_lightcone=_expected_lightcone(dimensions, long_range_edges, max_distance),
        initial_entropy=_initial_entropy(state),
        early_chi_pressure=_early_chi_pressure(flattening.total_edges, long_range_edges, high_stress_edges),
        contraction_risk=_contraction_risk(ansatz, dimensions, flattening.total_edges, long_range_edges, high_stress_edges),
        recommended_ansatz=_recommended_ansatz(ansatz, dimensions, long_range_edges, high_stress_edges),
        diagnosis=_diagnosis(ansatz, dimensions, long_range_edges, high_stress_edges),
        suggestions=_suggestions(ansatz, dimensions, long_range_edges, high_stress_edges, mismatch.suggestions),
    )


def render_preview(preview: ComplexityPreview, *, width: int = 100) -> str:
    lines = [
        "Model complexity preview",
        "------------------------",
        f"sites:              {_maybe_int(preview.sites)}",
        f"geometry:           {preview.geometry}",
        f"dimensions:         {_dimensions(preview.dimensions)}",
        f"boundary:           {preview.boundary or 'n/a'}",
        f"ansatz:             {preview.ansatz}",
        f"interaction range:  {preview.interaction_range}",
        f"expected lightcone: {preview.expected_lightcone}",
        f"initial entropy:    {preview.initial_entropy}",
        f"early chi pressure: {preview.early_chi_pressure}",
        f"contraction risk:   {preview.contraction_risk}",
        f"recommended ansatz: {preview.recommended_ansatz}",
        f"diagnosis:          {preview.diagnosis}",
    ]
    if preview.suggestions:
        lines.append("suggestions:")
        lines.extend(f"  - {suggestion}" for suggestion in preview.suggestions)
    return "\n".join(_fit_or_wrap(line, width) for line in lines)


def _site_count(state: RunState) -> int | None:
    if state.model_geometry is not None and state.model_geometry.sites is not None:
        return state.model_geometry.sites
    if state.ansatz_layout is not None and state.ansatz_layout.ordering:
        return len(state.ansatz_layout.ordering)
    sites: set[int] = set()
    for bond in state.ordered_bonds:
        sites.add(bond.site_left)
        sites.add(bond.site_right)
    return len(sites) if sites else None


def _interaction_range(total_edges: int, long_range_edges: int, max_distance: int) -> str:
    if total_edges == 0:
        return "unknown"
    if long_range_edges == 0:
        return "nearest-neighbor"
    if max_distance <= 3:
        return "finite-range"
    return "long-range"


def _expected_lightcone(dimensions: tuple[int, ...], long_range_edges: int, max_distance: int) -> str:
    if long_range_edges == 0 and len(dimensions) <= 1:
        return "linear"
    if max_distance >= 4:
        return "nonlocal / ordering-sensitive"
    if len(dimensions) >= 2:
        return "anisotropic across flattened geometry"
    if long_range_edges:
        return "broadened by nonlocal couplings"
    return "unknown"


def _initial_entropy(state: RunState) -> str:
    if not state.ordered_bonds:
        return "unknown before bond telemetry"
    max_entropy = max((bond.entropy for bond in state.ordered_bonds), default=0.0)
    if max_entropy < 0.1:
        return "low"
    if max_entropy < 2.0:
        return "moderate"
    return "high"


def _early_chi_pressure(total_edges: int, long_range_edges: int, high_stress_edges: int) -> str:
    if total_edges == 0:
        return "unknown"
    ratio = long_range_edges / total_edges
    if high_stress_edges or ratio >= 0.35:
        return "high"
    if long_range_edges:
        return "moderate"
    return "mild"


def _contraction_risk(
    ansatz: str,
    dimensions: tuple[int, ...],
    total_edges: int,
    long_range_edges: int,
    high_stress_edges: int,
) -> str:
    ratio = long_range_edges / total_edges if total_edges else 0.0
    ansatz_name = ansatz.upper()
    if ansatz_name in {"PEPS", "GENERIC", "GENERIC_TN"}:
        return "high"
    if high_stress_edges or ratio >= 0.35:
        return "high" if len(dimensions) >= 2 else "medium"
    if long_range_edges:
        return "medium"
    return "low"


def _recommended_ansatz(ansatz: str, dimensions: tuple[int, ...], long_range_edges: int, high_stress_edges: int) -> str:
    ansatz_name = ansatz.upper()
    if ansatz_name == "MPS" and (len(dimensions) >= 2 or high_stress_edges):
        return "MPS with better ordering / blocking, or PEPS-like / TTN"
    if ansatz_name == "MPS" and long_range_edges:
        return "MPS with reordered sites or blocked long-range pairs"
    if len(dimensions) <= 1 and long_range_edges == 0:
        return "MPS / TEBD"
    return ansatz if ansatz != "unknown" else "needs ansatz_layout telemetry"


def _diagnosis(ansatz: str, dimensions: tuple[int, ...], long_range_edges: int, high_stress_edges: int) -> str:
    if ansatz == "unknown":
        return "waiting for ansatz telemetry"
    if ansatz.upper() == "MPS" and high_stress_edges:
        return "MPS ordering is likely poor for this geometry"
    if ansatz.upper() == "MPS" and len(dimensions) >= 2 and long_range_edges:
        return "MPS is flattening higher-dimensional interactions"
    if long_range_edges:
        return "nonlocal interactions may dominate complexity growth"
    return "model and ansatz look aligned for an initial run"


def _suggestions(
    ansatz: str,
    dimensions: tuple[int, ...],
    long_range_edges: int,
    high_stress_edges: int,
    mismatch_suggestions: tuple[str, ...],
) -> tuple[str, ...]:
    suggestions = list(mismatch_suggestions)
    if ansatz.upper() == "MPS" and high_stress_edges:
        suggestions.append("preview alternate site orderings before increasing chi_max")
    if ansatz.upper() == "MPS" and len(dimensions) >= 2:
        suggestions.append("try blocking strongly coupled rows or rungs")
    if long_range_edges:
        suggestions.append("track truncation on crossed bonds early in the run")
    if not suggestions:
        suggestions.append("run a short low-chi pilot and compare max entropy growth")
    return tuple(dict.fromkeys(suggestions))


def _dimensions(dimensions: tuple[int, ...]) -> str:
    if not dimensions:
        return "n/a"
    return " x ".join(str(value) for value in dimensions)


def _maybe_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return str(value)


def _fit_or_wrap(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return "\n".join(textwrap.wrap(text, width=width, subsequent_indent="  "))
