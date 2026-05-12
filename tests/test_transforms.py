"""Tests for built-in transforms."""

from __future__ import annotations

import numpy as np
import pytest

from curveforge.curve import Curve, log_grid
from curveforge.transforms import get_transform, list_transforms
from curveforge.transforms.gain import GainParams
from curveforge.transforms.peq import PeqParams
from curveforge.transforms.rolloff import RolloffParams
from curveforge.transforms.shelf import ShelfParams
from curveforge.transforms.tilt import TiltParams


@pytest.fixture
def flat_curve() -> Curve:
    grid = log_grid(low_hz=10.0, high_hz=20000.0, points_per_octave=24)
    return Curve(freqs=grid, gains_db=np.zeros_like(grid))


def test_registry_contains_all_five():
    names = {spec.name for spec in list_transforms()}
    assert names == {"gain", "peq", "shelf", "rolloff", "tilt"}


def test_gain_band_centered_value(flat_curve: Curve):
    spec = get_transform("gain")
    params = GainParams(low_hz=80.0, high_hz=200.0, gain_db=6.0, taper=0.0)
    out = spec.apply(flat_curve, params)
    # Inside the hard band: full +6 dB
    inside = (flat_curve.freqs >= 80.0) & (flat_curve.freqs <= 200.0)
    assert np.allclose(out.gains_db[inside], 6.0)
    # Outside: 0 dB
    outside = (flat_curve.freqs < 60.0) | (flat_curve.freqs > 250.0)
    assert np.allclose(out.gains_db[outside], 0.0)


def test_gain_taper_smooths_edges(flat_curve: Curve):
    spec = get_transform("gain")
    params = GainParams(low_hz=80.0, high_hz=200.0, gain_db=6.0, taper=0.5)
    out = spec.apply(flat_curve, params)
    # Near the band edges, value is between 0 and 6
    edge_mask = (flat_curve.freqs > 50.0) & (flat_curve.freqs < 80.0)
    edge_vals = out.gains_db[edge_mask]
    assert np.any((edge_vals > 0.5) & (edge_vals < 5.5))


def test_peq_peaks_at_center(flat_curve: Curve):
    spec = get_transform("peq")
    params = PeqParams(freq=1000.0, gain_db=6.0, q=2.0)
    out = spec.apply(flat_curve, params)
    peak = float(out.gains_db.max())
    assert peak == pytest.approx(6.0, abs=0.1)


def test_shelf_low_boost(flat_curve: Curve):
    spec = get_transform("shelf")
    params = ShelfParams(type="low", corner=100.0, gain_db=8.0)
    out = spec.apply(flat_curve, params)
    # DC region close to +8
    low_mask = flat_curve.freqs < 20.0
    assert out.gains_db[low_mask].max() > 7.0
    # Above corner ramps down
    high_mask = flat_curve.freqs > 5000.0
    assert np.all(out.gains_db[high_mask] < 0.5)


def test_rolloff_attenuates_below_cutoff(flat_curve: Curve):
    spec = get_transform("rolloff")
    params = RolloffParams(freq=20.0, order=2)
    out = spec.apply(flat_curve, params)
    # At 10 Hz (1 octave below cutoff): 2nd-order = -12 dB
    idx = int(np.argmin(np.abs(flat_curve.freqs - 10.0)))
    assert out.gains_db[idx] == pytest.approx(-12.0, abs=0.5)


def test_tilt_anchor_unchanged(flat_curve: Curve):
    spec = get_transform("tilt")
    params = TiltParams(db_per_octave=-1.0, anchor_hz=1000.0)
    out = spec.apply(flat_curve, params)
    idx = int(np.argmin(np.abs(flat_curve.freqs - 1000.0)))
    assert out.gains_db[idx] == pytest.approx(0.0, abs=0.05)


def test_gain_rejects_inverted_band():
    with pytest.raises(ValueError, match="must be > low_hz"):
        GainParams(low_hz=1000.0, high_hz=100.0, gain_db=0.0)
