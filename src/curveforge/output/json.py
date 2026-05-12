"""JSON sidecar output for curveforge."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from curveforge.curve import Curve


def write_json(path: Path, curve: Curve, *, name: str, device_name: str) -> None:
    """Write the curve as a JSON document with a flat list of breakpoint pairs."""
    payload = {
        "name": name,
        "device_name": device_name,
        "breakpoints": [
            {"hz": float(f), "db": float(g)}
            for f, g in zip(curve.freqs, curve.gains_db, strict=True)
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
