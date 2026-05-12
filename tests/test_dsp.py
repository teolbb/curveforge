"""Tests for the magnitude DSP primitives."""

from __future__ import annotations

import numpy as np
import pytest

from curveforge.dsp import (
    butterworth_highpass_db,
    highshelf_db,
    linear_tilt_db,
    lowshelf_db,
    peaking_db,
)


def test_lowshelf_dc_equals_gain():
    freqs = np.array([1.0, 10.0, 100.0])
    gain = lowshelf_db(freqs=freqs, corner_hz=100.0, gain_db=8.0)
    assert gain[0] == pytest.approx(8.0, abs=0.05)


def test_lowshelf_above_corner_decays_to_zero():
    freqs = np.array([10000.0, 100000.0])
    gain = lowshelf_db(freqs=freqs, corner_hz=100.0, gain_db=8.0)
    assert gain[-1] == pytest.approx(0.0, abs=0.05)


def test_highshelf_high_freq_equals_gain():
    freqs = np.array([100000.0])
    gain = highshelf_db(freqs=freqs, corner_hz=1000.0, gain_db=4.0)
    assert gain[0] == pytest.approx(4.0, abs=0.05)


def test_peaking_zero_gain_is_flat():
    freqs = np.geomspace(20.0, 20000.0, 64)
    gain = peaking_db(freqs=freqs, center_hz=1000.0, gain_db=0.0, q=1.0)
    assert np.allclose(gain, 0.0)


def test_peaking_peaks_at_center():
    freqs = np.geomspace(100.0, 10000.0, 200)
    gain = peaking_db(freqs=freqs, center_hz=1000.0, gain_db=6.0, q=2.0)
    peak_index = int(np.argmax(gain))
    assert freqs[peak_index] == pytest.approx(1000.0, rel=0.05)
    assert gain[peak_index] == pytest.approx(6.0, abs=0.1)


def test_butterworth_highpass_at_cutoff_is_minus_3db():
    gain = butterworth_highpass_db(
        freqs=np.array([100.0]),
        cutoff_hz=100.0,
        order=2,
    )
    assert gain[0] == pytest.approx(-3.0103, abs=0.01)


def test_butterworth_highpass_above_cutoff_approaches_zero():
    gain = butterworth_highpass_db(
        freqs=np.array([10000.0]),
        cutoff_hz=100.0,
        order=2,
    )
    assert abs(gain[0]) < 0.01


def test_linear_tilt_zero_at_anchor():
    freqs = np.array([500.0, 1000.0, 2000.0])
    gain = linear_tilt_db(freqs=freqs, db_per_octave=-1.0, anchor_hz=1000.0)
    assert gain[1] == pytest.approx(0.0)
    assert gain[0] == pytest.approx(1.0)
    assert gain[2] == pytest.approx(-1.0)
