"""Run a tiny quimb TNOptimizer job with TNView telemetry.

This example is dependency-optional. Install TNView with the quimb extra before
running it:

    python -m pip install -e ".[quimb]"
    python examples/quimb_tnoptimizer_example.py

Then inspect the generated log:

    tnview tail runs/quimb_tnoptimizer.jsonl
"""

from __future__ import annotations

from pathlib import Path

from tnview import RunLogger
from tnview.adapters.quimb import tnoptimizer_callback


def main() -> int:
    try:
        import quimb.tensor as qtn
    except ImportError:
        print("quimb is not installed. Install with: python -m pip install -e '.[quimb]'")
        return 0

    output = Path("runs/quimb_tnoptimizer.jsonl")
    output.parent.mkdir(parents=True, exist_ok=True)

    with RunLogger(output, run_id="quimb-tnoptimizer") as log:
        log.emit("run_start", library="quimb", algorithm="tnoptimizer", example="tiny-norm-minimize")
        tn = qtn.TN_rand_reg(4, 2, 2, seed=7)

        def loss_fn(candidate):
            return candidate.contract(all, optimize="auto-hq") ** 2

        opt = qtn.TNOptimizer(
            tn,
            loss_fn,
            optimizer="L-BFGS-B",
            progbar=False,
            callback=tnoptimizer_callback(log),
        )
        try:
            opt.optimize(8, jac=False)
        except Exception as exc:  # quimb autodiff/backend availability can vary.
            log.emit("error", library="quimb", algorithm="tnoptimizer", message=str(exc))
            raise
        finally:
            log.emit("run_end", library="quimb", algorithm="tnoptimizer", status="complete")

    print(f"wrote {output}")
    print(f"try: tnview tail {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
