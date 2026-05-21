"""Telemetry event parsing for TNView."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Literal


EventName = Literal[
    "run_started",
    "model_geometry",
    "ansatz_layout",
    "observable_updated",
    "bond_updated",
    "checkpoint",
    "tdvp_sweep",
]


@dataclass(frozen=True)
class RunStarted:
    run_id: str
    time: float
    name: str | None
    simulator: str | None
    algorithm: str | None
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelGeometryEvent:
    step: int
    time: float
    name: str
    sites: int | None
    dimensions: tuple[int, ...] = field(default_factory=tuple)
    boundary: str | None = None
    edges: tuple[dict[str, Any], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AnsatzLayoutEvent:
    step: int
    time: float
    ansatz: str
    ordering: tuple[int, ...] = field(default_factory=tuple)
    tensors: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ObservableUpdated:
    step: int
    time: float
    name: str
    value: float
    site: int | None = None
    bond: int | None = None
    error: float | None = None
    diagnostic_tags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BondUpdated:
    step: int
    time: float
    layer: str
    bond: int
    site_left: int
    site_right: int
    entropy_before: float
    entropy_after: float
    renyi2_before: float | None
    renyi2_after: float | None
    chi_before: int
    chi_after: int
    chi_max: int
    trunc_error: float
    discarded_weight: float | None
    walltime_ms: float | None
    schmidt_values: tuple[float, ...] = field(default_factory=tuple)
    diagnostic_tags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Checkpoint:
    step: int
    time: float
    max_entropy: float | None
    mean_entropy: float | None
    max_chi: int | None
    num_saturated_bonds: int | None
    total_trunc_error: float | None
    energy: float | None
    energy_drift: float | None
    norm: float | None
    complexity_status: str | None


@dataclass(frozen=True)
class TdvpSweep:
    step: int
    time: float
    direction: str
    start_site: int
    end_site: int
    max_residual: float | None
    max_entropy_delta: float | None
    max_trunc_error: float | None
    walltime_ms: float | None
    diagnostic_tags: tuple[str, ...] = field(default_factory=tuple)


TelemetryEvent = (
    RunStarted
    | ModelGeometryEvent
    | AnsatzLayoutEvent
    | ObservableUpdated
    | BondUpdated
    | Checkpoint
    | TdvpSweep
)


class EventParseError(ValueError):
    """Raised when a telemetry line cannot be parsed."""


def parse_jsonl_line(line: str, *, line_number: int | None = None) -> TelemetryEvent | None:
    """Parse one JSONL telemetry line.

    Blank lines are ignored. Unknown event kinds are rejected because silent drops
    make replay debugging harder.
    """

    stripped = line.strip()
    if not stripped:
        return None

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise EventParseError(_prefix(line_number, f"invalid JSON: {exc.msg}")) from exc

    if not isinstance(payload, dict):
        raise EventParseError(_prefix(line_number, "event must be a JSON object"))

    event_name = payload.get("event")
    if event_name == "run_started":
        return _run_started(payload, line_number)
    if event_name == "model_geometry":
        return _model_geometry(payload, line_number)
    if event_name == "ansatz_layout":
        return _ansatz_layout(payload, line_number)
    if event_name == "observable_updated":
        return _observable_updated(payload, line_number)
    if event_name == "bond_updated":
        return _bond_updated(payload, line_number)
    if event_name == "checkpoint":
        return _checkpoint(payload, line_number)
    if event_name == "tdvp_sweep":
        return _tdvp_sweep(payload, line_number)

    raise EventParseError(_prefix(line_number, f"unknown event {event_name!r}"))


def parse_jsonl(lines: list[str] | Any) -> list[TelemetryEvent]:
    events: list[TelemetryEvent] = []
    for line_number, line in enumerate(lines, start=1):
        event = parse_jsonl_line(line, line_number=line_number)
        if event is not None:
            events.append(event)
    return events


def _run_started(payload: dict[str, Any], line_number: int | None) -> RunStarted:
    parameters = payload.get("parameters", {})
    if parameters is None:
        parameters = {}
    if not isinstance(parameters, dict):
        raise EventParseError(_prefix(line_number, "parameters must be an object"))
    return RunStarted(
        run_id=_required_str(payload, "run_id", line_number),
        time=_required_float(payload, "time", line_number),
        name=_optional_str(payload, "name", line_number),
        simulator=_optional_str(payload, "simulator", line_number),
        algorithm=_optional_str(payload, "algorithm", line_number),
        parameters=parameters,
    )


def _model_geometry(payload: dict[str, Any], line_number: int | None) -> ModelGeometryEvent:
    return ModelGeometryEvent(
        step=_required_int(payload, "step", line_number),
        time=_required_float(payload, "time", line_number),
        name=_required_str(payload, "name", line_number),
        sites=_optional_int(payload, "sites", line_number),
        dimensions=_int_tuple(payload.get("dimensions", []), "dimensions", line_number),
        boundary=_optional_str(payload, "boundary", line_number),
        edges=_object_tuple(payload.get("edges", []), "edges", line_number),
    )


def _ansatz_layout(payload: dict[str, Any], line_number: int | None) -> AnsatzLayoutEvent:
    parameters = payload.get("parameters", {})
    if parameters is None:
        parameters = {}
    if not isinstance(parameters, dict):
        raise EventParseError(_prefix(line_number, "parameters must be an object"))
    return AnsatzLayoutEvent(
        step=_required_int(payload, "step", line_number),
        time=_required_float(payload, "time", line_number),
        ansatz=_required_str(payload, "ansatz", line_number),
        ordering=_int_tuple(payload.get("ordering", []), "ordering", line_number),
        tensors=_object_tuple(payload.get("tensors", []), "tensors", line_number),
        parameters=parameters,
    )


def _observable_updated(payload: dict[str, Any], line_number: int | None) -> ObservableUpdated:
    tags = payload.get("diagnostic_tags", [])
    if tags is None:
        tags = []
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise EventParseError(_prefix(line_number, "diagnostic_tags must be a string array"))
    return ObservableUpdated(
        step=_required_int(payload, "step", line_number),
        time=_required_float(payload, "time", line_number),
        name=_required_str(payload, "name", line_number),
        value=_required_float(payload, "value", line_number),
        site=_optional_int(payload, "site", line_number),
        bond=_optional_int(payload, "bond", line_number),
        error=_optional_float(payload, "error", line_number),
        diagnostic_tags=tuple(tags),
    )


def _bond_updated(payload: dict[str, Any], line_number: int | None) -> BondUpdated:
    tags = payload.get("diagnostic_tags", [])
    if tags is None:
        tags = []
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise EventParseError(_prefix(line_number, "diagnostic_tags must be a string array"))
    schmidt_values = payload.get("schmidt_values", [])
    if schmidt_values is None:
        schmidt_values = []
    if not isinstance(schmidt_values, list) or not all(_is_number(value) for value in schmidt_values):
        raise EventParseError(_prefix(line_number, "schmidt_values must be a numeric array"))

    return BondUpdated(
        step=_required_int(payload, "step", line_number),
        time=_required_float(payload, "time", line_number),
        layer=_required_str(payload, "layer", line_number),
        bond=_required_int(payload, "bond", line_number),
        site_left=_required_int(payload, "site_left", line_number),
        site_right=_required_int(payload, "site_right", line_number),
        entropy_before=_required_float(payload, "entropy_before", line_number),
        entropy_after=_required_float(payload, "entropy_after", line_number),
        renyi2_before=_optional_float(payload, "renyi2_before", line_number),
        renyi2_after=_optional_float(payload, "renyi2_after", line_number),
        chi_before=_required_int(payload, "chi_before", line_number),
        chi_after=_required_int(payload, "chi_after", line_number),
        chi_max=_required_int(payload, "chi_max", line_number),
        trunc_error=_required_float(payload, "trunc_error", line_number),
        discarded_weight=_optional_float(payload, "discarded_weight", line_number),
        walltime_ms=_optional_float(payload, "walltime_ms", line_number),
        schmidt_values=tuple(float(value) for value in schmidt_values),
        diagnostic_tags=tuple(tags),
    )


def _checkpoint(payload: dict[str, Any], line_number: int | None) -> Checkpoint:
    return Checkpoint(
        step=_required_int(payload, "step", line_number),
        time=_required_float(payload, "time", line_number),
        max_entropy=_optional_float(payload, "max_entropy", line_number),
        mean_entropy=_optional_float(payload, "mean_entropy", line_number),
        max_chi=_optional_int(payload, "max_chi", line_number),
        num_saturated_bonds=_optional_int(payload, "num_saturated_bonds", line_number),
        total_trunc_error=_optional_float(payload, "total_trunc_error", line_number),
        energy=_optional_float(payload, "energy", line_number),
        energy_drift=_optional_float(payload, "energy_drift", line_number),
        norm=_optional_float(payload, "norm", line_number),
        complexity_status=_optional_str(payload, "complexity_status", line_number),
    )


def _tdvp_sweep(payload: dict[str, Any], line_number: int | None) -> TdvpSweep:
    tags = payload.get("diagnostic_tags", [])
    if tags is None:
        tags = []
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise EventParseError(_prefix(line_number, "diagnostic_tags must be a string array"))

    return TdvpSweep(
        step=_required_int(payload, "step", line_number),
        time=_required_float(payload, "time", line_number),
        direction=_required_str(payload, "direction", line_number),
        start_site=_required_int(payload, "start_site", line_number),
        end_site=_required_int(payload, "end_site", line_number),
        max_residual=_optional_float(payload, "max_residual", line_number),
        max_entropy_delta=_optional_float(payload, "max_entropy_delta", line_number),
        max_trunc_error=_optional_float(payload, "max_trunc_error", line_number),
        walltime_ms=_optional_float(payload, "walltime_ms", line_number),
        diagnostic_tags=tuple(tags),
    )


def _required_int(payload: dict[str, Any], key: str, line_number: int | None) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise EventParseError(_prefix(line_number, f"{key} must be an integer"))
    return value


def _optional_int(payload: dict[str, Any], key: str, line_number: int | None) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise EventParseError(_prefix(line_number, f"{key} must be an integer"))
    return value


def _required_float(payload: dict[str, Any], key: str, line_number: int | None) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise EventParseError(_prefix(line_number, f"{key} must be numeric"))
    return float(value)


def _optional_float(payload: dict[str, Any], key: str, line_number: int | None) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise EventParseError(_prefix(line_number, f"{key} must be numeric"))
    return float(value)


def _required_str(payload: dict[str, Any], key: str, line_number: int | None) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise EventParseError(_prefix(line_number, f"{key} must be a string"))
    return value


def _optional_str(payload: dict[str, Any], key: str, line_number: int | None) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise EventParseError(_prefix(line_number, f"{key} must be a string"))
    return value


def _is_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int | float)


def _int_tuple(value: Any, key: str, line_number: int | None) -> tuple[int, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, int) and not isinstance(item, bool) for item in value):
        raise EventParseError(_prefix(line_number, f"{key} must be an integer array"))
    return tuple(value)


def _object_tuple(value: Any, key: str, line_number: int | None) -> tuple[dict[str, Any], ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise EventParseError(_prefix(line_number, f"{key} must be an object array"))
    return tuple(value)


def _prefix(line_number: int | None, message: str) -> str:
    if line_number is None:
        return message
    return f"line {line_number}: {message}"
