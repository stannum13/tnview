"""Command-level actions shared by CLI renderers."""

from __future__ import annotations

from typing import Iterable

from tnview.cli_output import CliError, CommandResult
from tnview.diagnose import diagnose_events, render_diagnostics
from tnview.runlog import read_jsonl_records


def diagnose_run_log(lines: Iterable[str], *, path: str) -> CommandResult:
    report = read_jsonl_records(lines)
    if report.errors:
        raise CliError(
            code="RUN_LOG_PARSE_ERROR",
            message="Could not read run log",
            path=path,
            reason="; ".join(report.errors),
            suggestions=(
                f"tnview validate {path}",
                f"tnview diagnose {path} --json",
            ),
            exit_code=2,
        )

    records = list(report.records)
    diagnostics = diagnose_events(records)
    return CommandResult(
        ok=not diagnostics,
        text=render_diagnostics(diagnostics),
        data={
            "diagnostics": [
                {
                    "code": diagnostic.code,
                    "severity": diagnostic.severity,
                    "message": diagnostic.message,
                    "evidence": diagnostic.evidence,
                }
                for diagnostic in diagnostics
            ],
            "event_count": len(records),
            "warning_count": sum(1 for diagnostic in diagnostics if diagnostic.severity == "warn"),
            "error_count": sum(1 for diagnostic in diagnostics if diagnostic.severity == "error"),
        },
        exit_code=0,
    )
