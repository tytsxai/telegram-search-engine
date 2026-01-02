"""Historical message synchronization service."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Callable, Optional

from telegram_search.indexer.state_store import StateStore
from telegram_search.indexer.telethon_client import TelethonCrawler


class HistoricalSync:
    """Service for historical message fetching and sync."""

    def __init__(
        self,
        crawler: TelethonCrawler,
        state_store: StateStore,
        rate_limit_delay: float = 0.0,
    ) -> None:
        """Initialize sync service.

        Args:
            crawler: Telethon crawler instance.
            state_store: State persistence store.
            rate_limit_delay: Optional delay between messages to reduce API pressure.
        """
        self.crawler = crawler
        self.state_store = state_store
        self.rate_limit_delay = max(rate_limit_delay, 0.0)

    async def sync_channel(
        self,
        channel_id: str | int,
        limit: int = 100,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> AsyncIterator[dict]:
        """Sync messages from channel incrementally.

        Fetches messages starting from the last known message ID (min_id).
        Uses reverse=True to fetch from oldest to newest. The caller should
        persist progress as messages are processed.

        Args:
            channel_id: Channel identifier.
            limit: Maximum number of messages to fetch in this run.
            progress_callback: Optional callback for progress updates.

        Yields:
            Message dictionaries.
        """
        min_id = self.state_store.get_state(channel_id)
        count = 0

        # Fetch messages older->newer (reverse=True) starting from min_id
        async for msg in self.crawler.fetch_messages(
            channel_id,
            limit=limit,
            min_id=min_id,
            reverse=True,
        ):
            yield msg

            count += 1
            if progress_callback:
                progress_callback(count)

            if self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay)
