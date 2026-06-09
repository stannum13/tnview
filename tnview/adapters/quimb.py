"""Adapters for quimb-style matrix product states.

The adapter uses duck typing so TNView does not require quimb at install time.
It looks for the MPS attributes and methods quimb exposes, including ``L``,
``bond_size(i, j)``, and ``singular_values(i)``.
"""

from __future__ import annotations

import json
from math import log
from typing import Any

from tnview.events import parse_jsonl
from tnview.render import RenderOptions, render_run
from tnview.state import reduce_events


def mps_to_events(
    mps: Any,
    *,
    run_id: str = "quimb-mps",
    name: str | None = None,
    step: int = 0,
    time: float = 0.0,
    chi_max: int | None = None,
) -> list[dict[str, Any]]:
    """Convert a quimb-style MPS object into TNView telemetry events."""

    sites = _site_count(mps)
    chis = [_bond_size(mps, bond) for bond in range(max(0, sites - 1))]
    max_chi = max(chis, default=1)
    limit = chi_max or max_chi
    entropies = [_bond_entropy(mps, bond) for bond in range(max(0, sites - 1))]

    events: list[dict[str, Any]] = [
        {
            "event": "run_started",
            "run_id": run_id,
            "time": time,
            "name": name or _object_name(mps),
            "simulator": "quimb",
            "algorithm": "object_inspection",
            "parameters": {"source": type(mps).__name__},
        },
        {
            "event": "model_geometry",
            "step": step,
            "time": time,
            "name": "quimb MPS chain",
            "sites": sites,
            "dimensions": [sites],
            "boundary": "open",
            "edges": [{"source": site, "target": site + 1} for site in range(max(0, sites - 1))],
        },
        {
            "event": "ansatz_layout",
            "step": step,
            "time": time,
            "ansatz": "MPS",
            "ordering": list(range(sites)),
            "tensors": _tensor_metadata(mps, sites),
            "parameters": {"adapter": "quimb"},
        },
    ]

    for bond, (chi, entropy) in enumerate(zip(chis, entropies)):
        events.append(
            {
                "event": "bond_updated",
                "step": step,
                "time": time,
                "layer": "inspect",
                "bond": bond,
                "site_left": bond,
                "site_right": bond + 1,
                "entropy_before": entropy,
                "entropy_after": entropy,
                "renyi2_before": None,
                "renyi2_after": None,
                "chi_before": chi,
                "chi_after": chi,
                "chi_max": limit,
                "trunc_error": 0.0,
                "discarded_weight": None,
                "walltime_ms": None,
                "schmidt_values": list(_singular_values(mps, bond)),
                "diagnostic_tags": ["chi_saturated"] if chi >= limit else [],
            }
        )

    events.append(
        {
            "event": "checkpoint",
            "step": step,
            "time": time,
            "max_entropy": max(entropies, default=0.0),
            "mean_entropy": sum(entropies) / len(entropies) if entropies else 0.0,
            "max_chi": max_chi,
            "num_saturated_bonds": sum(1 for chi in chis if chi >= limit),
            "total_trunc_error": 0.0,
            "energy": None,
            "energy_drift": None,
            "norm": None,
            "complexity_status": "object_inspection",
        }
    )
    return events


def mps_to_jsonl(mps: Any, **kwargs: Any) -> str:
    return "\n".join(json.dumps(event, separators=(",", ":")) for event in mps_to_events(mps, **kwargs)) + "\n"


def view_mps(mps: Any, *, width: int | None = None, unicode: bool = True, **kwargs: Any) -> str:
    lines = mps_to_jsonl(mps, **kwargs).splitlines()
    state = reduce_events(parse_jsonl(lines))
    return render_run(state, RenderOptions(width=width, unicode=unicode))


def _site_count(mps: Any) -> int:
    value = getattr(mps, "L", None)
    if callable(value):
        value = value()
    if isinstance(value, int):
        return value
    sites = getattr(mps, "sites", None)
    if sites is not None:
        return len(tuple(sites))
    tensors = getattr(mps, "tensors", None)
    if tensors is not None:
        return len(tuple(tensors))
    raise TypeError("object does not look like a quimb MatrixProductState: missing L/sites/tensors")


def _bond_size(mps: Any, bond: int) -> int:
    bond_size = getattr(mps, "bond_size", None)
    if callable(bond_size):
        return int(bond_size(bond, bond + 1))
    bond_sizes = getattr(mps, "bond_sizes", None)
    if callable(bond_sizes):
        sizes = list(bond_sizes())
        return int(sizes[bond])
    return 1


def _bond_entropy(mps: Any, bond: int) -> float:
    entropy = getattr(mps, "entropy", None)
    if callable(entropy):
        try:
            return float(entropy(bond))
        except TypeError:
            return float(entropy(bond, bond + 1))

    values = _singular_values(mps, bond)
    if not values:
        return 0.0
    weights = [value * value for value in values]
    total = sum(weights)
    if total <= 0:
        return 0.0
    return -sum((weight / total) * log(weight / total) for weight in weights if weight > 0)


def _singular_values(mps: Any, bond: int) -> tuple[float, ...]:
    singular_values = getattr(mps, "singular_values", None)
    if callable(singular_values):
        try:
            return tuple(float(value) for value in singular_values(bond))
        except TypeError:
            return tuple(float(value) for value in singular_values(bond, bond + 1))
    return ()


def _tensor_metadata(mps: Any, sites: int) -> list[dict[str, Any]]:
    tensors = getattr(mps, "tensors", None)
    if tensors is None:
        return [{"name": f"A{site}", "site": site} for site in range(sites)]
    metadata = []
    for site, tensor in enumerate(tuple(tensors)[:sites]):
        shape = getattr(tensor, "shape", None)
        if shape is None and hasattr(tensor, "data"):
            shape = getattr(tensor.data, "shape", None)
        row: dict[str, Any] = {"name": f"A{site}", "site": site}
        if shape is not None:
            row["shape"] = " x ".join(str(dim) for dim in shape)
        metadata.append(row)
    return metadata


def _object_name(mps: Any) -> str:
    name = getattr(mps, "name", None)
    if isinstance(name, str):
        return name
    return type(mps).__name__
