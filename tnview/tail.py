"""Plain terminal tail view for run-log telemetry."""

from __future__ import annotations

from typing import Any

from tnview.diagnose import diagnose_events


def render_run_log_tail(records: list[dict[str, Any]], *, width: int = 100) -> str:
    latest = _latest_state(records)
    diagnostics = diagnose_events(records)
    lines = [
        _fit(
            "TNView run tail"
            + _suffix(latest, ["run_id", "library", "algorithm"]),
            width,
        ),
        "",
        "Current:",
    ]
    for key, label in [
        ("sweep", "sweep"),
        ("step", "step"),
        ("energy", "energy"),
        ("delta_energy", "delta energy"),
        ("loss", "loss"),
        ("max_chi", "max chi"),
        ("max_trunc_err", "truncation"),
        ("entropy_max", "entropy max"),
        ("step_wall_s", "step wall"),
        ("wall_s", "wall time"),
        ("rss_mb", "rss"),
    ]:
        if key in latest:
            lines.append(_fit(f"  {label:<13} {_format_value(latest[key])}", width))

    lines.extend(["", "Diagnostics:"])
    if diagnostics:
        for diagnostic in diagnostics:
            lines.append(_fit(f"  {diagnostic.severity.upper()} {diagnostic.code}: {diagnostic.message}", width))
    else:
        lines.append("  no warnings")

    lines.extend(["", "Recent events:"])
    for record in records[-5:]:
        lines.append(_fit("  " + _event_summary(record), width))
    return "\n".join(lines)


def _latest_state(records: list[dict[str, Any]]) -> dict[str, Any]:
    state: dict[str, Any] = {}
    for record in records:
        for key, value in record.items():
            if key in {"event", "schema_version", "timestamp", "notes"}:
                continue
            if value is not None:
                state[key] = value
    return state


def _suffix(state: dict[str, Any], keys: list[str]) -> str:
    parts = [f"{key}={state[key]}" for key in keys if state.get(key) is not None]
    if not parts:
        return ""
    return " | " + " ".join(parts)


def _event_summary(record: dict[str, Any]) -> str:
    fields = []
    for key in ["time", "event", "sweep", "step", "energy", "delta_energy", "loss", "max_chi", "max_trunc_err"]:
        if key in record:
            fields.append(f"{key}={_format_value(record[key])}")
    return " ".join(fields)


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _fit(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 1:
        return text[:width]
    return text[: width - 1] + "~"
