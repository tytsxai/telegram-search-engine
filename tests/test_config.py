"""Tests for configuration module."""



from telegram_search.config import (
    AppConfig,
    load_config,
    MeilisearchConfig,
    RedisConfig,
    TelegramConfig,
)


class TestTelegramConfig:
    """Tests for TelegramConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = TelegramConfig()
        assert config.bot_token == ""
        assert config.api_id == 0
        assert config.api_hash == ""

    def test_env_override(self, monkeypatch):
        """Test environment variable override."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token")
        config = TelegramConfig()
        assert config.bot_token == "test_token"


class TestMeilisearchConfig:
    """Tests for MeilisearchConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = MeilisearchConfig()
        assert config.host == "http://localhost:7700"
        assert config.api_key == ""
        assert config.index_name == "telegram_messages"

    def test_env_override(self, monkeypatch):
        """Test environment variable override."""
        monkeypatch.setenv("MEILI_HOST", "http://custom:7700")
        config = MeilisearchConfig()
        assert config.host == "http://custom:7700"


class TestRedisConfig:
    """Tests for RedisConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RedisConfig()
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.cache_ttl == 3600


class TestAppConfig:
    """Tests for AppConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AppConfig()
        assert config.name == "telegram-search-engine"
        assert config.debug is False
        assert config.indexer.state_flush_interval == 1.0

    def test_from_toml(self, tmp_path):
        """Test loading from TOML file."""
        toml_content = '''
[app]
name = "test-app"
debug = true

[meilisearch]
host = "http://test:7700"
'''
        toml_file = tmp_path / "test.toml"
        toml_file.write_text(toml_content)

        config = AppConfig.from_toml(toml_file)
        assert config.name == "test-app"
        assert config.debug is True
        assert config.meilisearch.host == "http://test:7700"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_default(self):
        """Test loading default config."""
        config = load_config()
        assert isinstance(config, AppConfig)

    def test_load_from_path(self, tmp_path):
        """Test loading from specific path."""
        toml_content = '''
[app]
name = "custom-app"
'''
        toml_file = tmp_path / "custom.toml"
        toml_file.write_text(toml_content)

        config = load_config(toml_file)
        assert config.name == "custom-app"
