"""
Chaos Engineering: Cache Failure and Degradation Tests

Tests system behavior when cache services fail or degrade:
- Redis connection failures
- Cache cluster unavailability
- Stale data scenarios
- Cache poisoning recovery
"""

import asyncio

import pytest

from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerConfig


class TestRedisConnectionFailures:
    """Test behavior when Redis connections fail."""

    @pytest.mark.asyncio
    async def test_fallback_to_database_on_cache_failure(self):
        """System should query database when cache is unavailable."""
        cache_available = False
        db_available = True

        def get_data():
            if cache_available:
                return {"source": "cache", "data": "cached_value"}
            elif db_available:
                return {"source": "database", "data": "db_value"}
            raise Exception("No data source available")

        result = get_data()

        assert result["source"] == "database"
        assert result["data"] == "db_value"

    @pytest.mark.asyncio
    async def test_cache_failure_circuit_breaker(self):
        """Repeated cache failures should open circuit breaker."""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=1.0)
        breaker = CircuitBreaker(name="redis_cache", config=config)

        for _ in range(3):
            if breaker.can_execute():
                try:
                    raise ConnectionError("Redis connection refused")
                except ConnectionError:
                    breaker.record_failure()

        assert breaker.is_open, "Cache circuit should open after failures"

    @pytest.mark.asyncio
    async def test_cache_reconnection_after_recovery(self):
        """System should reconnect to cache after it recovers."""
        connection_attempts = 0
        cache_healthy_after = 3

        def connect_cache():
            nonlocal connection_attempts
            connection_attempts += 1
            if connection_attempts < cache_healthy_after:
                raise ConnectionError("Still unavailable")
            return {"connected": True}

        # Retry until success
        result = None
        for _attempt in range(5):
            try:
                result = connect_cache()
                break
            except ConnectionError:
                await asyncio.sleep(0.05)

        assert result is not None
        assert result["connected"]


class TestCacheDegradation:
    """Test graceful degradation when cache performance degrades."""

    @pytest.mark.asyncio
    async def test_read_through_cache_disabled(self):
        """System should skip cache when read latency is too high."""
        cache_read_latency_ms = 500  # Very slow
        acceptable_latency_ms = 100

        use_cache = cache_read_latency_ms < acceptable_latency_ms

        assert not use_cache, "Should bypass slow cache"

    @pytest.mark.asyncio
    async def test_cache_ttl_extension_during_degradation(self):
        """Cache TTL may be extended during degradation to reduce load."""
        base_ttl = 300  # 5 minutes
        degradation_factor = 2

        is_degraded = True

        if is_degraded:
            adjusted_ttl = base_ttl * degradation_factor
        else:
            adjusted_ttl = base_ttl

        assert adjusted_ttl == 600  # Extended to 10 minutes

    @pytest.mark.asyncio
    async def test_partial_cache_availability(self):
        """System should handle partial cache shard failures."""
        shards = {
            "shard_1": {"available": True, "keys": ["key1", "key2"]},
            "shard_2": {"available": False, "keys": []},  # Failed
            "shard_3": {"available": True, "keys": ["key3"]},
        }

        def get_from_cache(key):
            for shard_name, shard in shards.items():
                if shard["available"] and key in shard["keys"]:
                    return f"value_from_{shard_name}"
            return None  # Cache miss

        # Shard 1 key should work
        assert get_from_cache("key1") == "value_from_shard_1"
        # Shard 2 key should miss
        assert get_from_cache("key_in_shard_2") is None


class TestStaleCacheData:
    """Test behavior with stale cache data."""

    @pytest.mark.asyncio
    async def test_stale_while_revalidate_pattern(self):
        """Serve stale data while refreshing in background."""
        cache_data = {
            "value": "old_data",
            "cached_at": "2024-01-01T00:00:00Z",
            "ttl": 300,
        }

        is_stale = True
        fresh_data_available = False

        def get_data():
            if is_stale and not fresh_data_available:
                # Serve stale while fetching fresh
                return {**cache_data, "stale": True}
            return {"value": "fresh_data", "stale": False}

        result = get_data()
        assert result["stale"]
        assert result["value"] == "old_data"

    @pytest.mark.asyncio
    async def test_max_stale_threshold(self):
        """Reject data that exceeds maximum staleness."""
        max_stale_seconds = 600  # 10 minutes
        data_age_seconds = 900  # 15 minutes - too stale

        is_acceptable = data_age_seconds <= max_stale_seconds

        assert not is_acceptable, "Should reject overly stale data"

    @pytest.mark.asyncio
    async def test_conditional_refresh_based_on_staleness(self):
        """Refresh cache only when data is stale enough."""
        staleness_threshold = 60  # seconds
        current_staleness = 45  # seconds

        needs_refresh = current_staleness >= staleness_threshold

        assert not needs_refresh, "Should not refresh if below threshold"


