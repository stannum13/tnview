#!/usr/bin/env python
"""Measure basic RunLogger write overhead for E001 smoke checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from tnview import RunLogger


def measure(events: int, output: str | None = None) -> dict[str, float | int | str]:
    if events <= 0:
        raise ValueError("--events must be positive")

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "logger-overhead.jsonl"
        started = perf_counter()
        with RunLogger(path, run_id="e001-overhead-smoke") as logger:
            logger.start(library="tnview", algorithm="logger_overhead", sites=0)
            for step in range(events):
                logger.step(
                    step=step,
                    loss=1.0 / (step + 1),
                    delta_energy=1e-9,
                    max_chi=64,
                    chi_max=128,
                    max_trunc_err=1e-8,
                )
            logger.end(status="complete")
        elapsed_s = max(perf_counter() - started, 1e-12)
        bytes_written = path.stat().st_size

    result: dict[str, float | int | str] = {
        "schema_version": 1,
        "events_requested": events,
        "records_written": events + 2,
        "elapsed_s": elapsed_s,
        "events_per_second": events / elapsed_s,
        "microseconds_per_event": elapsed_s * 1_000_000 / events,
        "bytes_written": bytes_written,
        "note": "smoke measurement; not canonical overhead evidence",
    }
    if output:
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, default=1000)
    parser.add_argument("--output")
    args = parser.parse_args()
    print(json.dumps(measure(args.events, args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
