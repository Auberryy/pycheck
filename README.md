# pycheck-tool

> Note: This is a Reference Implementation for a proposed Python Standard Library module. It is currently in the "Incubation" phase to test stability and feature sets.

## Metadata

- Author: Aubrey
- Current Version: 0.1.1
- License: MIT

**pycheck-tool** is a zero-dependency sanity checker for Python environments. It can quickly verify
that your stdlib is intact (`--os`) or run a heavier pass over every installed package (`--all`).

## Features

-  Pure Python — no third-party dependencies.
-  Fast stdlib check (`OS` mode) using dynamic discovery of available modules.
-  Full environment sweep (`ALL` mode) that attempts to import every installed distribution.
-  Both API (`pycheck_tool.doSanityCheck`) and CLI (`pycheck-tool`, `pycheck`, `do_check`) entry points.
-  Supports direct output, and JSON output (for developers).
  
## Installation
To install pycheck-tool, you can follow 2 methods. Firstly via ``pip``, or via powershell.
For contributions it is advised to use the second method, for usage it is advised to use the first method.
```powershell
pip install pycheck-tool
```

```powershell
# From the project root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

## Usage

### Python API

```python
import pycheck_tool as pycheck

if pycheck.doSanityCheck(pycheck.OS):
	print("OS Library is good")

result = pycheck.doSanityCheck(pycheck.ALL)
if result:
	print(result + " Libraries are fine!")
```

### CLI

```powershell
# Fast stdlib validation
pycheck-tool --os

# Full environment sweep (can be slow)
pycheck-tool --all

# Output sent to a newly created report.json in your current working directory
pycheck-tool --json > report.json

# Output sent to health.json this time in the folder "reports".
pycheck-tool --json > .\reports\health.json

# (pycheck-tool never writes to disk on its own; redirecting stdout is what creates the file.)

# If no flags are supplied, --os is run by default
pycheck-tool
```

The legacy `pycheck` and `do_check` console aliases are still provided for convenience; both map to the same CLI entry point.
```

## Development

```powershell
# Run tests
pytest

# Example script
python examples\demo.py
```

## Project Layout

- `src/pycheck_tool.py` — package source (single-file checker + CLI)
- `tests/` — pytest suite
- `examples/` — quick usage snippets


