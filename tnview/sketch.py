"""Deterministic prompt-like tensor-network sketch generation."""

from __future__ import annotations

from dataclasses import dataclass
import shlex
from typing import Any

from tnview.fixtures import FIXTURE_PROFILES, generate_chain_fixture


SUPPORTED_SKETCHES = ("mps",)


@dataclass(frozen=True)
class SketchSpec:
    topology: str
    sites: int = 32
    checkpoints: int = 10
    chi_max: int = 128
    profile: str = "hard"
    window: int = 16
    run_id: str = "tnview-sketch"


def parse_sketch_prompt(prompt: str) -> SketchSpec:
    """Parse a deterministic sketch prompt such as ``mps sites=32 chi=128``."""

    tokens = shlex.split(prompt)
    if not tokens:
        raise ValueError("sketch prompt cannot be empty")
    topology = tokens[0].lower()
    if topology == "chain":
        topology = "mps"
    if topology not in SUPPORTED_SKETCHES:
        raise ValueError(f"unsupported sketch topology {tokens[0]!r}")

    values: dict[str, str] = {}
    for token in tokens[1:]:
        if "=" not in token:
            raise ValueError(f"expected key=value option, got {token!r}")
        key, value = token.split("=", 1)
        key = key.lower().replace("-", "_")
        if key == "chi":
            key = "chi_max"
        values[key] = value

    allowed = {"sites", "checkpoints", "chi_max", "profile", "window", "run_id"}
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise ValueError(f"unsupported sketch option {unknown[0]!r}")

    spec = SketchSpec(
        topology=topology,
        sites=_int_option(values, "sites", SketchSpec.sites),
        checkpoints=_int_option(values, "checkpoints", SketchSpec.checkpoints),
        chi_max=_int_option(values, "chi_max", SketchSpec.chi_max),
        profile=values.get("profile", SketchSpec.profile),
        window=_int_option(values, "window", SketchSpec.window),
        run_id=values.get("run_id", SketchSpec.run_id),
    )
    if spec.profile not in FIXTURE_PROFILES:
        raise ValueError(f"profile must be one of: {', '.join(FIXTURE_PROFILES)}")
    if spec.window < 1:
        raise ValueError("window must be positive")
    return spec


def generate_sketch_replay(spec: SketchSpec) -> str:
    """Generate replay JSONL for a parsed sketch spec."""

    if spec.topology != "mps":
        raise ValueError(f"unsupported sketch topology {spec.topology!r}")
    return generate_chain_fixture(
        sites=spec.sites,
        checkpoints=spec.checkpoints,
        chi_max=spec.chi_max,
        profile=spec.profile,
        run_id=spec.run_id,
    )


def render_sketch_list() -> str:
    """Return supported sketch prompts and examples."""

    return "\n".join(
        [
            "TNView sketches",
            "",
            "Supported prompts:",
            "  mps sites=32 chi=128 profile=hard checkpoints=10",
            "",
            "Options:",
            "  sites=N        number of MPS sites",
            "  chi=N          maximum bond dimension",
            "  checkpoints=N  number of synthetic replay checkpoints",
            "  profile=easy|hard|front|spike",
            "  window=N       rendered focus window",
            "  run_id=NAME    replay run id",
            "",
            "Examples:",
            '  tnview sketch "mps sites=48 chi=128 profile=hard"',
            '  tnview sketch "mps sites=64 chi=256 profile=front" --interactive',
            '  tnview sketch "mps sites=32 chi=128 profile=spike" --output spike.jsonl',
            '  tnview sketch "mps sites=16 profile=easy" --interactive',
        ]
    )


def sketch_list_payload() -> dict[str, Any]:
    """Return stable machine-readable sketch prompt metadata."""

    return {
        "kind": "sketches",
        "topologies": list(SUPPORTED_SKETCHES),
        "profiles": list(FIXTURE_PROFILES),
        "options": {
            "sites": "number of MPS sites",
            "chi": "maximum bond dimension",
            "checkpoints": "number of synthetic replay checkpoints",
            "profile": "complexity profile",
            "window": "rendered focus window",
            "run_id": "replay run id",
        },
        "examples": [
            'tnview sketch "mps sites=48 chi=128 profile=hard"',
            'tnview sketch "mps sites=64 chi=256 profile=front" --interactive',
            'tnview sketch "mps sites=32 chi=128 profile=spike" --output spike.jsonl',
        ],
    }


def _int_option(values: dict[str, str], key: str, default: int) -> int:
    raw = values.get(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer") from exc
