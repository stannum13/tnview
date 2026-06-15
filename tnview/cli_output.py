"""Shared CLI output and error rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import sys
from typing import Any, TextIO


@dataclass(frozen=True)
class CliError(Exception):
    code: str
    message: str
    path: str | None = None
    reason: str | None = None
    suggestions: tuple[str, ...] = field(default_factory=tuple)
    exit_code: int = 2


@dataclass(frozen=True)
class CommandResult:
    ok: bool
    text: str
    data: dict[str, Any]
    exit_code: int = 0


def write_text(text: str, *, stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    print(text, file=target)


def write_json(payload: dict[str, Any], *, stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")), file=target)


def render_error(error: CliError) -> str:
    lines = [error.message]
    if error.path is not None:
        lines.extend(["", "Path:", f"  {error.path}"])
    if error.reason is not None:
        lines.extend(["", "Reason:", f"  {error.reason}"])
    if error.suggestions:
        lines.extend(["", "Try:"])
        lines.extend(f"  {suggestion}" for suggestion in error.suggestions)
    return "\n".join(lines)


def error_payload(error: CliError) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": False,
        "error": {
            "code": error.code,
            "message": error.message,
        },
    }
    if error.path is not None:
        payload["error"]["path"] = error.path
    if error.reason is not None:
        payload["error"]["reason"] = error.reason
    if error.suggestions:
        payload["error"]["suggestions"] = list(error.suggestions)
    return payload


def result_payload(result: CommandResult) -> dict[str, Any]:
    payload = {"ok": result.ok}
    payload.update(result.data)
    return payload
