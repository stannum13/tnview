"""Public TNView telemetry schema summaries."""

from __future__ import annotations

from typing import Any

from tnview.events import EventName
from tnview.runlog import RUN_LOG_EVENTS


SCHEMA_VERSION = "0.1"

REPLAY_EVENTS: tuple[str, ...] = tuple(EventName.__args__)  # type: ignore[attr-defined]
RUN_LOG_EVENT_ORDER: tuple[str, ...] = (
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
)

RUN_LOG_METADATA: tuple[str, ...] = ("schema_version", "run_id", "timestamp or time")
RUN_LOG_METRICS: tuple[str, ...] = (
    "energy",
    "delta_energy",
    "loss",
    "max_chi",
    "chi_max_configured",
    "max_trunc_err",
    "entropy_max",
    "canonical_error",
    "wall_s",
    "step_wall_s",
    "rss_mb",
)

REPLAY_REQUIRED: dict[str, tuple[str, ...]] = {
    "run_started": ("run_id", "time"),
    "model_geometry": ("step", "time", "name"),
    "ansatz_layout": ("step", "time", "ansatz"),
    "observable_updated": ("step", "time", "name", "value"),
    "bond_updated": (
        "step",
        "time",
        "layer",
        "bond",
        "site_left",
        "site_right",
        "entropy_before",
        "entropy_after",
        "chi_before",
        "chi_after",
        "chi_max",
        "trunc_error",
    ),
    "checkpoint": ("step", "time"),
    "tdvp_sweep": ("step", "time", "direction", "start_site", "end_site"),
    "contraction_path": ("step", "time", "name"),
}


def schema_payload() -> dict[str, Any]:
    """Return the stable machine-readable schema summary."""

    return {
        "schema_version": SCHEMA_VERSION,
        "run_log": {
            "events": [event for event in RUN_LOG_EVENT_ORDER if event in RUN_LOG_EVENTS],
            "metadata": list(RUN_LOG_METADATA),
            "metrics": list(RUN_LOG_METRICS),
        },
        "replay": {
            "events": list(REPLAY_EVENTS),
            "required_fields": {event: list(fields) for event, fields in REPLAY_REQUIRED.items()},
        },
    }


def render_schema(*, width: int = 100) -> str:
    """Render a compact human-readable schema summary."""

    lines = [
        "TNView telemetry schema",
        f"schema version: {SCHEMA_VERSION}",
        "",
        "Run-log events:",
        "  " + ", ".join(schema_payload()["run_log"]["events"]),
        "",
        "Run-log metadata:",
        "  " + ", ".join(RUN_LOG_METADATA),
        "",
        "Run-log diagnostic metrics:",
        "  " + _wrap_join(RUN_LOG_METRICS, width=width, indent=2),
        "",
        "Replay events:",
    ]
    for event in REPLAY_EVENTS:
        required = ", ".join(REPLAY_REQUIRED.get(event, ()))
        lines.append(_fit(f"  {event:<18} required: {required or 'none'}", width))
    return "\n".join(lines)


def _wrap_join(values: tuple[str, ...], *, width: int, indent: int) -> str:
    prefix = " " * indent
    line = ""
    lines = []
    for value in values:
        addition = value if not line else ", " + value
        if line and len(prefix) + len(line) + len(addition) > width:
            lines.append(line)
            line = value
        else:
            line += addition
    if line:
        lines.append(line)
    return ("\n" + prefix).join(lines)


def _fit(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 1:
        return text[:width]
    return text[: width - 1] + "~"
