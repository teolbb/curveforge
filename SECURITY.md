# Security policy

## Reporting a vulnerability

If you discover a security vulnerability in curveforge, please **do not**
open a public issue. Instead, report it privately by:

- Opening a GitHub Security Advisory on the repository
  ([Security tab → Report a vulnerability](https://github.com/teolbb/curveforge/security/advisories/new)), or
- Emailing the maintainer directly (address in commit metadata).

We will acknowledge receipt within a few days and aim to publish a fix or
mitigation within two weeks for typical issues.

## Threat model

curveforge is a CLI / library that:

- Reads YAML recipes from local disk via `yaml.safe_load` (no arbitrary
  Python code execution from YAML).
- Reads `.targetcurve` text files from local disk via a hand-rolled parser
  with strict type validation.
- Writes `.targetcurve` / JSON / CSV / PNG output files to local disk.
- Loads bundled `.targetcurve` fixture data via `importlib.resources`.

It does not make network calls, execute external processes, or evaluate
user-supplied code. The main attack surfaces to consider are:

- Malformed YAML or `.targetcurve` input causing parser crashes (treated as
  user errors; should never compromise process integrity).
- Path traversal via `output.path` in a recipe — the CLI writes wherever
  the user (or the recipe) tells it to. Treat untrusted recipes as untrusted
  filesystem operations.

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | ✅ |

Older versions are not maintained.
