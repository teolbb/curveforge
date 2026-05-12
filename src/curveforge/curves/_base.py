"""Base protocol and metadata for curve modules.

A curve module exposes a `CurveSpec` exposed as `SPEC`. The spec wires together
- a unique `name`,
- a Pydantic `params_model` describing the native parameters,
- a `render(params, freqs)` function that returns gains in dB on the given grid,
- a citation and short description for `info`/`list` output.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel

ParamsT = TypeVar("ParamsT", bound=BaseModel)

# Renderer signature: takes typed params and a grid → returns a parallel dB array.
Renderer = Callable[[ParamsT, NDArray[np.float64]], NDArray[np.float64]]


@dataclass(frozen=True, slots=True)
class CurveSpec(Generic[ParamsT]):
    """Static description of a curve module.

    Attributes:
        name: Short identifier used in YAML (`base.type`).
        title: Human-readable name.
        description: One-line description shown by `curveforge list`.
        citation: Source attribution shown by `curveforge info`.
        params_model: Pydantic model describing native parameters.
        render: Function `(params, freqs) -> gains_db`.
    """

    name: str
    title: str
    description: str
    citation: str
    params_model: type[ParamsT]
    render: Renderer[ParamsT]
