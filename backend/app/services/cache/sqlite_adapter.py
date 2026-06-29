import json
import sqlite3
import time
from typing import Any, Optional

from backend.app.services.cache.base import BaseCacheAdapter


class SQLiteCacheAdapter(BaseCacheAdapter):
    def __init__(self, database_url: str) -> None:
        path = database_url.replace("sqlite:///", "")
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at REAL
            )
            """
        )
        self._conn.commit()

    def get(self, key: str) -> Optional[Any]:
        row = self._conn.execute(
            "SELECT value, expires_at FROM cache_entries WHERE key = ?", (key,)
        ).fetchone()
        if not row:
            return None
        value, expires_at = row
        if expires_at and time.time() > expires_at:
            self.delete(key)
            return None
        return json.loads(value)

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds > 0 else None
        self._conn.execute(
            """
            INSERT INTO cache_entries (key, value, expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, expires_at = excluded.expires_at
            """,
            (key, json.dumps(value), expires_at),
        )
        self._conn.commit()

    def delete(self, key: str) -> None:
        self._conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
        self._conn.commit()

    def clear(self) -> None:
        self._conn.execute("DELETE FROM cache_entries")
        self._conn.commit()
