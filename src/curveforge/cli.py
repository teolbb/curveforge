"""curveforge CLI entry points (click-based)."""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import click

from curveforge import __version__
from curveforge.build import BuildError, build, tweak
from curveforge.config import (
    ConfigError,
    Recipe,
    TweakRecipe,
    load_recipe,
    load_tweak_recipe,
)
from curveforge.curves import get_curve, list_curves
from curveforge.output import (
    parse_targetcurve,
    write_csv,
    write_json,
    write_targetcurve,
)
from curveforge.output.targetcurve import TargetCurveError, serialize_targetcurve
from curveforge.transforms import get_transform, list_transforms

if TYPE_CHECKING:
    from curveforge.curve import Curve
    from curveforge.curves._base import CurveSpec
    from curveforge.transforms._base import TransformSpec

EXIT_OK: Final[int] = 0
EXIT_USAGE: Final[int] = 1
EXIT_IO: Final[int] = 2


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="curveforge")
def main() -> None:
    """Build Dirac Live target curves from research-grounded recipes."""


@main.command()
@click.argument("recipe_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--format",
    "format_",
    type=click.Choice(["targetcurve", "json", "csv"], case_sensitive=False),
    default="targetcurve",
    show_default=True,
    help="Output format.",
)
def build_cmd(recipe_path: Path, format_: str) -> None:
    """Build a curve from a YAML recipe and write the output."""
    recipe = _load_or_exit(recipe_path)
    curve = _build_or_exit(recipe)
    _write_output(recipe=recipe, curve=curve, format_=format_)
    click.echo(f"wrote {recipe.output.path}")


main.add_command(build_cmd, name="build")


@main.command(name="render")
@click.argument("recipe_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--format",
    "format_",
    type=click.Choice(["targetcurve", "json", "csv"], case_sensitive=False),
    default="targetcurve",
    show_default=True,
)
@click.option(
    "--stdout/--no-stdout",
    default=False,
    help="Write to stdout instead of the path declared in the recipe.",
)
def render_cmd(recipe_path: Path, format_: str, stdout: bool) -> None:  # noqa: FBT001 — click flag
    """Render a recipe to stdout or to its declared output path."""
    recipe = _load_or_exit(recipe_path)
    curve = _build_or_exit(recipe)
    if stdout:
        click.echo(_serialize_for_stdout(recipe=recipe, curve=curve, format_=format_), nl=False)
        return
    _write_output(recipe=recipe, curve=curve, format_=format_)
    click.echo(f"wrote {recipe.output.path}")


@main.command(name="list")
@click.argument(
    "kind",
    type=click.Choice(["curves", "transforms", "all"], case_sensitive=False),
    default="all",
)
def list_cmd(kind: str) -> None:
    """List available curves and/or transforms."""
    if kind in {"curves", "all"}:
        click.echo("Curves:")
        for curve_spec in list_curves():
            click.echo(
                f"  {curve_spec.name:24} {curve_spec.title} - {curve_spec.description}",
            )
    if kind in {"transforms", "all"}:
        click.echo("Transforms:")
        for transform_spec in list_transforms():
            click.echo(
                f"  {transform_spec.name:24} {transform_spec.title} - {transform_spec.description}",
            )


@main.command(name="info")
@click.argument("name")
def info_cmd(name: str) -> None:
    """Show parameters, defaults, and citations for a curve or transform."""
    curve_spec = _try_get_curve(name)
    if curve_spec is not None:
        _print_spec(
            kind="curve",
            name=curve_spec.name,
            title=curve_spec.title,
            description=curve_spec.description,
            citation=curve_spec.citation,
            params_schema=curve_spec.params_model.model_json_schema(),
        )
        return
    transform_spec = _try_get_transform(name)
    if transform_spec is not None:
        _print_spec(
            kind="transform",
            name=transform_spec.name,
            title=transform_spec.title,
            description=transform_spec.description,
            citation=None,
            params_schema=transform_spec.params_model.model_json_schema(),
        )
        return
    click.echo(f"unknown name {name!r}", err=True)
    sys.exit(EXIT_USAGE)


@main.command(name="validate")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def validate_cmd(path: Path) -> None:
    """Sanity-check an existing `.targetcurve` file."""
    try:
        text = path.read_text(encoding="utf-8")
        file = parse_targetcurve(text)
    except OSError as exc:
        click.echo(f"could not read {path}: {exc}", err=True)
        sys.exit(EXIT_IO)
    except TargetCurveError as exc:
        click.echo(f"invalid {path}: {exc}", err=True)
        sys.exit(EXIT_USAGE)
    n = file.curve.freqs.size
    click.echo(
        f"OK  {path.name}: {n} breakpoints, "
        f"{file.curve.freqs[0]:.4g}-{file.curve.freqs[-1]:.4g} Hz, "
        f"limits {file.low_limit_hz:.0f}-{file.high_limit_hz:.0f} Hz",
    )


