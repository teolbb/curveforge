"""Boost or cut a frequency band by a fixed amount in dB."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from curveforge.transforms._base import TransformSpec

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from curveforge.curve import Curve

# Cosine taper width at each band edge, expressed as octaves.
_DEFAULT_TAPER_OCTAVES: float = 1.0 / 6.0


class GainParams(BaseModel):
    """Parameters of the band-gain transform."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    low_hz: float = Field(..., gt=0.0, description="Lower edge of the band, in Hz.")
    high_hz: float = Field(..., gt=0.0, description="Upper edge of the band, in Hz.")
    gain_db: float = Field(..., description="Gain (positive) or cut (negative) in dB.")
    taper: float = Field(
        default=_DEFAULT_TAPER_OCTAVES,
        ge=0.0,
        le=1.0,
        description="Edge taper width in octaves (0 = hard rectangular band).",
    )

    @model_validator(mode="after")
    def _check_band(self) -> GainParams:
        if self.high_hz <= self.low_hz:
            msg = f"high_hz ({self.high_hz}) must be > low_hz ({self.low_hz})"
            raise ValueError(msg)
        return self


def _envelope(freqs: NDArray[np.float64], params: GainParams) -> NDArray[np.float64]:
    log_f = np.log2(freqs)
    log_lo = np.log2(params.low_hz)
    log_hi = np.log2(params.high_hz)
    if params.taper <= 0.0:
        return np.where((log_f >= log_lo) & (log_f <= log_hi), 1.0, 0.0)
    half = params.taper / 2.0
    rise = np.clip((log_f - (log_lo - half)) / params.taper, 0.0, 1.0)
    fall = np.clip(((log_hi + half) - log_f) / params.taper, 0.0, 1.0)
    smooth = 0.5 - 0.5 * np.cos(np.pi * np.minimum(rise, fall))
    return np.where((log_f < log_lo - half) | (log_f > log_hi + half), 0.0, smooth)


def _apply(curve: Curve, params: GainParams) -> Curve:
    delta = params.gain_db * _envelope(curve.freqs, params)
    return curve.add(delta)


SPEC: TransformSpec[GainParams] = TransformSpec(
    name="gain",
    title="Band gain",
    description="Add (or subtract) a fixed dB to a band, with cosine-tapered edges.",
    params_model=GainParams,
    apply=_apply,
)
