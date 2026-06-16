"""Static oscilloscope rendering for replay signals."""

from __future__ import annotations

from tnview.signals import SignalMarker, SignalPoint, detect_signal_markers, signal_series
from tnview.terminal import render_sparkline, render_status_dot


SIGNAL_LABELS = {
    "entropy": "entropy",
    "chi": "max chi",
    "trunc": "trunc",
    "front": "front",
    "selected_entropy": "sel S",
    "selected_chi": "sel chi",
    "selected_trunc": "sel eps",
}


def render_scope(
    points: list[SignalPoint],
    *,
    signals: tuple[str, ...] = ("entropy", "chi", "trunc", "front"),
    width: int = 100,
    unicode: bool = True,
    color: bool = False,
) -> str:
    """Render a static oscilloscope summary for replay signal points."""

    if not points:
        return "TNView scope\n(no checkpoint signal points)"

    markers = detect_signal_markers(points)
    lines = [
        _fit(
            f"TNView scope | points={len(points)}  window=[{points[0].time:g}, {points[-1].time:g}]",
            width,
        ),
        "",
        "Signals",
    ]
    for signal in signals:
        values = signal_series(points, signal)
        if values:
            lines.append(_signal_line(signal, values, width=width, unicode=unicode, color=color))

    if markers:
        lines.extend(["", render_marker_ticks(points, markers=markers, width=width, unicode=unicode)])
        lines.extend(["", "Event markers"])
        lines.extend(_marker_lines(markers, width=width, unicode=unicode, color=color))

    return "\n".join(lines)


def render_marker_ticks(
    points: list[SignalPoint],
    *,
    markers: list[SignalMarker] | None = None,
    width: int = 100,
    unicode: bool = True,
) -> str:
    """Render one compact marker row aligned to checkpoint signal points."""

    if not points:
        return _fit("Event ticks  (none)", width)
    by_index: dict[int, list[SignalMarker]] = {}
    for marker in markers or detect_signal_markers(points):
        by_index.setdefault(marker.index, []).append(marker)
    glyphs = [_tick_glyph(by_index.get(index, []), unicode=unicode) for index in range(len(points))]
    return _fit(f"Event ticks  {''.join(glyphs)}", width)


def _signal_line(signal: str, values: list[float], *, width: int, unicode: bool, color: bool) -> str:
    label = SIGNAL_LABELS.get(signal, signal)
    severity = _series_severity(signal, values)
    dot = render_status_dot(severity, unicode=unicode, color=color)
    trend = render_sparkline(values, unicode=unicode)
    latest = _format_value(values[-1])
    change = "--" if len(values) < 2 else _format_change(values[-1] - values[-2])
    return _fit(f"  {dot} {label:<8} {trend:<24} latest={latest}  change={change}", width)


def _marker_lines(markers: list[SignalMarker], *, width: int, unicode: bool, color: bool) -> list[str]:
    lines = []
    for marker in markers[-8:]:
        dot = render_status_dot(marker.severity, unicode=unicode, color=color)
        lines.append(_fit(f"  {dot} t={marker.time:g} step={marker.step:<5} {marker.code:<18} {marker.message}", width))
    return lines


def _tick_glyph(markers: list[SignalMarker], *, unicode: bool) -> str:
    if any(marker.severity == "error" for marker in markers):
        return "!" if not unicode else "!"
    if any(marker.severity == "warning" for marker in markers):
        return "!" if not unicode else "▲"
    if markers:
        return "|" if not unicode else "•"
    return "." if not unicode else "·"


def _series_severity(signal: str, values: list[float]) -> str:
    latest = values[-1]
    if signal in {"trunc", "selected_trunc"} and latest >= 1e-7:
        return "warning"
    if signal in {"chi", "selected_chi"} and len(values) >= 2 and latest >= values[-2] and latest > 0:
        return "warning"
    return "ok"


def _format_value(value: float) -> str:
    if abs(value) >= 1e4 or (0 < abs(value) < 1e-3):
        return f"{value:.2e}"
    return f"{value:.4g}"


def _format_change(value: float) -> str:
    return f"{value:+.2e}" if abs(value) >= 1e4 or (0 < abs(value) < 1e-3) else f"{value:+.4g}"


def _fit(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 1:
        return text[:width]
    return text[: width - 1] + "~"
