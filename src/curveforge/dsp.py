"""Magnitude-only DSP primitives used by curves and transforms.

All functions return arrays of dB values evaluated on a frequency grid in Hz.
Signals are not synthesised here — curveforge only models target curves, never
processes audio. Phase is intentionally ignored: Dirac determines phase from
its own measurement, and target curves are magnitude-only by definition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

# Tiny floor to keep log10 well-defined when a magnitude collapses to zero.
_MAG_FLOOR: float = 1e-12


def lowshelf_db(
    freqs: NDArray[np.float64],
    corner_hz: float,
    gain_db: float,
) -> NDArray[np.float64]:
    """First-order analog low-shelf magnitude in dB.

    At DC the response is `gain_db`; at high frequency it is 0 dB; the corner
    is the geometric centre of the transition.
    """
    if corner_hz <= 0:
        msg = f"corner_hz must be > 0, got {corner_hz}"
        raise ValueError(msg)
    a = 10.0 ** (gain_db / 20.0)
    f2 = freqs * freqs
    fc2 = corner_hz * corner_hz
    out: NDArray[np.float64] = 10.0 * np.log10((f2 + (a * a) * fc2) / (f2 + fc2))
    return out


def highshelf_db(
    freqs: NDArray[np.float64],
    corner_hz: float,
    gain_db: float,
) -> NDArray[np.float64]:
    """First-order analog high-shelf magnitude in dB.

    At DC the response is 0 dB; at high frequency it is `gain_db`.
    """
    if corner_hz <= 0:
        msg = f"corner_hz must be > 0, got {corner_hz}"
        raise ValueError(msg)
    a = 10.0 ** (gain_db / 20.0)
    f2 = freqs * freqs
    fc2 = corner_hz * corner_hz
    out: NDArray[np.float64] = 10.0 * np.log10(((a * a) * f2 + fc2) / (f2 + fc2))
    return out


def peaking_db(
    freqs: NDArray[np.float64],
    center_hz: float,
    gain_db: float,
    q: float,
) -> NDArray[np.float64]:
    """RBJ analog peaking biquad magnitude in dB.

    Standard parametric EQ shape: a bell of width controlled by `q` centered at
    `center_hz` with peak (or trough) of `gain_db`.
    """
    if center_hz <= 0:
        msg = f"center_hz must be > 0, got {center_hz}"
        raise ValueError(msg)
    if q <= 0:
        msg = f"q must be > 0, got {q}"
        raise ValueError(msg)
    a = 10.0 ** (gain_db / 40.0)
    omega_0 = 2.0 * np.pi * center_hz
    omega = 2.0 * np.pi * freqs
    real_num = omega_0 * omega_0 - omega * omega
    imag_num = (a / q) * omega * omega_0
    imag_den = (1.0 / (a * q)) * omega * omega_0
    num_mag2 = real_num * real_num + imag_num * imag_num
    den_mag2 = real_num * real_num + imag_den * imag_den
    safe_num = np.maximum(num_mag2, _MAG_FLOOR)
    safe_den = np.maximum(den_mag2, _MAG_FLOOR)
    out: NDArray[np.float64] = 10.0 * np.log10(safe_num / safe_den)
    return out


def butterworth_highpass_db(
    freqs: NDArray[np.float64],
    cutoff_hz: float,
    order: int,
) -> NDArray[np.float64]:
    """Butterworth high-pass magnitude in dB. Order 1 to 8 supported."""
    if cutoff_hz <= 0:
        msg = f"cutoff_hz must be > 0, got {cutoff_hz}"
        raise ValueError(msg)
    if order < 1 or order > 8:  # noqa: PLR2004
        msg = f"order must be in [1, 8], got {order}"
        raise ValueError(msg)
    ratio = freqs / cutoff_hz
    return -10.0 * np.log10(1.0 + ratio ** (-2 * order))


def linear_tilt_db(
    freqs: NDArray[np.float64],
    db_per_octave: float,
    anchor_hz: float,
) -> NDArray[np.float64]:
    """Linear tilt in dB across the spectrum, anchored to `anchor_hz` (0 dB there)."""
    if anchor_hz <= 0:
        msg = f"anchor_hz must be > 0, got {anchor_hz}"
        raise ValueError(msg)
    return db_per_octave * np.log2(freqs / anchor_hz)
