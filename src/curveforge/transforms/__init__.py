"""Registry of all built-in transform modules."""

from __future__ import annotations

from typing import Any

from curveforge.transforms._base import TransformSpec
from curveforge.transforms.gain import SPEC as GAIN_SPEC
from curveforge.transforms.peq import SPEC as PEQ_SPEC
from curveforge.transforms.rolloff import SPEC as ROLLOFF_SPEC
from curveforge.transforms.shelf import SPEC as SHELF_SPEC
from curveforge.transforms.tilt import SPEC as TILT_SPEC

_REGISTERED: tuple[TransformSpec[Any], ...] = (
    GAIN_SPEC,
    PEQ_SPEC,
    SHELF_SPEC,
    ROLLOFF_SPEC,
    TILT_SPEC,
)

_REGISTRY: dict[str, TransformSpec[Any]] = {spec.name: spec for spec in _REGISTERED}


def get_transform(name: str) -> TransformSpec[Any]:
    """Look up a registered transform by its YAML key.

    Raises:
        KeyError: if `name` is not registered.
    """
    spec = _REGISTRY.get(name)
    if spec is None:
        msg = f"unknown transform {name!r}; available: {sorted(_REGISTRY)}"
        raise KeyError(msg)
    return spec


def list_transforms() -> list[TransformSpec[Any]]:
    """Return all registered transforms in registration order."""
    return list(_REGISTERED)


__all__ = ["TransformSpec", "get_transform", "list_transforms"]
