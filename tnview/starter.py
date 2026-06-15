"""Starter emitter templates for TNView."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent


KINDS = ("runlog", "quimb", "tenpy")


def starter_script(kind: str) -> str:
    """Return a runnable starter script for a supported integration kind."""

    if kind == "runlog":
        return _RUNLOG_TEMPLATE
    if kind == "quimb":
        return _QUIMB_TEMPLATE
    if kind == "tenpy":
        return _TENPY_TEMPLATE
    raise ValueError(f"unsupported starter kind {kind!r}")


def write_starter(path: str | Path, *, kind: str = "runlog", force: bool = False) -> Path:
    """Write a starter script and return its path."""

    target = Path(path)
    if target.exists() and not force:
        raise FileExistsError(str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(starter_script(kind), encoding="utf-8")
    return target


_RUNLOG_TEMPLATE = dedent(
    """\
    from tnview import RunLogger


    def main():
        with RunLogger("runs/example.jsonl", run_id="example") as log:
            log.emit("run_start", library="my-code", algorithm="dmrg")
            for sweep in range(4):
                log.emit(
                    "sweep_end",
                    sweep=sweep,
                    energy=-1.0 - 0.01 * sweep,
                    delta_energy=1e-5 / (sweep + 1),
                    max_chi=64,
                    chi_max_configured=128,
                    max_trunc_err=1e-9,
                )
            log.emit("run_end", status="complete")


    if __name__ == "__main__":
        main()
    """
)

_QUIMB_TEMPLATE = dedent(
    """\
    import quimb.tensor as qtn

    from tnview import RunLogger
    from tnview.adapters.quimb import emit_mps_snapshot


    def main():
        with RunLogger("runs/quimb_mps.jsonl", run_id="quimb-mps") as log:
            log.emit("run_start", library="quimb", algorithm="mps_snapshot")
            for step, bond_dim in enumerate([2, 4, 8], start=1):
                psi = qtn.MPS_rand_state(8, bond_dim, phys_dim=2)
                emit_mps_snapshot(log, psi, step=step, chi_max=8)
            log.emit("run_end", status="complete")


    if __name__ == "__main__":
        main()
    """
)

_TENPY_TEMPLATE = dedent(
    """\
    from tnview import RunLogger
    from tnview.adapters.tenpy import DMRGObserver


    def attach_tnview(engine, output="runs/tenpy_dmrg.jsonl", chi_max=128):
        log = RunLogger(output, run_id="tenpy-dmrg")
        log.open()
        log.emit("run_start", library="tenpy", algorithm="dmrg")
        observer = DMRGObserver(log)
        energy, psi = engine.run()
        observer.emit_new_sweeps(engine, chi_max_configured=chi_max)
        log.emit("observable", library="tenpy", algorithm="dmrg", name="final_energy", value=energy)
        log.emit("run_end", status="complete")
        log.close()
        return energy, psi
    """
)
