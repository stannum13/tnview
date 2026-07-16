"""Raw JSONL helpers for TNView run-log telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
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
    "heartbeat",
}


@dataclass(frozen=True)
class RawLogReport:
    records: tuple[dict[str, Any], ...]
    errors: tuple[str, ...] = field(default_factory=tuple)
    pending_final_line: str | None = None

    @property
    def valid(self) -> bool:
        return not self.errors

    @property
    def has_pending_final_record(self) -> bool:
        return self.pending_final_line is not None


@dataclass(frozen=True)
class FollowRead:
    lines: tuple[str, ...]
    reset: bool = False
    pending_final_line: str | None = None


class JsonlFollower:
    """Incrementally read complete JSONL lines from a file path."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._offset = 0
        self._signature: tuple[int, int] | None = None
        self._pending = ""

    def read_new_lines(self) -> FollowRead:
        stat = self.path.stat()
        signature = (stat.st_dev, stat.st_ino)
        reset = False
        if self._signature is not None and (
            signature != self._signature or stat.st_size < self._offset
        ):
            reset = True
            self._offset = 0
            self._pending = ""
        self._signature = signature

        with self.path.open("r", encoding="utf-8") as handle:
            handle.seek(self._offset)
            data = handle.read()
            self._offset = handle.tell()

        if not data:
            return FollowRead(lines=(), reset=reset, pending_final_line=self._pending or None)

        text = self._pending + data
        parts = text.splitlines(keepends=True)
        if parts and not parts[-1].endswith(("\n", "\r")):
            possible_partial = parts[-1]
            try:
                json.loads(possible_partial.strip())
            except json.JSONDecodeError:
                self._pending = parts.pop()
            else:
                self._pending = ""
        else:
            self._pending = ""
        return FollowRead(
            lines=tuple(parts),
            reset=reset,
            pending_final_line=self._pending or None,
        )


def read_jsonl_records(
    lines: Iterable[str],
    *,
    allow_partial_final: bool = False,
) -> RawLogReport:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    pending_final_line: str | None = None
    items = list(lines)
    for line_number, line in enumerate(items, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            final_line = line_number == len(items)
            complete_line = line.endswith(("\n", "\r"))
            if allow_partial_final and final_line and not complete_line:
                pending_final_line = stripped
                continue
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
    return RawLogReport(
        records=tuple(records),
        errors=tuple(errors),
        pending_final_line=pending_final_line,
    )


def is_run_log_record(record: dict[str, Any]) -> bool:
    return record.get("event") in RUN_LOG_EVENTS


def is_run_log(lines: Iterable[str]) -> bool:
    report = read_jsonl_records(lines)
    return any(is_run_log_record(record) for record in report.records)
