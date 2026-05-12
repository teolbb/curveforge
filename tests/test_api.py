"""Tests for the high-level Python API."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from curveforge import (
    Curve,
    build_curve,
    list_curves,
    list_transforms,
    parse_targetcurve,
    write_targetcurve,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_build_curve_default_returns_curve():
    curve = build_curve(base="flat")
    assert isinstance(curve, Curve)
    assert np.allclose(curve.gains_db, 0.0)


def test_build_curve_with_base_params():
    """harman at shelf_level=8: deep bass approaches +8 dB, treble approaches 0."""
    curve = build_curve(base="harman", base_params={"shelf_level": 8.0})
    low_idx = int(np.argmin(np.abs(curve.freqs - 20.0)))
    high_idx = int(np.argmin(np.abs(curve.freqs - 10000.0)))
    assert curve.gains_db[low_idx] == pytest.approx(8.0, abs=0.2)
    assert curve.gains_db[high_idx] == pytest.approx(0.0, abs=0.2)


def test_build_curve_with_transforms():
    curve = build_curve(
        base="flat",
        transforms=[("peq", {"freq": 1000, "gain_db": 6, "q": 2})],
    )
    peak = float(curve.gains_db.max())
    assert peak == pytest.approx(6.0, abs=0.5)


def test_build_curve_writes_via_write_targetcurve(tmp_path: Path):
    curve = build_curve(base="harman", base_params={"shelf_level": 6})
    out = tmp_path / "out.targetcurve"
    write_targetcurve(
        path=out,
        curve=curve,
        name="test",
        device_name="test",
        low_limit_hz=10,
        high_limit_hz=24000,
    )
    parsed = parse_targetcurve(out.read_text(encoding="utf-8"))
    assert parsed.name == "test"
    np.testing.assert_allclose(parsed.curve.gains_db, curve.gains_db, atol=1e-3)


def test_registry_helpers_callable_from_top_level():
    curves = list_curves()
    transforms = list_transforms()
    assert any(c.name == "harman" for c in curves)
    assert any(t.name == "peq" for t in transforms)
