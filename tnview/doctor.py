"""Install and environment diagnostics for TNView."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
from pathlib import Path
from typing import Any

from tnview import __version__
from tnview.validate import validate_lines


@dataclass(frozen=True)
class IntegrationCheck:
    name: str
    module: str
    installed: bool
    install_hint: str


@dataclass(frozen=True)
class ExampleCheck:
    root: str
    files: int
    valid: int
    errors: tuple[str, ...]


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    version: str
    examples: ExampleCheck
    integrations: tuple[IntegrationCheck, ...]


def run_doctor(*, examples_root: str | Path = "examples") -> DoctorReport:
    examples = _check_examples(Path(examples_root))
    integrations = (
        _integration("quimb", "quimb", 'python -m pip install -e ".[quimb]"'),
        _integration("tenpy", "tenpy", 'python -m pip install -e ".[tenpy]"'),
    )
    return DoctorReport(
        ok=not examples.errors,
        version=__version__,
        examples=examples,
        integrations=integrations,
    )


def doctor_payload(report: DoctorReport) -> dict[str, Any]:
    return {
        "ok": report.ok,
        "version": report.version,
        "examples": asdict(report.examples),
        "integrations": [asdict(check) for check in report.integrations],
    }


def render_doctor(report: DoctorReport) -> str:
    status = "ok" if report.ok else "needs attention"
    lines = [
        "TNView doctor",
        f"status:   {status}",
        f"version:  {report.version}",
        "",
        "Examples:",
        f"  root:   {report.examples.root}",
        f"  files:  {report.examples.files}",
        f"  valid:  {report.examples.valid}",
    ]
    if report.examples.errors:
        lines.append("  errors:")
        lines.extend(f"    - {error}" for error in report.examples.errors)
    else:
        lines.append("  errors: none")

    lines.extend(["", "Optional integrations:"])
    for check in report.integrations:
        state = "installed" if check.installed else "missing"
        lines.append(f"  {check.name:<6} {state:<9} module={check.module}")
        if not check.installed:
            lines.append(f"         install: {check.install_hint}")
    return "\n".join(lines)


def _check_examples(root: Path) -> ExampleCheck:
    if not root.exists():
        return ExampleCheck(root=str(root), files=0, valid=0, errors=(f"{root} does not exist",))

    errors: list[str] = []
    files = sorted(root.glob("*.jsonl"))
    valid = 0
    for path in files:
        report = validate_lines(path.read_text(encoding="utf-8").splitlines(), strict=True)
        if report.valid:
            valid += 1
        else:
            errors.extend(f"{path}: {error}" for error in report.errors)
    if not files:
        errors.append(f"{root} contains no JSONL examples")
    return ExampleCheck(root=str(root), files=len(files), valid=valid, errors=tuple(errors))


def _integration(name: str, module: str, install_hint: str) -> IntegrationCheck:
    return IntegrationCheck(
        name=name,
        module=module,
        installed=importlib.util.find_spec(module) is not None,
        install_hint=install_hint,
    )
