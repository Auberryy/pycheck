"""Core sanity-check logic for pycheck.

This module provides the doSanityCheck function and the OS/ALL constants.

Everything is discovered dynamically at runtime — no hard-coded lists.
"""

from __future__ import annotations
import importlib
import sys
import tempfile
import warnings
from pathlib import Path
from importlib.metadata import distributions
from typing import Union, Dict, Any

# ---------------------------------------------------------------------------
# Suppress deprecation warnings from Python internals
# ---------------------------------------------------------------------------
# These warnings (e.g., "module 'sre_compile' is deprecated" in Python 3.13)
# leak file paths containing usernames to stderr. Since pycheck imports many
# modules dynamically, we suppress these to protect user privacy.
warnings.filterwarnings("ignore", category=DeprecationWarning, module=r"importlib.*")
warnings.filterwarnings("ignore", message=r"module 'sre_.*' is deprecated")

# ---------------------------------------------------------------------------
# Constants for check modes
# ---------------------------------------------------------------------------
OS = "OS"      # Check only standard-library / OS-level modules
ALL = "ALL"    # Check all installed packages (resource-heavy)
SPECIFIC = "SPECIFIC"  # Check specific packages


def _is_valid_module_name(name: str) -> bool:
    """Quick validation for candidate import names to avoid raising "relative import" errors.

    We only allow names that look like importable module/package names (no leading dots,
    no whitespace, and no path separators). This keeps `importlib.import_module` from
    being asked to resolve relative imports or paths which will raise a TypeError.
    """
    if not name:
        return False
    if name.startswith(('.', '/')):
        return False
    if any(c.isspace() for c in name):
        return False
    if '\\' in name or '/' in name:
        return False
    return True


def _try_import(module_name: str) -> bool:
    """Attempt to import a module by name. Returns True on success.

    This function is intentionally robust: any exception raised while importing
    will cause the function to return False rather than propagate up. Importing
    third-party packages can execute arbitrary code (including raising
    SystemExit), so we treat any failure as a non-importable package rather
    than failing the whole tool.
    """
    if not _is_valid_module_name(module_name):
        return False
    try:
        importlib.import_module(module_name)
        return True
    except Exception as e:
        # If the import raised a KeyboardInterrupt or SystemExit, re-raise them; these
        # are not import errors and should be propagated to allow the user to ctrl-c
        # or terminate the program normally.
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        # We explicitly catch Exception here — this prevents a single broken
        # installed package from causing the entire sanity check to crash.
        return False


def _get_stdlib_modules() -> list[str]:
    """Dynamically discover all stdlib module names for this Python.
    
    Filters out private modules (starting with _) and platform-specific
    modules that may not be available on all systems.
    """
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
    # These are Unix-only or Windows-only and won't import on the other OS
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

    # Filter out private and platform-specific modules
    filtered: list[str] = []
    for name in sorted(names):
        # Skip private/internal modules
        if name.startswith("_"):
            continue
        if name in _SKIP:
            continue
        filtered.append(name)
    return filtered


def _get_all_installed_packages() -> list[str]:
    """Return a list of top-level package names installed in the current env.

    Uses importlib.metadata to discover every installed distribution and
    extracts their importable top-level names.
    
    This function is designed to be robust against corrupted environments,
    including corrupted sys.modules entries for csv, importlib, etc.
    """
    seen: set[str] = set()
    
    # Wrap the entire distributions() call in case it fails
    try:
        dist_iter = distributions()
    except Exception:
        # If we can't even get the distributions iterator, return empty
        return []
    
    for dist in dist_iter:
        # Wrap each distribution's processing - a single broken dist shouldn't
        # crash the entire enumeration
        try:
            # Try reading top_level.txt if available
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

            # Fallback: infer from dist files
            # Wrap in try/except because dist.files can crash if csv module is corrupted
            try:
                files = dist.files
                if files:
                    for f in files:
                        parts = str(f).replace("\\", "/").split("/")
                        if parts:
                            first = parts[0]
                            if first.endswith(".py"):
                                name = first[:-3]
                            else:
                                name = first
                            if name and not name.startswith("_"):
                                seen.add(name)
            except Exception:
                pass

            # Also add normalized distribution name
            # Wrap because dist.metadata can crash in corrupted environments
            try:
                dist_name = dist.metadata.get("Name", "")
                if dist_name:
                    norm = dist_name.replace("-", "_").lower()
                    seen.add(norm)
            except Exception:
                pass
                
        except Exception:
            # If processing this distribution fails entirely, skip it
            continue

    return sorted(seen)


def doSanityCheck(mode: str) -> Union[bool, str]:
    """Perform a sanity check on installed libraries.

    Args:
        mode: Either pycheck.OS (fast, stdlib only) or pycheck.ALL (all packages).

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

    raise ValueError(f"Unknown mode: {mode!r}. Use pycheck.OS or pycheck.ALL.")


def get_failed_imports(mode: str) -> list[str]:
    """Return a list of module or package names that failed to import.

    This function is intended to be used for diagnostics only. It performs the same
    discovery as doSanityCheck but returns the names that failed to import so the
    CLI can report which specific modules caused failure.

    Returns:
        A list of module names that failed to import. Always returns a list,
        never None (defensive programming).
    """
    failed: list[str] = []  # Always initialized to empty list, never None
    if mode == OS:
        modules = _get_stdlib_modules()
        for m in modules:
            if not _try_import(m):
                failed.append(m)
        return failed
    if mode == ALL:
        packages = _get_all_installed_packages()
        for p in packages:
            if not _try_import(p):
                failed.append(p)
        return failed
    raise ValueError(f"Unknown mode: {mode!r}. Use pycheck.OS or pycheck.ALL.")


def check_filesystem_access() -> Dict[str, Any]:
    """Verify the interpreter can create, write, and read a temp file."""
    result: Dict[str, Any] = {
        "capability": "filesystem_access",
        "status": "ok",
        "detail": "Temporary directory write/read succeeded.",
    }
    
    try:
        # Use the context manager to ensure cleanup happens even if we crash
        with tempfile.TemporaryDirectory() as tmpdir:
            probe = Path(tmpdir) / "pycheck_probe.txt"
            
            # Test Write
            probe.write_text("pycheck", encoding="utf-8")
            
            # Test Read
            data = probe.read_text(encoding="utf-8")
            
            # Test Integrity
            if data != "pycheck":
                # We raise a custom error to differentiate from system I/O errors
                raise ValueError("Read data did not match written data.")
                
    except PermissionError:
        result["status"] = "fail"
        result["detail"] = "Permission denied: Cannot write to system temp directory."
        
    except (OSError, ValueError) as e:
        # Catch both System I/O errors AND our integrity check
        result["status"] = "warn"
        # Now the JSON will actually say "Read data did not match..." or "No space left on device"
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
