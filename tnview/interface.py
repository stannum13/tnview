"""High-level object inspection interface."""

from __future__ import annotations

from typing import Any

from tnview.adapters.quimb import view_mps


def view(obj: Any, **kwargs: Any) -> str:
    """Render a supported quantum object using the TNView terminal surface."""

    if _looks_like_mps(obj):
        return view_mps(obj, **kwargs)
    raise TypeError(f"no TNView adapter registered for {type(obj).__name__}")


def _looks_like_mps(obj: Any) -> bool:
    if not (hasattr(obj, "L") or hasattr(obj, "sites") or hasattr(obj, "tensors")):
        return False
    return callable(getattr(obj, "bond_size", None)) or callable(getattr(obj, "bond_sizes", None))
