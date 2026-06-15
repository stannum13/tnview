"""Plain terminal tail view for run-log telemetry."""

from __future__ import annotations

from typing import Any

from tnview.diagnose import diagnose_events
from tnview.terminal import compact_event_time, render_meter, render_status_dot


def render_run_log_tail(
    records: list[dict[str, Any]],
    *,
    width: int = 100,
    unicode: bool = True,
    color: bool = False,
    live: bool = False,
) -> str:
    latest = _latest_state(records)
    previous = _latest_state(records[:-1])
    changed = _changed_fields(latest, previous)
    diagnostics = diagnose_events(records)
    lines = []
    if live:
        lines.append(_fit(_status_line(records, latest, diagnostics, unicode=unicode, color=color), width))
    lines.extend(
        [
        _fit(
            "TNView run tail"
            + _suffix(latest, ["run_id", "library", "algorithm"]),
            width,
        ),
        _fit(f"events={len(records)}" + _updated_suffix(records), width),
        "",
        "Current:",
        ]
    )
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
            prefix = "*" if key in changed else " "
            suffix = f" (was {_format_value(previous[key])})" if key in changed and key in previous else ""
            lines.append(_fit(f"  {prefix} {label:<13} {_format_value(latest[key])}{suffix}", width))

    lines.extend(["", "Diagnostics:"])
    if diagnostics:
        for diagnostic in diagnostics:
            lines.append(_fit(f"  {diagnostic.severity.upper()} {diagnostic.code}: {diagnostic.message}", width))
    else:
        lines.append("  no warnings")

    pressure = _pressure_lines(records, latest, diagnostics, width=width, unicode=unicode, color=color)
    if pressure:
        lines.extend(["", "Pressure:"])
        lines.extend(pressure)

    trends = _trend_lines(records, width=width, unicode=unicode)
    if trends:
        lines.extend(["", "Trends:"])
        lines.extend(trends)

    lines.extend(["", "Events:"])
    lines.extend(_event_ticker(records[-5:], width=width))
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


def _changed_fields(latest: dict[str, Any], previous: dict[str, Any]) -> set[str]:
    return {
        key
        for key, value in latest.items()
        if key in previous and previous[key] != value
    }


def _updated_suffix(records: list[dict[str, Any]]) -> str:
    value = None
    if records:
        value = records[-1].get("timestamp") or records[-1].get("time")
    if value is None:
        return ""
    return f" updated={_format_value(value)}"


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


def _status_line(
    records: list[dict[str, Any]],
    latest: dict[str, Any],
    diagnostics: list[Any],
    *,
    unicode: bool,
    color: bool,
) -> str:
    status = "warning" if diagnostics else "live"
    dot = render_status_dot(status, unicode=unicode, color=color)
    parts = [f"{dot} {status}"]
    for key, label in [
        ("run_id", "run"),
        ("sweep", "sweep"),
        ("step", "step"),
        ("delta_energy", "dE"),
        ("loss", "loss"),
        ("rss_mb", "rss"),
    ]:
        if key in latest:
            parts.append(f"{label}={_format_value(latest[key])}")
    if latest.get("max_chi") is not None:
        chi = _format_value(latest["max_chi"])
        limit = latest.get("chi_max_configured")
        parts.append(f"chi={chi}/{_format_value(limit) if limit is not None else '?'}")
    if records:
        parts.append(f"events={len(records)}")
    return "  ".join(parts)


