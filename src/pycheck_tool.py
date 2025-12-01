"""pycheck-tool

A simple, dynamic sanity-check helper for Python distributions.

Usage:
    import pycheck_tool

    result = pycheck_tool.doSanityCheck(pycheck_tool.OS)
    if result:
        print("OS Library is good")

    result = pycheck_tool.doSanityCheck(pycheck_tool.ALL)
    if result:
        print(result + " Libraries are fine!")
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
import tempfile
from importlib.metadata import distributions
from pathlib import Path
from typing import Any, Dict, List, Union

__all__ = [
    "doSanityCheck",
    "check_filesystem_access",
    "print_json_report",
    "main",
    "OS",
    "ALL",
    "SPECIFIC",
]

__author__ = "Aubrey"
__license__ = "MIT"
__version__ = "0.1.1"

OS = "OS"      # Check only standard-library / OS-level modules
ALL = "ALL"    # Check all installed packages (resource-heavy)
SPECIFIC = "SPECIFIC"  # Check specific packages


def _try_import(module_name: str) -> bool:
    """Attempt to import a module by name. Returns True on success."""
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


def _get_stdlib_modules() -> list[str]:
    """Dynamically discover all stdlib module names for this Python."""
    if hasattr(sys, "stdlib_module_names"):
        names = set(sys.stdlib_module_names)
    else:
        import pkgutil
        import os as _os

        stdlib_path = _os.path.dirname(_os.__file__)
        names = {
            modname
            for _, modname, _ in pkgutil.iter_modules([stdlib_path])
        }

    _SKIP = {
        "tkinter",
        "turtle",
        "idlelib",
        "turtledemo",
        "test",
        "lib2to3",
        "ensurepip",
        "venv",
        "distutils",
        "curses",
        "fcntl",
        "grp",
        "posix",
        "pty",
        "pwd",
        "readline",
        "resource",
        "syslog",
        "termios",
        "tty",
        "spwd",
        "crypt",
        "msvcrt",
        "winreg",
        "winsound",
        "nt",
        "msilib",
        "antigravity",
        "this",
        "dbm",
        "ossaudiodev",
        "nis",
        "posixpath",
        "ntpath",
    }

    filtered: list[str] = []
    for name in sorted(names):
        if name.startswith("_"):
            continue
        if name in _SKIP:
            continue
        filtered.append(name)
    return filtered


def _get_all_installed_packages() -> list[str]:
    """Return a list of top-level package names installed in the current env."""
    seen: set[str] = set()
    for dist in distributions():
        try:
            top_level = dist.read_text("top_level.txt")
            if top_level:
                for line in top_level.strip().splitlines():
                    name = line.strip()
                    if name and not name.startswith("_"):
                        seen.add(name)
                continue
        except Exception:
            pass

        if dist.files:
            for file_ref in dist.files:
                parts = str(file_ref).replace("\\", "/").split("/")
                if not parts:
                    continue
                first = parts[0]
                if first.endswith(".py"):
                    name = first[:-3]
                else:
                    name = first
                if name and not name.startswith("_"):
                    seen.add(name)

        dist_name = dist.metadata.get("Name", "")
        if dist_name:
            norm = dist_name.replace("-", "_").lower()
            seen.add(norm)

    return sorted(seen)


def doSanityCheck(mode: str) -> Union[bool, str]:
    """Perform a sanity check on installed libraries."""
    if mode == OS:
        for mod in _get_stdlib_modules():
            if not _try_import(mod):
                return False
        return True

    if mode == ALL:
        passed = 0
        for pkg in _get_all_installed_packages():
            if _try_import(pkg):
                passed += 1
        if passed == 0:
            return False  # type: ignore[return-value]
        return str(passed)

    raise ValueError(
        f"Unknown mode: {mode!r}. Use pycheck_tool.OS or pycheck_tool.ALL."
    )


def check_filesystem_access() -> Dict[str, Any]:
    """Verify the interpreter can create, write, and read a temp file."""
    result: Dict[str, Any] = {
        "capability": "filesystem_access",
        "status": "ok",
        "detail": "Temporary directory write/read succeeded.",
    }
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe = Path(tmpdir) / "pycheck_tool_probe.txt"
            probe.write_text("pycheck_tool", encoding="utf-8")
            data = probe.read_text(encoding="utf-8")
            if data != "pycheck_tool":
                raise OSError("Failed to verify written bytes.")
    except PermissionError:
        result["status"] = "fail"
        result["detail"] = "Permission denied while accessing temporary storage."
    except OSError:
        result["status"] = "warn"
        result["detail"] = "Unexpected filesystem issue detected during probe."
    return result


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
    payload: Dict[str, Any] = {
        "pycheck_tool_version": __version__,
        "python": system_info,
        "results": entries,
        "exit_code": exit_code,
    }
    print(json.dumps(payload, indent=2))


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pycheck-tool",
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
            entry["detail"] = {"libraries_passed": result}
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

    if args.json:
        print_json_report(entries, exit_code)
    else:
        _print_capability(capability)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
