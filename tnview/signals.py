"""Signal extraction for visual replay telemetry."""

from __future__ import annotations

from dataclasses import dataclass

from tnview.events import Checkpoint, TelemetryEvent
from tnview.state import RunState, TimeSlice, reduce_events


@dataclass(frozen=True)
class SignalPoint:
    """One checkpoint-aligned point in a replay signal timeline."""

    step: int
    time: float
    entropy_max: float
    entropy_mean: float
    max_chi: int
    max_trunc_error: float
    total_trunc_error: float
    front_span: int
    front_bonds: tuple[int, ...]
    saturated_bonds: int | None = None
    energy: float | None = None
    energy_drift: float | None = None
    complexity_status: str | None = None
    selected_bond: int | None = None
    selected_entropy: float | None = None
    selected_chi: int | None = None
    selected_trunc_error: float | None = None


@dataclass(frozen=True)
class SignalMarker:
    """A compact event marker derived from replay signal dynamics."""

    index: int
    step: int
    time: float
    code: str
    severity: str
    message: str


def signal_points(
    state: RunState,
    *,
    selected_bond: int | None = None,
    time_min: float | None = None,
    time_max: float | None = None,
) -> list[SignalPoint]:
    """Extract checkpoint-aligned signal points from a reduced replay state."""

    selected = selected_bond if selected_bond is not None else state.selected_bond
    return [
        _point_from_slice(row, checkpoint=checkpoint, selected_bond=selected)
        for row, checkpoint in zip(state.history, state.checkpoints)
        if _inside_time_window(row.time, time_min=time_min, time_max=time_max)
    ]


def signal_points_from_events(
    events: list[TelemetryEvent],
    *,
    checkpoint_index: int | None = None,
    selected_bond: int | None = None,
    time_min: float | None = None,
    time_max: float | None = None,
) -> list[SignalPoint]:
    """Reduce events and extract replay signal points."""

    state = _state_at_checkpoint(events, checkpoint_index)
    return signal_points(state, selected_bond=selected_bond, time_min=time_min, time_max=time_max)


def signal_series(points: list[SignalPoint], name: str) -> list[float]:
    """Return a numeric series by stable signal name."""

    if name == "entropy":
        return [point.entropy_max for point in points]
    if name == "chi":
        return [float(point.max_chi) for point in points]
    if name == "trunc":
        return [point.max_trunc_error for point in points]
    if name == "front":
        return [float(point.front_span) for point in points]
    if name == "selected_entropy":
        return [point.selected_entropy for point in points if point.selected_entropy is not None]
    if name == "selected_chi":
        return [float(point.selected_chi) for point in points if point.selected_chi is not None]
    if name == "selected_trunc":
        return [point.selected_trunc_error for point in points if point.selected_trunc_error is not None]
    raise ValueError(f"unknown signal {name!r}")


def signal_payload(points: list[SignalPoint]) -> dict[str, object]:
    """Return a stable JSON-serializable signal payload."""

    return {
        "points": [
            {
                "step": point.step,
                "time": point.time,
                "entropy_max": point.entropy_max,
                "entropy_mean": point.entropy_mean,
                "max_chi": point.max_chi,
                "max_trunc_error": point.max_trunc_error,
                "total_trunc_error": point.total_trunc_error,
                "front_span": point.front_span,
                "front_bonds": list(point.front_bonds),
                "saturated_bonds": point.saturated_bonds,
                "energy": point.energy,
                "energy_drift": point.energy_drift,
                "complexity_status": point.complexity_status,
                "selected_bond": point.selected_bond,
                "selected_entropy": point.selected_entropy,
                "selected_chi": point.selected_chi,
                "selected_trunc_error": point.selected_trunc_error,
            }
            for point in points
        ]
    }


