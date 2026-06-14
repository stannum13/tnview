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

    source = stats if stats is not None else getattr(engine, "sweep_stats", None)
    if not isinstance(source, dict):
        raise TypeError("TeNPy DMRG adapter needs a sweep_stats dictionary")

    record: dict[str, Any] = {
        "event": "sweep_end",
        "library": library,
        "algorithm": algorithm,
        "sweep": _stat(source, "sweep"),
        "energy": _stat(source, "E"),
        "delta_energy": _stat(source, "Delta_E"),
        "entropy_mean": _stat(source, "S"),
        "entropy_delta": _stat(source, "Delta_S"),
        "entropy_max": _stat(source, "max_S"),
        "wall_s": _stat(source, "time"),
        "max_trunc_err": _stat(source, "max_trunc_err"),
        "max_energy_trunc": _stat(source, "max_E_trunc"),
        "max_chi": _stat(source, "max_chi"),
        "canonical_error": _stat(source, "norm_err"),
    }
    record.update(extra)
    return {key: value for key, value in record.items() if value is not None}


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


def _stat(stats: dict[str, Any], key: str) -> Any:
    value = stats.get(key)
    if isinstance(value, list | tuple):
        return _json_scalar(value[-1]) if value else None
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
