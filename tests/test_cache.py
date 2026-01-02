"""Tests for cache module."""

from unittest.mock import Mock, patch
from redis.exceptions import RedisError

from telegram_search.config import RedisConfig
from telegram_search.cache.redis_cache import RedisCache


class TestRedisCache:
    """Tests for RedisCache."""

    @patch("telegram_search.cache.redis_cache.redis.Redis")
    def test_init(self, mock_redis):
        """Test cache initialization."""
        config = RedisConfig()
        RedisCache(config)
        mock_redis.assert_called_once()

    @patch("telegram_search.cache.redis_cache.redis.Redis")
    def test_make_key(self, mock_redis):
        """Test cache key generation."""
        config = RedisConfig()
        cache = RedisCache(config)
        key = cache._make_key("test query", filters="f", limit=10)
        assert key.startswith("search:")

    @patch("telegram_search.cache.redis_cache.redis.Redis")
    def test_get_miss(self, mock_redis):
        """Test cache miss."""
        mock_redis.return_value.get.return_value = None
        config = RedisConfig()
        cache = RedisCache(config)
        result = cache.get("query")
        assert result is None

    @patch("telegram_search.cache.redis_cache.redis.Redis")
    def test_get_hit(self, mock_redis):
        """Test cache hit."""
        mock_redis.return_value.get.return_value = '{"hits": []}'
        config = RedisConfig()
        cache = RedisCache(config)
        result = cache.get("query")
        assert result == {"hits": []}

    @patch("telegram_search.cache.redis_cache.redis.Redis")
    def test_set(self, mock_redis):
        """Test cache set."""
        config = RedisConfig()
        cache = RedisCache(config)
        cache.set("query", {"hits": []}, filters="f")
        mock_redis.return_value.setex.assert_called_once()

    @patch("telegram_search.cache.redis_cache.redis.Redis")
    def test_get_or_compute_hit(self, mock_redis):
        """Test get_or_compute cache hit."""
        mock_redis.return_value.get.return_value = '{"hits": []}'
        config = RedisConfig()
        cache = RedisCache(config)
        
        compute = Mock()
        result = cache.get_or_compute("query", compute)
        
        assert result == {"hits": []}
        compute.assert_not_called()

    @patch("telegram_search.cache.redis_cache.redis.Redis")
    def test_get_or_compute_hit_empty_result(self, mock_redis):
        """Test get_or_compute cache hit with empty dict."""
        mock_redis.return_value.get.return_value = '{}'
        config = RedisConfig()
        cache = RedisCache(config)

        compute = Mock()
        result = cache.get_or_compute("query", compute)

        assert result == {}
        compute.assert_not_called()

    @patch("telegram_search.cache.redis_cache.redis.Redis")
    def test_get_or_compute_miss(self, mock_redis):
        """Test get_or_compute cache miss."""
        mock_redis.return_value.get.return_value = None
        config = RedisConfig()
        cache = RedisCache(config)
        
        expected = {"hits": [1]}
        compute = Mock(return_value=expected)
        
        result = cache.get_or_compute("query", compute, limit=10)
        
        assert result == expected
        compute.assert_called_once()
        mock_redis.return_value.setex.assert_called()

    @patch("telegram_search.cache.redis_cache.redis.Redis")
    def test_get_error(self, mock_redis):
        """Test get error handling."""
        mock_redis.return_value.get.side_effect = RedisError("Fail")
        config = RedisConfig()
        cache = RedisCache(config)
        
        # Should not raise
        result = cache.get("query")
        assert result is None

    @patch("telegram_search.cache.redis_cache.redis.Redis")
    def test_set_error(self, mock_redis):
        """Test set error handling."""
        mock_redis.return_value.setex.side_effect = RedisError("Fail")
        config = RedisConfig()
        cache = RedisCache(config)
        
        # Should not raise
        cache.set("query", {})
