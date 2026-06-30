"""Scriptable replay animation for visual telemetry."""

from __future__ import annotations

from dataclasses import dataclass

from tnview.events import Checkpoint, TelemetryEvent
from tnview.focus import choose_focus
from tnview.render import RenderOptions, render_run
from tnview.scope import render_marker_ticks
from tnview.signals import SignalPoint, signal_points, signal_series
from tnview.state import RunState, diagnose_bond, diagnose_run
from tnview.terminal import render_panel, render_sparkline, render_status_dot
from tnview.warnings import early_warning


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


def checkpoint_times(events: list[TelemetryEvent]) -> list[float]:
    return [event.time for event in events if isinstance(event, Checkpoint)]


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


def animation_frame_indices_for_times(
    events: list[TelemetryEvent],
    *,
    frames: int | None = None,
    time_min: float | None = None,
    time_max: float | None = None,
) -> list[int]:
    """Return checkpoint indices filtered by optional checkpoint time bounds."""

    candidates = [
        index
        for index, time in enumerate(checkpoint_times(events))
        if _inside_time_window(time, time_min=time_min, time_max=time_max)
    ]
    if frames is None or frames >= len(candidates):
        return candidates
    return [candidates[index] for index in animation_frame_indices(len(candidates), frames)]


def animation_playback_indices(
    indices: list[int],
    *,
    reverse: bool = False,
    bounce: bool = False,
) -> list[int]:
    """Apply playback order controls to checkpoint frame indices."""

    ordered = list(reversed(indices)) if reverse else list(indices)
    if bounce and len(ordered) > 1:
        ordered.extend(reversed(ordered[1:-1] or ordered[:1]))
    return ordered


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
    selected_bond: int | None = None,
    bond_start: int | None = None,
    bond_limit: int | None = None,
    signals: tuple[str, ...] = ("entropy", "chi", "trunc", "front"),
    style: str = "report",
) -> AnimationFrame:
    """Render one oscilloscope-style replay frame."""

    if window_radius < 0:
        raise ValueError("window_radius must be non-negative")
    if style not in {"report", "instrument"}:
        raise ValueError("style must be 'report' or 'instrument'")
    state = _state_at_checkpoint(events, checkpoint_index)
    checkpoint = state.latest_checkpoint
    if checkpoint is None:
        raise ValueError("animation requires at least one checkpoint")
    if focus != "none":
        selection = choose_focus(state, strategy=focus, window=None)
        if selection.bond is not None:
            state.select_bond(selection.bond)
    if selected_bond is not None:
        state.select_bond(selected_bond)

    time_min = checkpoint.time - window_radius
    time_max = checkpoint.time + window_radius
    points = signal_points(state, time_min=time_min, time_max=time_max)
    render_width = width or 100
    signal_panel = _signal_panel(state, points, signals=signals, width=render_width, unicode=unicode, color=color)
    body = render_run(
        state,
        RenderOptions(
            width=width,
            unicode=unicode,
            color=color,
            history_time_min=time_min,
            history_time_max=time_max,
            show_updates=style == "report",
            show_inspector=style == "report",
            show_diagnostics=style == "report",
            bond_start=bond_start,
            bond_limit=bond_limit,
            pulse_phase=frame_number if style == "instrument" else None,
        ),
    )
    header = (
        f"TNView oscilloscope frame {frame_number}/{frame_count} | "
        f"T={checkpoint.time:g}  window=[{time_min:g}, {time_max:g}]  checkpoint={checkpoint_index}"
    )
    if style == "instrument":
        text = _instrument_frame_text(
            state,
            header=header,
            signal_panel=signal_panel,
            body=body,
            points=points,
            frame_number=frame_number,
            width=render_width,
            unicode=unicode,
            color=color,
        )
    else:
        text = header + "\n" + signal_panel + "\n\n" + body if signal_panel else header + "\n" + body
    return AnimationFrame(
        checkpoint_index=checkpoint_index,
        frame_number=frame_number,
        frame_count=frame_count,
        time=checkpoint.time,
        window_radius=window_radius,
        text=text,
    )


