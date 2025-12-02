"""Command-line interface for pycheck sanity checks."""
from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import List, Dict, Any

if __package__ in {None, ""}:
    # Support running as `python src/pycheck/cli.py` by fixing sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from pycheck import __version__  # type: ignore
    from pycheck.checker import doSanityCheck, OS, ALL, check_filesystem_access, check_ssl_support  # type: ignore
    from utils import sanitize_value  # type: ignore
else:
    from . import __version__
    from .checker import doSanityCheck, OS, ALL, check_filesystem_access, check_ssl_support
    from .utils import sanitize_value


def _print_result(label: str, result: object) -> None:
    if result:
        if isinstance(result, str):
            print(f"{label}: {result} libraries passed")
        else:
            print(f"{label}: OK")
    else:
        print(f"{label}: FAILED")


def _print_capability(result: Dict[str, Any]) -> None:
    label = result.get("capability", "capability")
    status = result.get("status", "unknown")
    detail = result.get("detail", "")
    if status == "ok":
        print(f"Capability ({label}): OK")
        return
    print(f"Capability ({label}): {status.upper()} - {detail}")


def print_json_report(entries: List[Dict[str, Any]], exit_code: int) -> None:
    """Emit a structured JSON report for tooling integrations like Neovim."""
    system_info = {
        "version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
    }
    payload = {
        "pycheck_version": __version__,
        "python": system_info,
        "results": entries,
        "exit_code": exit_code,
    }
    print(json.dumps(payload, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pycheck",
        description="Run simple sanity checks against your Python environment.",
    )
    parser.add_argument(
        "--os",
        action="store_true",
        help="Check core stdlib modules only (fast).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check every installed package (can be slow).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of human-readable text.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args(argv)

    # default mode: run OS check if no flag provided
    modes: list[str] = []
    if args.os:
        modes.append(OS)
    if args.all:
        modes.append(ALL)
    if not modes:
        modes.append(OS)

    exit_code = 0
    entries: List[Dict[str, Any]] = []
    for mode in modes:
        result = doSanityCheck(mode)
        label = "OS" if mode == OS else "ALL"
        if not args.json:
            _print_result(label, result)
        entry: Dict[str, Any] = {
            "name": label,
            "type": "check",
            "status": "ok" if result else "fail",
        }
        if isinstance(result, str):
            entry["detail"] = {
                "libraries_passed": result,
            }
        entries.append(entry)
        if not result:
            exit_code = 1

    capability = check_filesystem_access()
    entries.append(
        {
            "name": capability.get("capability", "filesystem_access"),
            "type": "capability",
            "status": capability.get("status", "unknown"),
            "detail": capability.get("detail"),
        }
    )
    if capability.get("status") == "fail":
        exit_code = 1

    ssl_capability = check_ssl_support()
    entries.append(
        {
            "name": ssl_capability.get("capability", "ssl"),
            "type": "capability",
            "status": ssl_capability.get("status", "unknown"),
            "detail": ssl_capability.get("detail"),
        }
    )
    if ssl_capability.get("status") == "fail":
        exit_code = 1

    if args.json:
        # Sanitize all entries to remove PII before printing
        sanitized_entries = [sanitize_value(e) for e in entries]
        print_json_report(sanitized_entries, exit_code)
    else:
        _print_capability(capability)
        _print_capability(ssl_capability)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())