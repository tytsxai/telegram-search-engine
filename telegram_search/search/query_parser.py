"""Advanced query parser for search syntax."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ParsedQuery:
    """Parsed search query with filters."""

    keywords: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    sort: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    source: str | None = None


# Regex patterns
DATE_RANGE_PATTERN = re.compile(r"date:(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})")
SOURCE_PATTERN = re.compile(r"from:(\w+)")
SORT_PATTERN = re.compile(r"sort:(date|relevance)")


def parse_query(query: str) -> ParsedQuery:
    """Parse search query with advanced syntax."""
    result = ParsedQuery()

    # Extract date range
    date_match = DATE_RANGE_PATTERN.search(query)
    if date_match:
        try:
            result.date_from = datetime.fromisoformat(date_match.group(1))
            result.date_to = datetime.fromisoformat(date_match.group(2))
        except ValueError:
            result.date_from = None
            result.date_to = None
        else:
            if result.date_from > result.date_to:
                # Swap to keep a valid range
                result.date_from, result.date_to = result.date_to, result.date_from
            query = DATE_RANGE_PATTERN.sub("", query)

    # Extract source filter
    source_match = SOURCE_PATTERN.search(query)
    if source_match:
        result.source = source_match.group(1)
        query = SOURCE_PATTERN.sub("", query)

    # Extract sort option
    sort_match = SORT_PATTERN.search(query)
    if sort_match:
        result.sort = sort_match.group(1)
        query = SORT_PATTERN.sub("", query)

    # Parse remaining keywords
    result.keywords = query.strip().split()

    # Build filters
    result.filters = build_filters(result)

    return result


def build_filters(parsed: ParsedQuery) -> list[str]:
    """Build Meilisearch filter expressions."""
    filters = []

    if parsed.date_from and parsed.date_to:
        ts_from = int(parsed.date_from.timestamp())
        ts_to = int(parsed.date_to.timestamp())
        filters.append(f"date >= {ts_from} AND date <= {ts_to}")

    if parsed.source:
        filters.append(f'chat_username = "{parsed.source}"')

    return filters
