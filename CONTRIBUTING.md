# Contributing to curveforge

Thanks for considering a contribution. The most valuable additions are new
research-grounded curves and well-documented transforms — both can be added
without touching the rest of the codebase.

## Add a new curve

1. Create `src/curveforge/curves/my_curve.py` with three things:
   - A Pydantic `Params` model describing the native knobs (use `Field` with
     `description=`, `ge=`, `le=` so `info` and CLI errors stay informative).
   - A `_render(params, freqs) -> NDArray[float64]` function returning gains
     in dB at each frequency.
   - A module-level `SPEC: CurveSpec[MyParams]` referencing all of the above
     plus a one-line description and a citation string.

   Use `curveforge.dsp` for analytical shapes (low-shelf, high-shelf,
   peaking, tilt, Butterworth high-pass) so the math stays consistent.

2. Register it: add the import and SPEC to
   `src/curveforge/curves/__init__.py` in the `_REGISTERED` tuple.

3. Add a snapshot test in `tests/test_curves.py`. The convention is: render
   default params on a small log grid, compare against a checked-in
   reference array.

4. Cite your source in the module docstring (paper, page, or URL). The
   `info` command exposes this to users.

## Add a new transform

1. Create `src/curveforge/transforms/my_transform.py` with a Pydantic
   `Params` model, an `_apply(curve, params) -> Curve` function, and a
   `SPEC: TransformSpec[MyParams]`.

2. Register it in `src/curveforge/transforms/__init__.py`.

3. Add a unit test that applies the transform to a flat 0 dB curve and
   asserts a known shape.

## Keep data out of `.py` source

If a curve has to be expressed as raw breakpoints (e.g. a vendor's
published target file that's not analytically described), ship it as a
data file alongside the package source and load it via
`importlib.resources`. Don't encode big arrays in the Python source.

The literal-size check (`tools/check_literal_size.py`, run in CI) fails
the build if any `.py` file under `src/curveforge/` declares a list /
tuple / set / dict literal with more than 10 elements. Genuine in-code
reference constants (e.g. ISO 1/3-octave centers) can be exempted by
placing `# curveforge: allow-literal` on the line directly above the
literal.

## Style and lint

We use `ruff` (lint + format) and `mypy --strict`. Pyright runs as a
secondary checker in `standard` mode. Hard caps:

- 50 lines per function (max per ruff config).
- Cyclomatic complexity 12, cognitive complexity 15.
- Avoid `Any` in production code where a concrete type fits.
  `Any` is permitted at Pydantic / JSON-schema boundaries where raw
  user-supplied dicts are being coerced; each such use carries a
  `# noqa: ANN401 — <reason>` annotation explaining why.
- No `# type: ignore` without an inline explanation.
- Public symbols (modules, classes, top-level functions) carry a
  docstring; private helpers can be undocumented if the name is
  self-explanatory.
- Large literal collections (list/tuple/set/dict with >10 elements)
  in `src/curveforge/` are rejected by the literal-size linter;
  move them to data files or add `# curveforge: allow-literal`.

```sh
pip install -e '.[dev]'
ruff check
ruff format --check
mypy src
pyright src
python tools/check_literal_size.py src/curveforge
pytest
```

CI runs the same on Python 3.11, 3.12, 3.13 across Ubuntu and macOS.
