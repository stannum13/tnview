"""Rule-based diagnostics for TNView run-log telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import Any


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)


def diagnose_events(events: list[dict[str, Any]]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    diagnostics.extend(_energy_plateau(events))
    diagnostics.extend(_chi_saturation(events))
    diagnostics.extend(_truncation_floor(events))
    diagnostics.extend(_runtime_regression(events))
    diagnostics.extend(_memory_growth(events))
    diagnostics.extend(_optimizer_stagnation(events))
    return diagnostics


def render_diagnostics(diagnostics: list[Diagnostic]) -> str:
    lines = ["TNView diagnostics"]
    if not diagnostics:
        lines.append("no warnings")
        return "\n".join(lines)

    for diagnostic in diagnostics:
        evidence = _evidence_text(diagnostic.evidence)
        suffix = f" ({evidence})" if evidence else ""
        lines.append(f"{diagnostic.severity.upper()} {diagnostic.code}: {diagnostic.message}{suffix}")
    return "\n".join(lines)


def _energy_plateau(events: list[dict[str, Any]]) -> list[Diagnostic]:
    values = [_number(event.get("delta_energy")) for event in _progress_events(events)]
    recent = [value for value in values if value is not None][-4:]
    if len(recent) == 4 and all(abs(value) <= 1e-8 for value in recent):
        return [
            Diagnostic(
                code="energy_plateau",
                severity="warn",
                message="Energy appears plateaued; check truncation error and chi saturation.",
                evidence={"recent_delta_energy": recent},
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
                message="Bond dimension has saturated for 3 consecutive progress events.",
                evidence={"max_chi": latest.get("max_chi"), "chi_max_configured": latest.get("chi_max_configured")},
            )
        ]
    return []


def _truncation_floor(events: list[dict[str, Any]]) -> list[Diagnostic]:
    for event in reversed(_progress_events(events)):
        trunc = _number(event.get("max_trunc_err"))
        delta = _number(event.get("delta_energy"))
        if trunc is None or delta is None:
            continue
        if trunc > 1e-7 and abs(delta) <= 1e-8:
            return [
                Diagnostic(
                    code="truncation_floor",
                    severity="warn",
                    message="Truncation error remains high while energy improvement is small.",
                    evidence={"max_trunc_err": trunc, "delta_energy": delta},
                )
            ]
        return []
    return []


def _runtime_regression(events: list[dict[str, Any]]) -> list[Diagnostic]:
    values = [_runtime(event) for event in _progress_events(events)]
    runtimes = [value for value in values if value is not None]
    if len(runtimes) < 6:
        return []
    baseline = median(runtimes[-6:-1])
    latest = runtimes[-1]
    if baseline > 0 and latest >= 2.0 * baseline:
        return [
            Diagnostic(
                code="runtime_regression",
                severity="warn",
                message="Runtime increased sharply compared with recent progress events.",
                evidence={"latest_runtime": latest, "recent_median": baseline},
            )
        ]
    return []


def _memory_growth(events: list[dict[str, Any]]) -> list[Diagnostic]:
    rss_values = [_number(event.get("rss_mb")) for event in _progress_events(events)]
    recent = [value for value in rss_values if value is not None][-5:]
    if len(recent) == 5 and all(left <= right for left, right in zip(recent, recent[1:])) and recent[-1] >= 1.25 * recent[0]:
        return [
            Diagnostic(
                code="memory_growth",
                severity="warn",
                message="RSS memory is growing steadily across recent progress events.",
                evidence={"rss_mb_start": recent[0], "rss_mb_latest": recent[-1]},
            )
        ]
    return []


def _optimizer_stagnation(events: list[dict[str, Any]]) -> list[Diagnostic]:
    losses = [_number(event.get("loss")) for event in events if event.get("event") == "optimizer_step"]
    recent = [value for value in losses if value is not None][-10:]
    if len(recent) == 10 and abs(recent[0] - recent[-1]) < 1e-6:
        return [
            Diagnostic(
                code="optimizer_stagnation",
                severity="warn",
                message="Optimizer loss has stagnated over the last 10 steps.",
                evidence={"loss_start": recent[0], "loss_latest": recent[-1]},
            )
        ]
    return []


def _progress_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        event
        for event in events
        if event.get("event") in {"step_end", "sweep_end", "optimizer_step"}
    ]


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