def _pressure_lines(
    records: list[dict[str, Any]],
    latest: dict[str, Any],
    diagnostics: list[Any],
    *,
    width: int,
    unicode: bool,
    color: bool,
) -> list[str]:
    health = "warning" if diagnostics else "ok"
    if any(record.get("event") == "error" for record in records):
        health = "error"
    lines = [
        _fit("  " + render_meter("health", 1.0 if health != "ok" else 0.35, 1.0, severity=health, unicode=unicode, color=color), width)
    ]

    chi = _number(latest.get("max_chi"))
    chi_limit = _number(latest.get("chi_max_configured"))
    if chi is not None:
        severity = "warning" if chi_limit and chi >= chi_limit else "ok"
        lines.append(_fit("  " + render_meter("chi", chi, chi_limit or max(chi, 1.0), severity=severity, unicode=unicode, color=color), width))

    trunc = _number(latest.get("max_trunc_err"))
    if trunc is not None:
        severity = "warning" if trunc > 1e-7 else "ok"
        lines.append(_fit("  " + render_meter("trunc", min(trunc / 1e-7, 1.0), 1.0, severity=severity, unicode=unicode, color=color), width))

    rss_values = [_number(record.get("rss_mb")) for record in records]
    rss_series = [value for value in rss_values if value is not None][-5:]
    if rss_series:
        ratio = rss_series[-1] / rss_series[0] if rss_series[0] else 1.0
        severity = "warning" if len(rss_series) >= 5 and all(a <= b for a, b in zip(rss_series, rss_series[1:])) and ratio >= 1.25 else "ok"
        lines.append(_fit("  " + render_meter("memory", min(ratio - 1.0, 1.0), 1.0, severity=severity, unicode=unicode, color=color), width))

    progress = _progress_pressure(records)
    if progress is not None:
        severity = "warning" if progress >= 0.75 else "ok"
        lines.append(_fit("  " + render_meter("progress", progress, 1.0, severity=severity, unicode=unicode, color=color), width))
    return lines


def _progress_pressure(records: list[dict[str, Any]]) -> float | None:
    deltas = [_number(record.get("delta_energy")) for record in records if record.get("delta_energy") is not None]
    if deltas:
        return 1.0 if abs(deltas[-1]) <= 1e-8 else 0.25
    losses = [_number(record.get("loss")) for record in records if record.get("loss") is not None]
    if len(losses) >= 2:
        improvement = abs(losses[-2] - losses[-1])
        return 1.0 if improvement < 1e-6 else 0.25
    return None


def _event_ticker(records: list[dict[str, Any]], *, width: int) -> list[str]:
    lines = []
    for record in records:
        pieces = [compact_event_time(record), str(record.get("event", "event")).ljust(14)]
        for key, label in [
            ("sweep", "sweep"),
            ("step", "step"),
            ("energy", "E"),
            ("delta_energy", "dE"),
            ("loss", "loss"),
            ("max_chi", "chi"),
            ("max_trunc_err", "trunc"),
            ("rss_mb", "rss"),
        ]:
            if key in record:
                pieces.append(f"{label}={_format_value(record[key])}")
        if record.get("max_chi") is not None and record.get("chi_max_configured") is not None:
            if _number(record.get("max_chi")) == _number(record.get("chi_max_configured")):
                pieces.append("saturated")
        lines.append(_fit(("  " + "  ".join(pieces)).rstrip(), width))
    return lines


def _trend_lines(records: list[dict[str, Any]], *, width: int, unicode: bool) -> list[str]:
    lines = []
    for key, label in [
        ("energy", "energy"),
        ("delta_energy", "delta E"),
        ("loss", "loss"),
        ("max_chi", "max chi"),
        ("max_trunc_err", "trunc"),
        ("rss_mb", "rss"),
    ]:
        values = [_number(record.get(key)) for record in records]
        series = [value for value in values if value is not None][-24:]
        if len(series) < 2:
            continue
        sparkline = _sparkline(series, unicode=unicode)
        change = series[-1] - series[-2]
        lines.append(_fit(f"  {label:<8} {sparkline}  latest={_format_value(series[-1])} change={_format_value(change)}", width))
    return lines


def _sparkline(values: list[float], *, unicode: bool) -> str:
    marks = "▁▂▃▄▅▆▇█" if unicode else "._:-=+*#"
    low = min(values)
    high = max(values)
    if high == low:
        return marks[0] * len(values)
    span = high - low
    scale = len(marks) - 1
    return "".join(marks[int((value - low) / span * scale)] for value in values)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


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
