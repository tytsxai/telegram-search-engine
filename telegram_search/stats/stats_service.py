"""Statistics service using Redis."""

from __future__ import annotations

from typing import Any, cast

from redis.exceptions import RedisError

from telegram_search.cache.redis_factory import create_redis_client
from telegram_search.config import RedisConfig
from telegram_search.logging import get_logger, safe_error

logger = get_logger(__name__)


class StatsService:
    """Service to track search statistics."""

    def __init__(self, config: RedisConfig) -> None:
        """Initialize Redis connection."""
        self._client: Any = create_redis_client(config)
        self._key_prefix = "stats"

    def record_search(self, query: str) -> None:
        """Record a search query."""
        if not query or not query.strip():
            return

        try:
            self._client.incr(f"{self._key_prefix}:total_searches")
            normalized_query = query.strip().lower()
            if normalized_query:
                self._client.zincrby(
                    f"{self._key_prefix}:keywords",
                    1.0,
                    normalized_query,
                )
        except RedisError as e:
            logger.warning("stats_record_failed", **safe_error(e))

    def get_stats(self, top_k: int = 10) -> dict[str, Any]:
        """Get current statistics."""
        try:
            total = cast(str | None, self._client.get(f"{self._key_prefix}:total_searches"))
            keywords = cast(
                list[tuple[str, float]],
                self._client.zrevrange(
                f"{self._key_prefix}:keywords",
                0,
                top_k - 1,
                withscores=True,
                ),
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
