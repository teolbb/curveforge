"""Tests targeting the lowest-coverage paths: writers, validation guards, CLI edges."""

from __future__ import annotations

import json

import matplotlib as mpl
import numpy as np
import pytest
from click.testing import CliRunner

mpl.use("Agg")

from typing import TYPE_CHECKING

from curveforge.cli import main
from curveforge.curve import Curve, log_grid
from curveforge.dsp import (
    butterworth_highpass_db,
    highshelf_db,
    linear_tilt_db,
    lowshelf_db,
    peaking_db,
)
from curveforge.output.csv import write_csv
from curveforge.output.json import write_json

if TYPE_CHECKING:
    from pathlib import Path


# ---- output writers (csv + json) ----


def _sample_curve() -> Curve:
    freqs = np.array([10.0, 100.0, 1000.0, 20000.0])
    gains = np.array([6.0, 3.0, 0.0, -2.0])
    return Curve(freqs=freqs, gains_db=gains)


def test_write_csv_writes_header_and_rows(tmp_path: Path):
    out = tmp_path / "curve.csv"
    write_csv(out, _sample_curve())
    text = out.read_text(encoding="utf-8")
    lines = text.strip().splitlines()
    assert lines[0] == "hz,db"
    assert len(lines) == 5
    # first data row is 10 Hz, +6 dB
    assert lines[1].startswith("10,6")


def test_write_json_writes_structured_payload(tmp_path: Path):
    out = tmp_path / "curve.json"
    write_json(out, _sample_curve(), name="X", device_name="Y")
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["name"] == "X"
    assert payload["device_name"] == "Y"
    assert len(payload["breakpoints"]) == 4
    assert payload["breakpoints"][0]["hz"] == 10.0
    assert payload["breakpoints"][0]["db"] == 6.0


# ---- DSP guards ----


def test_lowshelf_rejects_invalid_corner():
    with pytest.raises(ValueError, match="corner_hz"):
        lowshelf_db(freqs=np.array([100.0]), corner_hz=0.0, gain_db=6.0)


def test_highshelf_rejects_invalid_corner():
    with pytest.raises(ValueError, match="corner_hz"):
        highshelf_db(freqs=np.array([100.0]), corner_hz=-1.0, gain_db=6.0)


def test_peaking_rejects_invalid_center():
    with pytest.raises(ValueError, match="center_hz"):
        peaking_db(freqs=np.array([100.0]), center_hz=0.0, gain_db=6.0, q=1.0)


def test_peaking_rejects_invalid_q():
    with pytest.raises(ValueError, match="q must be"):
        peaking_db(freqs=np.array([100.0]), center_hz=1000.0, gain_db=6.0, q=0.0)


def test_butterworth_rejects_invalid_cutoff():
    with pytest.raises(ValueError, match="cutoff_hz"):
        butterworth_highpass_db(freqs=np.array([100.0]), cutoff_hz=0.0, order=2)


def test_butterworth_rejects_out_of_range_order():
    with pytest.raises(ValueError, match="order"):
        butterworth_highpass_db(freqs=np.array([100.0]), cutoff_hz=100.0, order=99)


def test_linear_tilt_rejects_invalid_anchor():
    with pytest.raises(ValueError, match="anchor_hz"):
        linear_tilt_db(freqs=np.array([100.0]), db_per_octave=-1.0, anchor_hz=0.0)


# ---- Curve validation guards ----


def test_curve_rejects_2d_arrays():
    with pytest.raises(ValueError, match="1-D"):
        Curve(freqs=np.array([[10.0]]), gains_db=np.array([[0.0]]))


def test_curve_rejects_shape_mismatch():
    with pytest.raises(ValueError, match="shape mismatch"):
        Curve(freqs=np.array([10.0, 20.0, 30.0]), gains_db=np.array([0.0, 0.0]))


def test_curve_add_rejects_shape_mismatch():
    grid = log_grid(low_hz=10.0, high_hz=100.0)
    curve = Curve(freqs=grid, gains_db=np.zeros_like(grid))
    with pytest.raises(ValueError, match="delta_db shape"):
        curve.add(np.zeros(3))


