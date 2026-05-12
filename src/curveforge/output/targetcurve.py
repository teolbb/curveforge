"""Reader and writer for Dirac Live `.targetcurve` files.

Format (line-pair sections, as accepted by Dirac Live 2/3):

    NAME
    <name>
    DEVICENAME
    <device>
    BREAKPOINTS
    <freq> <gain_db>
    <freq> <gain_db>
    ...
    LOWLIMITHZ
    <hz>
    HIGHLIMITHZ
    <hz>

BREAKPOINTS must be strictly sorted by frequency. Optional sections
(HPSLOPEON / HPCUTOFF / HPORDER / LPSLOPEON / LPCUTOFF / LPORDER) are
preserved on read but not emitted by default — Dirac applies the curve
verbatim with no extra slopes when these are absent.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from itertools import pairwise
from typing import TYPE_CHECKING, Any

import numpy as np

from curveforge.curve import Curve

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray

_REQUIRED_SECTIONS: tuple[str, ...] = (
    "NAME",
    "DEVICENAME",
    "BREAKPOINTS",
    "LOWLIMITHZ",
    "HIGHLIMITHZ",
)


@dataclass(frozen=True, slots=True)
class TargetCurveFile:
    """In-memory representation of a `.targetcurve` file."""

    name: str
    device_name: str
    low_limit_hz: float
    high_limit_hz: float
    curve: Curve
    extras: dict[str, str]


class TargetCurveError(Exception):
    """Raised when a `.targetcurve` file is malformed or fails sanity checks."""


def serialize_targetcurve(
    curve: Curve,
    name: str,
    device_name: str,
    low_limit_hz: float,
    high_limit_hz: float,
    extras: dict[str, str] | None = None,
) -> str:
    """Render a Dirac `.targetcurve` document as a string."""
    _check_export_invariants(
        curve=curve,
        low_limit_hz=low_limit_hz,
        high_limit_hz=high_limit_hz,
    )
    buffer = StringIO()
    buffer.write(f"NAME\n{name}\n")
    buffer.write(f"DEVICENAME\n{device_name}\n")
    buffer.write("BREAKPOINTS\n")
    for freq, gain in zip(curve.freqs, curve.gains_db, strict=True):
        buffer.write(f"{_fmt_number(freq)} {_fmt_number(gain)}\n")
    buffer.write(f"LOWLIMITHZ\n{_fmt_number(low_limit_hz)}\n")
    buffer.write(f"HIGHLIMITHZ\n{_fmt_number(high_limit_hz)}\n")
    if extras:
        for key, value in extras.items():
            buffer.write(f"{key}\n{value}\n")
    return buffer.getvalue()


def write_targetcurve(
    path: Path,
    curve: Curve,
    name: str,
    device_name: str,
    low_limit_hz: float,
    high_limit_hz: float,
) -> None:
    """Write a Dirac `.targetcurve` file at `path`."""
    text = serialize_targetcurve(
        curve=curve,
        name=name,
        device_name=device_name,
        low_limit_hz=low_limit_hz,
        high_limit_hz=high_limit_hz,
    )
    path.write_text(text, encoding="utf-8")


def parse_targetcurve(text: str) -> TargetCurveFile:
    """Parse a `.targetcurve` file and return its in-memory representation."""
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip() != ""]
    sections = _split_sections(lines)
    _check_required_sections(sections)
    freqs, gains = _parse_breakpoints(sections.pop("BREAKPOINTS"))
    name = _scalar(sections.pop("NAME"), "NAME")
    device_name = _scalar(sections.pop("DEVICENAME"), "DEVICENAME")
    low = _float_scalar(sections.pop("LOWLIMITHZ"), "LOWLIMITHZ")
    high = _float_scalar(sections.pop("HIGHLIMITHZ"), "HIGHLIMITHZ")
    extras = {key: "\n".join(values) for key, values in sections.items()}
    return TargetCurveFile(
        name=name,
        device_name=device_name,
        low_limit_hz=low,
        high_limit_hz=high,
        curve=Curve(freqs=freqs, gains_db=gains),
        extras=extras,
    )


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        if line.isupper() and " " not in line and not _looks_like_breakpoint(line):
            current = line
            sections.setdefault(current, [])
            continue
        if current is None:
            msg = f"unexpected line before any section header: {line!r}"
            raise TargetCurveError(msg)
        sections[current].append(line)
    return sections


def _looks_like_breakpoint(line: str) -> bool:
    parts = line.split()
    if len(parts) != 2:  # noqa: PLR2004
        return False
    try:
        float(parts[0])
        float(parts[1])
    except ValueError:
        return False
    return True


def _check_required_sections(sections: dict[str, list[str]]) -> None:
    missing = [s for s in _REQUIRED_SECTIONS if s not in sections]
    if missing:
        msg = f"missing required section(s): {missing}"
        raise TargetCurveError(msg)


def _parse_breakpoints(
    body: list[str],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    if len(body) < 2:  # noqa: PLR2004
        msg = "BREAKPOINTS must contain at least 2 points"
        raise TargetCurveError(msg)
    freqs: list[float] = []
    gains: list[float] = []
    for raw in body:
        parts = raw.split()
        if len(parts) != 2:  # noqa: PLR2004
            msg = f"breakpoint line must be 'freq gain': {raw!r}"
            raise TargetCurveError(msg)
        freqs.append(float(parts[0]))
        gains.append(float(parts[1]))
    if any(b <= a for a, b in pairwise(freqs)):
        msg = "BREAKPOINTS must be strictly sorted by frequency"
        raise TargetCurveError(msg)
    return np.array(freqs, dtype=np.float64), np.array(gains, dtype=np.float64)


def _scalar(body: list[str], section: str) -> str:
    if len(body) != 1:
        msg = f"{section} must have exactly one value, got {body}"
        raise TargetCurveError(msg)
    return body[0]


def _float_scalar(body: list[str], section: str) -> float:
    raw = _scalar(body, section)
    try:
        return float(raw)
    except ValueError as exc:
        msg = f"{section} must be a number, got {raw!r}"
        raise TargetCurveError(msg) from exc


def _check_export_invariants(
    curve: Curve,
    low_limit_hz: float,
    high_limit_hz: float,
) -> None:
    if low_limit_hz <= 0 or high_limit_hz <= low_limit_hz:
        msg = f"invalid limits: low_limit_hz={low_limit_hz}, high_limit_hz={high_limit_hz}"
        raise TargetCurveError(msg)
    if curve.freqs.size < 2:  # noqa: PLR2004
        msg = "exported curve must have at least 2 breakpoints"
        raise TargetCurveError(msg)


def _fmt_number(value: float | Any) -> str:  # noqa: ANN401 — also accepts numpy scalars
    return f"{float(value):.6g}"
