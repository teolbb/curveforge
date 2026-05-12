"""Brüel & Kjær 1974 in-room target (parametric).

The B&K curve, derived from B&K Application Note 17-197 (1974) measuring
critical-listening rooms in domestic settings. The classical shape:

- A modest bass plateau (~+2.5 to +3 dB) up to about 200 Hz.
- A roughly linear downward slope above 200 Hz, ending at ~-3 dB at 20 kHz
  (≈0.83 dB/octave).

Often used as an alternative to Harman: more weight on smooth treble taper,
less explicit bass shelf. Implemented as a flat plateau below the corner
plus a linear tilt above the corner — a clamped piecewise that is faithful
to the published shape.

Sources:
- Brüel & Kjær Application Note 17-197 (1974).
- Discussion threads on AVS Forum, AVNirvana, HouseCurve documentation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from curveforge.curves._base import CurveSpec

if TYPE_CHECKING:
    from numpy.typing import NDArray


class BAndKParams(BaseModel):
    """Parameters of the Brüel & Kjær 1974 target."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bass_level: float = Field(
        default=3.0,
        ge=0.0,
        le=6.0,
        description="Bass plateau in dB (B&K original ~ 2.5 to 3 dB).",
    )
    bass_corner: float = Field(
        default=200.0,
        ge=100.0,
        le=400.0,
        description="Frequency at which the plateau ends and the tilt begins.",
    )
    treble_slope: float = Field(
        default=-0.83,
        ge=-1.5,
        le=0.0,
        description="Downward slope above the bass corner in dB/octave (B&K ≈ -0.83).",
    )


def _render(params: BAndKParams, freqs: NDArray[np.float64]) -> NDArray[np.float64]:
    octaves_above = np.maximum(np.log2(freqs / params.bass_corner), 0.0)
    return params.bass_level + params.treble_slope * octaves_above


SPEC: CurveSpec[BAndKParams] = CurveSpec(
    name="b_and_k",
    title="Brüel & Kjær 1974",
    description="Flat bass plateau plus linear downward slope above the corner.",
    citation=(
        "Brüel & Kjær Application Note 17-197 (1974), 'Relevant loudspeaker tests in "
        "studios in Hi-Fi dealers' demo rooms in the home etc., using 1/3 octave, "
        "pink-weighted, random noise.'"
    ),
    params_model=BAndKParams,
    render=_render,
)
