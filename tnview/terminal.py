"""Small terminal UI primitives for TNView."""

from __future__ import annotations

import os
import re
import unicodedata
from typing import TextIO


ANSI_CODES = {
    "green": "32",
    "yellow": "33",
    "red": "31",
    "cyan": "36",
    "gray": "90",
}

SEVERITY_COLORS = {
    "ok": "green",
    "live": "green",
    "info": "cyan",
    "watch": "yellow",
    "warning": "yellow",
    "warn": "yellow",
    "stale": "yellow",
    "high": "yellow",
    "error": "red",
    "critical": "red",
    "unknown": "gray",
}

SEVERITY_SYMBOLS = {
    "ok": ("●", "*"),
    "live": ("●", "*"),
    "info": ("●", "*"),
    "watch": ("▲", "!"),
    "warning": ("▲", "!"),
    "warn": ("▲", "!"),
    "stale": ("▲", "!"),
    "high": ("▲", "!"),
    "error": ("■", "x"),
    "critical": ("■", "x"),
    "unknown": ("·", "."),
}

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


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

    return severity_symbol(status, unicode=unicode, color=color)


def severity_color(severity: str) -> str:
    """Return the semantic color name for a severity string."""

    return SEVERITY_COLORS.get(severity, "gray")


def severity_symbol(severity: str, *, unicode: bool = True, color: bool = False) -> str:
    """Return a compact semantic symbol for a severity string."""

    glyphs = SEVERITY_SYMBOLS.get(severity, SEVERITY_SYMBOLS["unknown"])
    glyph = glyphs[0] if unicode else glyphs[1]
    return ansi(glyph, color=severity_color(severity), enabled=color)


def render_severity(severity: str, *, unicode: bool = True, color: bool = False) -> str:
    """Render a symbol plus severity label."""

    return f"{severity_symbol(severity, unicode=unicode, color=color)} {severity}"


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
    color_name = severity_color(severity)
    return f"{label:<9} [{ansi(bar, color=color_name, enabled=color)}] {severity}"


def render_panel(title: str, lines: list[str], *, width: int = 100, unicode: bool = True) -> str:
    """Render a simple width-bounded terminal panel."""

    width = max(16, width)
    content_width = width - 4
    if unicode:
        top_left, top_right, bottom_left, bottom_right = "┌", "┐", "└", "┘"
        horizontal, vertical = "─", "│"
    else:
        top_left, top_right, bottom_left, bottom_right = "+", "+", "+", "+"
        horizontal, vertical = "-", "|"

    label = f" {title} " if title else ""
    rule_width = max(0, width - _display_width(label) - 2)
    top = f"{top_left}{label}{horizontal * rule_width}{top_right}"
    bottom = f"{bottom_left}{horizontal * (width - 2)}{bottom_right}"
    body = [f"{vertical} {_pad_cells(_fit_cells(line, content_width), content_width)} {vertical}" for line in lines]
    return "\n".join([top, *body, bottom])


def render_sparkline(values: list[float], *, unicode: bool = True) -> str:
    """Render a compact trend line for a short numeric series."""

    marks = "▁▂▃▄▅▆▇█" if unicode else "._:-=+*#"
    if not values:
        return ""
    low = min(values)
    high = max(values)
    if high == low:
        return marks[0] * len(values)
    span = high - low
    scale = len(marks) - 1
    return "".join(marks[int((value - low) / span * scale)] for value in values)


def _fit_cells(text: str, width: int) -> str:
    if _display_width(text) <= width:
        return text
    suffix = "~"
    target = max(0, width - _display_width(suffix))
    output = ""
    for char in text:
        next_output = output + char
        if _display_width(next_output) > target:
            break
        output = next_output
    return output + suffix


def _pad_cells(text: str, width: int) -> str:
    return text + " " * max(0, width - _display_width(text))


def _display_width(text: str) -> int:
    clean = ANSI_RE.sub("", text)
    width = 0
    for char in clean:
        if unicodedata.combining(char):
            continue
        if unicodedata.category(char) in {"Cc", "Cf"}:
            continue
        width += 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
    return width


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