def _instrument_frame_text(
    state: RunState,
    *,
    header: str,
    signal_panel: str,
    body: str,
    points: list[SignalPoint],
    frame_number: int,
    width: int,
    unicode: bool,
    color: bool,
) -> str:
    sections = [
        _fit(header.replace("oscilloscope frame", "instrument frame"), width),
        _instrument_status_panel(state, width=width, unicode=unicode, color=color),
        _instrument_signal_panel(signal_panel, width=width, unicode=unicode) if signal_panel else "",
        _motion_panel(state, points, frame_number=frame_number, width=width, unicode=unicode),
        _focus_panel(state, width=width, unicode=unicode, color=color),
        body,
    ]
    return "\n\n".join(section for section in sections if section)


def _instrument_status_panel(state: RunState, *, width: int, unicode: bool, color: bool) -> str:
    checkpoint = state.latest_checkpoint
    warning = early_warning(state)
    status = checkpoint.complexity_status if checkpoint and checkpoint.complexity_status else diagnose_run(state)
    risk = warning.risk
    severity = _risk_severity(risk)
    dot = render_status_dot(severity, unicode=unicode, color=color)
    if checkpoint is None:
        time_text = "step=n/a  T=n/a"
    else:
        time_text = f"step={checkpoint.step}  T={checkpoint.time:g}"
    selected = "none" if state.selected_bond is None else f"b{state.selected_bond}"
    lines = [
        f"{dot} {time_text}  risk={risk}  status={status.replace('_', '-')}  focus={selected}",
        f"next: {_next_action(state, risk)}",
    ]
    return render_panel("STATUS", lines, width=width, unicode=unicode)


def _instrument_signal_panel(signal_panel: str, *, width: int, unicode: bool) -> str:
    lines = signal_panel.splitlines()
    if lines and lines[0] == "Oscilloscope signals":
        lines = lines[1:]
    return render_panel("SIGNALS", lines, width=width, unicode=unicode)


def _motion_panel(
    state: RunState,
    points: list[SignalPoint],
    *,
    frame_number: int,
    width: int,
    unicode: bool,
) -> str:
    checkpoint = state.latest_checkpoint
    active_time = checkpoint.time if checkpoint is not None else None
    lines = [
        _time_cursor_line(points, active_time=active_time, unicode=unicode),
        _sweep_cursor_line(state, frame_number=frame_number, unicode=unicode),
        _motion_legend_line(unicode=unicode),
    ]
    return render_panel("MOTION", lines, width=width, unicode=unicode)


def _focus_panel(state: RunState, *, width: int, unicode: bool, color: bool) -> str:
    bond = state.selected
    if bond is None:
        return ""
    severity = _risk_severity("high" if bond.saturated else "warning" if bond.chi_pressure >= 0.75 else "ok")
    dot = render_status_dot(severity, unicode=unicode, color=color)
    lines = [
        _fit(
            f"  {dot} b{bond.bond} sites {bond.site_left}|{bond.site_right}  "
            f"S={bond.entropy:.4g}  chi={bond.chi}/{bond.chi_max}  eps={bond.trunc_error:.2e}",
            max(16, width - 4),
        ),
        _fit(f"  diagnosis: {diagnose_bond(bond)}", max(16, width - 4)),
    ]
    return render_panel("FOCUS", lines, width=width, unicode=unicode)


def _time_cursor_line(
    points: list[SignalPoint],
    *,
    active_time: float | None,
    unicode: bool,
) -> str:
    if not points:
        return "time  no checkpoints in window"
    if active_time is None:
        active = len(points) - 1
    else:
        active = min(range(len(points)), key=lambda index: abs(points[index].time - active_time))
    cells = _cursor_cells(len(points), active=active, unicode=unicode)
    point = points[active]
    return f"time  {cells}  T={point.time:g} step={point.step}"


