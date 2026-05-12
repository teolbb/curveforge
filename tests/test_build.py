"""End-to-end build tests: recipe → curve."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from curveforge.build import BuildError, build
from curveforge.config import load_recipe

if TYPE_CHECKING:
    from pathlib import Path


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "recipe.yml"
    path.write_text(body, encoding="utf-8")
    return path


def test_build_flat_recipe(tmp_path: Path):
    recipe = load_recipe(
        _write(
            tmp_path,
            """
output:
  path: out.targetcurve
base:
  type: flat
breakpoints:
  resolution: third_octave
  freq_range: [20, 20000]
""",
        )
    )
    curve = build(recipe)
    assert curve.freqs.size > 10
    assert np.allclose(curve.gains_db, 0.0, atol=1e-6)


def test_build_harman_8_low_shelf_shape(tmp_path: Path):
    """harman shelf_level=8 must produce ~+8 dB at the bottom and ~0 at the top."""
    recipe = load_recipe(
        _write(
            tmp_path,
            """
output:
  path: out.targetcurve
base:
  type: harman
  params: { shelf_level: 8 }
breakpoints:
  resolution: twelfth_octave
  freq_range: [10, 20000]
""",
        )
    )
    curve = build(recipe)
    low_idx = int(np.argmin(np.abs(curve.freqs - 20.0)))
    high_idx = int(np.argmin(np.abs(curve.freqs - 10000.0)))
    assert curve.gains_db[low_idx] == pytest.approx(8.0, abs=0.2)
    assert curve.gains_db[high_idx] == pytest.approx(0.0, abs=0.2)


def test_build_with_transforms_applies_in_order(tmp_path: Path):
    recipe = load_recipe(
        _write(
            tmp_path,
            """
output:
  path: out.targetcurve
base:
  type: flat
transforms:
  - peq: { freq: 1000, gain_db: 6, q: 2 }
  - rolloff: { freq: 20, order: 2 }
breakpoints:
  resolution: sixth_octave
  freq_range: [10, 20000]
""",
        )
    )
    curve = build(recipe)
    peak_idx = int(np.argmin(np.abs(curve.freqs - 1000.0)))
    assert curve.gains_db[peak_idx] > 4.0
    low_idx = int(np.argmin(np.abs(curve.freqs - 10.0)))
    assert curve.gains_db[low_idx] < -10.0


def test_build_rejects_invalid_curve_params(tmp_path: Path):
    recipe = load_recipe(
        _write(
            tmp_path,
            """
output:
  path: out.targetcurve
base:
  type: harman
  params: { shelf_level: 9999 }
""",
        )
    )
    with pytest.raises(BuildError, match="invalid params"):
        build(recipe)
