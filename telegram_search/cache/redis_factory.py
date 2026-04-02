"""Redis connection factory."""

from __future__ import annotations

import redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError
from redis.retry import Retry

from telegram_search.config import RedisConfig


def create_redis_client(config: RedisConfig) -> redis.Redis:
    """Create a Redis client with retry strategy.

    Args:
        config: Redis configuration.

    Returns:
        Configured Redis client instance.
    """
    retry_strategy = Retry(
        ExponentialBackoff(),
        config.max_retries,
    )
    return redis.Redis(
        host=config.host,
        port=config.port,
        db=config.db,
        password=config.password or None,
        decode_responses=True,
        socket_timeout=config.socket_timeout,
        socket_connect_timeout=config.socket_connect_timeout,
        socket_keepalive=True,
        retry=retry_strategy,
        retry_on_error=[ConnectionError, TimeoutError],
    )
