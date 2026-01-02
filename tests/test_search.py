"""Tests for search module."""

import pytest
from unittest.mock import Mock, patch, call

from telegram_search.config import MeilisearchConfig, AppConfig, SearchConfig, RedisConfig
from telegram_search.search.meili_client import MeiliClient
from telegram_search.search.search_service import SearchService
from telegram_search.search.query_parser import ParsedQuery


class TestMeiliClient:
    """Tests for MeiliClient."""

    @patch("telegram_search.search.meili_client.meilisearch.Client")
    def test_init(self, mock_client):
        """Test client initialization."""
        config = MeilisearchConfig()
        MeiliClient(config)
        mock_client.assert_called_once()

    @patch("telegram_search.search.meili_client.meilisearch.Client")
    def test_add_documents(self, mock_client):
        """Test adding documents."""
        mock_index = Mock()
        mock_client.return_value.index.return_value = mock_index

        config = MeilisearchConfig()
        client = MeiliClient(config)
        client.add_documents([{"id": "1", "text": "test"}])

        mock_index.add_documents.assert_called_once()

    @patch("telegram_search.search.meili_client.meilisearch.Client")
    def test_search(self, mock_client):
        """Test search."""
        mock_index = Mock()
        mock_index.search.return_value = {"hits": []}
        mock_client.return_value.index.return_value = mock_index

        config = MeilisearchConfig()
        client = MeiliClient(config)
        
        # Test basic search
        result = client.search("test")
        assert "hits" in result

        # Test with filters and sort
        client.search("test", filters="chat_id=1", sort=["date:desc"])

        assert mock_index.search.call_args_list == [
            call("test", {"limit": 20, "offset": 0}),
            call(
                "test",
                {"limit": 20, "offset": 0, "filter": "chat_id=1", "sort": ["date:desc"]},
            ),
        ]
        
    @patch("telegram_search.search.meili_client.meilisearch.Client")
    def test_retry_on_failure(self, mock_client):
        """Test retry logic."""
        mock_index = Mock()
        mock_index.search.side_effect = [Exception("Fail 1"), Exception("Fail 2"), {"hits": []}]
        mock_client.return_value.index.return_value = mock_index

        config = MeilisearchConfig(max_retries=3)
        client = MeiliClient(config)
        
        with patch("time.sleep"):
            result = client.search("test")

        assert "hits" in result
        assert mock_index.search.call_count == 3

    @patch("telegram_search.search.meili_client.meilisearch.Client")
    def test_max_retries_exceeded(self, mock_client):
        """Test max retries exceeded."""
        mock_index = Mock()
        mock_index.search.side_effect = Exception("Persistent Fail")
        mock_client.return_value.index.return_value = mock_index

        config = MeilisearchConfig(max_retries=2)
        client = MeiliClient(config)
        
        with patch("time.sleep"), pytest.raises(Exception):
            client.search("test")
        
        assert mock_index.search.call_count == 3


class TestSearchService:
    """Tests for SearchService."""

    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=AppConfig)
        config.meilisearch = MeilisearchConfig()
        config.redis = RedisConfig()
        config.search = SearchConfig()
        return config

    @pytest.fixture
    def mock_meili(self):
        with patch("telegram_search.search.search_service.MeiliClient") as mock:
            yield mock

    @pytest.fixture
    def mock_cache(self):
        with patch("telegram_search.search.search_service.RedisCache") as mock:
            yield mock

    @patch("telegram_search.search.search_service.parse_query")
    def test_search_integration(self, mock_parse, mock_config, mock_meili, mock_cache):
        """Test search service integrates query parser correctly."""
        service = SearchService(mock_config)
        meili_instance = mock_meili.return_value
        cache_instance = mock_cache.return_value

        # Setup mock parser
        parsed = ParsedQuery(
            keywords=["keyword"],
            filters=["date >= 1000"],
            sort="date:desc"
        )
        mock_parse.return_value = parsed
        
        # Setup mock cache miss (get_or_compute calls compute_func)
        # We simulate get_or_compute behavior: it returns what compute_func returns
        def side_effect(**kwargs):
            return kwargs['compute_func']()
            
        cache_instance.get_or_compute.side_effect = side_effect
        
        # Setup mock meili result
        expected_result = {"hits": [{"id": 1}]}
        meili_instance.search.return_value = expected_result

        # Call search
        result = service.search("keyword date:2023", filters="chat_id=1")

        # Verify parse_query called
        mock_parse.assert_called_with("keyword date:2023")

        # Verify MeiliClient search called with correct params
        meili_instance.search.assert_called_with(
            "keyword",
            limit=20,
            offset=0,
            filters=["date >= 1000", "chat_id=1"],
            sort=["date:desc"]
        )

        # Verify caching - get_or_compute called
        cache_instance.get_or_compute.assert_called_once()
        _, kwargs = cache_instance.get_or_compute.call_args
        assert kwargs['query'] == "keyword"
        assert kwargs['limit'] == 20
        assert kwargs['offset'] == 0
        assert kwargs['sort'] == "['date:desc']"
        assert "['chat_id=1', 'date >= 1000']" in kwargs['filters'] or "['date >= 1000', 'chat_id=1']" in kwargs['filters']
        
        assert result == expected_result
