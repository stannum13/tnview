"""Replay validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any

from tnview.events import Checkpoint, EventParseError, TelemetryEvent, parse_jsonl_line
from tnview.runlog import is_run_log_record


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    event_count: int
    checkpoint_count: int
    bond_count: int
    run_log_count: int = 0
    warnings: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)


def validate_lines(lines: list[str]) -> ValidationReport:
    events: list[TelemetryEvent] = []
    run_log_records: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        try:
            event = parse_jsonl_line(line, line_number=line_number)
        except EventParseError as exc:
            record = _run_log_record(line)
            if record is not None:
                run_log_records.append(record)
                continue
            errors.append(str(exc))
            continue
        if event is not None:
            events.append(event)

    warnings = _warnings(events, run_log_records)
    bonds = {event.bond for event in events if event.__class__.__name__ == "BondUpdated"}
    checkpoints = [event for event in events if isinstance(event, Checkpoint)]
    return ValidationReport(
        valid=not errors,
        event_count=len(events),
        checkpoint_count=len(checkpoints),
        bond_count=len(bonds),
        run_log_count=len(run_log_records),
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def render_validation(report: ValidationReport) -> str:
    status = "valid" if report.valid else "invalid"
    lines = [
        f"Replay validation: {status}",
        f"events:            {report.event_count}",
        f"run-log events:    {report.run_log_count}",
        f"checkpoints:       {report.checkpoint_count}",
        f"bonds:             {report.bond_count}",
    ]
    if report.warnings:
        lines.append("warnings:")
        lines.extend(f"- {warning}" for warning in report.warnings)
    if report.errors:
        lines.append("errors:")
        lines.extend(f"- {error}" for error in report.errors)
    return "\n".join(lines)


def _warnings(events: list[TelemetryEvent], run_log_records: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    if not events and not run_log_records:
        warnings.append("no telemetry events found")
        return warnings
    if run_log_records and not events:
        return warnings
    if not any(isinstance(event, Checkpoint) for event in events):
        warnings.append("no checkpoints found; replay will render latest bond state only")
    if not any(getattr(event, "event", None) == "bond_updated" for event in events):
        bond_updates = [event for event in events if event.__class__.__name__ == "BondUpdated"]
        if not bond_updates:
            warnings.append("no bond updates found")
    return warnings


def _run_log_record(line: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    if is_run_log_record(payload):
        return payload
    return None
