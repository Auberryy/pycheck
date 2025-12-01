"""Simple configuration container with environment overrides."""
from typing import Any, Dict, Optional
import os


class Config:
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._data = dict(data or {})

    def get(self, key: str, default: Any = None) -> Any:
        # environment variables take precedence if set
        env_key = key.upper().replace(".", "_")
        if env_key in os.environ:
            return os.environ[env_key]
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._data)