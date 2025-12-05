# pycheck-tool

[![PyPI version](https://img.shields.io/pypi/v/pycheck-tool.svg)](https://pypi.org/project/pycheck-tool/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/pycheck-tool.svg)](https://pypi.org/project/pycheck-tool/)
[![Downloads](https://static.pepy.tech/badge/pycheck-tool)](https://pepy.tech/project/pycheck-tool)

> **pycheck-tool** is the safe, zero-dependency way to answer "Is this Python install healthy?" — whether you're a beginner sharing logs or a maintainer shipping CI. If you personally believe that it should have something it doesn't have, then feel free to put it in a pull request!
> If you want to make your own pycheck, then feel free to fork this repository!

## At a Glance

| | |
|-|-|
| **Current version** | `0.1.4` |
| **Python support** | 3.9 – 3.13 |
| **License** | MIT |
| **Maintainer** | Aubrey |

## Features

- **No dependencies** – works anywhere Python does.
- **Two-tier checks** – run `--os` for a quick stdlib sweep or `--all` when you need every package exercised.
- **Friendly CLI aliases** – `pycheck-tool`, `pycheck`, and `do_check` all point to the same entry point.
- **JSON with the *Dutcho* filter** – usernames and home paths are scrubbed automatically, so you can paste logs without leaking `/Users/you`.
- **Capability probes** – built-in filesystem + SSL diagnostics with clear pass/fail status codes.
- **Hostile environment resilience** – survives corrupted `sys.modules`, broken imports, and malformed distributions without crashing.
- **Debug diagnostics** – use `--debug` to see which modules failed to import.
- **Spam protection** – use `--limit N` to cap output when checking many packages.
- **Release automation** – published via Trusted Publishing as soon as you cut a GitHub Release.

## Quick Start

### Option A – use it

```powershell
pip install pycheck-tool

# Minimal health check (runs --os by default)
pycheck-tool
```

You can also get it via `curl`, by typing:

```bash
curl -fsSL https://raw.githubusercontent.com/Auberryy/pycheck/main/pycheck_tool.py | python3 - 
```

You can use the following arguments with every pycheck_tool.py command in the console:
```bash
-h (or) --help    Shows you the help message, and exists.
--os              Checks core stdlib modules only (stdlib is short for Standard Libraries, so the libraries that come with python)
--all             Checks every single library you have installed on that python version (can be slow)
--json            Changes your output into a JSON report, which you can then use for error reports
--limit [Number]  Max numbers of failed modules to show (default is 20)
--version         Shows your installed version
```
A little deeper you can also see a bigger cheat sheet.

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
| Fast confidence in stdlib modules | `pycheck --os` |
| Exhaustive audit of installed packages | `pycheck --all` |
| Shareable JSON (sanitized JSON will be saved) | `pycheck --json > report.json` |
| Human + JSON in one go | `pycheck --os --json` |
| Debug failing imports | `pycheck --os --debug` |
| Limit output spam (only 10 modules show) | `pycheck --all --limit 10` |
| Backwards-compatible names | `pycheck-tool` or `do_check` |

## JSON reports & the Dutcho filter

`--json` emits machine-friendly output (perfect for Neovim, editors, CI). Before printing, every string is sanitized:

- Home directory prefixes become `~`.
- Usernames are replaced with `<user>`.
- Capability entries (filesystem, SSL) share the exact status you can copy/paste online.

Thank you very much Dutcho for suggesting the filter!

```powershell
pycheck --json > reports\health.json
# Safe to share: no absolute paths or usernames leaked
```

## Python API
You can also make your own python scripts using the PiPY module!
The following is a simple and small check that checks your standard libraries, and then all of your libraries.

```python
import pycheck

# Quick stdlib check
passed, failures = pycheck.doSanityCheck(pycheck.OS)
if passed:
    print("OS Library is good")
else:
    print(f"Issues found: {failures}")

# Full package audit
passed, failures = pycheck.doSanityCheck(pycheck.ALL)
if passed:
    print("All libraries are fine!")
```

Use the API when you want to embed health checks into your own tooling or CI scripts.

## Capability probes

Each run appends capability entries to the report:

- `filesystem_access` – verifies we can write/read a temp file.
- `ssl` – ensures the `ssl` module imports and can create a default context.

Failures cause a non-zero exit code so CI can gate on them.

## Robustness

pycheck is designed to survive hostile environments:

- **Corrupted sys.modules** – handles `None`, integers, or broken objects where modules should be.
- **Broken distributions** – gracefully skips packages with corrupted metadata.
- **Import side effects** – catches exceptions from packages that crash during import.
- **Ctrl+C support** – properly propagates `KeyboardInterrupt` and `SystemExit`.

## Development & release flow

1. Work on a feature branch, add tests (use `unittest.mock` to simulate failures).
2. Run `pytest` and `pycheck --json` before pushing.
3. Open a PR. Once merged, create a GitHub Release — the `publish.yml` workflow builds and uploads to PyPI with trusted publishing (no tokens to copy).

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for full guidelines, including the "Zero Dependencies Forever" rule.

## Project layout

```
src/pycheck/
├── __init__.py   # Package exports and version
├── checker.py    # Core sanity-check logic
├── cli.py        # CLI entry point and argument parsing
└── utils.py      # Sanitization helpers
tests/            # pytest suite with mocked failure scenarios
examples/         # Tiny runnable snippets
pycheck_tool.py   # Standalone single-file version
```

## 🤝 Contributing

Found a bug? Have a fix? We welcome your help!

* **Found a bug?** [Open a Bug Report](https://github.com/Auberryy/pycheck/issues/new?template=bug_report.md).
* **Have a fix?** Fork the repo, make your changes, and submit a Pull Request.

