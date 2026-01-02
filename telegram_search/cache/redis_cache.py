"""Redis cache for search results."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

import redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, RedisError, TimeoutError
from redis.retry import Retry

from telegram_search.config import RedisConfig
from telegram_search.logging import get_logger, safe_error

logger = get_logger(__name__)


class RedisCache:
    """Cache layer using Redis."""

    def __init__(self, config: RedisConfig) -> None:
        """Initialize Redis connection."""
        retry_strategy = Retry(
            ExponentialBackoff(),
            config.max_retries,
        )
        self._client = redis.Redis(
            host=config.host,
            port=config.port,
            db=config.db,
            decode_responses=True,
            socket_timeout=config.socket_timeout,
            socket_connect_timeout=config.socket_connect_timeout,
            retry=retry_strategy,
            retry_on_error=[ConnectionError, TimeoutError],
        )
        self._ttl = config.cache_ttl

    @staticmethod
    def _make_key(query: str, **kwargs: Any) -> str:
        """Generate cache key from query."""
        # Create a stable key by sorting kwargs
        items = sorted((k, str(v)) for k, v in kwargs.items() if v is not None)
        key_data = f"{query}:{items}"
        return f"search:{hashlib.md5(key_data.encode()).hexdigest()}"

    def get(self, query: str, **kwargs: Any) -> dict | None:
        """Get cached result."""
        try:
            key = self._make_key(query, **kwargs)
            data = self._client.get(key)
            if data:
                return json.loads(data)
        except RedisError as e:
            logger.warning("redis_get_failed", **safe_error(e))
        except Exception as e:
            logger.error("redis_get_unexpected_error", **safe_error(e))
        return None

    def set(
        self,
        query: str,
        result: dict,
        **kwargs: Any,
    ) -> None:
        """Cache search result."""
        try:
            key = self._make_key(query, **kwargs)
            self._client.setex(key, self._ttl, json.dumps(result))
        except RedisError as e:
            logger.warning("redis_set_failed", **safe_error(e))
        except Exception as e:
            logger.error("redis_set_unexpected_error", **safe_error(e))

    def get_or_compute(
        self,
        query: str,
        compute_func: Callable[[], dict],
        **kwargs: Any,
    ) -> dict:
        """Get from cache or compute and cache."""
        cached = self.get(query, **kwargs)
        if cached is not None:  # Explicit None check to handle empty dict {} as valid cache hit
            return cached

        try:
            result = compute_func()
            self.set(query, result, **kwargs)
            return result
        except Exception as e:
            # If compute fails, we propagate the error
            # If set fails, it's caught inside set()
            raise e

    def close(self) -> None:
        """Close Redis connection."""
        try:
            self._client.close()
        except Exception as e:
            logger.warning("redis_close_failed", **safe_error(e))
