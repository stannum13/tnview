"""Runnable workflow recipes for TNView."""

from __future__ import annotations

from typing import Any


RECIPES = (
    {
        "name": "watch-run",
        "title": "Watch a run over SSH",
        "goal": "Attach to an append-only run-log file and see current metrics, pressure, and diagnostics.",
        "commands": (
            "tnview watch examples/quimb_tnoptimizer_run.jsonl --max-refreshes 1 --no-clear",
            "tnview tail examples/quimb_tnoptimizer_run.jsonl",
            "tnview diagnose examples/dmrg_bad_run.jsonl",
        ),
    },
    {
        "name": "compare-runs",
        "title": "Compare a baseline and candidate",
        "goal": "Sort run logs by risk and see diagnostic regressions between two jobs.",
        "commands": (
            "tnview compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --sort risk",
            "tnview compare examples/quimb_tnoptimizer_run.jsonl examples/dmrg_bad_run.jsonl --diagnostics",
        ),
    },
    {
        "name": "oscilloscope",
        "title": "Inspect moving replay signals",
        "goal": "View entanglement, chi, truncation, and event ticks around a time window.",
        "commands": (
            "tnview scope examples/moving_front.jsonl --signal front --ascii",
            "tnview scope examples/truncation_spike.jsonl --signal trunc --ascii",
            "tnview animate examples/tebd_run.jsonl --frames 3 --window 0.3 --signal selected --ascii",
        ),
    },
    {
        "name": "build-sketch",
        "title": "Build a synthetic tensor-network replay",
        "goal": "Generate a promptable MPS sketch when you do not have simulation output yet.",
        "commands": (
            "tnview sketch --wizard",
            'tnview sketch "mps sites=48 chi=128 profile=front" --interactive',
            'tnview sketch "mps sites=32 chi=128 profile=spike" --json',
        ),
    },
)


def render_recipes() -> str:
    """Render a compact human-readable recipe list."""

    lines = ["TNView recipes"]
    for recipe in RECIPES:
        lines.extend(["", f"{recipe['title']} ({recipe['name']})", f"  {recipe['goal']}"])
        lines.extend(f"  {command}" for command in recipe["commands"])
    return "\n".join(lines)


def recipes_payload() -> dict[str, Any]:
    """Return stable machine-readable recipe data."""

    return {
        "kind": "recipes",
        "recipes": [
            {
                "name": str(recipe["name"]),
                "title": str(recipe["title"]),
                "goal": str(recipe["goal"]),
                "commands": list(recipe["commands"]),
            }
            for recipe in RECIPES
        ],
    }
