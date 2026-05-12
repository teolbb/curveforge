"""Butterworth low-end rolloff (high-pass attenuation)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from curveforge.dsp import butterworth_highpass_db
from curveforge.transforms._base import TransformSpec

if TYPE_CHECKING:
    from curveforge.curve import Curve


class RolloffParams(BaseModel):
    """Parameters of the low-end rolloff transform."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    freq: float = Field(..., gt=0.0, description="Cutoff frequency in Hz (-3 dB point).")
    order: int = Field(
        default=2,
        ge=1,
        le=8,
        description="Butterworth order; 2 is a typical safe default.",
    )


def _apply(curve: Curve, params: RolloffParams) -> Curve:
    delta = butterworth_highpass_db(
        freqs=curve.freqs,
        cutoff_hz=params.freq,
        order=params.order,
    )
    return curve.add(delta)


SPEC: TransformSpec[RolloffParams] = TransformSpec(
    name="rolloff",
    title="Low-end rolloff",
    description="Nth-order Butterworth high-pass magnitude added to the curve.",
    params_model=RolloffParams,
    apply=_apply,
)
