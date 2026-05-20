"""State reducer and diagnostics for tensor-network telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field

from tnview.events import BondUpdated, Checkpoint, TdvpSweep, TelemetryEvent


@dataclass
class BondState:
    bond: int
    site_left: int
    site_right: int
    entropy: float = 0.0
    renyi2: float | None = None
    chi: int = 1
    chi_max: int = 1
    trunc_error: float = 0.0
    discarded_weight: float | None = None
    walltime_ms: float | None = None
    schmidt_values: tuple[float, ...] = field(default_factory=tuple)
    last_step: int = 0
    last_time: float = 0.0
    diagnostic_tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def chi_pressure(self) -> float:
        if self.chi_max <= 0:
            return 0.0
        return min(1.0, self.chi / self.chi_max)

    @property
    def saturated(self) -> bool:
        return self.chi_max > 0 and self.chi >= self.chi_max


@dataclass
class TimeSlice:
    step: int
    time: float
    entropy_by_bond: dict[int, float]
    chi_by_bond: dict[int, int]
    trunc_by_bond: dict[int, float]


@dataclass
class RunState:
    bonds: dict[int, BondState] = field(default_factory=dict)
    checkpoints: list[Checkpoint] = field(default_factory=list)
    updates: list[BondUpdated] = field(default_factory=list)
    sweeps: list[TdvpSweep] = field(default_factory=list)
    history: list[TimeSlice] = field(default_factory=list)
    selected_bond: int | None = None

    def apply(self, event: TelemetryEvent) -> None:
        if isinstance(event, BondUpdated):
            self._apply_bond_update(event)
        elif isinstance(event, Checkpoint):
            self.checkpoints.append(event)
            self._capture_history(event.step, event.time)
        elif isinstance(event, TdvpSweep):
            self.sweeps.append(event)

    def _apply_bond_update(self, event: BondUpdated) -> None:
        self.updates.append(event)
        self.bonds[event.bond] = BondState(
            bond=event.bond,
            site_left=event.site_left,
            site_right=event.site_right,
            entropy=event.entropy_after,
            renyi2=event.renyi2_after,
            chi=event.chi_after,
            chi_max=event.chi_max,
            trunc_error=event.trunc_error,
            discarded_weight=event.discarded_weight,
            walltime_ms=event.walltime_ms,
            schmidt_values=event.schmidt_values,
            last_step=event.step,
            last_time=event.time,
            diagnostic_tags=event.diagnostic_tags,
        )
        if self.selected_bond is None:
            self.selected_bond = event.bond

    def _capture_history(self, step: int, time: float) -> None:
        self.history.append(
            TimeSlice(
                step=step,
                time=time,
                entropy_by_bond={bond: state.entropy for bond, state in self.bonds.items()},
                chi_by_bond={bond: state.chi for bond, state in self.bonds.items()},
                trunc_by_bond={bond: state.trunc_error for bond, state in self.bonds.items()},
            )
        )

    @property
    def ordered_bonds(self) -> list[BondState]:
        return [self.bonds[key] for key in sorted(self.bonds)]

    @property
    def selected(self) -> BondState | None:
        if self.selected_bond is None:
            return None
        return self.bonds.get(self.selected_bond)

    @property
    def latest_checkpoint(self) -> Checkpoint | None:
        if not self.checkpoints:
            return None
        return self.checkpoints[-1]

    def select_bond(self, bond: int) -> bool:
        if bond not in self.bonds:
            return False
        self.selected_bond = bond
        return True


def reduce_events(events: list[TelemetryEvent]) -> RunState:
    state = RunState()
    for event in events:
        state.apply(event)
    return state


def diagnose_bond(bond: BondState) -> str:
    if bond.saturated and bond.trunc_error >= 1e-7:
        return "chi-limited local bottleneck"
    if bond.saturated and bond.entropy >= 2.0:
        return "chi-limited local bottleneck"
    if bond.saturated:
        return "chi pressure"
    if bond.trunc_error >= 1e-6:
        return "truncation-dominated local error"
    if bond.entropy < 0.1:
        return "trivial local dynamics"
    return "healthy local growth"


def diagnose_run(state: RunState) -> str:
    bonds = state.ordered_bonds
    if not bonds:
        return "waiting for telemetry"

    saturated = [bond for bond in bonds if bond.saturated]
    high_trunc = [bond for bond in bonds if bond.trunc_error >= 1e-7]
    entropies = [bond.entropy for bond in bonds]
    broad_growth = sum(1 for entropy in entropies if entropy >= 0.5 * max(entropies)) >= max(3, len(entropies) // 2)

    if saturated and (high_trunc or max(entropies) >= 2.0):
        return "chi-limited run"
    if high_trunc:
        return "truncation-dominated run"
    if broad_growth and max(entropies) >= 2.0:
        return "volume-law onset"
    if max(entropies) < 0.1:
        return "trivial dynamics"
    return "healthy growth"


def top_truncation_bonds(state: RunState, *, limit: int = 3) -> list[BondState]:
    return sorted(state.ordered_bonds, key=lambda bond: bond.trunc_error, reverse=True)[:limit]


@dataclass(frozen=True)
class EntanglementFront:
    threshold: float
    active_bonds: tuple[int, ...]
    span: int
    velocity_bonds_per_time: float | None


def entanglement_front(state: RunState, *, threshold_fraction: float = 0.5) -> EntanglementFront | None:
    if not state.history:
        return None

    latest = state.history[-1]
    max_entropy = max(latest.entropy_by_bond.values(), default=0.0)
    if max_entropy <= 0:
        return EntanglementFront(threshold=0.0, active_bonds=(), span=0, velocity_bonds_per_time=None)

    threshold = max_entropy * threshold_fraction
    active = tuple(sorted(bond for bond, entropy in latest.entropy_by_bond.items() if entropy >= threshold))
    span = _bond_span(active)
    velocity = _front_velocity(state, threshold)
    return EntanglementFront(
        threshold=threshold,
        active_bonds=active,
        span=span,
        velocity_bonds_per_time=velocity,
    )


def _front_velocity(state: RunState, threshold: float) -> float | None:
    if len(state.history) < 2:
        return None

    previous = state.history[-2]
    latest = state.history[-1]
    dt = latest.time - previous.time
    if dt <= 0:
        return None

    previous_active = tuple(
        sorted(bond for bond, entropy in previous.entropy_by_bond.items() if entropy >= threshold)
    )
    latest_active = tuple(sorted(bond for bond, entropy in latest.entropy_by_bond.items() if entropy >= threshold))
    return (_bond_span(latest_active) - _bond_span(previous_active)) / dt


def _bond_span(active_bonds: tuple[int, ...]) -> int:
    if not active_bonds:
        return 0
    return max(active_bonds) - min(active_bonds) + 1
