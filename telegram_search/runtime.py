"""Runtime validation and dependency bootstrap helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from redis.exceptions import RedisError

from telegram_search.cache.redis_factory import create_redis_client
from telegram_search.config import AppConfig
from telegram_search.indexer.channel_registry import ChannelRegistry
from telegram_search.logging import get_logger, safe_error
from telegram_search.search.meili_client import MeiliClient

logger = get_logger(__name__)


def validate_runtime_config(config: AppConfig, component: str) -> None:
    """Validate required runtime configuration for a component."""
    if component == "bot" and not config.telegram.bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not configured")

    if component == "crawler":
        if not config.telegram.api_id:
            raise ValueError("TELEGRAM_API_ID not configured")
        if not config.telegram.api_hash:
            raise ValueError("TELEGRAM_API_HASH not configured")

    if config.environment.lower() == "production":
        if not config.meilisearch.api_key:
            raise ValueError("MEILI_MASTER_KEY is required in production")
        if not config.redis.password:
            raise ValueError("REDIS_PASSWORD is required in production")

    if component == "crawler":
        session_path = Path(config.telegram.session_path)
        has_session = session_path.exists() or Path(f"{session_path}.session").exists()
        if config.environment.lower() == "production" and not has_session and not sys.stdin.isatty():
            raise ValueError(
                "Telegram session file is missing in non-interactive production startup. "
                "Bootstrap the session once before running the crawler service."
            )


def load_meili_settings(path: str | Path) -> dict[str, Any]:
    """Load Meilisearch settings from JSON file if present."""
    settings_path = Path(path)
    if not str(path):
        return {}
    if not settings_path.exists():
        raise FileNotFoundError(f"Meilisearch settings file not found: {settings_path}")

    with open(settings_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid Meilisearch settings file: {settings_path}")

    return data


def create_search_backend(config: AppConfig) -> MeiliClient:
    """Create the search backend client."""
    return MeiliClient(config.meilisearch)


def bootstrap_search_backend(config: AppConfig) -> MeiliClient:
    """Create and initialize the search backend."""
    client = create_search_backend(config)
    settings = load_meili_settings(config.meilisearch.settings_path)
    client.ensure_index(settings)
    return client


def validate_channels_config(path: str | Path) -> None:
    """Validate that at least one enabled channel is configured."""
    registry = ChannelRegistry(path)
    channels = registry.list_channels()
    if not channels:
        raise ValueError(
            f"No channels configured in {path}. Add at least one channel before starting the crawler."
        )
    if not any(channel.enabled for channel in channels):
        raise ValueError(
            f"No enabled channels configured in {path}. Enable at least one channel before starting the crawler."
        )


def check_writable_path(path: str | Path) -> None:
    """Ensure the parent directory of a path exists and is writable."""
    target = Path(path)
    parent = target.parent if target.parent != Path("") else Path(".")
    parent.mkdir(parents=True, exist_ok=True)
    if not parent.is_dir():
        raise ValueError(f"Path parent is not a directory: {parent}")

    probe = parent / ".write_test"
    try:
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
    finally:
        probe.unlink(missing_ok=True)


def check_optional_redis(config: AppConfig) -> None:
    """Probe Redis and log warnings without failing startup."""
    client = create_redis_client(config.redis)
    try:
        client.ping()
        logger.info("redis_ready")
    except RedisError as e:
        logger.warning("redis_unavailable", **safe_error(e))
    finally:
        try:
            client.close()
        except RedisError as e:
            logger.warning("redis_close_failed", **safe_error(e))
