"""Utility helpers for verydynamic."""
from typing import Any
import importlib


def dynamic_import(path: str) -> Any:
    """Dynamically import a symbol given a full import path like 'package.module:Symbol' or 'package.module.Symbol'.

    Returns the imported object or raises ImportError/AttributeError.
    """
    if ":" in path:
        module_path, attr = path.split(":", 1)
    elif "." in path:
        parts = path.rsplit(".", 1)
        module_path, attr = parts[0], parts[1]
    else:
        module_path, attr = path, ""

    module = importlib.import_module(module_path)
    if not attr:
        return module
    return getattr(module, attr)