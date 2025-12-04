#!/usr/bin/env python3
"""pycheck_tool - A single-file sanity-check tool for Python environments.

Drop this file into any project to get instant Python environment diagnostics.
Zero dependencies - uses only the standard library.

Usage as a module:
    import pycheck_tool as pycheck

    if pycheck.doSanityCheck(pycheck.OS):
        print("stdlib OK")

    result = pycheck.doSanityCheck(pycheck.ALL)
    if result:
        print(f"{result} packages importable")

Usage as CLI:
    python pycheck_tool.py --os          # Check stdlib only
    python pycheck_tool.py --all         # Check all packages
    python pycheck_tool.py --json        # JSON output for tooling

Author: Aubrey
License: MIT
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import re
import sys
import tempfile
from functools import lru_cache
from importlib.metadata import distributions
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Union

__all__ = [
    "doSanityCheck",
    "OS",
    "ALL",
    "SPECIFIC",
    "check_filesystem_access",
    "check_ssl_support",
    "main",
]

__author__ = "Aubrey"
__license__ = "MIT"
__version__ = "0.1.2.post1"

# ---------------------------------------------------------------------------
# Constants for check modes
# ---------------------------------------------------------------------------
OS = "OS"          # Check only standard-library / OS-level modules
ALL = "ALL"        # Check all installed packages (resource-heavy)
SPECIFIC = "SPECIFIC"  # Check specific packages (future use)


# ---------------------------------------------------------------------------
# Sanitization helpers (inline to keep single-file)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _get_username_pattern() -> Optional[Pattern[str]]:
    """Return a compiled regex pattern for the current username, cached."""
    try:
        username = os.environ.get("USERNAME") or os.environ.get("USER")
        if not username:
            username = Path.home().name
        if username and len(username) > 2:
            return re.compile(re.escape(username), re.IGNORECASE)
    except Exception:
        pass
    return None


def _sanitize_path(path_str: str) -> str:
    """Replace the user's home directory with '~' to avoid leaking PII."""
    try:
        home = os.path.expanduser("~")
        if home and path_str.startswith(home):
            return path_str.replace(home, "~", 1)
    except Exception:
        pass
    return path_str


def _sanitize_string(text: str) -> str:
    """Mask occurrences of the current username inside arbitrary text."""
    pattern = _get_username_pattern()
    if pattern:
        return pattern.sub("<user>", text)
    return text


def sanitize_value(value: Any) -> Any:
    """Sanitize arbitrary values (strings, dicts, lists) to remove PII."""
    if isinstance(value, str):
        return _sanitize_string(_sanitize_path(value))
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    return value


# ---------------------------------------------------------------------------
# Core check logic
# ---------------------------------------------------------------------------
def _try_import(module_name: str) -> bool:
    """Attempt to import a module by name. Returns True on success."""
    # Skip invalid module names (relative paths, empty, etc.)
    if not module_name or module_name.startswith('.') or module_name.startswith('-'):
        return False
    try:
        importlib.import_module(module_name)
        return True
    except (ImportError, AttributeError, ModuleNotFoundError):
        return False


def _get_stdlib_modules() -> list[str]:
    """Dynamically discover all stdlib module names for this Python."""
    # Python 3.10+ exposes this directly
    if hasattr(sys, "stdlib_module_names"):
        names = set(sys.stdlib_module_names)
    else:
        # Fallback for Python < 3.10: scan the stdlib path
        import pkgutil
        import os as _os
        stdlib_path = _os.path.dirname(_os.__file__)
        names = set()
        for importer, modname, ispkg in pkgutil.iter_modules([stdlib_path]):
            names.add(modname)

    # Platform-specific modules to skip
    _SKIP = {
        # GUI / optional
        "tkinter", "turtle", "idlelib", "turtledemo",
        # Test / dev
        "test", "lib2to3", "ensurepip", "venv", "distutils",
        # Unix-only
        "curses", "fcntl", "grp", "posix", "pty", "pwd",
        "readline", "resource", "syslog", "termios", "tty", "spwd", "crypt",
        # Windows-only (skip on Unix)
        "msvcrt", "winreg", "winsound", "nt", "msilib",
        # Easter eggs that have side effects (antigravity opens browser!)
        "antigravity", "this",
        # Other optional
        "dbm", "ossaudiodev", "nis", "posixpath", "ntpath",
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
            for f in dist.files:
                parts = str(f).replace("\\", "/").split("/")
                if parts:
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
    """Perform a sanity check on installed libraries.

    Args:
        mode: Either OS (fast, stdlib only) or ALL (all packages).

    Returns:
        - If mode == OS: True if all stdlib modules import successfully, else False.
        - If mode == ALL: A string like "142" indicating how many libraries passed,
          or False if none passed.
    """
    if mode == OS:
        stdlib_modules = _get_stdlib_modules()
        for mod in stdlib_modules:
            if not _try_import(mod):
                return False
        return True

    if mode == ALL:
        packages = _get_all_installed_packages()
        passed = 0
        for pkg in packages:
            if _try_import(pkg):
                passed += 1
        if passed == 0:
            return False  # type: ignore[return-value]
        return str(passed)

    raise ValueError(f"Unknown mode: {mode!r}. Use OS or ALL.")


def check_filesystem_access() -> Dict[str, Any]:
    """Verify the interpreter can create, write, and read a temp file."""
    result: Dict[str, Any] = {
        "capability": "filesystem_access",
        "status": "ok",
        "detail": "Temporary directory write/read succeeded.",
    }

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe = Path(tmpdir) / "pycheck_probe.txt"
            probe.write_text("pycheck", encoding="utf-8")
            data = probe.read_text(encoding="utf-8")
            if data != "pycheck":
                raise ValueError("Read data did not match written data.")

    except PermissionError:
        result["status"] = "fail"
        result["detail"] = "Permission denied: Cannot write to system temp directory."

    except (OSError, ValueError) as e:
        result["status"] = "warn"
        result["detail"] = f"Filesystem issue: {str(e)}"

    return result


def check_ssl_support() -> Dict[str, Any]:
    """Ensure the ssl module is importable and can create a default context."""
    result: Dict[str, Any] = {
        "capability": "ssl",
        "status": "ok",
        "detail": "SSL module and default context available.",
    }
    try:
        import ssl
        ssl.create_default_context()
    except (ImportError, AttributeError) as exc:
        result["status"] = "fail"
        result["detail"] = f"SSL unavailable: {exc.__class__.__name__}"
    except Exception as exc:
        result["status"] = "warn"
        result["detail"] = f"SSL issue: {exc.__class__.__name__}: {exc}"
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
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


def _print_json_report(entries: List[Dict[str, Any]], exit_code: int) -> None:
    """Emit a structured JSON report for tooling integrations."""
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
    """CLI entry point."""
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
    entries.append({
        "name": capability.get("capability", "filesystem_access"),
        "type": "capability",
        "status": capability.get("status", "unknown"),
        "detail": capability.get("detail"),
    })
    if capability.get("status") == "fail":
        exit_code = 1

    ssl_capability = check_ssl_support()
    entries.append({
        "name": ssl_capability.get("capability", "ssl"),
        "type": "capability",
        "status": ssl_capability.get("status", "unknown"),
        "detail": ssl_capability.get("detail"),
    })
    if ssl_capability.get("status") == "fail":
        exit_code = 1

    if args.json:
        sanitized_entries = [sanitize_value(e) for e in entries]
        _print_json_report(sanitized_entries, exit_code)
    else:
        _print_capability(capability)
        _print_capability(ssl_capability)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
