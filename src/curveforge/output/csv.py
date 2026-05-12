"""CSV output for curveforge."""

from __future__ import annotations

import csv
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from curveforge.curve import Curve


def write_csv(path: Path, curve: Curve) -> None:
    """Write the curve as a two-column CSV (Hz, dB)."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["hz", "db"])
        for f, g in zip(curve.freqs, curve.gains_db, strict=True):
            writer.writerow([f"{float(f):.6g}", f"{float(g):.6g}"])