def test_log_grid_rejects_zero_points_per_octave():
    with pytest.raises(ValueError, match="points_per_octave"):
        log_grid(low_hz=10.0, high_hz=100.0, points_per_octave=0)


# ---- CLI edge cases ----


def test_render_to_stdout_csv(tmp_path: Path):
    recipe = tmp_path / "r.yml"
    recipe.write_text(
        f"output:\n  path: {tmp_path}/x.targetcurve\nbase:\n  type: flat\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["render", str(recipe), "--stdout", "--format", "csv"])
    assert result.exit_code == 0
    assert result.output.startswith("hz,db")


def test_render_to_stdout_json(tmp_path: Path):
    recipe = tmp_path / "r.yml"
    recipe.write_text(
        f"output:\n  path: {tmp_path}/x.targetcurve\nbase:\n  type: flat\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["render", str(recipe), "--stdout", "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "breakpoints" in payload


def test_build_with_json_format_writes_json(tmp_path: Path):
    recipe = tmp_path / "r.yml"
    out = tmp_path / "out.json"
    recipe.write_text(
        f"output:\n  path: {out}\nbase:\n  type: flat\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["build", str(recipe), "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "breakpoints" in payload


def test_build_with_csv_format_writes_csv(tmp_path: Path):
    recipe = tmp_path / "r.yml"
    out = tmp_path / "out.csv"
    recipe.write_text(
        f"output:\n  path: {out}\nbase:\n  type: flat\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["build", str(recipe), "--format", "csv"])
    assert result.exit_code == 0
    assert out.read_text(encoding="utf-8").startswith("hz,db")


def test_validate_unreadable_file(tmp_path: Path):
    """Bad .targetcurve file should exit with usage error."""
    bad = tmp_path / "bad.targetcurve"
    bad.write_text("not a valid format", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(main, ["validate", str(bad)])
    assert result.exit_code == 1


def test_plot_writes_png(tmp_path: Path):
    recipe = tmp_path / "r.yml"
    recipe.write_text(
        f"output:\n  path: {tmp_path}/x.targetcurve\nbase:\n  type: flat\n",
        encoding="utf-8",
    )
    out = tmp_path / "plot.png"
    runner = CliRunner()
    result = runner.invoke(main, ["plot", str(recipe), "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert out.stat().st_size > 0


def test_plot_overlay_writes_png(tmp_path: Path):
    """Plot two recipes overlaid."""
    a = tmp_path / "a.yml"
    b = tmp_path / "b.yml"
    a.write_text(
        f"output:\n  path: {tmp_path}/a.targetcurve\nbase:\n  type: flat\n",
        encoding="utf-8",
    )
    b.write_text(
        f"output:\n  path: {tmp_path}/b.targetcurve\nbase:\n  type: harman\n",
        encoding="utf-8",
    )
    out = tmp_path / "overlay.png"
    runner = CliRunner()
    result = runner.invoke(main, ["plot", str(a), str(b), "-o", str(out)])
    assert result.exit_code == 0
    assert out.exists()


def test_tweak_cmd_writes_modified_targetcurve(tmp_path: Path):
    # Build a base file, then tweak it
    base_recipe = tmp_path / "base.yml"
    base_out = tmp_path / "base.targetcurve"
    base_recipe.write_text(
        f"output:\n  path: {base_out}\nbase:\n  type: flat\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    runner.invoke(main, ["build", str(base_recipe)])

    tweak_recipe = tmp_path / "tweak.yml"
    tweaked_out = tmp_path / "tweaked.targetcurve"
    tweak_recipe.write_text(
        f"""output:
  path: {tweaked_out}
transforms:
  - peq: {{ freq: 1000, gain_db: 6, q: 2 }}
""",
        encoding="utf-8",
    )
    result = runner.invoke(main, ["tweak", str(base_out), str(tweak_recipe)])
    assert result.exit_code == 0
    assert tweaked_out.exists()
