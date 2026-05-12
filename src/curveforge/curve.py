"""Curve dataclass and grid utilities.

A `Curve` is the in-memory representation of a magnitude response: a strictly
increasing array of frequencies (Hz) and a parallel array of gains (dB). All
curveforge math operates on dense, log-spaced grids; export rescales to the
breakpoint set requested by the recipe.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

DEFAULT_GRID_LOW_HZ: Final[float] = 5.0
DEFAULT_GRID_HIGH_HZ: Final[float] = 24000.0
DEFAULT_GRID_POINTS_PER_OCTAVE: Final[int] = 48  # 1/48 octave: dense enough for clean transforms

_MIN_GRID_POINTS: Final[int] = 2


@dataclass(frozen=True, slots=True)
class Curve:
    """An immutable magnitude response sampled on a log-spaced frequency grid.

    Attributes:
        freqs: Strictly increasing 1-D array of frequencies in Hz.
        gains_db: Magnitude in dB at each frequency in `freqs`. Same length.
    """

    freqs: NDArray[np.float64]
    gains_db: NDArray[np.float64]

    def __post_init__(self) -> None:
        """Validate invariants of the curve grid."""
        if self.freqs.ndim != 1 or self.gains_db.ndim != 1:
            msg = "freqs and gains_db must be 1-D arrays"
            raise ValueError(msg)
        if self.freqs.shape != self.gains_db.shape:
            msg = f"shape mismatch: freqs={self.freqs.shape}, gains_db={self.gains_db.shape}"
            raise ValueError(msg)
        if self.freqs.size < _MIN_GRID_POINTS:
            msg = f"curve must have at least {_MIN_GRID_POINTS} grid points"
            raise ValueError(msg)
        if not np.all(np.diff(self.freqs) > 0):
            msg = "freqs must be strictly increasing"
            raise ValueError(msg)
        if not np.all(np.isfinite(self.gains_db)):
            msg = "gains_db must be finite"
            raise ValueError(msg)

    def with_gains(self, gains_db: NDArray[np.float64]) -> Curve:
        """Return a new curve with the same grid and the given gains."""
        return Curve(freqs=self.freqs, gains_db=gains_db)

    def add(self, delta_db: NDArray[np.float64]) -> Curve:
        """Return a new curve with `delta_db` added to gains."""
        if delta_db.shape != self.gains_db.shape:
            msg = f"delta_db shape {delta_db.shape} != grid {self.gains_db.shape}"
            raise ValueError(msg)
        return self.with_gains(self.gains_db + delta_db)

    def resample(self, new_freqs: NDArray[np.float64]) -> Curve:
        """Return a new curve resampled at `new_freqs` (linear in log f, linear in dB).

        Frequencies outside the source range are clamped to the source endpoints.
        """
        log_src = np.log10(self.freqs)
        log_dst = np.log10(new_freqs)
        gains = np.interp(log_dst, log_src, self.gains_db)
        return Curve(freqs=new_freqs.copy(), gains_db=gains)


def log_grid(
    low_hz: float = DEFAULT_GRID_LOW_HZ,
    high_hz: float = DEFAULT_GRID_HIGH_HZ,
    points_per_octave: int = DEFAULT_GRID_POINTS_PER_OCTAVE,
) -> NDArray[np.float64]:
    """Build a log-spaced frequency grid from `low_hz` to `high_hz` inclusive."""
    if low_hz <= 0 or high_hz <= low_hz:
        msg = f"invalid grid range: low={low_hz}, high={high_hz}"
        raise ValueError(msg)
    if points_per_octave < 1:
        msg = f"points_per_octave must be >= 1, got {points_per_octave}"
        raise ValueError(msg)
    octaves = np.log2(high_hz / low_hz)
    n = round(octaves * points_per_octave) + 1
    grid: NDArray[np.float64] = np.logspace(np.log10(low_hz), np.log10(high_hz), n)
    return grid


# Standard ISO R10 1/3-octave centers between 10 Hz and 20 kHz. This is a
# fixed published series, so an in-code constant is correct.
# curveforge: allow-literal
_ISO_R10_THIRD_OCTAVE: Final[tuple[float, ...]] = (
    10.0,
    12.5,
    16.0,
    20.0,
    25.0,
    31.5,
    40.0,
    50.0,
    63.0,
    80.0,
    100.0,
    125.0,
    160.0,
    200.0,
    250.0,
    315.0,
    400.0,
    500.0,
    630.0,
    800.0,
    1000.0,
    1250.0,
    1600.0,
    2000.0,
    2500.0,
    3150.0,
    4000.0,
    5000.0,
    6300.0,
    8000.0,
    10000.0,
    12500.0,
    16000.0,
    20000.0,
)


def iso_third_octave(low_hz: float, high_hz: float) -> NDArray[np.float64]:
    """Return ISO R10 1/3-octave centers within `[low_hz, high_hz]`."""
    points = np.array(_ISO_R10_THIRD_OCTAVE, dtype=np.float64)
    mask = (points >= low_hz) & (points <= high_hz)
    return points[mask]


def iso_sixth_octave(low_hz: float, high_hz: float) -> NDArray[np.float64]:
    """Return 1/6-octave centers within `[low_hz, high_hz]` based on the 1 kHz reference."""
    return _octave_subdivision(low_hz=low_hz, high_hz=high_hz, divisions=6)


def _octave_subdivision(low_hz: float, high_hz: float, divisions: int) -> NDArray[np.float64]:
    if low_hz <= 0 or high_hz <= low_hz:
        msg = f"invalid range: low={low_hz}, high={high_hz}"
        raise ValueError(msg)
    n_low = int(np.floor(np.log2(low_hz / 1000.0) * divisions))
    n_high = int(np.ceil(np.log2(high_hz / 1000.0) * divisions))
    indices = np.arange(n_low, n_high + 1)
    points = 1000.0 * np.power(2.0, indices / divisions)
    mask = (points >= low_hz) & (points <= high_hz)
    return points[mask]
