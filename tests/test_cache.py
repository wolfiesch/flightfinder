"""Tests for FlightFinder caching."""

import time

from flightfinder.cache import CacheEntry, ResponseCache


class TestCacheEntry:
    """Tests for CacheEntry."""

    def test_entry_not_expired(self):
        """Test entry is not expired within TTL."""
        entry = CacheEntry(data={"test": "data"}, created_at=time.time(), ttl_seconds=60)
        assert entry.is_expired is False

    def test_entry_expired(self):
        """Test entry is expired after TTL."""
        entry = CacheEntry(data={"test": "data"}, created_at=time.time() - 120, ttl_seconds=60)
        assert entry.is_expired is True


class TestResponseCache:
    """Tests for ResponseCache."""

    def test_cache_set_get(self):
        """Test basic set and get operations."""
        cache = ResponseCache(max_size=10, default_ttl=60)
        query = "query { test }"
        variables = {"id": 1}
        data = {"result": "test"}

        cache.set(query, variables, data)
        result = cache.get(query, variables)

        assert result == data

    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = ResponseCache(max_size=10, default_ttl=60)
        result = cache.get("nonexistent", {})
        assert result is None

    def test_cache_expiration(self):
        """Test cache entries expire."""
        cache = ResponseCache(max_size=10, default_ttl=1)
        cache.set("query", {}, {"data": "test"})

        # Should hit initially
        assert cache.get("query", {}) is not None

        # Wait for expiration
        time.sleep(1.5)

        # Should miss after expiration
        assert cache.get("query", {}) is None

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = ResponseCache(max_size=3, default_ttl=60)

        # Fill cache
        cache.set("q1", {}, {"data": 1})
        cache.set("q2", {}, {"data": 2})
        cache.set("q3", {}, {"data": 3})

        # Access q1 to make it most recently used
        cache.get("q1", {})

        # Add new entry, should evict q2 (oldest)
        cache.set("q4", {}, {"data": 4})

        # q2 should be evicted
        assert cache.get("q2", {}) is None
        # q1, q3, q4 should still exist
        assert cache.get("q1", {}) is not None
        assert cache.get("q3", {}) is not None
        assert cache.get("q4", {}) is not None

    def test_cache_invalidate(self):
        """Test manual cache invalidation."""
        cache = ResponseCache(max_size=10, default_ttl=60)
        cache.set("query", {"id": 1}, {"data": "test"})

        # Should exist
        assert cache.get("query", {"id": 1}) is not None

        # Invalidate
        result = cache.invalidate("query", {"id": 1})
        assert result is True

        # Should be gone
        assert cache.get("query", {"id": 1}) is None

    def test_cache_clear(self):
        """Test clearing all cache entries."""
        cache = ResponseCache(max_size=10, default_ttl=60)
        cache.set("q1", {}, {"data": 1})
        cache.set("q2", {}, {"data": 2})

        count = cache.clear()
        assert count == 2
        assert cache.size == 0

    def test_cache_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = ResponseCache(max_size=10, default_ttl=1)
        cache.set("q1", {}, {"data": 1})
        cache.set("q2", {}, {"data": 2}, ttl=60)  # Long TTL

        time.sleep(1.5)

        removed = cache.cleanup_expired()
        assert removed == 1  # Only q1 should be removed
        assert cache.get("q2", {}) is not None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = ResponseCache(max_size=10, default_ttl=60)
        cache.set("q1", {}, {"data": 1})

        # Miss
        cache.get("nonexistent", {})
        # Hit
        cache.get("q1", {})
        cache.get("q1", {})

        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert "66.7%" in stats["hit_rate"]  # 2/3 = 66.7%

    def test_cache_hit_rate_zero(self):
        """Test hit rate with no operations."""
        cache = ResponseCache(max_size=10, default_ttl=60)
        assert cache.hit_rate == 0.0

    def test_cache_key_consistency(self):
        """Test that same query/variables produce same key."""
        cache = ResponseCache(max_size=10, default_ttl=60)

        query = "query { test }"
        variables = {"a": 1, "b": 2}

        cache.set(query, variables, {"result": "test"})

        # Same variables, different order
        variables_reordered = {"b": 2, "a": 1}
        result = cache.get(query, variables_reordered)

        assert result is not None
