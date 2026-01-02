"""Tests for query parser module."""

from datetime import datetime

from telegram_search.search.query_parser import (
    parse_query,
)


class TestParseQuery:
    """Tests for parse_query function."""

    def test_simple_query(self):
        """Test simple keyword query."""
        result = parse_query("Python")
        assert "Python" in result.keywords

    def test_date_range(self):
        """Test date range parsing."""
        result = parse_query("date:2024-01-01..2024-06-30 AI")
        assert result.date_from == datetime(2024, 1, 1)
        assert result.date_to == datetime(2024, 6, 30)

    def test_source_filter(self):
        """Test source filter parsing."""
        result = parse_query("from:tech_channel Python")
        assert result.source == "tech_channel"

    def test_sort_option(self):
        """Test sort option parsing."""
        result = parse_query("sort:date Python")
        assert result.sort == "date"

    def test_combined_query(self):
        """Test combined query with all options."""
        query = "date:2024-01-01..2024-12-31 from:news sort:date AI"
        result = parse_query(query)
        assert result.source == "news"
        assert result.sort == "date"
        assert "AI" in result.keywords
