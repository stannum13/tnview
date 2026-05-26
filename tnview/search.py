"""Search helpers for locating interesting bonds in a run."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tnview.state import BondState, RunState, diagnose_bond


@dataclass(frozen=True)
class SearchMatch:
    bond: BondState
    reason: str


@dataclass(frozen=True)
class TensorSearchMatch:
    name: str
    source: str
    location: str
    detail: str


def search_bonds(state: RunState, query: str) -> list[SearchMatch]:
    key, value = _parse_query(query)
    matches: list[SearchMatch] = []
    for bond in state.ordered_bonds:
        reason = _match_reason(bond, key, value)
        if reason is not None:
            matches.append(SearchMatch(bond=bond, reason=reason))
    return matches


def is_tensor_query(query: str) -> bool:
    key, _ = _parse_query(query)
    return key in {"tensor", "tensor_name", "name"}


def search_tensors(state: RunState, query: str) -> list[TensorSearchMatch]:
    _, value = _parse_query(query)
    matches: list[TensorSearchMatch] = []
    matches.extend(_search_ansatz_tensors(state, value))
    matches.extend(_search_contraction_steps(state, value))
    return matches


def render_search(matches: list[SearchMatch], *, query: str, width: int = 100) -> str:
    lines = [f"Search: {query}", "bond  sites   S_vN    chi       trunc err   diagnosis"]
    lines.append("----  ------  ------  --------  ----------  -----------------------------")
    if not matches:
        lines.append("no matches")
        return "\n".join(lines)

    for match in matches:
        bond = match.bond
        line = (
            f"b{bond.bond:<3}  "
            f"{bond.site_left:>2}|{bond.site_right:<2}   "
            f"{bond.entropy:<6.3g}  "
            f"{bond.chi:>3}/{bond.chi_max:<4}  "
            f"{bond.trunc_error:<10.2e}  "
            f"{match.reason}"
        )
        lines.append(_fit(line, width))
    return "\n".join(lines)


def render_tensor_search(matches: list[TensorSearchMatch], *, query: str, width: int = 100) -> str:
    lines = [f"Search: {query}", "kind        name        location          detail"]
    lines.append("----------  ----------  ----------------  --------------------------------")
    if not matches:
        lines.append("no matches")
        return "\n".join(lines)

    for match in matches:
        line = (
            f"{_clip(match.source, 10):<10}  "
            f"{_clip(match.name, 10):<10}  "
            f"{_clip(match.location, 16):<16}  "
            f"{match.detail}"
        )
        lines.append(_fit(line, width))
    return "\n".join(lines)


def _search_ansatz_tensors(state: RunState, value: str) -> list[TensorSearchMatch]:
    if state.ansatz_layout is None:
        return []
    matches: list[TensorSearchMatch] = []
    for tensor in state.ansatz_layout.tensors:
        name = _tensor_name(tensor)
        if name is None or value not in name.lower():
            continue
        matches.append(
            TensorSearchMatch(
                name=name,
                source="ansatz",
                location=_tensor_location(tensor),
                detail=f"{state.ansatz_layout.ansatz} tensor",
            )
        )
    return matches


def _search_contraction_steps(state: RunState, value: str) -> list[TensorSearchMatch]:
    matches: list[TensorSearchMatch] = []
    for path in state.contraction_paths:
        for index, step in enumerate(path.steps):
            for key, raw_name in _step_tensor_names(step):
                name = str(raw_name)
                if value not in name.lower():
                    continue
                matches.append(
                    TensorSearchMatch(
                        name=name,
                        source="path",
                        location=f"step {path.step}",
                        detail=_path_detail(path.name, index, key, step),
                    )
                )
    return matches


def _tensor_name(tensor: dict[str, Any]) -> str | None:
    for key in ("name", "id", "tensor"):
        value = tensor.get(key)
        if value is not None:
            return str(value)
    return None


def _tensor_location(tensor: dict[str, Any]) -> str:
    if tensor.get("site") is not None:
        return f"site {tensor['site']}"
    if tensor.get("bond") is not None:
        return f"bond {tensor['bond']}"
    if tensor.get("sites") is not None:
        return "sites " + ",".join(str(site) for site in tensor["sites"])
    return "n/a"


def _step_tensor_names(step: dict[str, Any]) -> list[tuple[str, Any]]:
    names: list[tuple[str, Any]] = []
    for key in ("left", "right", "result", "output", "tensor", "name"):
        value = step.get(key)
        if value is not None:
            names.append((key, value))
    for key in ("inputs", "tensors"):
        values = step.get(key)
        if isinstance(values, list | tuple):
            names.extend((key, value) for value in values)
    return names


def _path_detail(path_name: str, index: int, key: str, step: dict[str, Any]) -> str:
    partner = ""
    if key == "left" and step.get("right") is not None:
        partner = f" with {step['right']}"
    elif key == "right" and step.get("left") is not None:
        partner = f" with {step['left']}"
    size = f" size {step['size']}" if step.get("size") is not None else ""
    return f"{path_name} step {index}{partner}{size}"


def _parse_query(query: str) -> tuple[str, str]:
    if ":" not in query:
        return "text", query.strip().lower()
    key, value = query.split(":", 1)
    return key.strip().lower(), value.strip().lower()


def _match_reason(bond: BondState, key: str, value: str) -> str | None:
    diagnosis = diagnose_bond(bond)
    if key == "bond":
        return diagnosis if _int_value(value) == bond.bond else None
    if key == "site":
        site = _int_value(value)
        return diagnosis if site in (bond.site_left, bond.site_right) else None
    if key == "tag":
        return diagnosis if value in (tag.lower() for tag in bond.diagnostic_tags) else None
    if key == "status":
        return diagnosis if value in diagnosis.lower() else None
    if key == "text":
        haystack = " ".join([diagnosis, *bond.diagnostic_tags]).lower()
        return diagnosis if value in haystack else None
    return None


def _int_value(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def _fit(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 1:
        return text[:width]
    return text[: width - 1] + "~"


def _clip(value: str, size: int) -> str:
    if len(value) <= size:
        return value
    if size <= 1:
        return value[:size]
    return value[: size - 1] + "~"
