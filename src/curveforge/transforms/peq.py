"""Parametric peaking EQ (RBJ analog biquad)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from curveforge.dsp import peaking_db
from curveforge.transforms._base import TransformSpec

if TYPE_CHECKING:
    from curveforge.curve import Curve


class PeqParams(BaseModel):
    """Parameters of the peaking-EQ transform."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    freq: float = Field(..., gt=0.0, description="Center frequency in Hz.")
    gain_db: float = Field(..., ge=-24.0, le=24.0, description="Peak gain in dB.")
    q: float = Field(
        default=1.0,
        gt=0.3,
        le=10.0,
        description="Quality factor: higher = narrower peak.",
    )


def _apply(curve: Curve, params: PeqParams) -> Curve:
    delta = peaking_db(
        freqs=curve.freqs,
        center_hz=params.freq,
        gain_db=params.gain_db,
        q=params.q,
    )
    return curve.add(delta)


SPEC: TransformSpec[PeqParams] = TransformSpec(
    name="peq",
    title="Parametric peak EQ",
    description="Bell-shaped peak/cut at a given frequency and Q (RBJ biquad).",
    params_model=PeqParams,
    apply=_apply,
)
