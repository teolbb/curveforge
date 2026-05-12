"""Floyd Toole's preferred in-room target (parametric).

Toole's prescription for steady-state in-room response of a well-designed
loudspeaker (i.e. one with smooth on- and off-axis behaviour) is a gentle
downward tilt — typically 2 to 3 dB per decade (~ 0.6 to 0.9 dB/octave) above
~500 Hz, with the exact slope determined by the speaker's directivity. Below
~500 Hz the response should remain near flat; the bass region is dominated
by room modes and is not generally a place for spectral tilt corrections.

Toole emphasises that this is a description of what *naturally* happens with
good speakers in normal rooms, not a target to which arbitrary speakers
should be equalised. We expose `tilt`, `tilt_corner`, and an optional
`bass_shelf` for users who want to combine the Toole tilt with a bass
boost (a common practical compromise documented in the *Sound Reproduction*
3rd edition discussion of personal preferences).

Sources:
- Toole, F. E. *Sound Reproduction: The Acoustics and Psychoacoustics of
  Loudspeakers and Rooms*, 3rd ed. (Routledge / AES Presents, 2017).
- Toole, F. E. (2015). "The Measurement and Calibration of Sound
  Reproducing Systems." J. AES 63(7/8), pp. 512-541. (Open Access via the
  AES E-Library.)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from curveforge.curves._base import CurveSpec
from curveforge.dsp import linear_tilt_db, lowshelf_db

if TYPE_CHECKING:
    from numpy.typing import NDArray


class TooleInRoomParams(BaseModel):
    """Parameters of the Toole-style in-room target."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tilt: float = Field(
        default=-0.7,
        ge=-1.5,
        le=0.0,
        description="Downward tilt above tilt_corner in dB/octave (Toole: ~ -0.6 to -0.9).",
    )
    tilt_corner: float = Field(
        default=500.0,
        ge=200.0,
        le=2000.0,
        description="Frequency above which the tilt applies; flat below.",
    )
    bass_shelf: float = Field(
        default=0.0,
        ge=0.0,
        le=8.0,
        description="Optional low-shelf bass gain in dB (Toole-neutral default = 0).",
    )
    bass_corner: float = Field(
        default=120.0,
        ge=60.0,
        le=300.0,
        description="Low-shelf corner frequency for the optional bass boost.",
    )


def _render(params: TooleInRoomParams, freqs: NDArray[np.float64]) -> NDArray[np.float64]:
    tilt = linear_tilt_db(
        freqs=freqs,
        db_per_octave=params.tilt,
        anchor_hz=params.tilt_corner,
    )
    treble = np.where(freqs > params.tilt_corner, tilt, 0.0)
    bass = lowshelf_db(freqs=freqs, corner_hz=params.bass_corner, gain_db=params.bass_shelf)
    return bass + treble


SPEC: CurveSpec[TooleInRoomParams] = CurveSpec(
    name="toole_inroom",
    title="Toole in-room",
    description="Flat below ~500 Hz, gentle downward tilt above. Optional bass shelf.",
    citation=(
        "Toole, F. E. (2017). Sound Reproduction: The Acoustics and Psychoacoustics of "
        "Loudspeakers and Rooms (3rd ed.). Routledge / AES Presents."
    ),
    params_model=TooleInRoomParams,
    render=_render,
)
