"""Terminal rendering for TNView replay output."""

from __future__ import annotations

from dataclasses import dataclass
from math import log10
import shutil
import textwrap

from tnview.events import BondUpdated
from tnview.state import (
    BondState,
    RunState,
    diagnose_bond,
    diagnose_run,
    entanglement_front,
    top_truncation_bonds,
)
from tnview.warnings import early_warning


UNICODE_BLOCKS = " ▁▂▃▄▅▆▇█"
ASCII_BLOCKS = " .:-=+*#@"


@dataclass(frozen=True)
class RenderOptions:
    width: int | None = None
    unicode: bool = True
    color: bool = False
    history_limit: int = 12
    update_limit: int = 6
    show_updates: bool = True
    show_entropy: bool = True
    show_pressure: bool = True
    show_inspector: bool = True
    show_diagnostics: bool = True


def render_run(state: RunState, options: RenderOptions | None = None) -> str:
    options = options or RenderOptions()
    width = options.width or shutil.get_terminal_size((100, 30)).columns
    width = max(60, width)

    sections = [
        _title(state, width),
        _topology(state, width),
        _updates(state, width, options) if options.show_updates else "",
        _heatmap(state, width, options) if options.show_entropy else "",
        _pressure_rows(state, width, options) if options.show_pressure else "",
        _inspector(state, width, options) if options.show_inspector else "",
        _diagnostics(state, width) if options.show_diagnostics else "",
    ]
    return "\n\n".join(section for section in sections if section)


def _title(state: RunState, width: int) -> str:
    checkpoint = state.latest_checkpoint
    if checkpoint is None:
        suffix = "waiting for checkpoint"
    else:
        status = checkpoint.complexity_status or diagnose_run(state)
        suffix = f"step {checkpoint.step}  t={checkpoint.time:g}  {status.replace('_', '-')}"
    return _fit(f"TNView complexity microscope | {suffix}", width)


def _topology(state: RunState, width: int) -> str:
    bonds = state.ordered_bonds
    if not bonds:
        return "MPS topology\n(no bond telemetry yet)"

    min_site = min(bond.site_left for bond in bonds)
    max_site = max(bond.site_right for bond in bonds)
    sites = list(range(min_site, max_site + 1))
    cell_width = max(2, max(len(str(site)) for site in sites))
    site_sep = "   "
    bond_sep = " " * (cell_width + len(site_sep) - 2)
    site_row = site_sep.join(f"{site:^{cell_width}}" for site in sites).rstrip()
    bond_by_sites = {(bond.site_left, bond.site_right): bond for bond in bonds}

    link_cells = []
    for left, right in zip(sites, sites[1:]):
        bond = bond_by_sites.get((left, right))
        if bond is None:
            link_cells.append("  ")
        elif bond.saturated:
            link_cells.append("!!")
        elif bond.chi_pressure >= 0.75:
            link_cells.append("++")
        else:
            link_cells.append("--")

    link_indent = " " * (cell_width + 1)
    link_row = f"{link_indent}{bond_sep.join(link_cells)}"
    return "\n".join(
        [
            "MPS topology",
            _fit(f"sites: {site_row}", width),
            _fit(f"bonds: {link_row}", width),
            "legend: -- healthy  ++ pressure  !! saturated",
        ]
    )


def _updates(state: RunState, width: int, options: RenderOptions) -> str:
    updates = state.updates[-options.update_limit :]
    if not updates:
        return ""

    lines = ["TEBD brick-wall updates"]
    for update in updates:
        delta = update.entropy_after - update.entropy_before
        marker = _update_marker(update)
        line = (
            f"{marker} step {update.step:<5} {update.layer:<4} b{update.bond:<3} "
            f"S {update.entropy_before:.2f}->{update.entropy_after:.2f} "
            f"dS {delta:+.2f} chi {update.chi_after}/{update.chi_max} "
            f"eps {_sci(update.trunc_error)}"
        )
        lines.append(_fit(line, width))
    return "\n".join(lines)


def _heatmap(state: RunState, width: int, options: RenderOptions) -> str:
    if not state.history:
        return ""

    rows = state.history[-options.history_limit :]
    bonds = [bond.bond for bond in state.ordered_bonds]
    max_entropy = max((value for row in rows for value in row.entropy_by_bond.values()), default=0.0)
    glyphs = UNICODE_BLOCKS if options.unicode else ASCII_BLOCKS

    lines = ["Entanglement heatmap  time / bond ->"]
    header = "        " + "".join(str(bond % 10) for bond in bonds)
    lines.append(_fit(header, width))
    for row in rows:
        cells = "".join(_bucket(row.entropy_by_bond.get(bond, 0.0), max_entropy, glyphs) for bond in bonds)
        lines.append(_fit(f"t={row.time:<5g} {cells}", width))
    return "\n".join(lines)


def _pressure_rows(state: RunState, width: int, options: RenderOptions) -> str:
    bonds = state.ordered_bonds
    if not bonds:
        return ""

    glyphs = UNICODE_BLOCKS if options.unicode else ASCII_BLOCKS
    max_trunc = max((bond.trunc_error for bond in bonds), default=0.0)
    pressure = "".join(_bucket(bond.chi_pressure, 1.0, glyphs) for bond in bonds)
    saturation = "".join("!" if bond.saturated else "+" if bond.chi_pressure >= 0.75 else "." for bond in bonds)
    truncation = "".join(_log_bucket(bond.trunc_error, max_trunc, glyphs) for bond in bonds)
    labels = "".join(str(bond.bond % 10) for bond in bonds)

    return "\n".join(
        [
            "Complexity rows",
            _fit(f"bond:       {labels}", width),
            _fit(f"chi/max:    {pressure}", width),
            _fit(f"saturated:  {saturation}", width),
            _fit(f"trunc eps:  {truncation}", width),
        ]
    )


