"""Harman-style in-room target — bass-shelf only.

A first-order analog low-shelf that adds bass weight without affecting
the treble. The shelf transitions smoothly from `shelf_level` dB at low
frequencies to 0 dB at high frequencies, with the corner frequency
controlled by `shelf_corner`.

This shape captures the bass-boost recommendation from Harman
International's listener-preference research on in-room loudspeaker
response. The variant with an additional downward treble tilt is
implemented separately as `olive_welti_inroom`.

Sources:
- Olive, S. E. & Welti, T. — multiple AES papers on listener
  preference for loudspeaker frequency response.
- Toole, F. E. *Sound Reproduction: The Acoustics and Psychoacoustics
  of Loudspeakers and Rooms*, 3rd ed. (Routledge / AES Presents).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from curveforge.curves._base import CurveSpec
from curveforge.dsp import lowshelf_db

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


class HarmanParams(BaseModel):
    """Parameters of the Harman-style bass-shelf target."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    shelf_level: float = Field(
        default=6.0,
        ge=0.0,
        le=14.0,
        description=(
            "Bass-shelf gain in dB. Typical values: 4-6 for critical "
            "listening, 6-8 for balanced music, 10-14 for cinema or "
            "bass-heavy use."
        ),
    )
    shelf_corner: float = Field(
        default=105.0,
        ge=40.0,
        le=300.0,
        description=(
            "Shelf corner frequency in Hz. Higher values extend the shelf "
            "into mid-bass for a wider HT-style sound; lower values tighten "
            "the shelf to deep bass only."
        ),
    )


def _render(params: HarmanParams, freqs: NDArray[np.float64]) -> NDArray[np.float64]:
    return lowshelf_db(
        freqs=freqs,
        corner_hz=params.shelf_corner,
        gain_db=params.shelf_level,
    )


SPEC: CurveSpec[HarmanParams] = CurveSpec(
    name="harman",
    title="Harman-style bass shelf",
    description=(
        "First-order low-shelf bass boost with no treble adjustment. "
        "The community-standard Dirac target for music."
    ),
    citation=(
        "Olive, S. E. & Welti, T. — Harman International AES research on "
        "listener preference for in-room loudspeaker response. See also "
        "Toole, F. E., Sound Reproduction (3rd ed., 2017), Routledge / AES Presents."
    ),
    params_model=HarmanParams,
    render=_render,
)
