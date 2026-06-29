import json
from typing import Any, Optional

from backend.app.services.cache.base import BaseCacheAdapter


class RedisCacheAdapter(BaseCacheAdapter):
    def __init__(self, redis_url: str) -> None:
        import redis

        self._client = redis.from_url(redis_url, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        value = self._client.get(key)
        return json.loads(value) if value else None

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        self._client.setex(key, ttl_seconds, json.dumps(value))

    def delete(self, key: str) -> None:
        self._client.delete(key)

    def clear(self) -> None:
        self._client.flushdb()
