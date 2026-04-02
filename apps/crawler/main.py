"""Telegram message crawler entry point."""

from __future__ import annotations

import asyncio
import argparse
import signal
import sys
from typing import Any

from telegram_search.config import load_config
from telegram_search.logging import setup_logging, get_logger, safe_error
from telegram_search.indexer.telethon_client import TelethonCrawler
from telegram_search.indexer.realtime_listener import RealtimeListener
from telegram_search.indexer.historical_sync import HistoricalSync
from telegram_search.indexer.channel_registry import Channel, ChannelRegistry
from telegram_search.indexer.ingest_service import IngestService, IngestResult
from telegram_search.indexer.state_store import StateStore
from telegram_search.pipeline.filters import MessageFilter
from telegram_search.runtime import (
    bootstrap_search_backend,
    check_writable_path,
    validate_channels_config,
    validate_runtime_config,
)

logger = get_logger(__name__)


def enrich_message_with_channel(
    msg: dict[str, Any],
    channel: Channel | None,
) -> dict[str, Any]:
    """Fill missing message metadata from the configured channel registry."""
    if channel is None:
        return msg

    enriched = dict(msg)
    chat_title = enriched.get("chat_title")
    chat_username = enriched.get("chat_username")
    if not isinstance(chat_title, str) or not chat_title:
        enriched["chat_title"] = channel.title
    if not isinstance(chat_username, str) or not chat_username:
        enriched["chat_username"] = channel.username
    return enriched