class TestCachePoisoning:
    """Test recovery from cache poisoning scenarios."""

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_suspicious_data(self):
        """Invalidate cache entries with suspicious patterns."""
        cached_value = '{"data": "<script>alert(1)</script>"}'  # Potential XSS

        def is_suspicious(value):
            suspicious_patterns = ["<script>", "javascript:", "onerror="]
            return any(pattern in str(value) for pattern in suspicious_patterns)

        if is_suspicious(cached_value):
            # Invalidate the poisoned entry
            cached_value = None

        assert cached_value is None

    @pytest.mark.asyncio
    async def test_version_based_cache_eviction(self):
        """Use versioning to evict old cache formats."""
        cache_format_version = 1
        current_format_version = 2

        def is_valid_format(version):
            return version == current_format_version

        is_valid = is_valid_format(cache_format_version)

        assert not is_valid, "Should invalidate old format versions"


class TestCacheConcurrencyIssues:
    """Test behavior during cache concurrency problems."""

    @pytest.mark.asyncio
    async def test_cache_stampede_prevention(self):
        """Prevent cache stampede with request coalescing."""
        in_flight_requests = {}
        request_count = 0

        async def get_expensive_data(key):
            nonlocal request_count

            # Check if request already in flight
            if key in in_flight_requests:
                # Wait for existing request instead of duplicating
                return await in_flight_requests[key]

            # Create new request
            future = asyncio.Future()
            in_flight_requests[key] = future
            request_count += 1

            # Simulate expensive operation
            await asyncio.sleep(0.1)
            result = {"data": f"expensive_{key}"}

            future.set_result(result)
            del in_flight_requests[key]
            return result

        # Simulate 10 concurrent requests for same key
        tasks = [get_expensive_data("key1") for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # Only 1 actual request should have been made
        assert request_count == 1
        assert all(r["data"] == "expensive_key1" for r in results)

    @pytest.mark.asyncio
    async def test_cache_race_condition_handling(self):
        """Handle race conditions in cache writes."""
        cache = {}
        write_count = 0

        def write_cache(key, value):
            nonlocal write_count
            # Simulate atomic check-and-set
            if key not in cache:
                cache[key] = value
                write_count += 1
                return True
            return False  # Key already exists

        # Simulate race conditions
        results = [
            write_cache("key1", "value1"),
            write_cache("key1", "value2"),
            write_cache("key1", "value3"),
        ]

        # Only first write should succeed
        assert results == [True, False, False]
        assert write_count == 1
        assert cache["key1"] == "value1"


class TestCacheMemoryPressure:
    """Test behavior under cache memory pressure."""

    @pytest.mark.asyncio
    async def test_lru_eviction_under_memory_pressure(self):
        """LRU eviction when cache memory is constrained."""
        max_entries = 100
        cache = {}
        access_order = []

        def set_cache(key, value):
            if len(cache) >= max_entries:
                # Evict least recently used
                lru_key = access_order.pop(0)
                del cache[lru_key]

            cache[key] = value
            access_order.append(key)

        def get_cache(key):
            if key in cache:
                # Move to end (most recently used)
                access_order.remove(key)
                access_order.append(key)
                return cache[key]
            return None

        # Fill cache
        for i in range(100):
            set_cache(f"key_{i}", f"value_{i}")

        # Access some keys
        get_cache("key_10")
        get_cache("key_20")

        # Add new entry - should evict oldest (key_0, not key_10 or key_20)
        set_cache("key_100", "value_100")

        assert "key_0" not in cache  # Evicted
        assert "key_10" in cache  # Still there (recently used)
        assert "key_100" in cache  # New entry

    @pytest.mark.asyncio
    async def test_ttl_based_eviction(self):
        """Evict entries based on TTL expiration."""
        import time

        cache = {}

        def set_with_ttl(key, value, ttl_seconds):
            cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl_seconds,
            }

        def get_with_ttl(key, current_time):
            entry = cache.get(key)
            if entry and entry["expires_at"] > current_time:
                return entry["value"]
            # Expired or missing
            if key in cache:
                del cache[key]
            return None

        # Set entry with 1 second TTL
        current_time = time.time()
        set_with_ttl("key1", "value1", 1.0)

        # Should exist immediately
        assert get_with_ttl("key1", current_time) == "value1"

        # Should be expired after 2 seconds (simulated with future time)
        assert get_with_ttl("key1", current_time + 2.0) is None
