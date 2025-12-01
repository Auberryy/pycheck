"""A simple runtime registry for functions/classes/objects."""
from typing import Callable, Dict, Iterable, Optional, Any


class Registry:
    """Registry stores callables or objects under string keys.

    Usage:
        reg = Registry()
        @reg.register("task.name")
        def fn(...):
            ...
    """

    def __init__(self) -> None:
        self._items: Dict[str, Any] = {}

    def register(self, name: Optional[str] = None):
        """Decorator or direct register. If used as decorator, returns a wrapper.

        Examples:
            @reg.register('a')
            def f():
                pass
        """

        def _decorator(obj: Any):
            key = name or getattr(obj, "__name__", None)
            if not key:
                raise ValueError("Registry items must have a name")
            self._items[key] = obj
            return obj

        return _decorator

    def add(self, name: str, obj: Any) -> None:
        """Add an object directly."""
        self._items[name] = obj

    def get(self, name: str, default: Optional[Any] = None) -> Any:
        return self._items.get(name, default)

    def pop(self, name: str) -> Any:
        return self._items.pop(name)

    def list(self) -> Iterable[str]:
        return list(self._items.keys())

    def items(self):
        return self._items.items()

    def clear(self):
        self._items.clear()

    def __contains__(self, key: str) -> bool:
        return key in self._items