"""Raw JSONL helpers for TNView run-log telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Iterable


RUN_LOG_EVENTS = {
    "run_start",
    "run_end",
    "step_start",
    "step_end",
    "sweep_start",
    "sweep_end",
    "optimizer_step",
    "observable",
    "warning",
    "error",
    "diagnostic",
}


@dataclass(frozen=True)
class RawLogReport:
    records: tuple[dict[str, Any], ...]
    errors: tuple[str, ...] = field(default_factory=tuple)

    @property
    def valid(self) -> bool:
        return not self.errors


def read_jsonl_records(lines: Iterable[str]) -> RawLogReport:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"line {line_number}: event must be a JSON object")
            continue
        event = payload.get("event")
        if not isinstance(event, str):
            errors.append(f"line {line_number}: event must be a string")
            continue
        records.append(payload)
    return RawLogReport(records=tuple(records), errors=tuple(errors))


def is_run_log_record(record: dict[str, Any]) -> bool:
    return record.get("event") in RUN_LOG_EVENTS


def is_run_log(lines: Iterable[str]) -> bool:
    report = read_jsonl_records(lines)
    return any(is_run_log_record(record) for record in report.records)
