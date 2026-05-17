"""Response caching for FlightFinder."""

import hashlib
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached response with metadata."""

    data: Any
    created_at: float
    ttl_seconds: int

    @property
    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds


class ResponseCache:
    """
    Simple in-memory LRU cache for API responses.

    Features:
    - TTL-based expiration
    - LRU eviction when max size reached
    - Thread-safe for basic operations
    """

    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of entries to cache
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _make_key(self, query: str, variables: dict) -> str:
        """Generate a cache key from query and variables."""
        # Normalize the data for consistent hashing
        key_data = json.dumps(
            {"query": query, "variables": variables},
            sort_keys=True,
            default=str,
        )
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, query: str, variables: dict) -> Any | None:
        """
        Retrieve a cached response.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Cached data if found and not expired, None otherwise
        """
        key = self._make_key(query, variables)

        if key not in self._cache:
            self._misses += 1
            logger.debug(f"Cache miss for key: {key[:8]}...")
            return None

        entry = self._cache[key]

        if entry.is_expired:
            # Remove expired entry
            del self._cache[key]
            self._misses += 1
            logger.debug(f"Cache expired for key: {key[:8]}...")
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1
        logger.debug(f"Cache hit for key: {key[:8]}...")
        return entry.data

    def set(self, query: str, variables: dict, data: Any, ttl: int | None = None) -> None:
        """
        Store a response in the cache.

        Args:
            query: GraphQL query string
            variables: Query variables
            data: Response data to cache
            ttl: Optional custom TTL in seconds
        """
        key = self._make_key(query, variables)

        # Evict oldest entries if at capacity
        while len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.debug(f"Evicted cache entry: {oldest_key[:8]}...")

        self._cache[key] = CacheEntry(
            data=data,
            created_at=time.time(),
            ttl_seconds=ttl or self.default_ttl,
        )
        logger.debug(f"Cached response for key: {key[:8]}...")

    def invalidate(self, query: str, variables: dict) -> bool:
        """
        Remove a specific entry from the cache.

        Returns:
            True if entry was found and removed, False otherwise
        """
        key = self._make_key(query, variables)
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> int:
        """
        Clear all cached entries.

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cache entries")
        return count

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
        return len(expired_keys)

    @property
    def size(self) -> int:
        """Current number of cached entries."""
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        """Cache hit rate as a percentage."""
        total = self._hits + self._misses
        if total == 0:
            return 0.0
        return (self._hits / total) * 100

    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{self.hit_rate:.1f}%",
        }


# Global cache instance
_cache: ResponseCache | None = None


def get_cache(max_size: int = 100, default_ttl: int = 300) -> ResponseCache:
    """Get or create the global cache instance."""
    global _cache
    if _cache is None:
        _cache = ResponseCache(max_size=max_size, default_ttl=default_ttl)
    return _cache


def clear_cache() -> int:
    """Clear the global cache."""
    global _cache
    if _cache is not None:
        return _cache.clear()
    return 0
