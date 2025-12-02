"""Utility helpers for pycheck-tool.

Provides sanitization helpers to remove PII from paths/strings before
reporting, plus misc dynamic import helper for future extension.
"""

from __future__ import annotations

import importlib
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, Pattern


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


def sanitize_path(path_str: str) -> str:
    """Replace the user's home directory with '~' to avoid leaking PII."""
    try:
        home = os.path.expanduser("~")
        if home and path_str.startswith(home):
            return path_str.replace(home, "~", 1)
    except Exception:
        pass
    return path_str


def sanitize_string(text: str) -> str:
    """Mask occurrences of the current username inside arbitrary text."""
    pattern = _get_username_pattern()
    if pattern:
        return pattern.sub("<user>", text)
    return text


def sanitize_value(value: Any) -> Any:
    """Sanitize arbitrary values (strings, dicts, lists)."""
    if isinstance(value, str):
        return sanitize_string(sanitize_path(value))
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    return value


def dynamic_import(path: str) -> Any:
    """Dynamically import a symbol given a full import path string."""
    if ":" in path:
        module_path, attr = path.split(":", 1)
    elif "." in path:
        module_path, attr = path.rsplit(".", 1)
    else:
        module_path, attr = path, ""

    module = importlib.import_module(module_path)
    if not attr:
        return module
    return getattr(module, attr)
