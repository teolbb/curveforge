"""Fail if any source file contains a literal collection larger than a threshold.

Long hardcoded arrays in `.py` files almost always represent data — published
breakpoints, lookup tables, calibration values — that should live in a data
file (read at runtime via `importlib.resources`). Keeping them in code
inflates the file, breaks the line-length / function-size discipline, and
hides provenance.

Run with: `python tools/check_literal_size.py src/curveforge`

Allow a specific literal by placing the marker comment
`# curveforge: allow-literal` on the line *immediately preceding* its
opening bracket. The marker exists for genuine in-code constants like
small enumerations of well-known reference values.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Final

DEFAULT_THRESHOLD: Final[int] = 10
ALLOW_MARKER: Final[str] = "curveforge: allow-literal"


def _is_collection_literal(node: ast.AST) -> bool:
    return isinstance(node, (ast.Tuple, ast.List, ast.Set, ast.Dict))


def _literal_size(node: ast.AST) -> int:
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return len(node.elts)
    if isinstance(node, ast.Dict):
        return len(node.keys)
    msg = f"unexpected node type {type(node).__name__}"
    raise TypeError(msg)


def _is_allowed(source_lines: list[str], lineno: int) -> bool:
    """Return True if a `curveforge: allow-literal` marker precedes this line."""
    for offset in range(1, 4):
        index = lineno - 1 - offset
        if index < 0:
            return False
        line = source_lines[index].strip()
        if not line:
            continue
        return line.startswith("#") and ALLOW_MARKER in line
    return False


def find_violations(path: Path, threshold: int) -> list[tuple[int, int]]:
    """Return `(lineno, size)` pairs for literals exceeding `threshold` in `path`."""
    text = path.read_text(encoding="utf-8")
    source_lines = text.splitlines()
    tree = ast.parse(text, filename=str(path))
    out: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if not _is_collection_literal(node):
            continue
        size = _literal_size(node)
        if size <= threshold:
            continue
        if _is_allowed(source_lines, node.lineno):
            continue
        out.append((node.lineno, size))
    return out


def _iter_python_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            files.append(root)
            continue
        files.extend(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)
    return sorted(files)


def main(argv: list[str]) -> int:
    """Walk `argv` (paths) and return 0/1 based on whether any violation is found."""
    if not argv:
        argv = ["src/curveforge"]
    roots = [Path(arg) for arg in argv]
    failures: list[str] = []
    for path in _iter_python_files(roots):
        for lineno, size in find_violations(path, DEFAULT_THRESHOLD):
            failures.append(
                f"{path}:{lineno}: literal collection of {size} elements "
                f"(threshold {DEFAULT_THRESHOLD}); move to a data file "
                f"or add `# {ALLOW_MARKER}` above it.",
            )
    if failures:
        for line in failures:
            print(line, file=sys.stderr)  # noqa: T201 — CLI tool
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
