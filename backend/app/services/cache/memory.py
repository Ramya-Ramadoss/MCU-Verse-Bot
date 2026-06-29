import time
from typing import Any, Dict, Optional, Tuple

from backend.app.services.cache.base import BaseCacheAdapter


class MemoryCacheAdapter(BaseCacheAdapter):
    def __init__(self) -> None:
        self._store: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at and time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds > 0 else 0
        self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
