"""Registry of all built-in curve modules.

Each curve module exports a `SPEC: CurveSpec` and is registered here by name.
Adding a new curve is a 3-line change: implement the module, import it, add
its SPEC to the `_REGISTRY` mapping.
"""

from __future__ import annotations

from typing import Any

from curveforge.curves._base import CurveSpec
from curveforge.curves.b_and_k import SPEC as B_AND_K_SPEC
from curveforge.curves.breakpoints import SPEC as BREAKPOINTS_SPEC
from curveforge.curves.flat import SPEC as FLAT_SPEC
from curveforge.curves.harman import SPEC as HARMAN_SPEC
from curveforge.curves.olive_welti_inroom import SPEC as OLIVE_WELTI_INROOM_SPEC
from curveforge.curves.toole_inroom import SPEC as TOOLE_INROOM_SPEC
from curveforge.curves.welti_sub import SPEC as WELTI_SUB_SPEC

# Order is the documentation/listing order; not a priority.
_REGISTERED: tuple[CurveSpec[Any], ...] = (
    HARMAN_SPEC,
    OLIVE_WELTI_INROOM_SPEC,
    B_AND_K_SPEC,
    TOOLE_INROOM_SPEC,
    WELTI_SUB_SPEC,
    FLAT_SPEC,
    BREAKPOINTS_SPEC,
)

_REGISTRY: dict[str, CurveSpec[Any]] = {spec.name: spec for spec in _REGISTERED}


def get_curve(name: str) -> CurveSpec[Any]:
    """Look up a registered curve by its YAML name.

    Raises:
        KeyError: if `name` is not registered.
    """
    spec = _REGISTRY.get(name)
    if spec is None:
        msg = f"unknown curve {name!r}; available: {sorted(_REGISTRY)}"
        raise KeyError(msg)
    return spec


def list_curves() -> list[CurveSpec[Any]]:
    """Return all registered curves in registration order."""
    return list(_REGISTERED)


__all__ = ["CurveSpec", "get_curve", "list_curves"]
