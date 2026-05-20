"""Search helpers for locating interesting bonds in a run."""

from __future__ import annotations

from dataclasses import dataclass

from tnview.state import BondState, RunState, diagnose_bond


@dataclass(frozen=True)
class SearchMatch:
    bond: BondState
    reason: str


def search_bonds(state: RunState, query: str) -> list[SearchMatch]:
    key, value = _parse_query(query)
    matches: list[SearchMatch] = []
    for bond in state.ordered_bonds:
        reason = _match_reason(bond, key, value)
        if reason is not None:
            matches.append(SearchMatch(bond=bond, reason=reason))
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
