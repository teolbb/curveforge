"""Tests for built-in curves."""

from __future__ import annotations

import numpy as np
import pytest

from curveforge.curves import get_curve, list_curves
from curveforge.curves.b_and_k import BAndKParams
from curveforge.curves.breakpoints import BreakpointsParams
from curveforge.curves.flat import FlatParams
from curveforge.curves.harman import HarmanParams
from curveforge.curves.olive_welti_inroom import OliveWeltiInRoomParams
from curveforge.curves.toole_inroom import TooleInRoomParams
from curveforge.curves.welti_sub import WeltiSubParams


def test_registry_contains_all_seven():
    names = {spec.name for spec in list_curves()}
    expected = {
        "harman",
        "olive_welti_inroom",
        "b_and_k",
        "toole_inroom",
        "welti_sub",
        "flat",
        "breakpoints",
    }
    assert names == expected


def test_unknown_curve_raises():
    with pytest.raises(KeyError, match="unknown curve"):
        get_curve("not_a_curve")


def test_flat_returns_zeros():
    spec = get_curve("flat")
    freqs = np.geomspace(10.0, 20000.0, 32)
    gains = spec.render(FlatParams(), freqs)
    assert np.allclose(gains, 0.0)


def test_harman_dc_asymptote_equals_shelf_level():
    """At very low frequencies the shelf gain approaches shelf_level."""
    spec = get_curve("harman")
    gains = spec.render(HarmanParams(shelf_level=8.0), np.array([0.5]))
    assert gains[0] == pytest.approx(8.0, abs=0.05)


def test_harman_high_freq_asymptote_is_zero():
    """At very high frequencies the shelf approaches 0 dB."""
    spec = get_curve("harman")
    gains = spec.render(HarmanParams(shelf_level=8.0), np.array([100000.0]))
    assert gains[0] == pytest.approx(0.0, abs=0.05)


def test_harman_shelf_level_zero_is_flat():
    """A 0 dB shelf reduces to zero everywhere."""
    spec = get_curve("harman")
    freqs = np.geomspace(10.0, 20000.0, 50)
    gains = spec.render(HarmanParams(shelf_level=0.0), freqs)
    assert np.allclose(gains, 0.0, atol=1e-9)


def test_harman_is_monotonically_decreasing():
    """The low-shelf must never rise as frequency increases."""
    spec = get_curve("harman")
    freqs = np.geomspace(10.0, 20000.0, 200)
    gains = spec.render(HarmanParams(shelf_level=8.0), freqs)
    # Allow a tiny numerical tolerance.
    assert np.all(np.diff(gains) <= 1e-9)


def test_harman_higher_level_means_more_bass():
    """At any bass frequency, raising shelf_level monotonically increases gain."""
    spec = get_curve("harman")
    freqs = np.array([10.0, 30.0, 50.0, 100.0])
    g4 = spec.render(HarmanParams(shelf_level=4.0), freqs)
    g8 = spec.render(HarmanParams(shelf_level=8.0), freqs)
    g12 = spec.render(HarmanParams(shelf_level=12.0), freqs)
    assert np.all(g8 > g4)
    assert np.all(g12 > g8)


def test_harman_corner_shift_translates_shape():
    spec = get_curve("harman")
    freqs = np.array([100.0])
    base_gain = spec.render(HarmanParams(shelf_level=8.0, shelf_corner=105.0), freqs)
    # Move corner up: 100 Hz now sees more bass shelf left over
    shifted_gain = spec.render(HarmanParams(shelf_level=8.0, shelf_corner=200.0), freqs)
    assert shifted_gain[0] > base_gain[0]


def test_olive_welti_inroom_has_bass_shelf_and_treble_drop():
    spec = get_curve("olive_welti_inroom")
    params = OliveWeltiInRoomParams()
    freqs = np.array([20.0, 1000.0, 10000.0])
    gains = spec.render(params, freqs)
    assert gains[0] > 4.0  # bass boosted
    assert gains[1] == pytest.approx(0.0, abs=0.5)  # anchor near 0
    assert gains[2] < gains[1]  # treble tilted down


def test_b_and_k_treble_slope_about_minus_3db_at_20khz():
    spec = get_curve("b_and_k")
    params = BAndKParams()
    gains = spec.render(params, np.array([200.0, 20000.0]))
    assert gains[1] < gains[0]
    delta = gains[1] - gains[0]
    assert delta == pytest.approx(-5.5, abs=1.0)


def test_toole_default_flat_below_corner():
    spec = get_curve("toole_inroom")
    params = TooleInRoomParams()
    gains = spec.render(params, np.array([100.0, 200.0, 500.0]))
    assert np.allclose(gains, 0.0, atol=1e-6)


def test_toole_default_tilts_above_corner():
    spec = get_curve("toole_inroom")
    params = TooleInRoomParams()
    gains = spec.render(params, np.array([1000.0, 10000.0]))
    assert gains[0] < 0
    assert gains[1] < gains[0]


def test_welti_sub_above_crossover_drops_to_zero():
    spec = get_curve("welti_sub")
    params = WeltiSubParams()
    freqs = np.array([10.0, 30.0, 80.0, 1000.0])
    gains = spec.render(params, freqs)
    assert gains[0] == pytest.approx(params.shelf_level, abs=0.5)
    assert gains[-1] == pytest.approx(0.0, abs=0.5)


def test_breakpoints_curve_interpolates_log_linear():
    spec = get_curve("breakpoints")
    params = BreakpointsParams(points=[(10.0, 10.0), (1000.0, 0.0)])
    gains = spec.render(params, np.array([100.0]))
    # 100 Hz is the geometric midpoint of 10 and 1000 in log freq
    assert gains[0] == pytest.approx(5.0, abs=1e-6)


def test_breakpoints_rejects_unsorted_input():
    with pytest.raises(ValueError, match="strictly sorted"):
        BreakpointsParams(points=[(100.0, 0.0), (50.0, 1.0)])
