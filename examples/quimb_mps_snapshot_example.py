"""Record quimb MPS snapshots as TNView run-log telemetry.

Install TNView with the quimb extra before running it:

    python -m pip install -e ".[quimb]"
    python examples/quimb_mps_snapshot_example.py

Then inspect the generated log:

    tnview tail runs/quimb_mps_snapshots.jsonl
"""

from __future__ import annotations

from pathlib import Path

from tnview import RunLogger
from tnview.adapters.quimb import emit_mps_snapshot


def main() -> int:
    try:
        import quimb.tensor as qtn
    except ImportError:
        print("quimb is not installed. Install with: python -m pip install -e '.[quimb]'")
        return 0

    output = Path("runs/quimb_mps_snapshots.jsonl")
    output.parent.mkdir(parents=True, exist_ok=True)

    with RunLogger(output, run_id="quimb-mps-snapshots") as log:
        log.emit("run_start", library="quimb", algorithm="mps_snapshot", sites=8)
        for step, bond_dim in enumerate([2, 4, 8], start=1):
            psi = qtn.MPS_rand_state(8, bond_dim, phys_dim=2)
            emit_mps_snapshot(log, psi, step=step, chi_max=8)
        log.emit("run_end", library="quimb", algorithm="mps_snapshot", status="complete")

    print(f"wrote {output}")
    print(f"try: tnview tail {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
