import time
from typing import Any
from app.domain.interfaces import ICacheProvider

class InMemoryCacheProvider(ICacheProvider):
    """Local dictionary-based cache. 
    In Phase 3/4 this will be swapped for Redis if running distributed."""
    
    def __init__(self):
        self._cache: dict[str, dict[str, Any]] = {}

    async def get(self, key: str) -> Any | None:
        entry = self._cache.get(key)
        if not entry:
            return None
        if entry["expires_at"] and time.time() > entry["expires_at"]:
            del self._cache[key]
            return None
        return entry["value"]

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at
        }

    async def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    async def invalidate_tag(self, tag: str) -> None:
        # A simple implementation to delete any keys that start with the tag
        # e.g., "entity:123" -> delete all "entity:123:*"
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(tag)]
        for k in keys_to_delete:
            del self._cache[k]
