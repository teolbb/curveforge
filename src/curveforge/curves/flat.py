"""Flat reference curve (0 dB everywhere)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from pydantic import BaseModel, ConfigDict

from curveforge.curves._base import CurveSpec

if TYPE_CHECKING:
    from numpy.typing import NDArray


class FlatParams(BaseModel):
    """Parameters for the flat curve (none)."""

    model_config = ConfigDict(extra="forbid", frozen=True)


def _render(_params: FlatParams, freqs: NDArray[np.float64]) -> NDArray[np.float64]:
    return np.zeros_like(freqs)


SPEC: CurveSpec[FlatParams] = CurveSpec(
    name="flat",
    title="Flat / Unity",
    description="Zero dB at every frequency. Useful as a baseline before transforms.",
    citation="Reference baseline (no source).",
    params_model=FlatParams,
    render=_render,
)
