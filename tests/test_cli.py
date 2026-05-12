"""CLI smoke tests using click's CliRunner."""

from __future__ import annotations

from typing import TYPE_CHECKING

from click.testing import CliRunner

from curveforge.cli import main

if TYPE_CHECKING:
    from pathlib import Path


def _write_recipe(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "r.yml"
    path.write_text(body, encoding="utf-8")
    return path


def test_list_curves_and_transforms_outputs():
    runner = CliRunner()
    result = runner.invoke(main, ["list", "all"])
    assert result.exit_code == 0
    assert "harman" in result.output
    assert "peq" in result.output


def test_info_known_curve():
    runner = CliRunner()
    result = runner.invoke(main, ["info", "harman"])
    assert result.exit_code == 0
    assert "shelf_level" in result.output


def test_info_unknown_exits_1():
    runner = CliRunner()
    result = runner.invoke(main, ["info", "no_such_thing"])
    assert result.exit_code == 1


def test_build_flat_recipe_produces_targetcurve(tmp_path: Path):
    recipe = _write_recipe(
        tmp_path,
        f"""
output:
  path: {tmp_path}/out.targetcurve
base:
  type: flat
""",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["build", str(recipe)])
    assert result.exit_code == 0, result.output
    out = (tmp_path / "out.targetcurve").read_text(encoding="utf-8")
    assert "BREAKPOINTS" in out
    assert "LOWLIMITHZ" in out


def test_build_invalid_recipe_exits_1(tmp_path: Path):
    recipe = _write_recipe(
        tmp_path,
        """
output:
  path: x.targetcurve
base:
  type: not_real
""",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["build", str(recipe)])
    assert result.exit_code == 1


def test_validate_round_trips_a_built_file(tmp_path: Path):
    recipe = _write_recipe(
        tmp_path,
        f"""
output:
  path: {tmp_path}/out.targetcurve
base:
  type: harman
  params: {{ shelf_level: 6 }}
""",
    )
    runner = CliRunner()
    build_result = runner.invoke(main, ["build", str(recipe)])
    assert build_result.exit_code == 0
    val_result = runner.invoke(main, ["validate", str(tmp_path / "out.targetcurve")])
    assert val_result.exit_code == 0
    assert "OK" in val_result.output


def test_render_to_stdout_targetcurve(tmp_path: Path):
    recipe = _write_recipe(
        tmp_path,
        f"""
output:
  path: {tmp_path}/out.targetcurve
base:
  type: flat
""",
    )
    runner = CliRunner()
    result = runner.invoke(main, ["render", str(recipe), "--stdout"])
    assert result.exit_code == 0
    assert result.output.startswith("NAME")


def test_diff_self_is_zero(tmp_path: Path):
    recipe = _write_recipe(
        tmp_path,
        f"""
output:
  path: {tmp_path}/out.targetcurve
base:
  type: flat
""",
    )
    runner = CliRunner()
    runner.invoke(main, ["build", str(recipe)])
    out = tmp_path / "out.targetcurve"
    result = runner.invoke(main, ["diff", str(out), str(out)])
    assert result.exit_code == 0
    # All deltas zero
    for line in result.output.strip().splitlines():
        if line.startswith("#"):
            continue
        delta = float(line.rsplit(",", 1)[-1])
        assert abs(delta) < 1e-9
