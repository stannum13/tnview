#!/usr/bin/env python3
"""Render public TNView demo SVGs from real CLI output."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from html import escape
from pathlib import Path
import subprocess
import sys
import textwrap


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DemoCard:
    filename: str
    title: str
    command: tuple[str, ...]
    width: int
    max_lines: int


CARDS = (
    DemoCard(
        filename="demo-instrument.svg",
        title="Generated MPS/TEBD instrument",
        command=(
            "demo",
            "--sites",
            "20",
            "--checkpoints",
            "5",
            "--chi-max",
            "64",
            "--width",
            "92",
            "--no-color",
        ),
        width=92,
        max_lines=54,
    ),
    DemoCard(
        filename="watch-dashboard.svg",
        title="Live optimizer watch dashboard",
        command=(
            "watch",
            "examples/quimb_tnoptimizer_run.jsonl",
            "--max-refreshes",
            "1",
            "--no-clear",
            "--width",
            "92",
            "--no-color",
        ),
        width=92,
        max_lines=34,
    ),
    DemoCard(
        filename="diagnostics.svg",
        title="Run diagnostics with recovery hints",
        command=("diagnose", "examples/dmrg_bad_run.jsonl"),
        width=116,
        max_lines=30,
    ),
    DemoCard(
        filename="compare-runs.svg",
        title="Baseline vs candidate diagnostics",
        command=(
            "compare",
            "examples/quimb_tnoptimizer_run.jsonl",
            "examples/dmrg_bad_run.jsonl",
            "--diagnostics",
            "--width",
            "116",
        ),
        width=116,
        max_lines=16,
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="docs/demo", help="directory for generated SVG cards")
    parser.add_argument("--python", default=sys.executable, help="Python executable used to run tnview")
    args = parser.parse_args()

    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    for card in CARDS:
        output = _run_tnview(card.command, python=args.python)
        svg = _render_svg(card, output)
        path = output_dir / card.filename
        path.write_text(svg, encoding="utf-8")
        print(f"wrote {_display_path(path)}")

    return 0


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _run_tnview(command: tuple[str, ...], *, python: str) -> str:
    result = subprocess.run(
        [python, "-m", "tnview.cli", *command],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.rstrip()


def _render_svg(card: DemoCard, output: str) -> str:
    lines = output.splitlines()[: card.max_lines]
    if len(output.splitlines()) > card.max_lines:
        lines.append("...")
    command = "tnview " + " ".join(card.command)
    char_width = 8.6
    line_height = 18
    padding_x = 24
    top = 58
    command_top = 88
    body_top = 122
    body_width = int(card.width * char_width)
    width = body_width + padding_x * 2
    height = body_top + max(1, len(lines)) * line_height + 28
    clip_id = card.filename.replace(".", "-")

    text_rows = []
    for index, line in enumerate(lines):
        y = body_top + index * line_height
        text_rows.append(f'<text x="{padding_x}" y="{y}">{escape(line)}</text>')

    return textwrap.dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
          <title id="title">{escape(card.title)}</title>
          <desc id="desc">Terminal screenshot generated from: {escape(command)}</desc>
          <defs>
            <linearGradient id="bg-{clip_id}" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0%" stop-color="#071014"/>
              <stop offset="55%" stop-color="#0f1720"/>
              <stop offset="100%" stop-color="#15151e"/>
            </linearGradient>
            <clipPath id="clip-{clip_id}">
              <rect x="0" y="0" width="{width}" height="{height}" rx="14"/>
            </clipPath>
          </defs>
          <g clip-path="url(#clip-{clip_id})">
            <rect width="{width}" height="{height}" fill="url(#bg-{clip_id})"/>
            <rect x="0" y="0" width="{width}" height="40" fill="#111827"/>
            <circle cx="24" cy="20" r="6" fill="#ff5f57"/>
            <circle cx="44" cy="20" r="6" fill="#ffbd2e"/>
            <circle cx="64" cy="20" r="6" fill="#28c840"/>
            <text x="86" y="25" fill="#d8dee9" font-family="Menlo, Consolas, monospace" font-size="13">{escape(card.title)}</text>
            <rect x="{padding_x - 10}" y="{top}" width="{body_width + 20}" height="42" rx="8" fill="#101820" stroke="#243241"/>
            <text x="{padding_x}" y="{command_top}" fill="#8bd5ca" font-family="Menlo, Consolas, monospace" font-size="13">$ {escape(command)}</text>
            <g fill="#d8dee9" font-family="Menlo, Consolas, monospace" font-size="13">
              {''.join(text_rows)}
            </g>
          </g>
        </svg>
        """
    )


if __name__ == "__main__":
    raise SystemExit(main())
