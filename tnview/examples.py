"""Built-in example discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tnview.compare import summarize_run, summarize_run_log
from tnview.events import parse_jsonl
from tnview.runlog import RUN_LOG_EVENTS, read_jsonl_records
from tnview.state import reduce_events


@dataclass(frozen=True)
class ExampleReplay:
    path: Path
    name: str
    kind: str
    status: str
    events: int
    bonds: int
    checkpoints: int


def list_examples(root: Path | None = None) -> list[ExampleReplay]:
    base = root or Path("examples")
    examples: list[ExampleReplay] = []
    for path in sorted(base.glob("*.jsonl")):
        lines = path.read_text(encoding="utf-8").splitlines()
        raw = read_jsonl_records(lines)
        run_records = [record for record in raw.records if record.get("event") in RUN_LOG_EVENTS]
        if run_records:
            summary = summarize_run_log(str(path), run_records)
            examples.append(
                ExampleReplay(
                    path=path,
                    name=summary.name,
                    kind="run-log",
                    status=",".join(summary.diagnostics) if summary.diagnostics else "no warnings",
                    events=len(run_records),
                    bonds=0,
                    checkpoints=0,
                )
            )
            continue

        events = parse_jsonl(lines)
        state = reduce_events(events)
        summary = summarize_run(str(path), state)
        examples.append(
            ExampleReplay(
                path=path,
                name=summary.name,
                kind="replay",
                status=summary.status,
                events=len(events),
                bonds=len(state.bonds),
                checkpoints=len(state.checkpoints),
            )
        )
    return examples


def render_examples(examples: list[ExampleReplay]) -> str:
    lines = [
        "Built-in examples",
        "path                                      kind     events  bonds  checkpoints  status",
        "----------------------------------------  -------  ------  -----  -----------  ----------------",
    ]
    for example in examples:
        lines.append(
            f"{str(example.path):<40}  "
            f"{example.kind:<7}  "
            f"{example.events:<6}  "
            f"{example.bonds:<5}  "
            f"{example.checkpoints:<11}  "
            f"{example.status}"
        )
    if examples:
        replay_paths = " ".join(
            str(example.path)
            for example in examples
            if example.kind == "replay" and example.path.name != "tebd_run.jsonl"
        )
        run_log_paths = " ".join(str(example.path) for example in examples if example.kind == "run-log")
        if replay_paths:
            lines.extend(["", f"compare replay: tnview compare {replay_paths}"])
        if run_log_paths:
            lines.append(f"compare run logs: tnview compare {run_log_paths} --sort risk")
    return "\n".join(lines)
