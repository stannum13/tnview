"""Built-in replay example discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tnview.events import parse_jsonl
from tnview.compare import summarize_run
from tnview.state import reduce_events


@dataclass(frozen=True)
class ExampleReplay:
    path: Path
    name: str
    status: str
    bonds: int
    checkpoints: int


def list_examples(root: Path | None = None) -> list[ExampleReplay]:
    base = root or Path("examples")
    examples: list[ExampleReplay] = []
    for path in sorted(base.glob("*.jsonl")):
        events = parse_jsonl(path.read_text(encoding="utf-8").splitlines())
        state = reduce_events(events)
        summary = summarize_run(str(path), state)
        examples.append(
            ExampleReplay(
                path=path,
                name=summary.name,
                status=summary.status,
                bonds=len(state.bonds),
                checkpoints=len(state.checkpoints),
            )
        )
    return examples


def render_examples(examples: list[ExampleReplay]) -> str:
    lines = [
        "Built-in replay examples",
        "path                                      bonds  checkpoints  status",
        "----------------------------------------  -----  -----------  ----------------",
    ]
    for example in examples:
        lines.append(
            f"{str(example.path):<40}  "
            f"{example.bonds:<5}  "
            f"{example.checkpoints:<11}  "
            f"{example.status}"
        )
    if examples:
        paths = " ".join(str(example.path) for example in examples if example.path.name != "tebd_run.jsonl")
        lines.extend(["", f"compare: tnview compare {paths}"])
    return "\n".join(lines)
