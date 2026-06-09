"""Programmatic telemetry writer for TNView JSONL streams."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any, TextIO


class Recorder:
    """Write TNView telemetry events as newline-delimited JSON.

    The recorder is intentionally small: simulation libraries keep ownership of
    physics objects and TNView records observable summaries for replay.
    """

    def __init__(self, path: str | Path | TextIO):
        self._target = path
        self._handle: TextIO | None = path if hasattr(path, "write") else None
        self._owns_handle = False

    def __enter__(self) -> Recorder:
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
        handle = self._require_handle()
        record = {"event": event, **payload}
        handle.write(json.dumps(record, separators=(",", ":")) + "\n")
        handle.flush()

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
