"""Tests for the tweak path: load existing .targetcurve, apply transforms."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from curveforge.build import tweak
from curveforge.config import ConfigError, load_tweak_recipe
from curveforge.curve import Curve
from curveforge.output.targetcurve import parse_targetcurve, serialize_targetcurve

if TYPE_CHECKING:
    from pathlib import Path


def _flat_targetcurve_text() -> str:
    freqs = np.array([10.0, 100.0, 1000.0, 20000.0])
    gains = np.zeros_like(freqs)
    return serialize_targetcurve(
        curve=Curve(freqs=freqs, gains_db=gains),
        name="seed",
        device_name="seed",
        low_limit_hz=10.0,
        high_limit_hz=24000.0,
    )


def _write(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_tweak_recipe_loads(tmp_path: Path):
    recipe = load_tweak_recipe(
        _write(
            tmp_path / "tweak.yml",
            f"""
output:
  path: {tmp_path}/out.targetcurve
transforms:
  - peq: {{ freq: 100, gain_db: 4, q: 1 }}
""",
        ),
    )
    assert recipe.transforms[0].kind == "peq"


def test_tweak_recipe_rejects_base_field(tmp_path: Path):
    with pytest.raises(ConfigError, match="invalid tweak recipe"):
        load_tweak_recipe(
            _write(
                tmp_path / "bad.yml",
                f"""
output:
  path: {tmp_path}/out.targetcurve
base:
  type: harman
""",
            ),
        )


def test_tweak_applies_transforms_to_seed_curve(tmp_path: Path):
    parsed = parse_targetcurve(_flat_targetcurve_text())
    recipe = load_tweak_recipe(
        _write(
            tmp_path / "tweak.yml",
            f"""
output:
  path: {tmp_path}/out.targetcurve
transforms:
  - peq: {{ freq: 1000, gain_db: 6, q: 2 }}
""",
        ),
    )
    out = tweak(parsed.curve, recipe)
    # Peak at 1000 Hz should reach close to +6 dB
    idx = int(np.argmin(np.abs(out.freqs - 1000.0)))
    assert out.gains_db[idx] == pytest.approx(6.0, abs=0.5)


def test_tweak_with_no_transforms_preserves_input(tmp_path: Path):
    parsed = parse_targetcurve(_flat_targetcurve_text())
    recipe = load_tweak_recipe(
        _write(
            tmp_path / "noop.yml",
            f"""
output:
  path: {tmp_path}/out.targetcurve
transforms: []
""",
        ),
    )
    out = tweak(parsed.curve, recipe)
    # All zeros (the seed) should remain near zero everywhere
    assert np.allclose(out.gains_db, 0.0, atol=1e-6)
