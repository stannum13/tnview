"""Comparison rendering for multiple TNView replay files."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from dataclasses import asdict
from io import StringIO
from pathlib import Path
from typing import Any

from tnview.diagnose import diagnose_events
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


@dataclass(frozen=True)
class RunLogSummary:
    name: str
    run_id: str | None
    library: str | None
    algorithm: str | None
    event_count: int
    latest_event: str | None
    sweep: int | None
    step: int | None
    energy: float | None
    delta_energy: float | None
    loss: float | None
    max_chi: int | None
    entropy_max: float | None
    max_trunc_err: float | None
    wall_s: float | None
    rss_mb: float | None
    diagnostics: tuple[str, ...]


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


def summarize_run_log(name: str, records: list[dict[str, Any]]) -> RunLogSummary:
    state: dict[str, Any] = {}
    for record in records:
        for key, value in record.items():
            if key in {"schema_version", "timestamp", "time"}:
                continue
            if value is not None:
                state[key] = value
    diagnostics = tuple(diagnostic.code for diagnostic in diagnose_events(records))
    return RunLogSummary(
        name=Path(name).name,
        run_id=_string(state.get("run_id")),
        library=_string(state.get("library")),
        algorithm=_string(state.get("algorithm")),
        event_count=len(records),
        latest_event=_string(records[-1].get("event")) if records else None,
        sweep=_int(state.get("sweep")),
        step=_int(state.get("step")),
        energy=_number(state.get("energy")),
        delta_energy=_number(state.get("delta_energy")),
        loss=_number(state.get("loss")),
        max_chi=_int(state.get("max_chi")),
        entropy_max=_number(state.get("entropy_max")),
        max_trunc_err=_number(state.get("max_trunc_err")),
        wall_s=_number(state.get("wall_s")),
        rss_mb=_number(state.get("rss_mb")),
        diagnostics=diagnostics,
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
    lines = ["Replay comparison", _fit(header, width), _fit(divider, width)]
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


def render_run_log_comparison(summaries: list[RunLogSummary], *, width: int = 160) -> str:
    columns = [
        ("run", 22),
        ("id", 12),
        ("lib", 8),
        ("alg", 12),
        ("sweep", 6),
        ("step", 6),
        ("energy", 11),
        ("dE", 10),
        ("loss", 10),
        ("chi", 6),
        ("trunc", 10),
        ("rss", 8),
        ("diagnostics", 24),
    ]
    header = "  ".join(label.ljust(size) for label, size in columns)
    divider = "  ".join("-" * size for _, size in columns)
    lines = ["Run-log comparison", _fit(header, width), _fit(divider, width)]
    for summary in summaries:
        row = [
            _clip(summary.name, 22).ljust(22),
            _clip(summary.run_id or "n/a", 12).ljust(12),
            _clip(summary.library or "n/a", 8).ljust(8),
            _clip(summary.algorithm or "n/a", 12).ljust(12),
            _maybe_int(summary.sweep).ljust(6),
            _maybe_int(summary.step).ljust(6),
            _maybe_float(summary.energy).ljust(11),
            _maybe_float(summary.delta_energy).ljust(10),
            _maybe_float(summary.loss).ljust(10),
            _maybe_int(summary.max_chi).ljust(6),
            _maybe_float(summary.max_trunc_err).ljust(10),
            _maybe_float(summary.rss_mb).ljust(8),
            _clip(",".join(summary.diagnostics) or "none", 24).ljust(24),
        ]
        lines.append(_fit("  ".join(row), width))
    return "\n".join(lines)


def sort_summaries(summaries: list[RunSummary], key: str) -> list[RunSummary]:
    if key == "name":
        return sorted(summaries, key=lambda summary: summary.name)
    if key == "risk":
        return sorted(summaries, key=lambda summary: _risk_rank(summary), reverse=True)
    if key == "max-entropy":
        return sorted(summaries, key=lambda summary: summary.max_entropy, reverse=True)
    if key == "trunc":
        return sorted(summaries, key=lambda summary: summary.total_trunc_error, reverse=True)
    if key == "chi":
        return sorted(summaries, key=lambda summary: summary.max_chi, reverse=True)
    return summaries


def sort_run_log_summaries(
    summaries: list[RunLogSummary],
    key: str,
    *,
    metric: str | None = None,
) -> list[RunLogSummary]:
    if metric is not None:
        return sorted(summaries, key=lambda summary: _metric_value(summary, metric), reverse=True)
    if key == "name":
        return sorted(summaries, key=lambda summary: summary.name)
    if key == "risk":
        return sorted(summaries, key=lambda summary: (len(summary.diagnostics), summary.max_trunc_err or 0.0), reverse=True)
    if key == "max-entropy":
        return sorted(summaries, key=lambda summary: summary.entropy_max or 0.0, reverse=True)
    if key == "trunc":
        return sorted(summaries, key=lambda summary: summary.max_trunc_err or 0.0, reverse=True)
    if key == "chi":
        return sorted(summaries, key=lambda summary: summary.max_chi or 0, reverse=True)
    return summaries


def render_comparison_csv(summaries: list[RunSummary]) -> str:
    handle = StringIO()
    writer = csv.writer(handle)
    writer.writerow(
        [
            "model",
            "step",
            "time",
            "max_entropy",
            "max_chi",
            "saturated_bonds",
            "total_trunc_error",
            "bottleneck_bond",
            "drift_risk",
            "geometry_diagnosis",
            "diagnosis",
        ]
    )
    for summary in summaries:
        writer.writerow(
            [
                summary.name,
                summary.step,
                summary.time,
                summary.max_entropy,
                summary.max_chi,
                summary.saturated_bonds,
                summary.total_trunc_error,
                summary.bottleneck_bond,
                summary.drift_risk,
                summary.geometry_diagnosis,
                summary.status,
            ]
        )
    return handle.getvalue().rstrip("\r\n")


def comparison_payload(summaries: list[RunSummary]) -> dict[str, Any]:
    return {
        "kind": "replay",
        "runs": [asdict(summary) for summary in summaries],
    }


def run_log_comparison_payload(summaries: list[RunLogSummary]) -> dict[str, Any]:
    payload = {
        "kind": "run-log",
        "runs": [],
    }
    for summary in summaries:
        row = asdict(summary)
        row["diagnostics"] = list(summary.diagnostics)
        payload["runs"].append(row)
    return payload


def render_run_log_comparison_csv(summaries: list[RunLogSummary]) -> str:
    handle = StringIO()
    writer = csv.writer(handle)
    writer.writerow(
        [
            "run",
            "run_id",
            "library",
            "algorithm",
            "event_count",
            "latest_event",
            "sweep",
            "step",
            "energy",
            "delta_energy",
            "loss",
            "max_chi",
            "entropy_max",
            "max_trunc_err",
            "wall_s",
            "rss_mb",
            "diagnostics",
        ]
    )
    for summary in summaries:
        writer.writerow(
            [
                summary.name,
                summary.run_id,
                summary.library,
                summary.algorithm,
                summary.event_count,
                summary.latest_event,
                summary.sweep,
                summary.step,
                summary.energy,
                summary.delta_energy,
                summary.loss,
                summary.max_chi,
                summary.entropy_max,
                summary.max_trunc_err,
                summary.wall_s,
                summary.rss_mb,
                ";".join(summary.diagnostics),
            ]
        )
    return handle.getvalue().rstrip("\r\n")


def _risk_rank(summary: RunSummary) -> tuple[int, int, int]:
    run_risk = 2 if "limited" in summary.status else 1 if "pressure" in summary.status else 0
    drift_risk = {"unknown": 0, "low": 0, "medium": 1, "high": 2}.get(summary.drift_risk, 0)
    geometry_risk = 2 if "mismatch" in summary.geometry_diagnosis else 0
    return (max(run_risk, drift_risk, geometry_risk), summary.saturated_bonds, summary.max_chi)


def _metric_value(summary: RunLogSummary, metric: str) -> float:
    values = {
        "energy": summary.energy,
        "delta-energy": abs(summary.delta_energy) if summary.delta_energy is not None else None,
        "loss": summary.loss,
        "trunc": summary.max_trunc_err,
        "chi": summary.max_chi,
        "entropy": summary.entropy_max,
        "rss": summary.rss_mb,
        "wall": summary.wall_s,
    }
    return float(values.get(metric) or 0.0)


def _string(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


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
