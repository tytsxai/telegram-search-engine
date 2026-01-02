"""Real-time listener for Telegram messages."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, List, Union

from telethon import events
from telethon.tl.types import Message

from telegram_search.indexer.telethon_client import TelethonCrawler
from telegram_search.logging import get_logger, safe_error

logger = get_logger(__name__)


class RealtimeListener:
    """Listener for real-time Telegram messages."""

    def __init__(
        self,
        client: TelethonCrawler,
        callback: Callable[[dict[str, Any]], Awaitable[None] | None],
    ) -> None:
        """Initialize listener.

        Args:
            client: The Telethon client wrapper.
            callback: Function to call when a new message is received.
                      Receives a dict with message data.
        """
        self._client = client
        self._callback = callback
        self._channels: List[Union[str, int]] = []

    async def start(self, channels: List[Union[str, int]]) -> None:
        """Start listening to specified channels.

        Args:
            channels: List of channel usernames or IDs to listen to.
        """
        self._channels = channels
        await self._client.connect()

        self._client.add_event_handler(
            self._handle_new_message,
            events.NewMessage(chats=self._channels),
        )

        logger.info("realtime_listening_started", channels=len(channels))
        await self._client.run_until_disconnected()

    async def _handle_new_message(self, event: events.NewMessage.Event) -> None:
        """Handle incoming new message event."""
        try:
            msg = event.message
            if isinstance(msg, Message) and msg.text:
                data = {
                    "chat_id": msg.chat_id,
                    "msg_id": msg.id,
                    "text": msg.text,
                    "date": msg.date,
                }
                logger.debug("realtime_message_received", chat_id=msg.chat_id, msg_id=msg.id)

                result = self._callback(data)
                if asyncio.iscoroutine(result) or asyncio.isfuture(result):
                    await result

        except Exception as e:
            logger.error("realtime_message_error", **safe_error(e))
