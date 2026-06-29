import hashlib
import json
from typing import Any, Optional

from backend.app.core.config import settings
from backend.app.services.cache.base import BaseCacheAdapter
from backend.app.services.cache.memory import MemoryCacheAdapter


class CacheService:
    def __init__(self, adapter: Optional[BaseCacheAdapter] = None) -> None:
        self._adapter = adapter or self._create_adapter()

    def _create_adapter(self) -> BaseCacheAdapter:
        provider = settings.CACHE_PROVIDER.lower()
        if provider == "redis":
            try:
                from backend.app.services.cache.redis_adapter import RedisCacheAdapter

                return RedisCacheAdapter(settings.REDIS_URL)
            except Exception:
                return MemoryCacheAdapter()
        if provider == "sqlite":
            from backend.app.services.cache.sqlite_adapter import SQLiteCacheAdapter

            return SQLiteCacheAdapter(settings.DATABASE_URL)
        return MemoryCacheAdapter()

    @staticmethod
    def make_key(prefix: str, payload: dict) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str)
        digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"{prefix}:{digest}"

    def get(self, key: str) -> Optional[Any]:
        return self._adapter.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        self._adapter.set(key, value, ttl_seconds)

    def delete(self, key: str) -> None:
        self._adapter.delete(key)

    def clear(self) -> None:
        self._adapter.clear()
