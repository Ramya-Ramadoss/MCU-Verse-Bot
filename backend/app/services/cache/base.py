from abc import ABC, abstractmethod
from typing import Optional, Any

class BaseCache(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """
        Retrieves a value from the cache. Returns None if key doesn't exist or is expired.
        """
        pass

    @abstractmethod
    def set(self, key: str, value: str, expire_seconds: int = 3600) -> None:
        """
        Sets a key-value pair in the cache with an expiration in seconds.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        Deletes a key from the cache.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clears all cached items.
        """
        pass