@main.command(name="diff")
@click.argument("a", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("b", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def diff_cmd(a: Path, b: Path) -> None:
    """Numerically diff two `.targetcurve` files at the breakpoints of A."""
    file_a = parse_targetcurve(a.read_text(encoding="utf-8"))
    file_b = parse_targetcurve(b.read_text(encoding="utf-8"))
    resampled_b = file_b.curve.resample(file_a.curve.freqs)
    delta = file_a.curve.gains_db - resampled_b.gains_db
    click.echo("# Hz, A_dB, B_dB, A-B")
    for freq, gain_a, gain_b, d in zip(
        file_a.curve.freqs,
        file_a.curve.gains_db,
        resampled_b.gains_db,
        delta,
        strict=True,
    ):
        click.echo(
            f"{float(freq):.4g}, {float(gain_a):+.3f}, {float(gain_b):+.3f}, {float(d):+.3f}",
        )


@main.command(name="tweak")
@click.argument(
    "input_targetcurve",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "tweak_recipe",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
def tweak_cmd(input_targetcurve: Path, tweak_recipe: Path) -> None:
    """Apply transforms from a tweak recipe to an existing `.targetcurve` file."""
    recipe = _load_tweak_or_exit(tweak_recipe)
    try:
        parsed = parse_targetcurve(input_targetcurve.read_text(encoding="utf-8"))
    except (OSError, TargetCurveError) as exc:
        click.echo(f"could not read {input_targetcurve}: {exc}", err=True)
        sys.exit(EXIT_IO if isinstance(exc, OSError) else EXIT_USAGE)
    try:
        tweaked = tweak(parsed.curve, recipe)
    except BuildError as exc:
        click.echo(str(exc), err=True)
        sys.exit(EXIT_USAGE)
    write_targetcurve(
        path=recipe.output.path,
        curve=tweaked,
        name=recipe.name,
        device_name=recipe.output.device_name,
        low_limit_hz=recipe.output.low_limit_hz,
        high_limit_hz=recipe.output.high_limit_hz,
    )
    click.echo(f"wrote {recipe.output.path}")


@main.command(name="plot")
@click.argument(
    "recipe_paths",
    nargs=-1,
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Save the plot to this path (PNG/PDF/SVG by extension). If omitted, opens a window.",
)
def plot_cmd(recipe_paths: tuple[Path, ...], output_path: Path | None) -> None:
    """Plot one or more recipes as overlaid magnitude responses.

    Requires the `plot` extra: ``pip install curveforge[plot]``.
    """
    try:
        from curveforge.plot import (  # noqa: PLC0415 — optional import
            plot_curve,
            plot_overlay,
            save_figure,
            show_figure,
        )
    except ImportError as exc:
        click.echo(str(exc), err=True)
        sys.exit(EXIT_USAGE)

    curves = [(path.stem, _build_or_exit(_load_or_exit(path))) for path in recipe_paths]
    if len(curves) == 1:
        title, curve = curves[0]
        fig = plot_curve(curve, title=title)
    else:
        fig = plot_overlay(curves)

    if output_path is not None:
        save_figure(fig, output_path)
        click.echo(f"wrote {output_path}")
    else:
        show_figure(fig)


# --- helpers ---------------------------------------------------------------


def _load_or_exit(path: Path) -> Recipe:
    try:
        return load_recipe(path)
    except ConfigError as exc:
        click.echo(str(exc), err=True)
        sys.exit(EXIT_USAGE)


def _load_tweak_or_exit(path: Path) -> TweakRecipe:
    try:
        return load_tweak_recipe(path)
    except ConfigError as exc:
        click.echo(str(exc), err=True)
        sys.exit(EXIT_USAGE)


def _build_or_exit(recipe: Recipe) -> Curve:
    try:
        return build(recipe)
    except BuildError as exc:
        click.echo(str(exc), err=True)
        sys.exit(EXIT_USAGE)


def _write_output(recipe: Recipe, curve: Curve, format_: str) -> None:
    path = recipe.output.path
    fmt = format_.lower()
    if fmt == "targetcurve":
        write_targetcurve(
            path=path,
            curve=curve,
            name=recipe.name,
            device_name=recipe.output.device_name,
            low_limit_hz=recipe.output.low_limit_hz,
            high_limit_hz=recipe.output.high_limit_hz,
        )
    elif fmt == "json":
        write_json(
            path=path,
            curve=curve,
            name=recipe.name,
            device_name=recipe.output.device_name,
        )
    else:
        write_csv(path=path, curve=curve)


def _csv_rows(curve: Curve) -> list[str]:
    rows = ["hz,db"]
    rows.extend(
        f"{float(f):.6g},{float(g):.6g}" for f, g in zip(curve.freqs, curve.gains_db, strict=True)
    )
    return rows


def _serialize_for_stdout(recipe: Recipe, curve: Curve, format_: str) -> str:
    fmt = format_.lower()
    if fmt == "targetcurve":
        return serialize_targetcurve(
            curve=curve,
            name=recipe.name,
            device_name=recipe.output.device_name,
            low_limit_hz=recipe.output.low_limit_hz,
            high_limit_hz=recipe.output.high_limit_hz,
        )
    if fmt == "csv":
        return "\n".join(_csv_rows(curve)) + "\n"
    return _json.dumps(
        {
            "name": recipe.name,
            "device_name": recipe.output.device_name,
            "breakpoints": [
                {"hz": float(f), "db": float(g)}
                for f, g in zip(curve.freqs, curve.gains_db, strict=True)
            ],
        },
        indent=2,
    )


def _try_get_curve(name: str) -> CurveSpec[Any] | None:
    try:
        return get_curve(name)
    except KeyError:
        return None


def _try_get_transform(name: str) -> TransformSpec[Any] | None:
    try:
        return get_transform(name)
    except KeyError:
        return None


def _print_spec(
    *,
    kind: str,
    name: str,
    title: str,
    description: str,
    citation: str | None,
    params_schema: dict[str, Any],
) -> None:
    click.echo(f"{kind}: {name}  ({title})")
    click.echo(description)
    if citation:
        click.echo(f"\nSource: {citation}")
    click.echo("\nParameters:")
    properties_raw = params_schema.get("properties")
    if not isinstance(properties_raw, dict):
        return
    properties: dict[str, Any] = properties_raw
    for prop_name, prop_def in properties.items():
        if not isinstance(prop_def, dict):
            continue
        prop: dict[str, Any] = prop_def
        default = prop.get("default", "<required>")
        descr = prop.get("description", "")
        click.echo(f"  - {prop_name}: default={default}  {descr}")
