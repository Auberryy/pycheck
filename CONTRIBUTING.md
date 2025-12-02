# Contributing to pycheck-tool

Thanks for your interest in improving pycheck-tool!

## Quick Start

1. **Clone and install dev deps**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -e .[dev]
   ```
2. **Run the test suite**
   ```powershell
   pytest
   ```
3. **Create feature branches** based off `master`, and submit pull requests via GitHub.

## Pull Request Checklist

- Include tests for new functionality (use `unittest.mock` where appropriate).
- Keep runtime dependencies at zero.
- Ensure `pycheck_tool --json` output remains sanitized (no usernames/home paths).
- Update documentation (README, examples) to describe user-visible changes.
- Run `pytest` and the CLI (`pycheck-tool --os`, `pycheck-tool --json`) before submitting.

## Release Process

Publishing to PyPI is automated via GitHub Releases. After merging, tag a release in GitHub and the `publish` workflow will build and upload the package using trusted publishing.
