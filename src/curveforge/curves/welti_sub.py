"""Welti subwoofer-band target (parametric).

Welti's published research focuses on optimum subwoofer placement and
multi-sub summation rather than on a single named target curve. For a
sub-only Dirac calibration, the practical target derived from the Welti
tradition is a low-shelf gain across the sub band that rolls down to 0 dB
near the crossover to the mains.

We model it as a single low-shelf with corner at the crossover frequency
and gain set by the user. Set Dirac's HIGHLIMITHZ to your crossover so the
correction stays in the sub band.

Sources:
- Welti, T. (2002). 'How Many Subwoofers Are Enough?' AES 112th Convention.
- Welti, T. and Devantier, A. (2006). 'Low-Frequency Optimization Using
  Multiple Subwoofers.' J. AES 54(5), pp. 347-364.
- Welti, T. *Subwoofers: Optimum Number and Locations* (Harman whitepaper).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from curveforge.curves._base import CurveSpec
from curveforge.dsp import lowshelf_db

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


class WeltiSubParams(BaseModel):
    """Parameters of the Welti-style subwoofer-band target."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    shelf_level: float = Field(
        default=6.0,
        ge=0.0,
        le=14.0,
        description="Sub-band low-shelf gain in dB.",
    )
    crossover_hz: float = Field(
        default=80.0,
        ge=40.0,
        le=200.0,
        description=(
            "Shelf corner frequency, matching your sub-to-mains crossover. "
            "Above this frequency the shelf has rolled down toward 0 dB."
        ),
    )


def _render(params: WeltiSubParams, freqs: NDArray[np.float64]) -> NDArray[np.float64]:
    return lowshelf_db(
        freqs=freqs,
        corner_hz=params.crossover_hz,
        gain_db=params.shelf_level,
    )


SPEC: CurveSpec[WeltiSubParams] = CurveSpec(
    name="welti_sub",
    title="Welti subwoofer band",
    description="Sub-band low-shelf with corner at the crossover frequency.",
    citation=(
        "Welti, T. & Devantier, A. (2006). 'Low-Frequency Optimization Using Multiple "
        "Subwoofers.' J. AES 54(5). See also Welti, 'Subwoofers: Optimum Number and "
        "Locations' (Harman International)."
    ),
    params_model=WeltiSubParams,
    render=_render,
)
