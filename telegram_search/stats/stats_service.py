"""Statistics service using Redis."""

from __future__ import annotations

import redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import RedisError, ConnectionError, TimeoutError
from redis.retry import Retry

from telegram_search.config import RedisConfig
from telegram_search.logging import get_logger, safe_error

logger = get_logger(__name__)


class StatsService:
    """Service to track search statistics."""

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
        self._key_prefix = "stats"

    def record_search(self, query: str) -> None:
        """Record a search query."""
        if not query or not query.strip():
            return

        try:
            # Increment total searches
            self._client.incr(f"{self._key_prefix}:total_searches")

            # Increment keyword frequency
            # Use lower case for normalization
            normalized_query = query.strip().lower()
            if normalized_query:
                self._client.zincrby(
                    f"{self._key_prefix}:keywords",
                    1.0,
                    normalized_query,
                )
        except RedisError as e:
            logger.warning("stats_record_failed", **safe_error(e))

    def get_stats(self, top_k: int = 10) -> dict:
        """Get current statistics.
        
        Returns:
            dict: {
                "total_searches": int,
                "top_keywords": list[tuple[str, float]]
            }
        """
        try:
            total = self._client.get(f"{self._key_prefix}:total_searches")
            keywords = self._client.zrevrange(
                f"{self._key_prefix}:keywords",
                0,
                top_k - 1,
                withscores=True,
            )

            return {
                "total_searches": int(total) if total else 0,
                "top_keywords": keywords,
            }
        except RedisError as e:
            logger.warning("stats_fetch_failed", **safe_error(e))
            return {"total_searches": 0, "top_keywords": []}

    def close(self) -> None:
        """Close Redis connection."""
        try:
            self._client.close()
        except RedisError as e:
            logger.warning("stats_close_failed", **safe_error(e))
