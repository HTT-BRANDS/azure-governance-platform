"""Rate limiting module for API security.

Provides Redis-based rate limiting with per-endpoint and per-user limits.
Includes automatic cleanup, configurable windows, and graceful fallback.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies."""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests: int = 100
    window_seconds: int = 60
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW
    key_prefix: str = "rl"


# Default rate limits per endpoint type
DEFAULT_LIMITS = {
    "default": RateLimitConfig(requests=100, window_seconds=60),
    "auth": RateLimitConfig(requests=10, window_seconds=60),  # Stricter for auth
    "login": RateLimitConfig(requests=5, window_seconds=300),  # Very strict for login
    "sync": RateLimitConfig(requests=5, window_seconds=60),  # Expensive operations
    "bulk": RateLimitConfig(requests=3, window_seconds=60),
    "exports": RateLimitConfig(requests=10, window_seconds=60),
    "health": RateLimitConfig(requests=30, window_seconds=60),
}


class RateLimiter:
    """Redis-based rate limiter with fallback to in-memory.

    Features:
    - Per-user and per-endpoint rate limiting
    - Configurable time windows and request counts
    - Automatic key expiration
    - Graceful degradation without Redis
    """

    def __init__(self) -> None:
        self._redis = None
        self._memory_cache: dict[str, tuple[int, float]] = {}  # (count, reset_time)
        self._settings = get_settings()
        self._enabled = True
        self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis connection if available."""
        if not self._settings.redis_url:
            logger.info("Redis URL not configured, using in-memory rate limiting")
            return

        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(
                self._settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("Redis rate limiter initialized")
        except ImportError:
            logger.warning("redis package not installed, using in-memory rate limiting")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}, using in-memory")

    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate rate limit key."""
        return f"rate_limit:{endpoint}:{identifier}"

    def _get_client_identifier(self, request: Request) -> str:
        """Extract client identifier from request.

        Uses X-Forwarded-For header if present, falls back to client host.
        Also includes user ID if authenticated.
        """
        # Get IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        # Add user ID if authenticated
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"{ip}:{user_id}"

        return ip

    async def _check_redis_limit(
        self, key: str, config: RateLimitConfig
    ) -> tuple[bool, dict]:
        """Check rate limit using Redis.

        Returns:
            Tuple of (allowed, headers_dict)
        """
        if not self._redis:
            raise RuntimeError("Redis not available")

        import time

        now = time.time()
        window_start = int(now // config.window_seconds) * config.window_seconds
        window_key = f"{key}:{window_start}"

        pipe = self._redis.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, config.window_seconds)
        results = await pipe.execute()

        current_count = results[0]
        remaining = max(0, config.requests - current_count)
        reset_time = window_start + config.window_seconds

        headers = {
            "X-RateLimit-Limit": str(config.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(reset_time)),
            "X-RateLimit-Window": str(config.window_seconds),
        }

        if current_count > config.requests:
            return False, headers

        return True, headers

    def _check_memory_limit(
        self, key: str, config: RateLimitConfig
    ) -> tuple[bool, dict]:
        """Check rate limit using in-memory cache.

        Returns:
            Tuple of (allowed, headers_dict)
        """
        import time

        now = time.time()
        window_start = int(now // config.window_seconds) * config.window_seconds
        window_key = f"{key}:{window_start}"

        # Clean old entries periodically
        if len(self._memory_cache) > 10000:
            self._memory_cache = {
                k: v for k, v in self._memory_cache.items() if v[1] > now
            }

        # Get or create entry
        if window_key not in self._memory_cache:
            self._memory_cache[window_key] = (0, window_start + config.window_seconds)

        count, reset_time = self._memory_cache[window_key]
        count += 1
        self._memory_cache[window_key] = (count, reset_time)

        remaining = max(0, config.requests - count)

        headers = {
            "X-RateLimit-Limit": str(config.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(reset_time)),
            "X-RateLimit-Window": str(config.window_seconds),
        }

        if count > config.requests:
            return False, headers

        return True, headers

    async def is_allowed(
        self, request: Request, config: RateLimitConfig | None = None
    ) -> tuple[bool, dict]:
        """Check if request is within rate limit.

        Args:
            request: FastAPI request object
            config: Rate limit config, uses default if not provided

        Returns:
            Tuple of (allowed, rate_limit_headers)
        """
        if not self._enabled:
            return True, {}

        config = config or DEFAULT_LIMITS["default"]
        identifier = self._get_client_identifier(request)
        endpoint = request.url.path
        key = self._get_key(identifier, endpoint)

        try:
            if self._redis:
                return await self._check_redis_limit(key, config)
            else:
                return self._check_memory_limit(key, config)
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if rate limiting fails
            return True, {}

    async def check_rate_limit(
        self,
        request: Request,
        limit_type: str = "default",
        custom_config: RateLimitConfig | None = None,
    ) -> None:
        """Check rate limit and raise HTTPException if exceeded.

        Args:
            request: FastAPI request object
            limit_type: Type of limit to apply (key in DEFAULT_LIMITS)
            custom_config: Optional custom config override

        Raises:
            HTTPException: 429 Too Many Requests if limit exceeded
        """
        config = custom_config or DEFAULT_LIMITS.get(limit_type, DEFAULT_LIMITS["default"])
        allowed, headers = await self.is_allowed(request, config)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    **headers,
                    "Retry-After": str(config.window_seconds),
                },
            )

        # Store headers for response
        request.state.rate_limit_headers = headers

    def get_limit_config(self, endpoint_path: str) -> RateLimitConfig:
        """Get appropriate rate limit config for an endpoint.

        Args:
            endpoint_path: The API endpoint path

        Returns:
            RateLimitConfig for the endpoint
        """
        path_lower = endpoint_path.lower()

        # Check for specific endpoint types
        if any(p in path_lower for p in ["/auth/login", "/token"]):
            return DEFAULT_LIMITS["login"]
        elif "/auth/" in path_lower:
            return DEFAULT_LIMITS["auth"]
        elif "/sync" in path_lower:
            return DEFAULT_LIMITS["sync"]
        elif "/bulk" in path_lower:
            return DEFAULT_LIMITS["bulk"]
        elif "/exports" in path_lower:
            return DEFAULT_LIMITS["exports"]
        elif "/health" in path_lower:
            return DEFAULT_LIMITS["health"]

        return DEFAULT_LIMITS["default"]


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(
    limit_type: str = "default",
    custom_config: RateLimitConfig | None = None,
) -> Callable:
    """Decorator/FastAPI dependency for rate limiting.

    Usage:
        @router.get("/endpoint")
        async def endpoint(request: Request, _=Depends(rate_limit("default"))):
            pass

    Args:
        limit_type: Type of limit to apply
        custom_config: Optional custom rate limit config

    Returns:
        Dependency callable
    """

    async def check_limit(request: Request) -> None:
        await rate_limiter.check_rate_limit(request, limit_type, custom_config)

    return check_limit


async def apply_rate_limit_headers(request: Request, response: JSONResponse) -> None:
    """Apply rate limit headers to response.

    Call this in a response middleware to add rate limit headers.

    Args:
        request: FastAPI request object
        response: FastAPI response object
    """
    headers = getattr(request.state, "rate_limit_headers", {})
    for key, value in headers.items():
        response.headers[key] = str(value)