def _sweep_cursor_line(state: RunState, *, frame_number: int, unicode: bool) -> str:
    bonds = state.ordered_bonds
    if not bonds:
        return "sweep no bond telemetry"
    active_index = (frame_number - 1) % len(bonds)
    selected = state.selected_bond
    cells = []
    for index, bond in enumerate(bonds):
        if index == active_index:
            cells.append("◆" if unicode else ">")
        elif bond.bond == selected:
            cells.append("◇" if unicode else "^")
        elif bond.saturated:
            cells.append("■" if unicode else "!")
        elif bond.chi_pressure >= 0.75:
            cells.append("▲" if unicode else "+")
        else:
            cells.append("·" if unicode else ".")
    return f"sweep {' '.join(cells)}  active=b{bonds[active_index].bond}"


def _motion_legend_line(*, unicode: bool) -> str:
    if unicode:
        return "legend ◆ active  ◇ selected  ■ saturated  ▲ pressure"
    return "legend > active  ^ selected  ! saturated  + pressure"


def _cursor_cells(count: int, *, active: int, unicode: bool) -> str:
    if count <= 0:
        return ""
    active = min(count - 1, max(0, active))
    on = "●" if unicode else "o"
    off = "─" if unicode else "-"
    return "".join(on if index == active else off for index in range(count))


def _next_action(state: RunState, risk: str) -> str:
    bond = state.selected
    if bond is None:
        return "wait for replay telemetry"
    if bond.saturated:
        return f"increase chi_max or inspect b{bond.bond} truncation"
    if risk in {"high", "medium"} and bond.chi_pressure >= 0.5:
        return f"watch b{bond.bond}; compare against larger chi"
    if bond.trunc_error >= 1e-7:
        return f"inspect truncation around b{bond.bond}"
    return "continue; no local bottleneck yet"


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


def _signal_panel(
    state: RunState,
    points: list[SignalPoint],
    *,
    signals: tuple[str, ...],
    width: int,
    unicode: bool,
    color: bool,
) -> str:
    if not points:
        return ""

    lines = ["Oscilloscope signals"]
    for signal in signals:
        values = signal_series(points, signal)
        if not values:
            continue
        lines.append(
            _signal_line(
                _signal_label(signal),
                values,
                unit=_signal_unit(signal),
                severity=_signal_severity(signal, values, state),
                width=width,
                unicode=unicode,
                color=color,
            )
        )
    lines.append(render_marker_ticks(points, width=width, unicode=unicode))
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


def _signal_label(signal: str) -> str:
    return {
        "entropy": "entropy",
        "chi": "chi",
        "trunc": "trunc",
        "front": "front",
        "selected_entropy": "sel S",
        "selected_chi": "sel chi",
        "selected_trunc": "sel eps",
    }.get(signal, signal)


def _signal_unit(signal: str) -> str:
    return " bonds" if signal == "front" else ""


def _signal_severity(signal: str, values: list[float], state: RunState) -> str:
    if signal in {"chi", "selected_chi"}:
        return _chi_severity(state)
    if signal in {"trunc", "selected_trunc"}:
        return _trunc_severity(values[-1])
    return "ok"


def _chi_severity(state: RunState) -> str:
    if any(bond.saturated or bond.chi_pressure >= 0.9 for bond in state.ordered_bonds):
        return "warning"
    return "ok"


def _trunc_severity(value: float) -> str:
    return "warning" if value >= 1e-7 else "ok"


def _risk_severity(value: str) -> str:
    normalized = value.lower().replace("_", "-")
    if normalized in {"critical", "error", "high"}:
        return "critical"
    if normalized in {"warning", "warn", "medium", "watch", "stale"}:
        return "warning"
    if normalized in {"ok", "low", "controlled"}:
        return "ok"
    return "unknown"


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


def _inside_time_window(time: float, *, time_min: float | None, time_max: float | None) -> bool:
    if time_min is not None and time < time_min:
        return False
    if time_max is not None and time > time_max:
        return False
    return True
