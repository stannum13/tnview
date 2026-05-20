"""Energy and norm drift diagnostics derived from checkpoints."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

from tnview.events import Checkpoint
from tnview.state import RunState


@dataclass(frozen=True)
class DriftPoint:
    step: int
    time: float
    energy: float | None
    energy_drift: float | None
    norm: float | None
    norm_drift: float | None


@dataclass(frozen=True)
class DriftMetric:
    name: str
    latest: float | None
    previous: float | None
    delta: float | None
    slope_per_time: float | None
    trend: str
    severity: str


@dataclass(frozen=True)
class DriftDiagnostics:
    points: tuple[DriftPoint, ...]
    energy: DriftMetric
    norm: DriftMetric
    risk: str
    diagnosis: str
    recommendation: str


def drift_diagnostics(
    state: RunState,
    *,
    energy_watch: float = 1e-7,
    energy_critical: float = 1e-5,
    norm_watch: float = 1e-8,
    norm_critical: float = 1e-6,
) -> DriftDiagnostics:
    """Summarize conservation drift from RunState checkpoints.

    Energy drift uses the checkpoint-provided absolute drift when available and
    otherwise falls back to absolute deviation from the first checkpoint energy.
    Norm drift is reported as ``abs(norm - 1)``.
    """

    points = _drift_points(state.checkpoints)
    energy = _metric(
        "energy",
        [(point.time, point.energy_drift) for point in points],
        watch=energy_watch,
        critical=energy_critical,
    )
    norm = _metric(
        "norm",
        [(point.time, point.norm_drift) for point in points],
        watch=norm_watch,
        critical=norm_critical,
    )
    risk = _risk(energy.severity, norm.severity)
    diagnosis = _diagnosis(energy, norm, risk)
    return DriftDiagnostics(
        points=tuple(points),
        energy=energy,
        norm=norm,
        risk=risk,
        diagnosis=diagnosis,
        recommendation=_recommendation(risk, energy, norm),
    )


def _drift_points(checkpoints: list[Checkpoint]) -> list[DriftPoint]:
    reference_energy = _first_finite(checkpoint.energy for checkpoint in checkpoints)
    points = []
    for checkpoint in checkpoints:
        energy_drift = _energy_drift(checkpoint, reference_energy)
        norm_drift = _abs_if_finite(checkpoint.norm - 1.0) if checkpoint.norm is not None else None
        points.append(
            DriftPoint(
                step=checkpoint.step,
                time=checkpoint.time,
                energy=checkpoint.energy if _is_finite(checkpoint.energy) else None,
                energy_drift=energy_drift,
                norm=checkpoint.norm if _is_finite(checkpoint.norm) else None,
                norm_drift=norm_drift,
            )
        )
    return points


def _energy_drift(checkpoint: Checkpoint, reference_energy: float | None) -> float | None:
    if _is_finite(checkpoint.energy_drift):
        return abs(checkpoint.energy_drift)
    if reference_energy is None or not _is_finite(checkpoint.energy):
        return None
    return abs(checkpoint.energy - reference_energy)


def _metric(
    name: str,
    samples: list[tuple[float, float | None]],
    *,
    watch: float,
    critical: float,
) -> DriftMetric:
    usable = [(time, value) for time, value in samples if _is_finite(value)]
    if not usable:
        return DriftMetric(
            name=name,
            latest=None,
            previous=None,
            delta=None,
            slope_per_time=None,
            trend="unknown",
            severity="unknown",
        )

    latest_time, latest = usable[-1]
    previous = usable[-2][1] if len(usable) >= 2 else None
    delta = latest - previous if previous is not None else None
    slope = None
    if len(usable) >= 2:
        previous_time = usable[-2][0]
        dt = latest_time - previous_time
        if dt > 0:
            slope = delta / dt if delta is not None else None

    return DriftMetric(
        name=name,
        latest=latest,
        previous=previous,
        delta=delta,
        slope_per_time=slope,
        trend=_trend(usable, critical=critical),
        severity=_severity(latest, watch=watch, critical=critical),
    )


def _trend(samples: list[tuple[float, float]], *, critical: float) -> str:
    if len(samples) < 2:
        return "unknown"

    previous = samples[-2][1]
    current = samples[-1][1]
    tolerance = max(critical * 0.01, abs(previous) * 0.05)
    delta = current - previous
    if abs(delta) <= tolerance:
        return "stable"
    if delta < 0:
        return "recovering"
    if previous > 0 and current >= critical and current / previous >= 10:
        return "rising sharply"
    if previous == 0 and current >= critical:
        return "rising sharply"
    return "rising"


def _severity(value: float, *, watch: float, critical: float) -> str:
    if value >= critical:
        return "critical"
    if value >= watch:
        return "watch"
    return "ok"


def _risk(energy_severity: str, norm_severity: str) -> str:
    severities = {energy_severity, norm_severity}
    if "critical" in severities:
        return "high"
    if "watch" in severities:
        return "medium"
    if severities == {"unknown"}:
        return "unknown"
    return "low"


def _diagnosis(energy: DriftMetric, norm: DriftMetric, risk: str) -> str:
    if risk == "unknown":
        return "waiting for conservation telemetry"
    if energy.severity == "critical" and norm.severity == "critical":
        return "energy and norm conservation are breaking down"
    if energy.severity == "critical":
        return "energy conservation drift is too large"
    if norm.severity == "critical":
        return "state norm drift is too large"
    if energy.trend == "rising sharply" or norm.trend == "rising sharply":
        return "conservation drift is accelerating"
    if risk == "medium":
        return "conservation drift is visible but below critical threshold"
    return "energy and norm conservation look controlled"


def _recommendation(risk: str, energy: DriftMetric, norm: DriftMetric) -> str:
    if risk == "unknown":
        return "emit checkpoint energy and norm fields to enable drift diagnostics"
    if risk == "high":
        return "reduce time step or compare against a stricter truncation replay"
    if energy.trend == "rising" or norm.trend == "rising":
        return "keep monitoring drift before extending target time"
    return "continue; conservation drift is within configured tolerances"


def _first_finite(values: Iterable[float | int | None]) -> float | None:
    for value in values:
        if _is_finite(value):
            return float(value)
    return None


def _abs_if_finite(value: float) -> float | None:
    if not isfinite(value):
        return None
    return abs(value)


def _is_finite(value: float | int | None) -> bool:
    return value is not None and isfinite(value)
