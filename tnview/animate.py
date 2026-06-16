"""Scriptable replay animation for visual telemetry."""

from __future__ import annotations

from dataclasses import dataclass

from tnview.events import Checkpoint, TelemetryEvent
from tnview.focus import choose_focus
from tnview.render import RenderOptions, render_run
from tnview.signals import SignalPoint, signal_points
from tnview.state import RunState
from tnview.terminal import render_sparkline, render_status_dot


@dataclass(frozen=True)
class AnimationFrame:
    checkpoint_index: int
    frame_number: int
    frame_count: int
    time: float
    window_radius: float
    text: str


def checkpoint_count(events: list[TelemetryEvent]) -> int:
    return sum(1 for event in events if isinstance(event, Checkpoint))


def animation_frame_indices(checkpoints: int, frames: int | None = None) -> list[int]:
    """Return checkpoint indices to render for a scripted animation."""

    if checkpoints <= 0:
        return []
    if frames is None or frames >= checkpoints:
        return list(range(checkpoints))
    if frames <= 0:
        raise ValueError("frames must be positive")
    if frames == 1:
        return [0]
    scale = (checkpoints - 1) / (frames - 1)
    indices = [round(index * scale) for index in range(frames)]
    deduped: list[int] = []
    for index in indices:
        if not deduped or deduped[-1] != index:
            deduped.append(index)
    return deduped


def render_animation_frame(
    events: list[TelemetryEvent],
    *,
    checkpoint_index: int,
    frame_number: int,
    frame_count: int,
    window_radius: float,
    width: int | None = None,
    unicode: bool = True,
    color: bool = False,
    focus: str = "bottleneck",
) -> AnimationFrame:
    """Render one oscilloscope-style replay frame."""

    if window_radius < 0:
        raise ValueError("window_radius must be non-negative")
    state = _state_at_checkpoint(events, checkpoint_index)
    checkpoint = state.latest_checkpoint
    if checkpoint is None:
        raise ValueError("animation requires at least one checkpoint")
    if focus != "none":
        selection = choose_focus(state, strategy=focus, window=None)
        if selection.bond is not None:
            state.select_bond(selection.bond)

    time_min = checkpoint.time - window_radius
    time_max = checkpoint.time + window_radius
    points = signal_points(state, time_min=time_min, time_max=time_max)
    signal_panel = _signal_panel(state, points, width=width or 100, unicode=unicode, color=color)
    body = render_run(
        state,
        RenderOptions(
            width=width,
            unicode=unicode,
            color=color,
            history_time_min=time_min,
            history_time_max=time_max,
        ),
    )
    header = (
        f"TNView oscilloscope frame {frame_number}/{frame_count} | "
        f"T={checkpoint.time:g}  window=[{time_min:g}, {time_max:g}]  checkpoint={checkpoint_index}"
    )
    text = header + "\n" + signal_panel + "\n\n" + body if signal_panel else header + "\n" + body
    return AnimationFrame(
        checkpoint_index=checkpoint_index,
        frame_number=frame_number,
        frame_count=frame_count,
        time=checkpoint.time,
        window_radius=window_radius,
        text=text,
    )


def _state_at_checkpoint(events: list[TelemetryEvent], checkpoint_index: int) -> RunState:
    if checkpoint_index < 0:
        raise ValueError("checkpoint_index must be non-negative")
    state = RunState()
    seen = 0
    found = False
    for event in events:
        state.apply(event)
        if isinstance(event, Checkpoint):
            if seen == checkpoint_index:
                found = True
                break
            seen += 1
    if not found:
        raise ValueError(f"checkpoint_index {checkpoint_index} is out of range")
    return state


def _signal_panel(state: RunState, points: list[SignalPoint], *, width: int, unicode: bool, color: bool) -> str:
    if not points:
        return ""

    entropy = [point.entropy_max for point in points]
    chi = [float(point.max_chi) for point in points]
    trunc = [point.max_trunc_error for point in points]
    front = [float(point.front_span) for point in points]

    lines = ["Oscilloscope signals"]
    lines.append(_signal_line("entropy", entropy, unit="", severity="ok", width=width, unicode=unicode, color=color))
    lines.append(_signal_line("chi", chi, unit="", severity=_chi_severity(state), width=width, unicode=unicode, color=color))
    lines.append(_signal_line("trunc", trunc, unit="", severity=_trunc_severity(trunc[-1]), width=width, unicode=unicode, color=color))
    lines.append(_signal_line("front", front, unit=" bonds", severity="ok", width=width, unicode=unicode, color=color))
    return "\n".join(lines)


def _signal_line(
    label: str,
    values: list[float],
    *,
    unit: str,
    severity: str,
    width: int,
    unicode: bool,
    color: bool,
) -> str:
    dot = render_status_dot(severity, unicode=unicode, color=color)
    trend = render_sparkline(values, unicode=unicode)
    latest = _format_value(values[-1])
    change = "--" if len(values) < 2 else _format_change(values[-1] - values[-2])
    return _fit(f"  {dot} {label:<7} {trend:<12} latest={latest}{unit}  change={change}", width)


def _chi_severity(state: RunState) -> str:
    if any(bond.saturated or bond.chi_pressure >= 0.9 for bond in state.ordered_bonds):
        return "warning"
    return "ok"


def _trunc_severity(value: float) -> str:
    return "warning" if value >= 1e-7 else "ok"


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
