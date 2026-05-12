"""Olive-Welti-McMullin 2013 in-room preferred target (parametric).

Approximates the in-room loudspeaker target that emerged from Olive, Welti
& McMullin's listener-preference work at Harman International. Two
in-room target shapes are commonly referenced:

- ``RR_G``: flat, with a bass boost.
- ``RR1_G``: a straight line that slopes downwards with frequency, with
  bass boost. The downward-tilted variant performed best in their in-room
  loudspeaker preference tests.

We model ``RR1_G`` here: a low-shelf bass enhancement plus a linear downward
tilt above the tilt anchor. The published results note that listeners
prefer roughly +2 dB more bass and treble in the in-room loudspeaker target
than in the headphone target — implying user-tunable shelf and tilt are
important to capture taste variation.

Sources:
- Olive, S. E., Welti, T., & McMullin, E. (2013). 'Listener Preferences
  for In-Room Loudspeaker and Headphone Target Responses.' AES 135th
  Convention, paper 8994. (Primary preference data for the in-room target.)
- Olive, S. E., Welti, T., & McMullin, E. (2013). 'Listener Preferences
  for Different Headphone Target Response Curves.' AES 134th Convention,
  paper 8867. (Introduces RR1_G as the reference in-room curve from which
  the corresponding headphone target was derived.)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from curveforge.curves._base import CurveSpec
from curveforge.dsp import linear_tilt_db, lowshelf_db

if TYPE_CHECKING:
    from numpy.typing import NDArray


class OliveWeltiInRoomParams(BaseModel):
    """Parameters of the Olive-Welti RR1_G in-room target."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bass_shelf: float = Field(
        default=6.0,
        ge=0.0,
        le=10.0,
        description=(
            "Low-shelf bass gain in dB. Olive, Welti & McMullin 2013 found preference for ~+6 dB."
        ),
    )
    bass_corner: float = Field(
        default=105.0,
        ge=60.0,
        le=250.0,
        description=(
            "Low-shelf corner frequency in Hz (≈105 Hz to match the published RR1_G shape)."
        ),
    )
    treble_tilt: float = Field(
        default=-1.0,
        ge=-2.0,
        le=0.0,
        description="Linear tilt above the anchor in dB/octave (negative = darker).",
    )
    tilt_anchor: float = Field(
        default=1000.0,
        ge=500.0,
        le=2000.0,
        description="Frequency at which the tilt has 0 dB effect.",
    )


def _render(
    params: OliveWeltiInRoomParams,
    freqs: NDArray[np.float64],
) -> NDArray[np.float64]:
    bass = lowshelf_db(freqs=freqs, corner_hz=params.bass_corner, gain_db=params.bass_shelf)
    tilt = linear_tilt_db(
        freqs=freqs,
        db_per_octave=params.treble_tilt,
        anchor_hz=params.tilt_anchor,
    )
    treble = np.where(freqs > params.tilt_anchor, tilt, 0.0)
    return bass + treble


SPEC: CurveSpec[OliveWeltiInRoomParams] = CurveSpec(
    name="olive_welti_inroom",
    title="Olive-Welti in-room (RR1_G family)",
    description=(
        "Bass shelf plus linear downward tilt above 1 kHz. "
        "Tracks the Olive-Welti-McMullin RR1_G shape."
    ),
    citation=(
        "Olive, S. E., Welti, T., & McMullin, E. (2013). 'Listener Preferences "
        "for In-Room Loudspeaker and Headphone Target Responses.' AES 135th "
        "Convention, paper 8994. See also paper 8867 (AES 134th, 2013) for the "
        "RR1_G reference curve."
    ),
    params_model=OliveWeltiInRoomParams,
    render=_render,
)
