# pycheck-tool

[![PyPI version](https://img.shields.io/pypi/v/pycheck-tool.svg)](https://pypi.org/project/pycheck-tool/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

> **pycheck-tool** is the safe, zero-dependency way to answer “Is this Python install healthy?” — whether you’re a beginner sharing logs or a maintainer shipping CI.

## At a Glance

| | |
|-|-|
| **Current version** | `0.1.2` |
| **Python support** | 3.9 – 3.13 |
| **License** | MIT |
| **Maintainer** | Aubrey |
| **Status** | Reference implementation in incubation |

## Features

- **No dependencies** – works anywhere Python does.
- **Two-tier checks** – run `--os` for a quick stdlib sweep or `--all` when you need every package exercised.
- **Friendly CLI aliases** – `pycheck-tool`, `pycheck`, and `do_check` all point to the same entry point.
- **JSON with the *Dutcho* filter** – usernames and home paths are scrubbed automatically, so you can paste logs without leaking `/Users/you`.
- **Capability probes** – built-in filesystem + SSL diagnostics with clear pass/fail status codes.
- **Release automation** – published via Trusted Publishing as soon as you cut a GitHub Release.

## Quick Start

### Option A – use it

```powershell
pip install pycheck-tool

# Minimal health check (runs --os by default)
pycheck-tool
```

### Option B – hack on it

```powershell
git clone https://github.com/Auberryy/pycheck.git
cd pycheck
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
pytest
```

## Command cheat sheet

| When you need… | Run |
| --- | --- |
| Fast confidence in stdlib modules | `pycheck-tool --os`
| Exhaustive audit of installed packages | `pycheck-tool --all`
| Shareable JSON (sanitized) | `pycheck-tool --json > report.json`
| Human + JSON in one go | `pycheck-tool --os --json`
| Backwards-compatible names | `pycheck` or `do_check`

## JSON reports & the Dutcho filter

`--json` emits machine-friendly output (perfect for Neovim, editors, CI). Before printing, every string is sanitized:

- Home directory prefixes become `~`.
- Usernames are replaced with `<user>`.
- Capability entries (filesystem, SSL) share the exact status you can copy/paste online.

```powershell
pycheck-tool --json > reports\health.json
# Safe to share: no absolute paths or usernames leaked
```

## Python API

```python
import pycheck_tool as pycheck

if pycheck.doSanityCheck(pycheck.OS):
    print("OS Library is good")

result = pycheck.doSanityCheck(pycheck.ALL)
if result:
    print(result + " Libraries are fine!")
```

Use the API when you want to embed health checks into your own tooling or CI scripts.

## Capability probes

Each run appends capability entries to the report:

- `filesystem_access` – verifies we can write/read a temp file.
- `ssl` – ensures the `ssl` module imports and can create a default context (mocked in tests).

Failures cause a non-zero exit code so CI can gate on them.

## Development & release flow

1. Work on a feature branch, add tests (use `unittest.mock` to simulate failures).
2. Run `pytest` and `pycheck-tool --json` before pushing.
3. Open a PR. Once merged, create a GitHub Release — the `publish.yml` workflow builds and uploads to PyPI with trusted publishing (no tokens to copy).

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for full guidelines, including the “Zero Dependencies Forever” rule.

## Project layout

- `src/pycheck_tool.py` – core logic + CLI.
- `src/utils.py` – sanitization helpers shared by reports/tests.
- `tests/` – pytest suite with mocked failure scenarios.
- `examples/` – tiny runnable snippets.


