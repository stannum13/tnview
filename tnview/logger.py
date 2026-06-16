"""Programmatic run logger for TNView JSONL streams."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json
from typing import Any, TextIO


LEGACY_REPLAY_EVENTS = {
    "run_started",
    "model_geometry",
    "ansatz_layout",
    "observable_updated",
    "bond_updated",
    "checkpoint",
    "tdvp_sweep",
    "contraction_path",
}


class RunLogger:
    """Write TNView telemetry events as newline-delimited JSON.

    The logger is intentionally small: simulation libraries keep ownership of
    physics objects and TNView records observable summaries for replay.
    """

    def __init__(
        self,
        path: str | Path | TextIO,
        *,
        run_id: str | None = None,
        schema_version: str = "0.1",
        flush: bool = True,
        strict: bool = False,
    ):
        self._target = path
        self._handle: TextIO | None = path if hasattr(path, "write") else None
        self._owns_handle = False
        self.run_id = run_id or "run"
        self.schema_version = schema_version
        self.flush = flush
        self.strict = strict

    def __enter__(self) -> RunLogger:
        self.open()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def open(self) -> None:
        if self._handle is not None:
            return
        try:
            path = Path(self._target)  # type: ignore[arg-type]
            path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = path.open("a", encoding="utf-8")
            self._owns_handle = True
        except Exception:
            if self.strict:
                raise

    def close(self) -> None:
        if self._handle is not None and self._owns_handle:
            self._handle.close()
        self._handle = None
        self._owns_handle = False

    def emit(self, event: str, **payload: Any) -> None:
        record = {"event": event, **payload}
        self.emit_record(record)

    def start(
        self,
        *,
        library: str | None = None,
        algorithm: str | None = None,
        model: str | None = None,
        sites: int | None = None,
        parameters: dict[str, Any] | None = None,
        tags: list[str] | tuple[str, ...] = (),
        **fields: Any,
    ) -> None:
        """Emit a run-log ``run_start`` event."""

        self.emit(
            "run_start",
            **_clean(
                {
                    "library": library,
                    "algorithm": algorithm,
                    "model": model,
                    "sites": sites,
                    "parameters": parameters,
                    "tags": list(tags),
                    **fields,
                }
            ),
        )

    def end(self, *, status: str = "complete", **fields: Any) -> None:
        """Emit a run-log ``run_end`` event."""

        self.emit("run_end", **_clean({"status": status, **fields}))

    def step_start(self, *, step: int, **fields: Any) -> None:
        """Emit a run-log ``step_start`` event."""

        self.emit("step_start", **_clean({"step": step, **fields}))

    def step(
        self,
        *,
        step: int,
        energy: float | None = None,
        delta_energy: float | None = None,
        loss: float | None = None,
        max_chi: int | None = None,
        chi_max: int | None = None,
        max_trunc_err: float | None = None,
        entropy_max: float | None = None,
        entropy_mean: float | None = None,
        wall_s: float | None = None,
        step_wall_s: float | None = None,
        rss_mb: float | None = None,
        status: str | None = None,
        **fields: Any,
    ) -> None:
        """Emit a run-log ``step_end`` event with canonical metric fields."""

        self.emit(
            "step_end",
            **_clean(
                {
                    "step": step,
                    "energy": energy,
                    "delta_energy": delta_energy,
                    "loss": loss,
                    "max_chi": max_chi,
                    "chi_max_configured": chi_max,
                    "max_trunc_err": max_trunc_err,
                    "entropy_max": entropy_max,
                    "entropy_mean": entropy_mean,
                    "wall_s": wall_s,
                    "step_wall_s": step_wall_s,
                    "rss_mb": rss_mb,
                    "status": status,
                    **fields,
                }
            ),
        )

    def sweep_start(self, *, sweep: int, **fields: Any) -> None:
        """Emit a run-log ``sweep_start`` event."""

        self.emit("sweep_start", **_clean({"sweep": sweep, **fields}))

    def sweep(
        self,
        *,
        sweep: int,
        energy: float | None = None,
        delta_energy: float | None = None,
        max_chi: int | None = None,
        chi_max: int | None = None,
        max_trunc_err: float | None = None,
        entropy_max: float | None = None,
        entropy_mean: float | None = None,
        wall_s: float | None = None,
        step_wall_s: float | None = None,
        rss_mb: float | None = None,
        status: str | None = None,
        **fields: Any,
    ) -> None:
        """Emit a run-log ``sweep_end`` event with canonical metric fields."""

        self.emit(
            "sweep_end",
            **_clean(
                {
                    "sweep": sweep,
                    "energy": energy,
                    "delta_energy": delta_energy,
                    "max_chi": max_chi,
                    "chi_max_configured": chi_max,
                    "max_trunc_err": max_trunc_err,
                    "entropy_max": entropy_max,
                    "entropy_mean": entropy_mean,
                    "wall_s": wall_s,
                    "step_wall_s": step_wall_s,
                    "rss_mb": rss_mb,
                    "status": status,
                    **fields,
                }
            ),
        )

    def dmrg_sweep(self, *, sweep: int, library: str | None = None, **fields: Any) -> None:
        """Emit a DMRG ``sweep_end`` event with algorithm metadata."""

        self.sweep(sweep=sweep, library=library, algorithm="dmrg", **fields)

    def tebd_step(self, *, step: int, library: str | None = None, **fields: Any) -> None:
        """Emit a TEBD ``step_end`` event with algorithm metadata."""

        self.step(step=step, library=library, algorithm="tebd", **fields)

    def optimizer_step(
        self,
        *,
        step: int,
        loss: float | None = None,
        loss_best: float | None = None,
        wall_s: float | None = None,
        step_wall_s: float | None = None,
        rss_mb: float | None = None,
        status: str | None = None,
        **fields: Any,
    ) -> None:
        """Emit a run-log ``optimizer_step`` event."""

        self.emit(
            "optimizer_step",
            **_clean(
                {
                    "step": step,
                    "loss": loss,
                    "loss_best": loss_best,
                    "wall_s": wall_s,
                    "step_wall_s": step_wall_s,
                    "rss_mb": rss_mb,
                    "status": status,
                    **fields,
                }
            ),
        )

    def observable(
        self,
        name: str,
        value: Any,
        *,
        site: int | None = None,
        bond: int | None = None,
        error: float | None = None,
        **fields: Any,
    ) -> None:
        """Emit a run-log ``observable`` event."""

        self.emit(
            "observable",
            **_clean({"name": name, "value": value, "site": site, "bond": bond, "error": error, **fields}),
        )

    def warning(self, code: str, message: str, **fields: Any) -> None:
        """Emit a run-log ``warning`` event."""

        self.emit("warning", **_clean({"code": code, "message": message, **fields}))

    def error(self, code: str, message: str, **fields: Any) -> None:
        """Emit a run-log ``error`` event."""

        self.emit("error", **_clean({"code": code, "message": message, **fields}))

    def diagnostic(self, code: str, message: str, *, severity: str = "info", **fields: Any) -> None:
        """Emit a run-log ``diagnostic`` event."""

        self.emit("diagnostic", **_clean({"code": code, "severity": severity, "message": message, **fields}))

    def heartbeat(self, **fields: Any) -> None:
        """Emit a run-log ``heartbeat`` event for long-running jobs."""

        self.emit("heartbeat", **_clean(fields))

    def emit_record(self, record: dict[str, Any]) -> None:
        try:
            handle = self._require_handle()
            if handle is None:
                return
            prepared = self._prepare_record(record)
            handle.write(json.dumps(prepared, separators=(",", ":")) + "\n")
            if self.flush:
                handle.flush()
        except Exception:
            if self.strict:
                raise

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

    def _prepare_record(self, record: dict[str, Any]) -> dict[str, Any]:
        prepared = dict(record)
        event = str(prepared.get("event", ""))
        timestamp = _utc_timestamp()
        prepared.setdefault("schema_version", self.schema_version)
        prepared.setdefault("run_id", self.run_id)
        prepared.setdefault("timestamp", timestamp)
        if "time" not in prepared and event not in LEGACY_REPLAY_EVENTS:
            prepared["time"] = timestamp
        return prepared

    def _require_handle(self) -> TextIO | None:
        if self._handle is None:
            self.open()
        return self._handle


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _clean(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if value is not None}
