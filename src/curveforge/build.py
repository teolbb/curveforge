"""Recipe → Curve build pipeline.

Walks a validated `Recipe`: instantiates the base curve on a dense log-spaced
grid, applies each transform in order, then resamples down to the requested
breakpoint set for export.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
from pydantic import BaseModel, ValidationError

from curveforge.config import (
    BaseConfig,
    BreakpointResolution,
    BreakpointsConfig,
    Recipe,
    TransformEntry,
    TweakRecipe,
)
from curveforge.curve import (
    DEFAULT_GRID_HIGH_HZ,
    DEFAULT_GRID_LOW_HZ,
    Curve,
    iso_sixth_octave,
    iso_third_octave,
    log_grid,
)
from curveforge.curves import get_curve
from curveforge.transforms import get_transform

if TYPE_CHECKING:
    from numpy.typing import NDArray


class BuildError(Exception):
    """Raised when a recipe cannot be built (bad params for a curve or transform)."""


def build(recipe: Recipe) -> Curve:
    """Build the dense in-memory curve for a recipe and return it ready for export."""
    grid = _build_grid(recipe.breakpoints)
    base_curve = _render_base(recipe.base, grid)
    transformed = _apply_transforms(base_curve, recipe.transforms)
    export_freqs = _export_freqs(recipe.breakpoints)
    return transformed.resample(export_freqs)


def tweak(input_curve: Curve, recipe: TweakRecipe) -> Curve:
    """Apply a tweak recipe's transforms to an existing curve and return the result."""
    grid = _build_grid(recipe.breakpoints)
    seeded = input_curve.resample(grid)
    transformed = _apply_transforms(seeded, recipe.transforms)
    export_freqs = _export_freqs(recipe.breakpoints)
    return transformed.resample(export_freqs)


def _build_grid(bp: BreakpointsConfig) -> NDArray[np.float64]:
    low = max(DEFAULT_GRID_LOW_HZ, bp.freq_range[0] / 2.0)
    high = min(DEFAULT_GRID_HIGH_HZ, bp.freq_range[1] * 1.2)
    return log_grid(low_hz=low, high_hz=high)


def _render_base(base: BaseConfig, grid: NDArray[np.float64]) -> Curve:
    spec = get_curve(base.type)
    params = _validate_params(
        model=spec.params_model,
        payload=base.params,
        where=f"base curve '{base.type}'",
    )
    gains = spec.render(params, grid)
    return Curve(freqs=grid, gains_db=gains)


def _apply_transforms(curve: Curve, entries: list[TransformEntry]) -> Curve:
    out = curve
    for index, entry in enumerate(entries):
        spec = get_transform(entry.kind)
        params = _validate_params(
            model=spec.params_model,
            payload=entry.params,
            where=f"transforms[{index}] ({entry.kind})",
        )
        out = spec.apply(out, params)
    return out


def _export_freqs(bp: BreakpointsConfig) -> NDArray[np.float64]:
    low, high = bp.freq_range
    if bp.resolution == "third_octave":
        return iso_third_octave(low_hz=low, high_hz=high)
    if bp.resolution == "sixth_octave":
        return iso_sixth_octave(low_hz=low, high_hz=high)
    return _twelfth_octave(low_hz=low, high_hz=high)


def _twelfth_octave(low_hz: float, high_hz: float) -> NDArray[np.float64]:
    n_low = int(np.floor(np.log2(low_hz / 1000.0) * 12))
    n_high = int(np.ceil(np.log2(high_hz / 1000.0) * 12))
    indices = np.arange(n_low, n_high + 1)
    points = 1000.0 * np.power(2.0, indices / 12.0)
    mask = (points >= low_hz) & (points <= high_hz)
    return points[mask]


def _validate_params(
    model: type[BaseModel],
    payload: dict[str, Any],
    where: str,
) -> BaseModel:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        msg = f"invalid params for {where}:\n{exc}"
        raise BuildError(msg) from exc


__all__ = ["BreakpointResolution", "BuildError", "build", "tweak"]
