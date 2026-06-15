"""Scriptable replay animation for visual telemetry."""

from __future__ import annotations

from dataclasses import dataclass

from tnview.events import Checkpoint, TelemetryEvent
from tnview.focus import choose_focus
from tnview.render import RenderOptions, render_run
from tnview.state import RunState


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
    body = render_run(
        state,
        RenderOptions(
            width=width,
            unicode=unicode,
            history_time_min=time_min,
            history_time_max=time_max,
        ),
    )
    header = (
        f"TNView oscilloscope frame {frame_number}/{frame_count} | "
        f"T={checkpoint.time:g}  window=[{time_min:g}, {time_max:g}]  checkpoint={checkpoint_index}"
    )
    return AnimationFrame(
        checkpoint_index=checkpoint_index,
        frame_number=frame_number,
        frame_count=frame_count,
        time=checkpoint.time,
        window_radius=window_radius,
        text=header + "\n" + body,
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
