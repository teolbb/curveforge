"""Base protocol and metadata for transform modules.

Transforms are pure functions `(curve, params) -> curve` that operate on the
dense in-memory grid. Order matters: transforms are applied in the order they
appear in the recipe's `transforms` list.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel

from curveforge.curve import Curve

ParamsT = TypeVar("ParamsT", bound=BaseModel)

Applier = Callable[[Curve, ParamsT], Curve]


@dataclass(frozen=True, slots=True)
class TransformSpec(Generic[ParamsT]):
    """Static description of a transform module.

    Attributes:
        name: Short identifier used as the YAML key (e.g. "peq").
        title: Human-readable name.
        description: One-line description shown by `curveforge list`.
        params_model: Pydantic model describing parameters.
        apply: Function `(curve, params) -> curve`.
    """

    name: str
    title: str
    description: str
    params_model: type[ParamsT]
    apply: Applier[ParamsT]
