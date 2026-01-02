"""Configuration management with environment variable override support."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import tomli
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramConfig(BaseSettings):
    """Telegram API configuration."""

    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    api_id: int = Field(default=0, alias="TELEGRAM_API_ID")
    api_hash: str = Field(default="", alias="TELEGRAM_API_HASH")


class MeilisearchConfig(BaseSettings):
    """Meilisearch configuration."""

    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    host: str = Field(default="http://localhost:7700", alias="MEILI_HOST")
    api_key: str = Field(default="", alias="MEILI_MASTER_KEY")
    index_name: str = Field(default="telegram_messages", alias="MEILI_INDEX")
    timeout: int = Field(default=5, alias="MEILI_TIMEOUT")
    max_retries: int = Field(default=3, alias="MEILI_MAX_RETRIES")


class RedisConfig(BaseSettings):
    """Redis configuration."""

    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    db: int = Field(default=0, alias="REDIS_DB")
    cache_ttl: int = Field(default=3600, alias="REDIS_CACHE_TTL")
    socket_timeout: int = Field(default=5, alias="REDIS_SOCKET_TIMEOUT")
    socket_connect_timeout: int = Field(default=5, alias="REDIS_CONNECT_TIMEOUT")
    max_retries: int = Field(default=3, alias="REDIS_MAX_RETRIES")


class SearchConfig(BaseSettings):
    """Search configuration."""

    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    default_limit: int = Field(default=20)
    max_limit: int = Field(default=100)


class IndexerConfig(BaseSettings):
    """Indexer configuration."""

    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    batch_size: int = Field(default=100)
    rate_limit_delay: float = Field(default=1.0)
    state_flush_interval: float = Field(default=1.0, alias="STATE_FLUSH_INTERVAL")


class AppConfig(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    name: str = Field(default="telegram-search-engine")
    debug: bool = Field(default=False, validation_alias="DEBUG")

    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    meilisearch: MeilisearchConfig = Field(default_factory=MeilisearchConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    indexer: IndexerConfig = Field(default_factory=IndexerConfig)

    @classmethod
    def from_toml(cls, path: str | Path) -> "AppConfig":
        """Load configuration from TOML file with env override."""
        path = Path(path)
        if path.exists():
            with open(path, "rb") as f:
                data = tomli.load(f)
            return cls._merge_config(data)
        return cls()

    @classmethod
    def _merge_config(cls, data: dict[str, Any]) -> "AppConfig":
        """Merge TOML data with environment variables."""
        app_data = data.get("app", {})
        return cls(
            name=app_data.get("name", "telegram-search-engine"),
            debug=app_data.get("debug", False),
            telegram=TelegramConfig(**data.get("telegram", {})),
            meilisearch=MeilisearchConfig(**data.get("meilisearch", {})),
            redis=RedisConfig(**data.get("redis", {})),
            search=SearchConfig(**data.get("search", {})),
            indexer=IndexerConfig(**data.get("indexer", {})),
        )


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load configuration from file or environment."""
    if config_path:
        return AppConfig.from_toml(config_path)

    default_path = Path("configs/app.toml")
    if default_path.exists():
        return AppConfig.from_toml(default_path)

    return AppConfig()
