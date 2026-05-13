# Changelog

All notable changes to this project will be documented in this file. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0.post1]

### Fixed
- README image references are now absolute URLs so they render on the
  PyPI project page (relative paths only resolve on GitHub).

## [0.1.0]

Initial public release.

### Added
- Curve library: `harman` (first-order bass shelf), `olive_welti_inroom`,
  `b_and_k`, `toole_inroom`, `welti_sub`, `flat`, `breakpoints`. Each
  parametric, with cited research source.
- Transform library: `gain` (band, cosine-tapered), `peq` (RBJ peaking
  biquad), `shelf` (low/high), `rolloff` (Butterworth), `tilt` (linear).
- CLI: `build`, `render`, `list`, `info`, `validate`, `diff`, `plot`,
  `tweak`. Exit codes 0 / 1 (usage) / 2 (I/O).
- Python library API: `build_curve()` for programmatic use without YAML.
- `.targetcurve` reader and writer compatible with Dirac Live 2/3.
- Recipe gallery under `gallery/` with annotated real-world recipes.
- Triangle BR09 + SVS SB-2000 case study illustrating the iterative
  voicing workflow.
- Plot command with matplotlib (optional `[plot]` extra).
- Strict lint stack: ruff (~50 rule families), mypy strict, pyright,
  pydocstyle, pylint complexity caps.
- Custom AST-based literal-size linter to keep big arrays out of source.
- PEP 561 typed package (`py.typed` marker).
- 92% test coverage on Python 3.11 / 3.12 / 3.13.
