"""Programmatic run logger for TNView JSONL streams."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any, TextIO


class RunLogger:
    """Write TNView telemetry events as newline-delimited JSON.

    The logger is intentionally small: simulation libraries keep ownership of
    physics objects and TNView records observable summaries for replay.
    """

    def __init__(self, path: str | Path | TextIO):
        self._target = path
        self._handle: TextIO | None = path if hasattr(path, "write") else None
        self._owns_handle = False

    def __enter__(self) -> RunLogger:
        self.open()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def open(self) -> None:
        if self._handle is not None:
            return
        self._handle = Path(self._target).open("w", encoding="utf-8")  # type: ignore[arg-type]
        self._owns_handle = True

    def close(self) -> None:
        if self._handle is not None and self._owns_handle:
            self._handle.close()
        self._handle = None
        self._owns_handle = False

    def emit(self, event: str, **payload: Any) -> None:
        record = {"event": event, **payload}
        self.emit_record(record)

    def emit_record(self, record: dict[str, Any]) -> None:
        handle = self._require_handle()
        handle.write(json.dumps(record, separators=(",", ":")) + "\n")
        handle.flush()

    def observe_mps(
        self,
        mps: Any,
        *,
        run_id: str = "mps",
        name: str | None = None,
        step: int = 0,
        time: float = 0.0,
        chi_max: int | None = None,
        include_setup: bool = False,
        include_checkpoint: bool = True,
    ) -> None:
        """Record a quimb-style MPS snapshot as TNView telemetry."""

        from tnview.adapters.quimb import mps_to_events

        events = mps_to_events(
            mps,
            run_id=run_id,
            name=name,
            step=step,
            time=time,
            chi_max=chi_max,
        )
        for event in events:
            if not include_setup and event["event"] in {"run_started", "model_geometry", "ansatz_layout"}:
                continue
            if not include_checkpoint and event["event"] == "checkpoint":
                continue
            self.emit_record(event)

    def run_started(
        self,
        *,
        run_id: str,
        time: float = 0.0,
        name: str | None = None,
        simulator: str | None = None,
        algorithm: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.emit(
            "run_started",
            run_id=run_id,
            time=time,
            name=name,
            simulator=simulator,
            algorithm=algorithm,
            parameters=parameters or {},
        )

    def model_geometry(
        self,
        *,
        step: int = 0,
        time: float = 0.0,
        name: str,
        sites: int | None,
        dimensions: list[int] | tuple[int, ...] = (),
        boundary: str | None = None,
        edges: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    ) -> None:
        self.emit(
            "model_geometry",
            step=step,
            time=time,
            name=name,
            sites=sites,
            dimensions=list(dimensions),
            boundary=boundary,
            edges=list(edges),
        )

    def ansatz_layout(
        self,
        *,
        step: int = 0,
        time: float = 0.0,
        ansatz: str,
        ordering: list[int] | tuple[int, ...] = (),
        tensors: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.emit(
            "ansatz_layout",
            step=step,
            time=time,
            ansatz=ansatz,
            ordering=list(ordering),
            tensors=list(tensors),
            parameters=parameters or {},
        )

    def bond_updated(
        self,
        *,
        step: int,
        time: float,
        layer: str,
        bond: int,
        site_left: int,
        site_right: int,
        entropy_before: float,
        entropy_after: float,
        chi_before: int,
        chi_after: int,
        chi_max: int,
        trunc_error: float,
        renyi2_before: float | None = None,
        renyi2_after: float | None = None,
        discarded_weight: float | None = None,
        walltime_ms: float | None = None,
        schmidt_values: list[float] | tuple[float, ...] = (),
        diagnostic_tags: list[str] | tuple[str, ...] = (),
    ) -> None:
        self.emit(
            "bond_updated",
            step=step,
            time=time,
            layer=layer,
            bond=bond,
            site_left=site_left,
            site_right=site_right,
            entropy_before=entropy_before,
            entropy_after=entropy_after,
            renyi2_before=renyi2_before,
            renyi2_after=renyi2_after,
            chi_before=chi_before,
            chi_after=chi_after,
            chi_max=chi_max,
            trunc_error=trunc_error,
            discarded_weight=discarded_weight,
            walltime_ms=walltime_ms,
            schmidt_values=list(schmidt_values),
            diagnostic_tags=list(diagnostic_tags),
        )

    def checkpoint(
        self,
        *,
        step: int,
        time: float,
        max_entropy: float | None = None,
        mean_entropy: float | None = None,
        max_chi: int | None = None,
        num_saturated_bonds: int | None = None,
        total_trunc_error: float | None = None,
        energy: float | None = None,
        energy_drift: float | None = None,
        norm: float | None = None,
        complexity_status: str | None = None,
    ) -> None:
        self.emit(
            "checkpoint",
            step=step,
            time=time,
            max_entropy=max_entropy,
            mean_entropy=mean_entropy,
            max_chi=max_chi,
            num_saturated_bonds=num_saturated_bonds,
            total_trunc_error=total_trunc_error,
            energy=energy,
            energy_drift=energy_drift,
            norm=norm,
            complexity_status=complexity_status,
        )

    def _require_handle(self) -> TextIO:
        if self._handle is None:
            self.open()
        assert self._handle is not None
        return self._handle
