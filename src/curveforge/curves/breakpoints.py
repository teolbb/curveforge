"""Raw user-supplied breakpoints curve (no math, just interpolation)."""

from __future__ import annotations

from itertools import pairwise
from typing import TYPE_CHECKING

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

from curveforge.curves._base import CurveSpec

if TYPE_CHECKING:
    from numpy.typing import NDArray


class BreakpointsParams(BaseModel):
    """Parameters of the raw-breakpoints curve."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    points: list[tuple[float, float]] = Field(
        ...,
        min_length=2,
        description="List of (freq_hz, gain_db) pairs, strictly sorted by frequency.",
    )

    @field_validator("points")
    @classmethod
    def _check_sorted(cls, value: list[tuple[float, float]]) -> list[tuple[float, float]]:
        freqs = [p[0] for p in value]
        if any(f <= 0 for f in freqs):
            msg = "all breakpoint frequencies must be positive"
            raise ValueError(msg)
        if any(b <= a for a, b in pairwise(freqs)):
            msg = "breakpoints must be strictly sorted by frequency"
            raise ValueError(msg)
        return value


def _render(params: BreakpointsParams, freqs: NDArray[np.float64]) -> NDArray[np.float64]:
    template_freqs = np.array([p[0] for p in params.points], dtype=np.float64)
    template_gains = np.array([p[1] for p in params.points], dtype=np.float64)
    return np.interp(np.log10(freqs), np.log10(template_freqs), template_gains)


SPEC: CurveSpec[BreakpointsParams] = CurveSpec(
    name="breakpoints",
    title="Raw breakpoints",
    description="User-supplied list of (Hz, dB) pairs interpolated log-linearly.",
    citation="User-defined.",
    params_model=BreakpointsParams,
    render=_render,
)
