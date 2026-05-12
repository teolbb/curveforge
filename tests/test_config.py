"""Tests for config loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from curveforge.config import ConfigError, load_recipe


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "recipe.yml"
    path.write_text(body, encoding="utf-8")
    return path


def test_minimal_recipe_loads(tmp_path: Path):
    recipe = load_recipe(
        _write(
            tmp_path,
            """
output:
  path: out.targetcurve
base:
  type: flat
""",
        )
    )
    assert recipe.base.type == "flat"
    assert recipe.output.path == Path("out.targetcurve")
    assert recipe.transforms == []


def test_shorthand_transform_form(tmp_path: Path):
    recipe = load_recipe(
        _write(
            tmp_path,
            """
output:
  path: out.targetcurve
base:
  type: harman
  params: { shelf_level: 8 }
transforms:
  - peq: { freq: 22, gain_db: 4, q: 1.5 }
  - rolloff: { freq: 15, order: 2 }
""",
        )
    )
    assert [t.kind for t in recipe.transforms] == ["peq", "rolloff"]


def test_explicit_transform_form(tmp_path: Path):
    recipe = load_recipe(
        _write(
            tmp_path,
            """
output:
  path: out.targetcurve
base:
  type: flat
transforms:
  - kind: peq
    params: { freq: 100, gain_db: 2, q: 1 }
""",
        )
    )
    assert recipe.transforms[0].kind == "peq"


def test_unknown_curve_is_rejected(tmp_path: Path):
    with pytest.raises(ConfigError, match="invalid recipe"):
        load_recipe(
            _write(
                tmp_path,
                """
output:
  path: out.targetcurve
base:
  type: not_a_curve
""",
            )
        )


def test_unknown_transform_is_rejected(tmp_path: Path):
    with pytest.raises(ConfigError, match="invalid recipe"):
        load_recipe(
            _write(
                tmp_path,
                """
output:
  path: out.targetcurve
base:
  type: flat
transforms:
  - notatransform: { x: 1 }
""",
            )
        )


def test_extra_fields_are_rejected(tmp_path: Path):
    with pytest.raises(ConfigError, match="invalid recipe"):
        load_recipe(
            _write(
                tmp_path,
                """
output:
  path: out.targetcurve
  unexpected: 1
base:
  type: flat
""",
            )
        )


def test_yaml_parse_error(tmp_path: Path):
    with pytest.raises(ConfigError, match="YAML parse error"):
        load_recipe(_write(tmp_path, "not: valid: yaml: ::"))


def test_missing_file(tmp_path: Path):
    with pytest.raises(ConfigError, match="could not read"):
        load_recipe(tmp_path / "nope.yml")
