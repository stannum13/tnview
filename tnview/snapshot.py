"""JSON snapshot export for TNView run state."""

from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any

from tnview.state import RunState, diagnose_bond, diagnose_run, top_truncation_bonds


def snapshot_dict(state: RunState) -> dict[str, Any]:
    checkpoint = state.latest_checkpoint
    selected = state.selected
    return {
        "checkpoint": asdict(checkpoint) if checkpoint is not None else None,
        "run_status": diagnose_run(state),
        "selected_bond": _bond_snapshot(selected) if selected is not None else None,
        "bonds": [_bond_snapshot(bond) for bond in state.ordered_bonds],
        "top_truncation_bonds": [
            {
                "bond": bond.bond,
                "trunc_error": bond.trunc_error,
                "fraction": _fraction(bond.trunc_error, _total_truncation(state)),
            }
            for bond in top_truncation_bonds(state)
        ],
        "history": [
            {
                "step": row.step,
                "time": row.time,
                "entropy_by_bond": row.entropy_by_bond,
                "chi_by_bond": row.chi_by_bond,
                "trunc_by_bond": row.trunc_by_bond,
            }
            for row in state.history
        ],
    }


def snapshot_json(state: RunState) -> str:
    return json.dumps(snapshot_dict(state), indent=2, sort_keys=True)


def _bond_snapshot(bond: Any) -> dict[str, Any]:
    return {
        "bond": bond.bond,
        "site_left": bond.site_left,
        "site_right": bond.site_right,
        "entropy": bond.entropy,
        "renyi2": bond.renyi2,
        "chi": bond.chi,
        "chi_max": bond.chi_max,
        "chi_pressure": bond.chi_pressure,
        "saturated": bond.saturated,
        "trunc_error": bond.trunc_error,
        "discarded_weight": bond.discarded_weight,
        "walltime_ms": bond.walltime_ms,
        "diagnosis": diagnose_bond(bond),
        "diagnostic_tags": list(bond.diagnostic_tags),
    }


def _total_truncation(state: RunState) -> float:
    return sum(bond.trunc_error for bond in state.ordered_bonds)


def _fraction(value: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return value / total
