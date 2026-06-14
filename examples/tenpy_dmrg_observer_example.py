"""Sketch a TeNPy DMRG run with TNView sweep telemetry.

This script is dependency-optional. It exits cleanly if TeNPy is not installed,
but shows the integration point used by real DMRG workflows.
"""

from __future__ import annotations

from pathlib import Path

from tnview import RunLogger
from tnview.adapters.tenpy import DMRGObserver


def main() -> int:
    try:
        from tenpy.algorithms import dmrg
        from tenpy.models.tf_ising import TFIChain
        from tenpy.networks.mps import MPS
    except ImportError:
        print("TeNPy is not installed. See https://tenpy.readthedocs.io/ for installation instructions.")
        return 0

    output = Path("runs/tenpy_dmrg.jsonl")
    output.parent.mkdir(parents=True, exist_ok=True)

    model = TFIChain({"L": 8, "J": 1.0, "g": 1.2, "bc_MPS": "finite"})
    psi = MPS.from_product_state(model.lat.mps_sites(), ["up"] * model.lat.N_sites, bc=model.lat.bc_MPS)
    options = {"max_sweeps": 4, "trunc_params": {"chi_max": 32, "svd_min": 1e-10}}

    with RunLogger(output, run_id="tenpy-dmrg") as log:
        log.emit("run_start", library="tenpy", algorithm="dmrg", model="TFIChain", sites=model.lat.N_sites)
        observer = DMRGObserver(log)
        engine = dmrg.TwoSiteDMRGEngine(psi, model, options)
        energy, _psi = engine.run()
        observer.sweep_end(engine, chi_max_configured=options["trunc_params"]["chi_max"])
        log.emit("observable", library="tenpy", algorithm="dmrg", name="final_energy", value=energy)
        log.emit("run_end", library="tenpy", algorithm="dmrg", status="complete")

    print(f"wrote {output}")
    print(f"try: tnview tail {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
