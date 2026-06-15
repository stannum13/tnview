"""Adapters for TeNPy-style sweep statistics.

The adapter is dependency-optional. It reads the ``sweep_stats`` dictionary
exposed by TeNPy DMRG engines and emits TNView run-log events.
"""

from __future__ import annotations

from typing import Any


def dmrg_sweep_record(
    engine: Any | None = None,
    *,
    stats: dict[str, Any] | None = None,
    library: str = "tenpy",
    algorithm: str = "dmrg",
    **extra: Any,
) -> dict[str, Any]:
    """Build a ``sweep_end`` event from TeNPy-like DMRG sweep statistics."""

    records = dmrg_sweep_records(engine, stats=stats, library=library, algorithm=algorithm, **extra)
    if not records:
        raise TypeError("TeNPy DMRG adapter needs at least one sweep statistic row")
    return records[-1]


def dmrg_sweep_records(
    engine: Any | None = None,
    *,
    stats: dict[str, Any] | None = None,
    library: str = "tenpy",
    algorithm: str = "dmrg",
    **extra: Any,
) -> list[dict[str, Any]]:
    """Build all available ``sweep_end`` events from TeNPy sweep statistics."""

    source = stats if stats is not None else getattr(engine, "sweep_stats", None)
    if not isinstance(source, dict):
        raise TypeError("TeNPy DMRG adapter needs a sweep_stats dictionary")

    rows = _stat_count(source)
    records: list[dict[str, Any]] = []
    for index in range(rows):
        record: dict[str, Any] = {
            "event": "sweep_end",
            "library": library,
            "algorithm": algorithm,
            "sweep": _stat_at(source, "sweep", index),
            "energy": _stat_at(source, "E", index),
            "delta_energy": _stat_at(source, "Delta_E", index),
            "entropy_mean": _stat_at(source, "S", index),
            "entropy_delta": _stat_at(source, "Delta_S", index),
            "entropy_max": _stat_at(source, "max_S", index),
            "wall_s": _stat_at(source, "time", index),
            "max_trunc_err": _stat_at(source, "max_trunc_err", index),
            "max_energy_trunc": _stat_at(source, "max_E_trunc", index),
            "max_chi": _stat_at(source, "max_chi", index),
            "canonical_error": _stat_at(source, "norm_err", index),
        }
        record.update(extra)
        records.append({key: value for key, value in record.items() if value is not None})
    return records


def emit_dmrg_sweep(logger: Any, engine: Any | None = None, *, stats: dict[str, Any] | None = None, **extra: Any) -> None:
    """Emit a TeNPy DMRG ``sweep_end`` event through a ``RunLogger``."""

    record = dmrg_sweep_record(engine, stats=stats, **extra)
    event = str(record.pop("event"))
    logger.emit(event, **record)


class DMRGObserver:
    """Small callable observer for TeNPy-style DMRG engines.

    Use this when code has an explicit hook after each sweep. The observer is
    intentionally duck-typed and can receive either an engine object with
    ``sweep_stats`` or a raw stats dictionary.
    """

    def __init__(self, logger: Any, *, library: str = "tenpy", algorithm: str = "dmrg"):
        self.logger = logger
        self.library = library
        self.algorithm = algorithm
        self._emitted_sweep_rows = 0

    def __call__(self, engine: Any | None = None, **kwargs: Any) -> None:
        self.sweep_end(engine, **kwargs)

    def sweep_end(self, engine: Any | None = None, *, stats: dict[str, Any] | None = None, **extra: Any) -> None:
        emit_dmrg_sweep(
            self.logger,
            engine,
            stats=stats,
            library=self.library,
            algorithm=self.algorithm,
            **extra,
        )

    def emit_new_sweeps(
        self,
        engine: Any | None = None,
        *,
        stats: dict[str, Any] | None = None,
        **extra: Any,
    ) -> int:
        """Emit sweep rows that have appeared since the previous call."""

        records = dmrg_sweep_records(
            engine,
            stats=stats,
            library=self.library,
            algorithm=self.algorithm,
            **extra,
        )
        if len(records) < self._emitted_sweep_rows:
            self._emitted_sweep_rows = 0

        emitted = 0
        for record in records[self._emitted_sweep_rows :]:
            event = str(record.pop("event"))
            self.logger.emit(event, **record)
            emitted += 1
        self._emitted_sweep_rows = len(records)
        return emitted


def _stat_count(stats: dict[str, Any]) -> int:
    lengths = [len(value) for value in stats.values() if isinstance(value, list | tuple)]
    if lengths:
        return max(lengths)
    return 1 if stats else 0


def _stat_at(stats: dict[str, Any], key: str, index: int) -> Any:
    value = stats.get(key)
    if isinstance(value, list | tuple):
        if index >= len(value):
            return None
        return _json_scalar(value[index])
    return _json_scalar(value)


def _json_scalar(value: Any) -> str | int | float | bool | None:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    item = getattr(value, "item", None)
    if callable(item):
        try:
            candidate = item()
        except (TypeError, ValueError):
            return None
        if isinstance(candidate, str | int | float | bool):
            return candidate
    return None