def detect_signal_markers(
    points: list[SignalPoint],
    *,
    truncation_floor: float = 1e-7,
    truncation_spike_factor: float = 10.0,
) -> list[SignalMarker]:
    """Detect compact oscilloscope markers from a signal timeline."""

    markers: list[SignalMarker] = []
    for index, point in enumerate(points):
        markers.append(
            SignalMarker(
                index=index,
                step=point.step,
                time=point.time,
                code="checkpoint",
                severity="info",
                message=f"checkpoint step {point.step}",
            )
        )
        if point.saturated_bonds and point.saturated_bonds > 0:
            markers.append(
                SignalMarker(
                    index=index,
                    step=point.step,
                    time=point.time,
                    code="chi_saturation",
                    severity="warning",
                    message=f"{point.saturated_bonds} saturated bond(s)",
                )
            )
        if _is_truncation_spike(points, index, floor=truncation_floor, factor=truncation_spike_factor):
            markers.append(
                SignalMarker(
                    index=index,
                    step=point.step,
                    time=point.time,
                    code="truncation_spike",
                    severity="warning",
                    message=f"truncation spike {_format_float(point.max_trunc_error)}",
                )
            )
        if index > 0 and point.front_span > points[index - 1].front_span:
            markers.append(
                SignalMarker(
                    index=index,
                    step=point.step,
                    time=point.time,
                    code="front_growth",
                    severity="info",
                    message=f"front span {points[index - 1].front_span}->{point.front_span}",
                )
            )
        if (
            point.selected_bond is not None
            and point.selected_chi is not None
            and point.max_chi > 0
            and point.selected_chi >= point.max_chi
        ):
            markers.append(
                SignalMarker(
                    index=index,
                    step=point.step,
                    time=point.time,
                    code="selected_pressure",
                    severity="warning",
                    message=f"selected b{point.selected_bond} at max chi",
                )
            )
    return markers


def _state_at_checkpoint(events: list[TelemetryEvent], checkpoint_index: int | None) -> RunState:
    if checkpoint_index is None:
        return reduce_events(events)
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


def _point_from_slice(row: TimeSlice, *, checkpoint: Checkpoint, selected_bond: int | None) -> SignalPoint:
    entropies = list(row.entropy_by_bond.values())
    trunc_errors = list(row.trunc_by_bond.values())
    front_bonds = _front_bonds(row)
    return SignalPoint(
        step=row.step,
        time=row.time,
        entropy_max=max(entropies, default=0.0),
        entropy_mean=sum(entropies) / len(entropies) if entropies else 0.0,
        max_chi=max(row.chi_by_bond.values(), default=0),
        max_trunc_error=max(trunc_errors, default=0.0),
        total_trunc_error=sum(trunc_errors),
        front_span=_bond_span(front_bonds),
        front_bonds=front_bonds,
        saturated_bonds=checkpoint.num_saturated_bonds,
        energy=checkpoint.energy,
        energy_drift=checkpoint.energy_drift,
        complexity_status=checkpoint.complexity_status,
        selected_bond=selected_bond,
        selected_entropy=row.entropy_by_bond.get(selected_bond) if selected_bond is not None else None,
        selected_chi=row.chi_by_bond.get(selected_bond) if selected_bond is not None else None,
        selected_trunc_error=row.trunc_by_bond.get(selected_bond) if selected_bond is not None else None,
    )


def _front_bonds(row: TimeSlice) -> tuple[int, ...]:
    max_entropy = max(row.entropy_by_bond.values(), default=0.0)
    if max_entropy <= 0:
        return ()
    threshold = 0.5 * max_entropy
    return tuple(sorted(bond for bond, entropy in row.entropy_by_bond.items() if entropy >= threshold))


def _bond_span(bonds: tuple[int, ...]) -> int:
    if not bonds:
        return 0
    return max(bonds) - min(bonds) + 1


def _inside_time_window(time: float, *, time_min: float | None, time_max: float | None) -> bool:
    if time_min is not None and time < time_min:
        return False
    if time_max is not None and time > time_max:
        return False
    return True


def _is_truncation_spike(points: list[SignalPoint], index: int, *, floor: float, factor: float) -> bool:
    value = points[index].max_trunc_error
    if value <= 0:
        return False
    if value >= floor:
        return True
    if index == 0:
        return False
    previous = points[index - 1].max_trunc_error
    if previous <= 0:
        return False
    return value >= previous * factor


def _format_float(value: float) -> str:
    if abs(value) >= 1e4 or (0 < abs(value) < 1e-3):
        return f"{value:.2e}"
    return f"{value:.4g}"
