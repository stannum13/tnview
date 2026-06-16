"""Interactive parameter collection for sketch prompts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]


@dataclass(frozen=True)
class WizardResult:
    prompt: str
    interactive: bool
    output: str | None


def run_sketch_wizard(
    *,
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
) -> WizardResult:
    """Ask for sketch parameters and return the equivalent deterministic prompt."""

    output_fn("TNView sketch wizard")
    output_fn("")
    output_fn("Topology:")
    output_fn("  1. MPS chain")
    topology = _choice(
        "Topology",
        choices={"1": "mps", "mps": "mps", "chain": "mps"},
        default="mps",
        input_fn=input_fn,
        output_fn=output_fn,
    )
    sites = _integer("Sites", default=32, minimum=2, input_fn=input_fn, output_fn=output_fn)
    chi = _integer("Chi max", default=128, minimum=1, input_fn=input_fn, output_fn=output_fn)
    checkpoints = _integer("Checkpoints", default=10, minimum=1, input_fn=input_fn, output_fn=output_fn)
    profile = _choice(
        "Profile",
        choices={"hard": "hard", "easy": "easy", "front": "front", "spike": "spike"},
        default="hard",
        input_fn=input_fn,
        output_fn=output_fn,
    )
    window = _integer("Focus window", default=16, minimum=1, input_fn=input_fn, output_fn=output_fn)
    interactive = _yes_no("Open interactive viewer?", default=True, input_fn=input_fn, output_fn=output_fn)
    save = _yes_no("Save replay JSONL?", default=False, input_fn=input_fn, output_fn=output_fn)
    output = None
    if save:
        output = _text("Output path", default="sketch.jsonl", input_fn=input_fn)

    prompt = (
        f"{topology} sites={sites} chi={chi} "
        f"profile={profile} checkpoints={checkpoints} window={window}"
    )
    output_fn("")
    output_fn("Generated sketch:")
    output_fn(f"  {prompt}")
    output_fn("")
    output_fn("Equivalent command:")
    output_fn(f"  {_equivalent_command(prompt, interactive=interactive, output=output)}")
    return WizardResult(prompt=prompt, interactive=interactive, output=output)


def _integer(
    label: str,
    *,
    default: int,
    minimum: int,
    input_fn: InputFn,
    output_fn: OutputFn,
) -> int:
    while True:
        raw = input_fn(f"{label} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            value = int(raw)
        except ValueError:
            output_fn("Please enter an integer.")
            continue
        if value < minimum:
            output_fn(f"Please enter a value >= {minimum}.")
            continue
        return value


def _choice(
    label: str,
    *,
    choices: dict[str, str],
    default: str,
    input_fn: InputFn,
    output_fn: OutputFn,
) -> str:
    options = "/".join(sorted(set(choices.values())))
    while True:
        raw = input_fn(f"{label} [{default}] ({options}): ").strip().lower()
        if raw == "":
            return default
        if raw in choices:
            return choices[raw]
        output_fn(f"Please choose one of: {options}.")


def _yes_no(
    label: str,
    *,
    default: bool,
    input_fn: InputFn,
    output_fn: OutputFn,
) -> bool:
    suffix = "Y/n" if default else "y/N"
    while True:
        raw = input_fn(f"{label} [{suffix}]: ").strip().lower()
        if raw == "":
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        output_fn("Please answer yes or no.")


def _text(label: str, *, default: str, input_fn: InputFn) -> str:
    raw = input_fn(f"{label} [{default}]: ").strip()
    return raw or default


def _equivalent_command(prompt: str, *, interactive: bool, output: str | None) -> str:
    command = f'tnview sketch "{prompt}"'
    if interactive:
        command += " --interactive"
    if output is not None:
        command += f" --output {output}"
    return command
