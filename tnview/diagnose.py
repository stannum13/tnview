"""Rule-based diagnostics for TNView run-log telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from statistics import median
from typing import Any

from tnview.terminal import render_severity


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    category: str = "general"
    evidence: dict[str, Any] = field(default_factory=dict)
    suggestions: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiagnosticThresholds:
    energy_epsilon: float = 1e-8
    truncation_floor: float = 1e-7
    runtime_factor: float = 2.0
    memory_factor: float = 1.25
    optimizer_loss_epsilon: float = 1e-6
    canonical_error: float = 1e-8
    entropy_growth_factor: float = 1.5


DIAGNOSTIC_PROFILES = {
    "default": DiagnosticThresholds(),
    "strict": DiagnosticThresholds(
        energy_epsilon=1e-7,
        truncation_floor=1e-8,
        runtime_factor=1.5,
        memory_factor=1.15,
        optimizer_loss_epsilon=1e-5,
        canonical_error=1e-9,
        entropy_growth_factor=1.25,
    ),
    "loose": DiagnosticThresholds(
        energy_epsilon=1e-10,
        truncation_floor=1e-6,
        runtime_factor=3.0,
        memory_factor=1.5,
        optimizer_loss_epsilon=1e-8,
        canonical_error=1e-7,
        entropy_growth_factor=2.0,
    ),
}


def diagnostic_thresholds_for_profile(profile: str) -> DiagnosticThresholds:
    """Return named diagnostic thresholds."""

    try:
        return DIAGNOSTIC_PROFILES[profile]
    except KeyError as exc:
        choices = ", ".join(sorted(DIAGNOSTIC_PROFILES))
        raise ValueError(f"unknown diagnostic profile {profile!r}; choose one of: {choices}") from exc


def diagnose_events(
    events: list[dict[str, Any]],
    *,
    thresholds: DiagnosticThresholds | None = None,
    suppress_codes: set[str] | frozenset[str] | tuple[str, ...] = (),
) -> list[Diagnostic]:
    limits = thresholds or DiagnosticThresholds()
    diagnostics: list[Diagnostic] = []
    diagnostics.extend(_energy_plateau(events, limits))
    diagnostics.extend(_chi_saturation(events))
    diagnostics.extend(_truncation_floor(events, limits))
    diagnostics.extend(_runtime_regression(events, limits))
    diagnostics.extend(_memory_growth(events, limits))
    diagnostics.extend(_optimizer_stagnation(events, limits))
    diagnostics.extend(_nonfinite_metrics(events))
    diagnostics.extend(_canonical_form_drift(events, limits))
    diagnostics.extend(_entropy_growth(events, limits))
    suppressed = set(suppress_codes)
    if suppressed:
        diagnostics = [diagnostic for diagnostic in diagnostics if diagnostic.code not in suppressed]
    return diagnostics


def render_diagnostics(diagnostics: list[Diagnostic], *, unicode: bool = True, color: bool = False) -> str:
    lines = ["TNView diagnostics"]
    if not diagnostics:
        lines.append("no warnings")
        return "\n".join(lines)

    for diagnostic in diagnostics:
        evidence = _evidence_text(diagnostic.evidence)
        suffix = f" ({evidence})" if evidence else ""
        severity = render_severity(diagnostic.severity, unicode=unicode, color=color).upper()
        lines.append(f"{severity} {diagnostic.code} [{diagnostic.category}]: {diagnostic.message}{suffix}")
        if diagnostic.suggestions:
            lines.append("  Try:")
            lines.extend(f"    - {suggestion}" for suggestion in diagnostic.suggestions)
    return "\n".join(lines)


def _energy_plateau(events: list[dict[str, Any]], thresholds: DiagnosticThresholds) -> list[Diagnostic]:
    values = [_number(event.get("delta_energy")) for event in _progress_events(events)]
    recent = [value for value in values if value is not None][-4:]
    if len(recent) == 4 and all(abs(value) <= thresholds.energy_epsilon for value in recent):
        return [
            Diagnostic(
                code="energy_plateau",
                severity="warn",
                category="convergence",
                message="Energy appears plateaued; check truncation error and chi saturation.",
                evidence={"recent_delta_energy": recent},
                suggestions=(
                    "inspect chi_saturation and truncation_floor diagnostics",
                    "compare against a larger chi_max run",
                    "stop early if observables are stable",
                ),
            )
        ]
    return []


def _chi_saturation(events: list[dict[str, Any]]) -> list[Diagnostic]:
    saturated = []
    for event in _progress_events(events):
        max_chi = _number(event.get("max_chi"))
        chi_max = _number(event.get("chi_max_configured"))
        if max_chi is None or chi_max is None:
            continue
        saturated.append(max_chi >= chi_max)
    if len(saturated) >= 3 and all(saturated[-3:]):
        latest = _latest_with(events, "max_chi")
        return [
            Diagnostic(
                code="chi_saturation",
                severity="warn",
                category="capacity",
                message="Bond dimension has saturated for 3 consecutive progress events.",
                evidence={"max_chi": latest.get("max_chi"), "chi_max_configured": latest.get("chi_max_configured")},
                suggestions=(
                    "increase chi_max for a short comparison run",
                    "check whether the saturated bonds align with the physical cut",
                    "try a different site ordering before only increasing chi",
                ),
            )
        ]
    return []


def _truncation_floor(events: list[dict[str, Any]], thresholds: DiagnosticThresholds) -> list[Diagnostic]:
    for event in reversed(_progress_events(events)):
        trunc = _number(event.get("max_trunc_err"))
        delta = _number(event.get("delta_energy"))
        if trunc is None or delta is None:
            continue
        if trunc > thresholds.truncation_floor and abs(delta) <= thresholds.energy_epsilon:
            return [
                Diagnostic(
                    code="truncation_floor",
                    severity="warn",
                    category="accuracy",
                    message="Truncation error remains high while energy improvement is small.",
                    evidence={"max_trunc_err": trunc, "delta_energy": delta},
                    suggestions=(
                        "increase chi_max or reduce truncation tolerance",
                        "compare observables against a higher-accuracy run",
                        "inspect the bonds with the largest truncation error",
                    ),
                )
            ]
        return []
    return []


def _runtime_regression(events: list[dict[str, Any]], thresholds: DiagnosticThresholds) -> list[Diagnostic]:
    values = [_runtime(event) for event in _progress_events(events)]
    runtimes = [value for value in values if value is not None]
    if len(runtimes) < 6:
        return []
    baseline = median(runtimes[-6:-1])
    latest = runtimes[-1]
    if baseline > 0 and latest >= thresholds.runtime_factor * baseline:
        return [
            Diagnostic(
                code="runtime_regression",
                severity="warn",
                category="performance",
                message="Runtime increased sharply compared with recent progress events.",
                evidence={"latest_runtime": latest, "recent_median": baseline},
                suggestions=(
                    "check whether chi or tensor dimensions jumped at the same step",
                    "inspect memory pressure and backend thread settings",
                    "compare wall time against a lower-chi pilot run",
                ),
            )
        ]
    return []


def _memory_growth(events: list[dict[str, Any]], thresholds: DiagnosticThresholds) -> list[Diagnostic]:
    rss_values = [_number(event.get("rss_mb")) for event in _progress_events(events)]
    recent = [value for value in rss_values if value is not None][-5:]
    if len(recent) == 5 and all(left <= right for left, right in zip(recent, recent[1:])) and recent[-1] >= thresholds.memory_factor * recent[0]:
        return [
            Diagnostic(
                code="memory_growth",
                severity="warn",
                category="resource",
                message="RSS memory is growing steadily across recent progress events.",
                evidence={"rss_mb_start": recent[0], "rss_mb_latest": recent[-1]},
                suggestions=(
                    "confirm tensors or environments are not being retained accidentally",
                    "checkpoint and restart the run if memory pressure is near the job limit",
                    "compare RSS growth across parameter variants",
                ),
            )
        ]
    return []


def _optimizer_stagnation(events: list[dict[str, Any]], thresholds: DiagnosticThresholds) -> list[Diagnostic]:
    losses = [_number(event.get("loss")) for event in events if event.get("event") == "optimizer_step"]
    recent = [value for value in losses if value is not None][-10:]
    if len(recent) == 10 and abs(recent[0] - recent[-1]) < thresholds.optimizer_loss_epsilon:
        return [
            Diagnostic(
                code="optimizer_stagnation",
                severity="warn",
                category="optimization",
                message="Optimizer loss has stagnated over the last 10 steps.",
                evidence={"loss_start": recent[0], "loss_latest": recent[-1]},
                suggestions=(
                    "try a different optimizer or learning-rate schedule",
                    "restart from the best checkpoint with tighter tolerances",
                    "check gradients and loss scaling if available",
                ),
            )
        ]
    return []


def _nonfinite_metrics(events: list[dict[str, Any]]) -> list[Diagnostic]:
    keys = [
        "energy",
        "delta_energy",
        "loss",
        "max_trunc_err",
        "entropy_max",
        "entropy_mean",
        "wall_s",
        "step_wall_s",
        "rss_mb",
        "canonical_error",
    ]
    for event in events:
        for key in keys:
            value = event.get(key)
            if isinstance(value, float) and not isfinite(value):
                return [
                    Diagnostic(
                        code="nonfinite_metric",
                        severity="error",
                        category="numerical",
                        message="A run metric became NaN or infinite.",
                        evidence={"event": event.get("event"), "field": key, "value": value},
                        suggestions=(
                            "stop the run and inspect the first non-finite event",
                            "check normalization, optimizer step size, and input tensors",
                            "restart from the last finite checkpoint",
                        ),
                    )
                ]
    return []


def _canonical_form_drift(events: list[dict[str, Any]], thresholds: DiagnosticThresholds) -> list[Diagnostic]:
    for event in reversed(_progress_events(events)):
        error = _number(event.get("canonical_error"))
        if error is None:
            error = _number(event.get("norm_err"))
        if error is None:
            continue
        if error > thresholds.canonical_error:
            return [
                Diagnostic(
                    code="canonical_form_drift",
                    severity="warn",
                    category="numerical",
                    message="Canonical-form or norm error is above the expected tolerance.",
                    evidence={"canonical_error": error},
                    suggestions=(
                        "recanonicalize or renormalize before continuing",
                        "tighten canonicalization tolerances",
                        "inspect whether truncation or optimizer steps destabilized the state",
                    ),
                )
            ]
        return []
    return []


def _entropy_growth(events: list[dict[str, Any]], thresholds: DiagnosticThresholds) -> list[Diagnostic]:
    values = [_number(event.get("entropy_max")) for event in _progress_events(events)]
    recent = [value for value in values if value is not None][-5:]
    if len(recent) == 5 and recent[0] > 0 and all(left <= right for left, right in zip(recent, recent[1:])) and recent[-1] >= thresholds.entropy_growth_factor * recent[0]:
        return [
            Diagnostic(
                code="entropy_growth",
                severity="warn",
                category="dynamics",
                message="Entanglement entropy is growing steadily across recent progress events.",
                evidence={"entropy_start": recent[0], "entropy_latest": recent[-1]},
                suggestions=(
                    "watch central bonds for upcoming chi saturation",
                    "increase chi_max only after checking geometry/order effects",
                    "run a short higher-chi pilot to estimate required capacity",
                ),
            )
        ]
    return []


def _progress_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        event
        for event in events
        if event.get("event") in {"step_end", "sweep_end", "optimizer_step"} or _is_snapshot_progress_event(event)
    ]


def _is_snapshot_progress_event(event: dict[str, Any]) -> bool:
    if event.get("event") != "diagnostic":
        return False
    if event.get("algorithm") != "mps_snapshot":
        return False
    return any(
        key in event
        for key in (
            "energy",
            "delta_energy",
            "max_chi",
            "chi_max_configured",
            "max_trunc_err",
            "entropy_max",
            "entropy_mean",
        )
    )


def _latest_with(events: list[dict[str, Any]], key: str) -> dict[str, Any]:
    for event in reversed(events):
        if key in event:
            return event
    return {}


def _runtime(event: dict[str, Any]) -> float | None:
    value = _number(event.get("step_wall_s"))
    if value is not None:
        return value
    return _number(event.get("wall_s"))


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _evidence_text(evidence: dict[str, Any]) -> str:
    return ", ".join(f"{key}={value}" for key, value in evidence.items())