class Crawler:
    """Main crawler orchestrator."""

    def __init__(self) -> None:
        self.config = load_config()
        self.client: TelethonCrawler | None = None
        self.ingest: IngestService | None = None
        self.registry: ChannelRegistry | None = None
        self.state_store: StateStore | None = None
        self._channels_by_id: dict[int, Channel] = {}
        self._ingest_lock = asyncio.Lock()
        self._shutdown = False

    async def setup(self) -> None:
        """Initialize all components."""
        validate_runtime_config(self.config, component="crawler")
        check_writable_path(self.config.telegram.session_path)
        check_writable_path(self.config.indexer.state_path)
        check_writable_path(self.config.indexer.channels_path)
        validate_channels_config(self.config.indexer.channels_path)

        # Initialize components
        self.client = TelethonCrawler(self.config.telegram)
        meili = bootstrap_search_backend(self.config)
        self.ingest = IngestService(meili, MessageFilter())
        self.registry = ChannelRegistry(self.config.indexer.channels_path)
        self._channels_by_id = {channel.channel_id: channel for channel in self.registry.list_channels()}
        self.state_store = StateStore(
            file_path=self.config.indexer.state_path,
            flush_interval=self.config.indexer.state_flush_interval
        )

        await self.client.connect()
        logger.info("crawler_initialized")

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        self._shutdown = True
        if self.state_store:
            self.state_store.flush()
        if self.client:
            await self.client.disconnect()
        logger.info("crawler_shutdown")

    async def on_message(self, msg: dict[str, Any]) -> IngestResult:
        """Handle incoming message."""
        try:
            if not self.ingest:
                raise RuntimeError("Ingest service not initialized")
            chat_id = msg.get("chat_id")
            channel = self._channels_by_id.get(chat_id) if isinstance(chat_id, int) else None
            enriched = enrich_message_with_channel(msg, channel)
            async with self._ingest_lock:
                result = await asyncio.to_thread(self.ingest.ingest_message, enriched)
            if result != IngestResult.ERROR and self.state_store:
                msg_id = enriched.get("msg_id")
                if isinstance(chat_id, int) and isinstance(msg_id, int):
                    self.state_store.set_state(chat_id, msg_id)
            if result == IngestResult.INDEXED:
                logger.debug("message_indexed", msg_id=enriched["msg_id"])
            elif result == IngestResult.SKIPPED:
                logger.debug("message_not_indexed", msg_id=enriched["msg_id"])
            return result
        except Exception as e:
            logger.error("ingest_error", **safe_error(e))
            return IngestResult.ERROR

    async def _ingest_batch(
        self,
        channel_id: int,
        channel_name: str,
        batch: list[dict[str, Any]],
        last_msg_id: int | None,
    ) -> bool:
        """Ingest a batch and update state. Returns False on fatal error."""
        if not self.ingest:
            raise RuntimeError("Ingest service not initialized")

        try:
            await asyncio.to_thread(
                self.ingest.ingest_batch, batch, raise_on_error=True
            )
        except Exception as e:
            logger.error(
                "batch_ingest_error",
                channel=channel_name,
                **safe_error(e),
            )
            return False

        if self.state_store and last_msg_id is not None:
            self.state_store.set_state(channel_id, last_msg_id)
        return True

    async def run_realtime(self) -> None:
        """Run real-time listener."""
        if self._shutdown:
            logger.info("crawler_shutdown_requested")
            return
        channels = self.registry.list_channels()
        if not channels:
            logger.warning("no_channels_configured")
            return

        channel_ids = [c.channel_id for c in channels if c.enabled]
        if not channel_ids:
            logger.warning("no_enabled_channels_configured")
            return
        logger.info("starting_realtime", channels=len(channel_ids))

        listener = RealtimeListener(self.client, self.on_message)
        await listener.start(channel_ids)

    async def run_historical(self, limit: int = 1000) -> None:
        """Run historical sync for all channels."""
        channels = self.registry.list_channels()
        if not channels:
            logger.warning("no_channels_configured")
            return

        if not self.client or not self.state_store:
            raise RuntimeError("Crawler not initialized")

        sync = HistoricalSync(
            self.client,
            self.state_store,
            rate_limit_delay=self.config.indexer.rate_limit_delay,
        )

        batch_size = max(self.config.indexer.batch_size, 1)

        for channel in channels:
            if self._shutdown:
                logger.info("crawler_shutdown_requested")
                break
            if not channel.enabled:
                continue

            logger.info("syncing_channel", channel=channel.username)

            def progress(current):
                logger.info("sync_progress",
                           channel=channel.username,
                           current=current, total=limit)

            count = 0
            batch: list[dict[str, Any]] = []
            last_msg_id: int | None = None
            async for msg in sync.sync_channel(
                channel.channel_id,
                limit=limit,
                progress_callback=progress,
            ):
                if self._shutdown:
                    logger.info("crawler_shutdown_requested")
                    break
                enriched = enrich_message_with_channel(msg, channel)
                batch.append(enriched)
                msg_id = enriched.get("msg_id")
                if isinstance(msg_id, int):
                    last_msg_id = msg_id
                count += 1
                if len(batch) >= batch_size:
                    ok = await self._ingest_batch(
                        channel.channel_id,
                        channel.username,
                        batch,
                        last_msg_id,
                    )
                    batch = []
                    if not ok:
                        logger.error("ingest_error_stop", channel=channel.username, msg_id=msg.get("msg_id"))
                        break

            if not self._shutdown and batch:
                ok = await self._ingest_batch(
                    channel.channel_id,
                    channel.username,
                    batch,
                    last_msg_id,
                )
                if not ok:
                    logger.error("ingest_error_stop", channel=channel.username, msg_id=last_msg_id)

            logger.info("channel_synced",
                       channel=channel.username,
                       messages=count)

        if self.state_store:
            self.state_store.flush()


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Telegram Crawler")
    parser.add_argument(
        "--mode",
        choices=["realtime", "historical", "both"],
        default="realtime",
        help="Crawl mode",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Message limit for historical sync",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    setup_logging(args.debug)
    crawler = Crawler()

    # Handle shutdown signals
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda: asyncio.create_task(crawler.shutdown())
        )

    try:
        await crawler.setup()

        if args.mode == "historical":
            await crawler.run_historical(args.limit)
        elif args.mode == "realtime":
            await crawler.run_realtime()
        else:  # both
            await crawler.run_historical(args.limit)
            if not crawler._shutdown:
                await crawler.run_realtime()

    except KeyboardInterrupt:
        logger.info("interrupted")
    except Exception as e:
        logger.error("crawler_error", **safe_error(e))
        sys.exit(1)
    finally:
        await crawler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
