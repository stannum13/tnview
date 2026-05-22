"""Synthetic replay fixture generation."""

from __future__ import annotations

import json
from math import exp
from typing import Any


def generate_chain_fixture(
    *,
    sites: int,
    checkpoints: int,
    chi_max: int,
    profile: str,
    run_id: str = "generated-chain",
) -> str:
    if sites < 2:
        raise ValueError("sites must be at least 2")
    if checkpoints < 1:
        raise ValueError("checkpoints must be at least 1")
    if chi_max < 1:
        raise ValueError("chi_max must be positive")
    if profile not in {"easy", "hard"}:
        raise ValueError("profile must be 'easy' or 'hard'")

    events: list[dict[str, Any]] = [
        {
            "event": "run_started",
            "run_id": run_id,
            "time": 0.0,
            "name": f"Generated {profile} chain",
            "simulator": "tnview-fixture",
            "algorithm": "TEBD",
            "parameters": {"chi_max": chi_max, "profile": profile},
        },
        {
            "event": "model_geometry",
            "step": 0,
            "time": 0.0,
            "name": "generated 1D chain",
            "sites": sites,
            "dimensions": [sites],
            "boundary": "open",
            "edges": [{"source": site, "target": site + 1} for site in range(sites - 1)],
        },
        {
            "event": "ansatz_layout",
            "step": 0,
            "time": 0.0,
            "ansatz": "MPS",
            "ordering": list(range(sites)),
            "parameters": {"physical_dim": 2},
        },
    ]

    previous_entropy = [0.0 for _ in range(sites - 1)]
    previous_chi = [1 for _ in range(sites - 1)]
    for checkpoint in range(checkpoints):
        step = checkpoint * 50
        time = checkpoint * 0.5
        entropy = [_entropy_value(bond, sites, checkpoint, checkpoints, profile) for bond in range(sites - 1)]
        chi = [_chi_value(value, chi_max, profile) for value in entropy]
        trunc = [_truncation_value(value, chi_value, chi_max, profile) for value, chi_value in zip(entropy, chi)]

        for bond in range(sites - 1):
            tags = []
            if chi[bond] >= chi_max:
                tags.append("chi_saturated")
            if trunc[bond] >= 1e-7:
                tags.append("local_bottleneck")
            events.append(
                {
                    "event": "bond_updated",
                    "step": step,
                    "time": time,
                    "layer": "init" if checkpoint == 0 else ("even" if bond % 2 == 0 else "odd"),
                    "bond": bond,
                    "site_left": bond,
                    "site_right": bond + 1,
                    "entropy_before": previous_entropy[bond],
                    "entropy_after": entropy[bond],
                    "renyi2_before": previous_entropy[bond] * 0.75,
                    "renyi2_after": entropy[bond] * 0.75,
                    "chi_before": previous_chi[bond],
                    "chi_after": chi[bond],
                    "chi_max": chi_max,
                    "trunc_error": trunc[bond],
                    "discarded_weight": trunc[bond],
                    "walltime_ms": round(1.0 + 0.1 * chi[bond], 3),
                    "diagnostic_tags": tags,
                }
            )

        previous_entropy = entropy
        previous_chi = chi
        max_entropy = max(entropy)
        total_trunc = sum(trunc)
        saturated = sum(1 for value in chi if value >= chi_max)
        events.append(
            {
                "event": "checkpoint",
                "step": step,
                "time": time,
                "max_entropy": max_entropy,
                "mean_entropy": sum(entropy) / len(entropy),
                "max_chi": max(chi),
                "num_saturated_bonds": saturated,
                "total_trunc_error": total_trunc,
                "energy": -float(sites) + total_trunc * 10,
                "energy_drift": total_trunc,
                "norm": 1.0 - min(total_trunc, 1e-3),
                "complexity_status": _status(max_entropy, saturated, total_trunc),
            }
        )

    return "\n".join(json.dumps(event, separators=(",", ":")) for event in events) + "\n"


def _entropy_value(bond: int, sites: int, checkpoint: int, checkpoints: int, profile: str) -> float:
    center = (sites - 2) / 2
    spread = max(1.0, sites / (5 if profile == "hard" else 8))
    distance = abs(bond - center)
    shape = exp(-(distance * distance) / (2 * spread * spread))
    growth = checkpoint / max(1, checkpoints - 1)
    amplitude = 4.2 if profile == "hard" else 1.2
    floor = 0.02 if checkpoint == 0 else 0.0
    return round(floor + amplitude * growth * shape, 6)


def _chi_value(entropy: float, chi_max: int, profile: str) -> int:
    pressure = entropy / (3.2 if profile == "hard" else 2.8)
    chi = int(max(2, round(2 ** (1 + 6 * pressure))))
    return min(chi_max, chi)


def _truncation_value(entropy: float, chi: int, chi_max: int, profile: str) -> float:
    if profile == "easy":
        return 1e-13 * max(1.0, entropy)
    if chi >= chi_max:
        return 1e-7 * max(1.0, entropy)
    return 1e-10 * max(1.0, entropy)


def _status(max_entropy: float, saturated: int, total_trunc: float) -> str:
    if saturated and total_trunc >= 1e-7:
        return "chi_limited"
    if max_entropy < 0.1:
        return "trivial dynamics"
    return "healthy growth"
