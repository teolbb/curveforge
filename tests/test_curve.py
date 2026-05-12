"""Tests for the Curve dataclass and grid utilities."""

from __future__ import annotations

import numpy as np
import pytest

from curveforge.curve import (
    Curve,
    iso_sixth_octave,
    iso_third_octave,
    log_grid,
)


def test_log_grid_endpoints_inclusive():
    grid = log_grid(low_hz=10.0, high_hz=20000.0, points_per_octave=24)
    assert grid[0] == pytest.approx(10.0)
    assert grid[-1] == pytest.approx(20000.0)


def test_log_grid_points_per_octave():
    grid = log_grid(low_hz=100.0, high_hz=200.0, points_per_octave=12)
    # 1 octave at 12 ppo => 13 points (inclusive)
    assert grid.size == 13


def test_log_grid_rejects_bad_range():
    with pytest.raises(ValueError, match="invalid grid range"):
        log_grid(low_hz=200.0, high_hz=100.0)


def test_curve_requires_strictly_increasing():
    with pytest.raises(ValueError, match="strictly increasing"):
        Curve(freqs=np.array([10.0, 10.0, 20.0]), gains_db=np.array([0.0, 0.0, 0.0]))


def test_curve_requires_finite_gains():
    with pytest.raises(ValueError, match="finite"):
        Curve(freqs=np.array([10.0, 20.0]), gains_db=np.array([0.0, np.inf]))


def test_curve_resample_is_log_linear():
    freqs = np.array([10.0, 100.0, 1000.0])
    gains = np.array([10.0, 0.0, -10.0])
    curve = Curve(freqs=freqs, gains_db=gains)
    new_freqs = np.array([10.0, np.sqrt(10.0 * 100.0), 100.0, 1000.0])
    out = curve.resample(new_freqs)
    # midpoint in log freq → midpoint in dB
    assert out.gains_db[1] == pytest.approx(5.0)


def test_iso_third_octave_contains_anchors():
    grid = iso_third_octave(low_hz=20.0, high_hz=20000.0)
    for anchor in (20.0, 100.0, 1000.0, 10000.0, 20000.0):
        assert anchor in grid.tolist()


def test_iso_sixth_octave_contains_1khz():
    grid = iso_sixth_octave(low_hz=100.0, high_hz=10000.0)
    assert any(abs(p - 1000.0) < 1e-6 for p in grid)
