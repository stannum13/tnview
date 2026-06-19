#!/usr/bin/env python3
"""Review generated TNView UI snapshots for obvious terminal UX regressions."""

from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

EXPECTED = {
    "instrument.txt": {
        "width": 100,
        "required": ("STATUS", "SIGNALS", "MOTION", "FOCUS", "MPS topology", "Complexity rows"),
        "forbidden": ("Selected bond b",),
    },
    "instrument-ascii-80.txt": {
        "width": 80,
        "required": ("STATUS", "SIGNALS", "MOTION", "FOCUS", "MPS topology", "Complexity rows"),
        "forbidden": ("Selected bond b",),
    },
    "replay-focus.txt": {
        "width": 100,
        "required": ("MPS topology", "Entanglement heatmap", "Complexity rows", "Selected bond"),
        "forbidden": (),
    },
    "demo.txt": {
        "width": 100,
        "required": ("TNView demo", "MPS topology", "Entanglement heatmap", "Complexity rows"),
        "forbidden": (),
    },
    "runlog-watch.txt": {
        "width": 100,
        "required": ("TNView watch", "Run", "Signals", "Recent events"),
        "forbidden": (),
    },
    "runlog-tail.txt": {
        "width": 100,
        "required": ("TNView run tail", "Current:", "Diagnostics:", "Pressure:"),
        "forbidden": (),
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_dir", nargs="?", default=".artifacts/ui")
    parser.add_argument("--output", default=".artifacts/ui/review.txt")
    args = parser.parse_args()

    snapshot_dir = Path(args.snapshot_dir)
    output = Path(args.output)
    findings: list[str] = []
    summaries: list[str] = []

    for name, spec in EXPECTED.items():
        path = snapshot_dir / name
        if not path.exists():
            findings.append(f"ERROR {name}: snapshot is missing")
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        visible_lines = [_strip_ansi(line) for line in lines]
        body_lines = [line for line in visible_lines if not line.startswith("$ ")]
        max_width = max((_display_width(line) for line in body_lines), default=0)
        blank_runs = _max_blank_run(lines)
        summaries.append(f"{name}: {len(lines)} lines, max visible width {max_width}, blank run {blank_runs}")

        for required in spec["required"]:
            if required not in text:
                findings.append(f"ERROR {name}: missing required landmark {required!r}")
        for forbidden in spec["forbidden"]:
            if forbidden in text:
                findings.append(f"WARN {name}: duplicate or noisy landmark {forbidden!r}")
        if max_width > int(spec["width"]):
            findings.append(f"WARN {name}: body line width {max_width} exceeds target {spec['width']}")
        if blank_runs >= 4:
            findings.append(f"WARN {name}: has {blank_runs} consecutive blank lines")
        if any(line.endswith("~") or line.endswith("…") for line in visible_lines):
            findings.append(f"WARN {name}: contains fitted/truncated line endings")

    report = _render_report(summaries, findings)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report, end="")
    return 1 if any(finding.startswith("ERROR") for finding in findings) else 0


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def _display_width(text: str) -> int:
    width = 0
    for char in text:
        if unicodedata.combining(char):
            continue
        if unicodedata.category(char) in {"Cc", "Cf"}:
            continue
        width += 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
    return width


def _max_blank_run(lines: list[str]) -> int:
    longest = 0
    current = 0
    for line in lines:
        if line.strip():
            longest = max(longest, current)
            current = 0
        else:
            current += 1
    return max(longest, current)


def _render_report(summaries: list[str], findings: list[str]) -> str:
    lines = ["TNView UI snapshot review", "", "Snapshots"]
    lines.extend(f"  {summary}" for summary in summaries)
    lines.append("")
    lines.append("Findings")
    if findings:
        lines.extend(f"  {finding}" for finding in findings)
    else:
        lines.append("  OK no blocking snapshot issues found")
    lines.append("")
    lines.append("Next")
    lines.append("  Inspect .artifacts/ui/*.txt for qualitative spacing, hierarchy, and tone.")
    lines.append("  Iterate in a ui/* worktree, then integrate the best small slice into main.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
