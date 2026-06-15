"""Small terminal UI primitives for TNView."""

from __future__ import annotations

import os
from typing import TextIO


ANSI_CODES = {
    "green": "32",
    "yellow": "33",
    "red": "31",
    "cyan": "36",
    "gray": "90",
}


def supports_color(stream: TextIO | None = None) -> bool:
    """Return whether semantic ANSI color should be emitted."""

    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    if stream is None:
        return False
    isatty = getattr(stream, "isatty", None)
    return bool(callable(isatty) and isatty())


def ansi(
    text: str,
    *,
    color: str | None = None,
    bold: bool = False,
    dim: bool = False,
    enabled: bool = False,
) -> str:
    """Apply a small semantic ANSI style if enabled."""

    if not enabled:
        return text
    codes = []
    if bold:
        codes.append("1")
    if dim:
        codes.append("2")
    if color in ANSI_CODES:
        codes.append(ANSI_CODES[color])
    if not codes:
        return text
    return f"\033[{';'.join(codes)}m{text}\033[0m"


def render_status_dot(status: str, *, unicode: bool = True, color: bool = False) -> str:
    """Render a compact status dot for live/stale/warning/error state."""

    glyph = "●" if unicode else "*"
    color_name = {
        "live": "green",
        "ok": "green",
        "warning": "yellow",
        "stale": "yellow",
        "error": "red",
    }.get(status, "gray")
    return ansi(glyph, color=color_name, enabled=color)


def render_meter(
    label: str,
    value: float | None,
    limit: float | None = 1.0,
    *,
    width: int = 10,
    severity: str = "ok",
    unicode: bool = True,
    color: bool = False,
) -> str:
    """Render a bounded pressure meter."""

    if width < 1:
        width = 1
    ratio = _ratio(value, limit)
    filled = int(round(ratio * width))
    full = "█" if unicode else "#"
    empty = "░" if unicode else "."
    bar = full * filled + empty * (width - filled)
    color_name = {"ok": "green", "warning": "yellow", "error": "red"}.get(severity, "gray")
    return f"{label:<9} [{ansi(bar, color=color_name, enabled=color)}] {severity}"


def compact_event_time(record: dict[str, object]) -> str:
    """Return a compact timestamp/time label for an event record."""

    value = record.get("timestamp") or record.get("time")
    if isinstance(value, str):
        if "T" in value:
            return value.split("T", 1)[1].replace("Z", "")[:8]
        return value[:8]
    if isinstance(value, int | float) and not isinstance(value, bool):
        return f"t={value:.3g}"
    return "--:--:--"


def _ratio(value: float | None, limit: float | None) -> float:
    if value is None:
        return 0.0
    if limit is None or limit <= 0:
        return 1.0 if value > 0 else 0.0
    return max(0.0, min(1.0, value / limit))
