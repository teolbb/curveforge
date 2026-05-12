"""Tests for the .targetcurve reader and writer."""

from __future__ import annotations

import numpy as np
import pytest

from curveforge.curve import Curve
from curveforge.output.targetcurve import (
    TargetCurveError,
    parse_targetcurve,
    serialize_targetcurve,
)


def _sample_curve() -> Curve:
    freqs = np.array([10.0, 100.0, 1000.0, 20000.0])
    gains = np.array([8.0, 4.0, 0.0, 0.0])
    return Curve(freqs=freqs, gains_db=gains)


def test_serialize_then_parse_roundtrip():
    curve = _sample_curve()
    text = serialize_targetcurve(
        curve=curve,
        name="Test",
        device_name="Living Room",
        low_limit_hz=10.0,
        high_limit_hz=24000.0,
    )
    parsed = parse_targetcurve(text)
    assert parsed.name == "Test"
    assert parsed.device_name == "Living Room"
    assert parsed.low_limit_hz == 10.0
    assert parsed.high_limit_hz == 24000.0
    assert np.allclose(parsed.curve.freqs, curve.freqs)
    assert np.allclose(parsed.curve.gains_db, curve.gains_db)


def test_serialized_format_has_required_sections():
    text = serialize_targetcurve(
        curve=_sample_curve(),
        name="X",
        device_name="Y",
        low_limit_hz=10.0,
        high_limit_hz=24000.0,
    )
    for section in ("NAME\n", "DEVICENAME\n", "BREAKPOINTS\n", "LOWLIMITHZ\n", "HIGHLIMITHZ\n"):
        assert section in text


def test_parse_rejects_unsorted_breakpoints():
    text = "NAME\nx\nDEVICENAME\nx\nBREAKPOINTS\n100 0\n50 0\nLOWLIMITHZ\n10\nHIGHLIMITHZ\n20000\n"
    with pytest.raises(TargetCurveError, match="strictly sorted"):
        parse_targetcurve(text)


def test_parse_rejects_missing_section():
    text = "NAME\nx\nBREAKPOINTS\n10 0\n20 0\nLOWLIMITHZ\n10\nHIGHLIMITHZ\n20000\n"
    with pytest.raises(TargetCurveError, match="missing required section"):
        parse_targetcurve(text)


def test_serialize_rejects_invalid_limits():
    with pytest.raises(TargetCurveError, match="invalid limits"):
        serialize_targetcurve(
            curve=_sample_curve(),
            name="x",
            device_name="x",
            low_limit_hz=-1.0,
            high_limit_hz=10.0,
        )
