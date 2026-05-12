"""Recipe schema and YAML loading.

A *recipe* is the user-facing description of what to build: a base curve, an
ordered list of transforms, the export breakpoints, and where to write the
output. Recipes are validated with Pydantic; invalid recipes raise a
`ConfigError` with a structured, line-oriented message.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)

from curveforge.curves import get_curve
from curveforge.transforms import get_transform

DEFAULT_LOW_LIMIT_HZ: float = 20.0
DEFAULT_HIGH_LIMIT_HZ: float = 20000.0


class ConfigError(Exception):
    """Raised when a recipe is missing required fields or has invalid values."""


BreakpointResolution = Literal["third_octave", "sixth_octave", "twelfth_octave"]


class OutputConfig(BaseModel):
    """Output settings of a recipe."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: Path = Field(..., description="Destination path for the exported file.")
    device_name: str = Field(default="Unnamed", description="Written to DEVICENAME header.")
    low_limit_hz: float = Field(
        default=DEFAULT_LOW_LIMIT_HZ,
        gt=0.0,
        description="Written to LOWLIMITHZ; below this Dirac applies no correction.",
    )
    high_limit_hz: float = Field(
        default=DEFAULT_HIGH_LIMIT_HZ,
        gt=0.0,
        description="Written to HIGHLIMITHZ; above this Dirac applies no correction.",
    )

    @field_validator("path", mode="before")
    @classmethod
    def _coerce_path(cls, value: Any) -> Path:  # noqa: ANN401 — Pydantic boundary
        return Path(value)


class BreakpointsConfig(BaseModel):
    """Breakpoint set used when exporting the curve."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    resolution: BreakpointResolution = Field(
        default="third_octave",
        description="Density of exported breakpoints.",
    )
    freq_range: tuple[float, float] = Field(
        default=(10.0, 20000.0),
        description="Inclusive frequency range over which breakpoints are emitted.",
    )

    @field_validator("freq_range")
    @classmethod
    def _check_range(cls, value: tuple[float, float]) -> tuple[float, float]:
        low, high = value
        if low <= 0 or high <= low:
            msg = f"freq_range must be (low > 0, high > low); got {value}"
            raise ValueError(msg)
        return value


class BaseConfig(BaseModel):
    """Base curve selection and its native parameters."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    type: str = Field(..., description="Registered curve name (e.g. 'harman').")
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Native parameters; validated against the curve.",
    )

    @field_validator("type")
    @classmethod
    def _check_type(cls, value: str) -> str:
        try:
            get_curve(value)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        return value


def _coerce_single_key_dict(value: Any) -> Any:  # noqa: ANN401 — Pydantic boundary
    """Allow shorthand `{ peq: { freq: 22, ... } }` instead of explicit `kind/params`."""
    # Programmatic API: pre-built BaseModel passes straight through.
    if isinstance(value, BaseModel):
        return value
    if not isinstance(value, dict):
        msg = f"transform entry must be a mapping, got {type(value).__name__}"
        raise TypeError(msg)
    payload: dict[str, Any] = value
    if "kind" in payload:
        return payload
    if len(payload) != 1:
        msg = (
            "transform entry must be either {kind: ..., params: ...} or a single-key "
            f"mapping like {{peq: {{...}}}}; got keys {sorted(payload)}"
        )
        raise ValueError(msg)
    kind, params = next(iter(payload.items()))
    if not isinstance(params, dict):
        msg = f"transform '{kind}' params must be a mapping, got {type(params).__name__}"
        raise TypeError(msg)
    return {"kind": kind, "params": params}


class TransformEntry(BaseModel):
    """A single ordered transform in the recipe."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str = Field(..., description="Registered transform name (e.g. 'peq').")
    params: dict[str, Any] = Field(default_factory=dict)

    @field_validator("kind")
    @classmethod
    def _check_kind(cls, value: str) -> str:
        try:
            get_transform(value)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        return value


# Accept both `{kind: peq, params: {...}}` and `{peq: {...}}` shorthand at the YAML layer.
TransformEntryField = Annotated[TransformEntry, BeforeValidator(_coerce_single_key_dict)]


class Recipe(BaseModel):
    """Top-level recipe: base curve + transforms + export."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(default="curveforge target")
    description: str = Field(default="")
    output: OutputConfig
    base: BaseConfig
    transforms: list[TransformEntryField] = Field(default_factory=list)
    breakpoints: BreakpointsConfig = Field(default_factory=BreakpointsConfig)


class TweakRecipe(BaseModel):
    """Recipe for modifying an existing .targetcurve: just output + transforms."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(default="curveforge tweak")
    description: str = Field(default="")
    output: OutputConfig
    transforms: list[TransformEntryField] = Field(default_factory=list)
    breakpoints: BreakpointsConfig = Field(default_factory=BreakpointsConfig)


def load_recipe(path: Path) -> Recipe:
    """Read and validate a YAML recipe.

    Raises:
        ConfigError: if the file cannot be parsed or fails validation.
    """
    raw = _load_yaml_mapping(path)
    try:
        return Recipe.model_validate(raw)
    except ValidationError as exc:
        msg = f"invalid recipe at {path}:\n{exc}"
        raise ConfigError(msg) from exc


def load_tweak_recipe(path: Path) -> TweakRecipe:
    """Read and validate a YAML tweak recipe (output + transforms, no base)."""
    raw = _load_yaml_mapping(path)
    try:
        return TweakRecipe.model_validate(raw)
    except ValidationError as exc:
        msg = f"invalid tweak recipe at {path}:\n{exc}"
        raise ConfigError(msg) from exc


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        msg = f"could not read recipe at {path}: {exc}"
        raise ConfigError(msg) from exc

    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        msg = f"YAML parse error in {path}: {exc}"
        raise ConfigError(msg) from exc

    if not isinstance(raw, dict):
        msg = f"recipe at {path} must be a mapping at the top level, got {type(raw).__name__}"
        raise ConfigError(msg)
    return raw
