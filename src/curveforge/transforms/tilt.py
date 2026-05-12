"""Linear spectral tilt (in dB per octave) added across the audible band."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from curveforge.dsp import linear_tilt_db
from curveforge.transforms._base import TransformSpec

if TYPE_CHECKING:
    from curveforge.curve import Curve


class TiltParams(BaseModel):
    """Parameters of the linear-tilt transform."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    db_per_octave: float = Field(
        ...,
        ge=-3.0,
        le=3.0,
        description="Tilt slope in dB per octave (negative = darker).",
    )
    anchor_hz: float = Field(
        default=1000.0,
        gt=0.0,
        description="Frequency at which the tilt has zero effect.",
    )


def _apply(curve: Curve, params: TiltParams) -> Curve:
    delta = linear_tilt_db(
        freqs=curve.freqs,
        db_per_octave=params.db_per_octave,
        anchor_hz=params.anchor_hz,
    )
    return curve.add(delta)


SPEC: TransformSpec[TiltParams] = TransformSpec(
    name="tilt",
    title="Linear tilt",
    description="Linear dB/octave slope across the spectrum, anchored to a chosen Hz.",
    params_model=TiltParams,
    apply=_apply,
)
