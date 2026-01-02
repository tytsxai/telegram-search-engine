"""Search service with caching."""

from __future__ import annotations

from typing import Any

from telegram_search.config import AppConfig
from telegram_search.search.meili_client import MeiliClient
from telegram_search.search.query_parser import parse_query
from telegram_search.cache.redis_cache import RedisCache


class SearchService:
    """Search service with cache-aside pattern."""

    def __init__(self, config: AppConfig) -> None:
        """Initialize search service."""
        self._meili = MeiliClient(config.meilisearch)
        self._cache = RedisCache(config.redis)
        self._config = config.search

    def search(
        self,
        query: str,
        limit: int | None = None,
        offset: int = 0,
        filters: str | None = None,
        sort: str | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Search with cache-aside pattern."""
        if not isinstance(query, str):
            raise TypeError("query must be a string")

        query = query.strip()
        limit_value = self._config.default_limit if limit is None else limit
        if limit_value <= 0:
            limit_value = self._config.default_limit
        limit_value = min(limit_value, self._config.max_limit)
        offset = max(offset, 0)

        # Parse query
        parsed = parse_query(query)
        search_query = " ".join(parsed.keywords)

        # Combine filters
        search_filters: list[str] = parsed.filters.copy()
        if filters:
            search_filters.append(filters)

        # Handle sort - prefer passed sort, fallback to parsed sort
        # Note: parsed.sort is a string (e.g. "date:desc")
        search_sort: list[str] | None = None
        if sort:
            search_sort = [sort]
        elif parsed.sort:
            if parsed.sort == "date":
                search_sort = ["date:desc"]
            elif parsed.sort == "relevance":
                search_sort = None
            else:
                search_sort = [parsed.sort]

        # Prepare cache key components
        # We need a stable string representation for the cache key
        # Sorting filters list to ensure stability
        cache_filters = f"{sorted(search_filters)}:{search_sort}"

        def compute() -> dict[str, Any]:
            return self._meili.search(
                search_query,
                limit=limit_value,
                offset=offset,
                filters=search_filters,
                sort=search_sort,
            )

        # Check cache first
        if use_cache:
            return self._cache.get_or_compute(
                query=search_query,
                compute_func=compute,
                limit=limit_value,
                offset=offset,
                sort=str(search_sort), # Convert list to string for cache key
                filters=cache_filters,
            )

        return compute()

    def close(self) -> None:
        """Close underlying resources."""
        self._cache.close()
