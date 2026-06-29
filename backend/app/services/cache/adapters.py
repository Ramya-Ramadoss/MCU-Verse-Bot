import datetime
from typing import Optional
from backend.app.services.cache.base import BaseCache
from backend.app.db.database import SessionLocal
from backend.app.db.models.cache import CacheEntry

class MemoryCache(BaseCache):
    def __init__(self):
        self._store = {}

    def get(self, key: str) -> Optional[str]:
        item = self._store.get(key)
        if not item:
            return None
        # Check expiry
        val, expiry = item
        if datetime.datetime.utcnow() > expiry:
            self.delete(key)
            return None
        return val

    def set(self, key: str, value: str, expire_seconds: int = 3600) -> None:
        expiry = datetime.datetime.utcnow() + datetime.timedelta(seconds=expire_seconds)
        self._store[key] = (value, expiry)

    def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]

    def clear(self) -> None:
        self._store.clear()


class SQLiteCache(BaseCache):
    def get(self, key: str) -> Optional[str]:
        db = SessionLocal()
        try:
            now = datetime.datetime.utcnow()
            # Clean expired keys on read to prevent DB growth
            db.query(CacheEntry).filter(CacheEntry.expires_at < now).delete()
            db.commit()
            
            entry = db.query(CacheEntry).filter(CacheEntry.key == key).first()
            if not entry:
                return None
            if entry.expires_at < now:
                db.delete(entry)
                db.commit()
                return None
            return entry.value
        except Exception as e:
            print(f"SQLite Cache GET error: {e}")
            return None
        finally:
            db.close()

    def set(self, key: str, value: str, expire_seconds: int = 3600) -> None:
        db = SessionLocal()
        try:
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=expire_seconds)
            
            # Upsert
            entry = db.query(CacheEntry).filter(CacheEntry.key == key).first()
            if not entry:
                entry = CacheEntry(key=key)
                db.add(entry)
                
            entry.value = value
            entry.expires_at = expires_at
            db.commit()
        except Exception as e:
            print(f"SQLite Cache SET error: {e}")
        finally:
            db.close()

    def delete(self, key: str) -> None:
        db = SessionLocal()
        try:
            db.query(CacheEntry).filter(CacheEntry.key == key).delete()
            db.commit()
        except Exception as e:
            print(f"SQLite Cache DELETE error: {e}")
        finally:
            db.close()

    def clear(self) -> None:
        db = SessionLocal()
        try:
            db.query(CacheEntry).delete()
            db.commit()
        except Exception as e:
            print(f"SQLite Cache CLEAR error: {e}")
        finally:
            db.close()


class RedisCache(BaseCache):
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = None
        
        # Lazy import of redis library
        try:
            import redis
            self.client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.client.ping()
            print("Successfully connected to Redis cache backend.")
        except Exception as e:
            print(f"Redis Cache connection failed: {e}. Falling back to MemoryCache.")
            self.fallback = MemoryCache()

    def get(self, key: str) -> Optional[str]:
        if not self.client:
            return self.fallback.get(key)
        try:
            return self.client.get(key)
        except Exception as e:
            print(f"Redis Cache GET error: {e}")
            return None

    def set(self, key: str, value: str, expire_seconds: int = 3600) -> None:
        if not self.client:
            self.fallback.set(key, value, expire_seconds)
            return
        try:
            self.client.setex(key, expire_seconds, value)
        except Exception as e:
            print(f"Redis Cache SET error: {e}")

    def delete(self, key: str) -> None:
        if not self.client:
            self.fallback.delete(key)
            return
        try:
            self.client.delete(key)
        except Exception as e:
            print(f"Redis Cache DELETE error: {e}")

    def clear(self) -> None:
        if not self.client:
            self.fallback.clear()
            return
        try:
            self.client.flushdb()
        except Exception as e:
            print(f"Redis Cache CLEAR error: {e}")
