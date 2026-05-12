"""Tests for the plot module (uses matplotlib's Agg backend, no display required)."""

from __future__ import annotations

import matplotlib as mpl
import numpy as np
import pytest

# Force the headless Agg backend before any pyplot import. Must be at module top.
mpl.use("Agg")

from typing import TYPE_CHECKING

from curveforge.curve import Curve, log_grid
from curveforge.plot import plot_curve, plot_overlay, save_figure

if TYPE_CHECKING:
    from pathlib import Path


def _flat_curve(value_db: float = 0.0) -> Curve:
    grid = log_grid(low_hz=10.0, high_hz=20000.0, points_per_octave=24)
    return Curve(freqs=grid, gains_db=np.full_like(grid, value_db))


def test_plot_curve_returns_figure():
    fig = plot_curve(_flat_curve(0.0), title="test")
    assert fig is not None


def test_plot_overlay_with_multiple_curves():
    fig = plot_overlay(
        [
            ("flat 0", _flat_curve(0.0)),
            ("flat 5", _flat_curve(5.0)),
        ],
    )
    assert fig is not None


def test_save_figure_writes_png(tmp_path: Path):
    fig = plot_curve(_flat_curve(2.5), title="save")
    out = tmp_path / "out.png"
    save_figure(fig, out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_save_figure_supports_pdf(tmp_path: Path):
    fig = plot_curve(_flat_curve(0.0), title="pdf")
    out = tmp_path / "out.pdf"
    save_figure(fig, out)
    assert out.exists()


@pytest.mark.parametrize("count", [1, 2, 5])
def test_overlay_handles_n_curves(count: int):
    curves = [(f"c{i}", _flat_curve(float(i))) for i in range(count)]
    fig = plot_overlay(curves)
    assert fig is not None
