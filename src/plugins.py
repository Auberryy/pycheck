"""Plugin discovery and management helpers."""
from typing import Iterable, Any, Callable, Optional
import importlib
import pkgutil
import inspect
from .registry import Registry


class PluginManager:
    """Discover and load plugins.

    A plugin is any module that exposes a `register` function or a `plugin` attribute.
    """

    def __init__(self, namespace_package: str = "verydynamic.plugins") -> None:
        self.namespace_package = namespace_package
        self.registry = Registry()

    def discover_from_package(self, package: str | None = None) -> Iterable[str]:
        pkg = package or self.namespace_package
        try:
            module = importlib.import_module(pkg)
        except Exception:
            return []
        base = module.__path__  # type: ignore[attr-defined]
        names = [name for _, name, _ in pkgutil.iter_modules(base)]
        return [f"{pkg}.{name}" for name in names]

    def load(self, module_path: str) -> Any:
        """Import a plugin module and call its register function if present.

        Returns the module object.
        """
        mod = importlib.import_module(module_path)
        # allow `register(registry)` or `plugin` attribute
        if hasattr(mod, "register") and callable(getattr(mod, "register")):
            getattr(mod, "register")(self.registry)
        elif hasattr(mod, "plugin"):
            plugin = getattr(mod, "plugin")
            # if plugin is callable, call it with registry
            if callable(plugin):
                plugin(self.registry)
            else:
                # assume mapping of name->obj
                if isinstance(plugin, dict):
                    for k, v in plugin.items():
                        self.registry.add(k, v)
        else:
            # scan for top-level functions/classes with `__plugin_name__` attribute
            for name, obj in inspect.getmembers(mod):
                if getattr(obj, "__plugin_name__", None):
                    self.registry.add(getattr(obj, "__plugin_name__"), obj)
        return mod

    def load_all(self, package: str | None = None) -> int:
        modules = self.discover_from_package(package)
        count = 0
        for m in modules:
            try:
                self.load(m)
                count += 1
            except Exception:
                # ignore plugin load errors by default
                continue
        return count

    def list_plugins(self) -> Iterable[str]:
        return self.registry.list()

    def get(self, name: str) -> Any:
        return self.registry.get(name)