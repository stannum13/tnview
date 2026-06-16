"""First-run onboarding copy for TNView."""

from __future__ import annotations


TOUR_STEPS = (
    {
        "name": "try_without_data",
        "title": "Start without any data",
        "commands": (
            'tnview sketch "mps sites=48 chi=128 profile=hard" --interactive',
            "tnview sketch --wizard",
            "tnview scope examples/tebd_run.jsonl --center-time 0.8 --window 0.3 --bond 1 --ascii",
            "tnview animate examples/tebd_run.jsonl --frames 3 --window 0.3 --no-clear --ascii",
        ),
    },
    {
        "name": "watch_run",
        "title": "Watch a real or example run log",
        "commands": (
            "tnview watch examples/quimb_tnoptimizer_run.jsonl --max-refreshes 1 --no-clear",
            "tnview diagnose examples/dmrg_bad_run.jsonl",
            "tnview compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --sort risk",
            "tnview compare examples/quimb_tnoptimizer_run.jsonl examples/dmrg_bad_run.jsonl --diagnostics",
        ),
    },
    {
        "name": "instrument_code",
        "title": "Instrument your own code",
        "commands": (
            "tnview init emit_tnview.py",
            "python emit_tnview.py",
            "tnview watch runs/example.jsonl",
        ),
    },
)


def render_tour() -> str:
    """Render a short product tour with runnable next steps."""

    lines = [
        "TNView tour",
        "",
        "Why this exists",
        "  Tensor-network runs often fail slowly: chi saturates, truncation stops",
        "  improving, memory creeps upward, or an optimizer plateaus after hours.",
        "  TNView records lightweight JSONL while the job runs, then turns that log",
        "  into a terminal cockpit you can inspect over SSH or replay after a crash.",
        "",
        "Choose your path",
    ]
    for step in TOUR_STEPS:
        lines.extend(["", str(step["title"])])
        lines.extend(f"  {command}" for command in step["commands"])

    lines.extend(
        [
            "",
            "Mental model",
            "  RunLogger records events. watch shows the live state. diagnose explains",
            "  convergence trouble. replay/sketch make visual telemetry navigable.",
            "  scope shows a static oscilloscope around a chosen time window.",
            "  animate turns replay heatmaps into a moving oscilloscope window.",
            "",
            "Next",
            "  tnview sketch --wizard",
            "  tnview recipes",
            "  tnview examples",
            "  tnview doctor",
        ]
    )
    return "\n".join(lines)


def tour_payload() -> dict[str, object]:
    """Return stable first-run tour data for scripts and docs checks."""

    return {
        "kind": "tour",
        "purpose": "terminal-first black-box recorder for tensor-network runs",
        "steps": [
            {
                "name": str(step["name"]),
                "title": str(step["title"]),
                "commands": list(step["commands"]),
            }
            for step in TOUR_STEPS
        ],
    }
