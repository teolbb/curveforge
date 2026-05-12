"""Tests that every gallery recipe builds without errors."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from curveforge.cli import main

GALLERY_DIR = Path(__file__).resolve().parent.parent / "gallery"


def _gallery_recipes() -> list[Path]:
    return sorted(GALLERY_DIR.glob("*.yml"))


def _output_filename(recipe_path: Path) -> str:
    """Return the basename of the `output.path` declared in the recipe."""
    data = yaml.safe_load(recipe_path.read_text(encoding="utf-8"))
    return Path(data["output"]["path"]).name


@pytest.mark.parametrize("recipe", _gallery_recipes(), ids=lambda p: p.stem)
def test_gallery_recipe_builds(recipe: Path, tmp_path: Path):
    text = recipe.read_text(encoding="utf-8")
    out_name = _output_filename(recipe)
    # Replace the declared output path with a tmp_path version, regardless of original
    rewritten = re.sub(
        r"^(\s*path:\s*).*$",
        rf"\g<1>{tmp_path / out_name}",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    rewritten_path = tmp_path / recipe.name
    rewritten_path.write_text(rewritten, encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(main, ["build", str(rewritten_path)])
    assert result.exit_code == 0, f"{recipe.name}: {result.output}"
    assert (tmp_path / out_name).exists()


def test_gallery_has_recipes():
    assert len(_gallery_recipes()) >= 5
