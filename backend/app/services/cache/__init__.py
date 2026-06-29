from backend.app.core.config import settings
from backend.app.services.cache.base import BaseCache
from backend.app.services.cache.adapters import MemoryCache, SQLiteCache, RedisCache

_cache_instance = None

def get_cache() -> BaseCache:
    """
    Unified cache accessor initializing the correct provider based on configuration.
    """
    global _cache_instance
    if _cache_instance is not None:
        return _cache_instance

    provider = settings.CACHE_PROVIDER.lower().strip()
    print(f"Initializing CacheService with provider: {provider}")
    
    if provider == "redis":
        _cache_instance = RedisCache(settings.REDIS_URL)
    elif provider == "sqlite":
        _cache_instance = SQLiteCache()
    else:
        _cache_instance = MemoryCache()
        
    return _cache_instance
