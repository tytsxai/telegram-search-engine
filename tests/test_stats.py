"""Tests for stats module."""

from unittest.mock import patch

import pytest
from telegram_search.config import RedisConfig
from telegram_search.stats import StatsService


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("redis.Redis") as mock:
        yield mock


@pytest.fixture
def stats_service(mock_redis):
    """Create StatsService with mocked Redis."""
    config = RedisConfig(host="localhost", port=6379, db=0)
    return StatsService(config)


def test_init(mock_redis):
    """Test initialization."""
    config = RedisConfig(host="test", port=1234, db=1)
    StatsService(config)
    mock_redis.assert_called_once()
    _, kwargs = mock_redis.call_args
    assert kwargs["host"] == "test"
    assert kwargs["port"] == 1234
    assert kwargs["db"] == 1
    assert kwargs["decode_responses"] is True
    assert kwargs["socket_timeout"] == config.socket_timeout
    assert kwargs["socket_connect_timeout"] == config.socket_connect_timeout
    assert "retry" in kwargs


def test_record_search(stats_service, mock_redis):
    """Test recording a search."""
    client = mock_redis.return_value
    
    stats_service.record_search("Test Query")
    
    client.incr.assert_called_with("stats:total_searches")
    client.zincrby.assert_called_with(
        "stats:keywords",
        1.0,
        "test query",
    )


def test_record_search_empty(stats_service, mock_redis):
    """Test recording empty search."""
    client = mock_redis.return_value
    
    stats_service.record_search("")
    stats_service.record_search("   ")
    
    client.incr.assert_not_called()
    client.zincrby.assert_not_called()


def test_get_stats(stats_service, mock_redis):
    """Test getting stats."""
    client = mock_redis.return_value
    client.get.return_value = "42"
    client.zrevrange.return_value = [("foo", 10.0), ("bar", 5.0)]
    
    stats = stats_service.get_stats(top_k=5)
    
    assert stats["total_searches"] == 42
    assert stats["top_keywords"] == [("foo", 10.0), ("bar", 5.0)]
    
    client.get.assert_called_with("stats:total_searches")
    client.zrevrange.assert_called_with(
        "stats:keywords",
        0,
        4,
        withscores=True,
    )


def test_get_stats_empty(stats_service, mock_redis):
    """Test getting stats when empty."""
    client = mock_redis.return_value
    client.get.return_value = None
    client.zrevrange.return_value = []
    
    stats = stats_service.get_stats()
    
    assert stats["total_searches"] == 0
    assert stats["top_keywords"] == []
