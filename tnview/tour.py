"""First-run onboarding copy for TNView."""

from __future__ import annotations


def render_tour() -> str:
    """Render a short product tour with runnable next steps."""

    return "\n".join(
        [
            "TNView tour",
            "",
            "Why this exists",
            "  Tensor-network runs often fail slowly: chi saturates, truncation stops",
            "  improving, memory creeps upward, or an optimizer plateaus after hours.",
            "  TNView records lightweight JSONL while the job runs, then turns that log",
            "  into a terminal cockpit you can inspect over SSH or replay after a crash.",
            "",
            "Start without any data",
            '  tnview sketch "mps sites=48 chi=128 profile=hard" --interactive',
            "  tnview sketch --wizard",
            "",
            "Watch a real or example run log",
            "  tnview watch examples/quimb_tnoptimizer_run.jsonl --max-refreshes 1 --no-clear",
            "  tnview diagnose examples/dmrg_bad_run.jsonl",
            "  tnview compare examples/dmrg_bad_run.jsonl examples/quimb_tnoptimizer_run.jsonl --sort risk",
            "",
            "Instrument your own code",
            "  tnview init emit_tnview.py",
            "  python emit_tnview.py",
            "  tnview watch runs/example.jsonl",
            "",
            "Mental model",
            "  RunLogger records events. watch shows the live state. diagnose explains",
            "  convergence trouble. replay/sketch make visual telemetry navigable.",
            "",
            "Next",
            "  tnview sketch --wizard",
            "  tnview examples",
            "  tnview doctor",
        ]
    )
