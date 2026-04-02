"""Telegram client for message crawling."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, AsyncIterator, Callable, TypeVar

from telethon import TelegramClient  # type: ignore[import-untyped]
from telethon.errors import FloodWaitError  # type: ignore[import-untyped]
from telethon.tl.types import Message  # type: ignore[import-untyped]

from telegram_search.config import TelegramConfig
from telegram_search.logging import get_logger, safe_error

T = TypeVar("T")

logger = get_logger(__name__)


def build_message_payload(msg: Message) -> dict[str, Any]:
    """Normalize a Telethon message into the internal ingest payload."""
    chat = getattr(msg, "chat", None)
    chat_title = getattr(chat, "title", "") or ""
    chat_username = getattr(chat, "username", "") or ""

    return {
        "chat_id": msg.chat_id,
        "chat_title": chat_title,
        "chat_username": chat_username,
        "msg_id": msg.id,
        "text": msg.text or "",
        "date": msg.date,
    }


class TelethonCrawler:
    """Crawler for Telegram channels."""

    def __init__(self, config: TelegramConfig) -> None:
        """Initialize Telethon client."""
        self._config = config
        self._client: TelegramClient | None = None
        self._session_path = Path(config.session_path)

    async def connect(self) -> None:
        """Connect to Telegram."""
        if self._client:
            return

        self._session_path.parent.mkdir(parents=True, exist_ok=True)

        self._client = TelegramClient(
            str(self._session_path),
            self._config.api_id,
            self._config.api_hash,
        )
        try:
            await self._client.start()
        except Exception:
            # Avoid leaving a half-initialized client around
            self._client = None
            raise

    async def start(self) -> None:
        """Start the client."""
        await self.connect()

    async def disconnect(self) -> None:
        """Disconnect from Telegram."""
        if self._client:
            await self._client.disconnect()
            self._client = None

    def add_event_handler(self, callback: Callable[..., T], event: Any) -> None:
        """Add an event handler."""
        if not self._client:
            raise RuntimeError("Client not connected")
        self._client.add_event_handler(callback, event)

    async def run_until_disconnected(self) -> None:
        """Run the client until disconnected."""
        if not self._client:
            raise RuntimeError("Client not connected")
        await self._client.run_until_disconnected()

    async def fetch_messages(
        self,
        channel: str | int,
        limit: int = 100,
        min_id: int = 0,
        reverse: bool = False,
    ) -> AsyncIterator[dict[str, Any]]:
        """Fetch messages from channel."""
        if not self._client:
            raise RuntimeError("Client not connected")

        fetched = 0
        last_id = min_id

        while True:
            if limit and fetched >= limit:
                break

            remaining = None
            if limit:
                remaining = max(limit - fetched, 0)
                if remaining == 0:
                    break

            try:
                async for msg in self._client.iter_messages(
                    channel,
                    limit=remaining or limit,
                    min_id=last_id if reverse else min_id,
                    reverse=reverse,
                ):
                    if isinstance(msg, Message):
                        last_id = msg.id
                        fetched += 1
                        yield build_message_payload(msg)
                break
            except FloodWaitError as e:
                wait_for = max(int(e.seconds), 1)
                logger.warning(
                    "telegram_flood_wait",
                    seconds=wait_for,
                    channel=channel,
                )
                await asyncio.sleep(wait_for)
                continue
            except Exception as e:
                logger.error("telegram_fetch_error", channel=channel, **safe_error(e))
                raise
