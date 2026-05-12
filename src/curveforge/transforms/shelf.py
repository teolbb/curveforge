"""First-order low- or high-shelf added on top of an existing curve."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field

from curveforge.dsp import highshelf_db, lowshelf_db
from curveforge.transforms._base import TransformSpec

if TYPE_CHECKING:
    from curveforge.curve import Curve

ShelfType = Literal["low", "high"]


class ShelfParams(BaseModel):
    """Parameters of the shelf transform."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    type: ShelfType = Field(..., description="'low' for bass shelf, 'high' for treble shelf.")
    corner: float = Field(..., gt=0.0, description="Shelf corner frequency in Hz.")
    gain_db: float = Field(..., ge=-18.0, le=18.0, description="Shelf gain in dB.")


def _apply(curve: Curve, params: ShelfParams) -> Curve:
    if params.type == "low":
        delta = lowshelf_db(
            freqs=curve.freqs,
            corner_hz=params.corner,
            gain_db=params.gain_db,
        )
    else:
        delta = highshelf_db(
            freqs=curve.freqs,
            corner_hz=params.corner,
            gain_db=params.gain_db,
        )
    return curve.add(delta)


SPEC: TransformSpec[ShelfParams] = TransformSpec(
    name="shelf",
    title="Shelf",
    description="First-order low or high shelf added on top of the current curve.",
    params_model=ShelfParams,
    apply=_apply,
)
