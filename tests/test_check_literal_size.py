"""Tests for tools/check_literal_size.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from check_literal_size import find_violations, main  # noqa: E402


@pytest.mark.parametrize(
    ("source", "expected_violations"),
    [
        ("X = (1, 2, 3)\n", 0),
        ("X = (" + ", ".join(str(i) for i in range(11)) + ")\n", 1),
        ("X = [" + ", ".join(str(i) for i in range(20)) + "]\n", 1),
        ("X = {" + ", ".join(f"{i}: {i}" for i in range(11)) + "}\n", 1),
    ],
)
def test_find_violations_threshold(
    source: str,
    expected_violations: int,
    tmp_path: Path,
):
    target = tmp_path / "sample.py"
    target.write_text(source, encoding="utf-8")
    assert len(find_violations(target, threshold=10)) == expected_violations


def test_find_violations_respects_allow_marker(tmp_path: Path):
    target = tmp_path / "sample.py"
    target.write_text(
        "# curveforge: allow-literal\nX = (" + ", ".join(str(i) for i in range(20)) + ")\n",
        encoding="utf-8",
    )
    assert find_violations(target, threshold=10) == []


def test_check_passes_on_curveforge_src():
    """Sanity check: this very codebase must not contain unmarked big literals."""
    assert main([str(ROOT / "src" / "curveforge")]) == 0
