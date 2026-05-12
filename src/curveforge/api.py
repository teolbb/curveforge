"""High-level library API for building and exporting curves from Python.

For users who want to script curveforge from a Python program (notebooks,
batch jobs, web tools) without going through YAML files. The CLI is built on
top of these same primitives.

Example:
    >>> from curveforge import build_curve, write_targetcurve
    >>> curve = build_curve(
    ...     base="harman",
    ...     base_params={"shelf_level": 8},
    ...     transforms=[("peq", {"freq": 25, "gain_db": 4, "q": 1.0})],
    ... )
    >>> write_targetcurve("out.targetcurve", curve, name="My target",
    ...                   device_name="Living Room",
    ...                   low_limit_hz=10, high_limit_hz=24000)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from curveforge.build import build
from curveforge.config import (
    BaseConfig,
    BreakpointResolution,
    BreakpointsConfig,
    OutputConfig,
    Recipe,
    TransformEntry,
)

if TYPE_CHECKING:
    from curveforge.curve import Curve

# `output.path` is required by the Recipe schema for CLI use, but unused when
# `build_curve` is called from Python (the caller handles their own writing).
# A non-existent placeholder satisfies the schema without touching disk.
_UNUSED_OUTPUT_PATH: Final[Path] = Path("curveforge-api-unused.targetcurve")


def build_curve(
    base: str,
    base_params: dict[str, Any] | None = None,
    transforms: list[tuple[str, dict[str, Any]]] | None = None,
    *,
    resolution: BreakpointResolution = "third_octave",
    freq_range: tuple[float, float] = (10.0, 20000.0),
) -> Curve:
    """Build a curve programmatically from a base name and optional transforms.

    Args:
        base: Registered curve name (see ``curveforge.curves.list_curves()``).
        base_params: Native parameters for the base curve. Defaults if omitted.
        transforms: Ordered list of ``(transform_name, params_dict)`` tuples.
        resolution: Breakpoint density for the export grid.
        freq_range: Inclusive frequency range to emit.

    Returns:
        A `Curve` ready for export or further analysis.
    """
    transform_entries = [
        TransformEntry(kind=name, params=params) for name, params in (transforms or [])
    ]
    recipe = Recipe(
        output=OutputConfig(path=_UNUSED_OUTPUT_PATH),
        base=BaseConfig(type=base, params=base_params or {}),
        transforms=transform_entries,
        breakpoints=BreakpointsConfig(resolution=resolution, freq_range=freq_range),
    )
    return build(recipe)