def _inspector(state: RunState, width: int, options: RenderOptions) -> str:
    bond = state.selected
    if bond is None:
        return ""

    spectrum = _schmidt_sparkline(bond, options)
    lines = [
        f"Selected bond b{bond.bond} = sites {bond.site_left}|{bond.site_right}",
        f"S_vN:              {bond.entropy:.4g}",
        f"Renyi-2:           {_maybe_float(bond.renyi2)}",
        f"chi:               {bond.chi} / {bond.chi_max}",
        f"saturated:         {'yes' if bond.saturated else 'no'}",
        f"truncation error:  {_sci(bond.trunc_error)}",
        f"discarded weight:  {_maybe_float(bond.discarded_weight, scientific=True)}",
        f"SVD walltime:      {_maybe_float(bond.walltime_ms)} ms",
        f"Schmidt lambda^2:  {spectrum}",
        f"diagnosis:         {diagnose_bond(bond)}",
    ]
    return "\n".join(_fit(line, width) for line in lines)


def _diagnostics(state: RunState, width: int) -> str:
    checkpoint = state.latest_checkpoint
    top = top_truncation_bonds(state)
    front = entanglement_front(state)
    top_text = ", ".join(f"b{bond.bond} ({_sci(bond.trunc_error)})" for bond in top) or "none"
    lines = [
        "Diagnostics",
        f"run status:          {diagnose_run(state)}",
        f"top error bonds:     {top_text}",
    ]
    if checkpoint is not None:
        lines.extend(
            [
                f"max entropy:         {_maybe_float(checkpoint.max_entropy)}",
                f"mean entropy:        {_maybe_float(checkpoint.mean_entropy)}",
                f"max chi:             {_maybe_int(checkpoint.max_chi)}",
                f"saturated bonds:     {_maybe_int(checkpoint.num_saturated_bonds)}",
                f"total trunc error:   {_maybe_float(checkpoint.total_trunc_error, scientific=True)}",
                f"energy drift:        {_maybe_float(checkpoint.energy_drift, scientific=True)}",
                f"norm:                {_maybe_float(checkpoint.norm)}",
            ]
        )
    if front is not None:
        active = ", ".join(f"b{bond}" for bond in front.active_bonds) or "none"
        lines.extend(
            [
                f"entropy front:       {active}",
                f"front threshold:     {front.threshold:.3g}",
                f"front span:          {front.span} bonds",
                f"front velocity:      {_maybe_float(front.velocity_bonds_per_time)} bonds / time",
            ]
        )
    warning = early_warning(state)
    lines.extend(
        [
            f"chi trend:           {warning.chi_saturation_trend}",
            f"truncation trend:    {warning.truncation_trend}",
            f"estimated chi need:  {_maybe_int(warning.estimated_chi_need)}",
            f"risk:                {warning.risk}",
            f"recommendation:      {warning.recommendation}",
        ]
    )
    return "\n".join(_wrap_kv(line, width) for line in lines)


def _update_marker(update: BondUpdated) -> str:
    delta = update.entropy_after - update.entropy_before
    if update.trunc_error >= 1e-7:
        return "!"
    if delta >= 0.4:
        return "#"
    if delta >= 0.15:
        return "+"
    return "."


def _schmidt_sparkline(bond: BondState, options: RenderOptions) -> str:
    glyphs = UNICODE_BLOCKS if options.unicode else ASCII_BLOCKS
    # Telemetry intentionally avoids streaming full tensors. This synthetic profile
    # gives the inspector a visual summary tied to entropy and chi pressure.
    effective_rank = max(1, min(16, bond.chi))
    decay = max(0.15, min(0.85, 1.0 / (1.0 + bond.entropy)))
    values = [decay**idx for idx in range(effective_rank)]
    max_value = max(values)
    return "".join(_bucket(value, max_value, glyphs) for value in values)


def _bucket(value: float, max_value: float, glyphs: str) -> str:
    if max_value <= 0:
        return glyphs[0]
    ratio = max(0.0, min(1.0, value / max_value))
    return glyphs[round(ratio * (len(glyphs) - 1))]


def _log_bucket(value: float, max_value: float, glyphs: str) -> str:
    if value <= 0 or max_value <= 0:
        return glyphs[0]
    floor = max(max_value * 1e-6, 1e-15)
    normalized = (log10(max(value, floor)) - log10(floor)) / (log10(max_value) - log10(floor))
    return glyphs[round(max(0.0, min(1.0, normalized)) * (len(glyphs) - 1))]


def _maybe_float(value: float | None, *, scientific: bool = False) -> str:
    if value is None:
        return "n/a"
    if scientific:
        return _sci(value)
    return f"{value:.6g}"


def _maybe_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return str(value)


def _sci(value: float) -> str:
    return f"{value:.2e}"


def _fit(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 1:
        return text[:width]
    return text[: width - 1] + "…"


def _wrap_kv(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    return "\n".join(textwrap.wrap(text, width=width, subsequent_indent="  "))
