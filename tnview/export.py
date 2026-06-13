"""Replay export helpers for parsed TNView telemetry."""

from __future__ import annotations

import csv
from dataclasses import fields, is_dataclass
from io import StringIO
import json
import re
from typing import Any, Iterable

from tnview.events import (
    AnsatzLayoutEvent,
    BondUpdated,
    Checkpoint,
    ContractionPathEvent,
    ModelGeometryEvent,
    ObservableUpdated,
    RunStarted,
    TdvpSweep,
    TelemetryEvent,
)
from tnview.state import reduce_events

_EVENT_NAMES = {
    RunStarted: "run_started",
    ModelGeometryEvent: "model_geometry",
    AnsatzLayoutEvent: "ansatz_layout",
    ObservableUpdated: "observable_updated",
    BondUpdated: "bond_updated",
    Checkpoint: "checkpoint",
    TdvpSweep: "tdvp_sweep",
    ContractionPathEvent: "contraction_path",
}


def normalize_event(event: TelemetryEvent) -> dict[str, Any]:
    """Return a JSON-ready event object with TNView's canonical event name."""

    if not is_dataclass(event) or isinstance(event, type):
        raise TypeError(f"unsupported telemetry event: {event!r}")
    return _event_dict(_event_name(event), event)


def export_replay_jsonl(events: Iterable[TelemetryEvent]) -> str:
    """Serialize parsed telemetry events as normalized JSONL."""

    lines = [
        json.dumps(normalize_event(event), sort_keys=True, separators=(",", ":"))
        for event in events
    ]
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def export_replay_csv(events: Iterable[TelemetryEvent]) -> str:
    """Serialize parsed telemetry events as normalized CSV rows."""

    return export_records_csv(normalize_event(event) for event in events)


def export_records_csv(records: Iterable[dict[str, Any]]) -> str:
    """Serialize JSON-like event dictionaries as a stable CSV table."""

    rows = list(records)
    columns = _columns(rows)
    handle = StringIO()
    writer = csv.writer(handle)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_csv_value(row.get(column)) for column in columns])
    return handle.getvalue().rstrip("\r\n")


def export_manifest(events: Iterable[TelemetryEvent]) -> dict[str, Any]:
    """Return compact replay metadata for parsed telemetry events."""

    event_list = list(events)
    state = reduce_events(event_list)
    times = [event.time for event in event_list]

    return {
        "event_count": len(event_list),
        "checkpoint_count": len(state.checkpoints),
        "bond_count": len(state.bonds),
        "time_range": {
            "start": min(times) if times else None,
            "end": max(times) if times else None,
        },
        "statuses": _statuses(state.checkpoints),
    }


def export_manifest_json(events: Iterable[TelemetryEvent]) -> str:
    """Serialize compact replay metadata as stable JSON."""

    return json.dumps(export_manifest(events), sort_keys=True, separators=(",", ":"))


def _event_dict(event_name: str, event: TelemetryEvent) -> dict[str, Any]:
    payload: dict[str, Any] = {"event": event_name}
    for field in fields(event):
        payload[field.name] = _json_value(getattr(event, field.name))
    return payload


def _event_name(event: TelemetryEvent) -> str:
    event_type = type(event)
    if event_type in _EVENT_NAMES:
        return _EVENT_NAMES[event_type]
    return re.sub(r"(?<!^)(?=[A-Z])", "_", event_type.__name__).lower()


def _json_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _columns(records: list[dict[str, Any]]) -> list[str]:
    priority = [
        "event",
        "schema_version",
        "run_id",
        "timestamp",
        "time",
        "library",
        "algorithm",
        "sweep",
        "step",
        "energy",
        "delta_energy",
        "loss",
        "max_chi",
        "chi_max_configured",
        "max_trunc_err",
        "entropy_max",
        "wall_s",
        "step_wall_s",
        "rss_mb",
        "status",
        "message",
    ]
    keys = {key for record in records for key in record}
    ordered = [key for key in priority if key in keys]
    ordered.extend(sorted(keys - set(ordered)))
    return ordered


def _csv_value(value: Any) -> Any:
    if isinstance(value, dict | list | tuple):
        return json.dumps(_json_value(value), sort_keys=True, separators=(",", ":"))
    return value


def _statuses(checkpoints: list[Checkpoint]) -> list[str]:
    statuses: list[str] = []
    for checkpoint in checkpoints:
        status = checkpoint.complexity_status
        if status is not None and status not in statuses:
            statuses.append(status)
    return statuses


__all__ = [
    "export_records_csv",
    "export_manifest",
    "export_manifest_json",
    "export_replay_csv",
    "export_replay_jsonl",
    "normalize_event",
]
