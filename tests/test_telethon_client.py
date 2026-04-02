"""Tests for TelethonCrawler."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telethon.errors import FloodWaitError
from telethon.tl.types import Message, PeerChannel

from telegram_search.config import TelegramConfig
from telegram_search.indexer.telethon_client import TelethonCrawler


def _make_message(msg_id: int, chat_id: int = 100, text: str = "hello") -> Message:
    msg = Message(
        id=msg_id,
        peer_id=PeerChannel(chat_id),
        message=text,
        date=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    msg._text = text
    msg._chat = SimpleNamespace(title="Test Channel", username="testchannel")
    return msg


@pytest.fixture
def config() -> TelegramConfig:
    return TelegramConfig(TELEGRAM_API_ID=12345, TELEGRAM_API_HASH="test_hash")


class TestTelethonCrawlerInit:
    """Tests for TelethonCrawler initialization."""

    def test_init_stores_config(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        assert crawler._config is config

    def test_init_client_is_none(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        assert crawler._client is None


class TestConnectDisconnect:
    """Tests for connect and disconnect methods."""

    @pytest.mark.asyncio
    async def test_connect_creates_client(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        with patch("telegram_search.indexer.telethon_client.TelegramClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.start = AsyncMock()
            mock_cls.return_value = mock_client

            await crawler.connect()

            mock_cls.assert_called_once_with("session", 12345, "test_hash")
            mock_client.start.assert_awaited_once()
            assert crawler._client is mock_client

    @pytest.mark.asyncio
    async def test_connect_idempotent(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        with patch("telegram_search.indexer.telethon_client.TelegramClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.start = AsyncMock()
            mock_cls.return_value = mock_client

            await crawler.connect()
            await crawler.connect()

            mock_cls.assert_called_once()
            mock_client.start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_resets_on_failure(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        with patch("telegram_search.indexer.telethon_client.TelegramClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.start = AsyncMock(side_effect=ConnectionError("fail"))
            mock_cls.return_value = mock_client

            with pytest.raises(ConnectionError):
                await crawler.connect()

            assert crawler._client is None

    @pytest.mark.asyncio
    async def test_disconnect(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        with patch("telegram_search.indexer.telethon_client.TelegramClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.start = AsyncMock()
            mock_client.disconnect = AsyncMock()
            mock_cls.return_value = mock_client

            await crawler.connect()
            await crawler.disconnect()

            mock_client.disconnect.assert_awaited_once()
            assert crawler._client is None

    @pytest.mark.asyncio
    async def test_disconnect_noop_when_not_connected(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        await crawler.disconnect()
        assert crawler._client is None

    @pytest.mark.asyncio
    async def test_start_is_connect(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        with patch.object(crawler, "connect", new_callable=AsyncMock) as mock_connect:
            await crawler.start()
            mock_connect.assert_awaited_once()


class TestFetchMessages:
    """Tests for fetch_messages method."""

    def _make_message(self, msg_id: int, chat_id: int = 100, text: str = "hello") -> Message:
        msg = Message(
            id=msg_id,
            peer_id=PeerChannel(chat_id),
            message=text,
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        msg._text = text
        msg._chat = SimpleNamespace(title="Test Channel", username="testchannel")
        return msg

    @pytest.mark.asyncio
    async def test_fetch_raises_when_not_connected(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        with pytest.raises(RuntimeError, match="Client not connected"):
            async for _ in crawler.fetch_messages("test_channel"):
                pass

    @pytest.mark.asyncio
    async def test_fetch_basic(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        mock_client = AsyncMock()

        msg1 = self._make_message(1, 100, "first")
        msg2 = self._make_message(2, 100, "second")

        async def mock_iter(*args, **kwargs):
            for m in [msg1, msg2]:
                yield m

        mock_client.iter_messages = mock_iter
        crawler._client = mock_client

        results = [m async for m in crawler.fetch_messages("test_channel")]

        assert len(results) == 2
        assert results[0]["msg_id"] == 1
        assert results[0]["text"] == "first"
        assert results[0]["chat_id"] == -1000000000100
        assert results[0]["chat_title"] == "Test Channel"
        assert results[0]["chat_username"] == "testchannel"
        assert results[1]["msg_id"] == 2
        assert results[1]["text"] == "second"

    @pytest.mark.asyncio
    async def test_fetch_respects_limit(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        mock_client = AsyncMock()

        messages = [self._make_message(i, 100, f"msg{i}") for i in range(1, 11)]

        async def mock_iter(*args, **kwargs):
            for m in messages[: kwargs.get("limit", len(messages))]:
                yield m

        mock_client.iter_messages = mock_iter
        crawler._client = mock_client

        results = [m async for m in crawler.fetch_messages("test_channel", limit=3)]

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_fetch_with_min_id(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        mock_client = AsyncMock()

        msg = self._make_message(50, 100, "after min_id")

        async def mock_iter(*args, **kwargs):
            assert kwargs.get("min_id") == 40
            yield msg

        mock_client.iter_messages = mock_iter
        crawler._client = mock_client

        results = [m async for m in crawler.fetch_messages("test_channel", min_id=40)]
        assert len(results) == 1
        assert results[0]["msg_id"] == 50

    @pytest.mark.asyncio
    async def test_fetch_reverse(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        mock_client = AsyncMock()

        msg = self._make_message(10, 100, "reversed")

        async def mock_iter(*args, **kwargs):
            assert kwargs.get("reverse") is True
            assert kwargs.get("min_id") == 5
            yield msg

        mock_client.iter_messages = mock_iter
        crawler._client = mock_client

        results = [m async for m in crawler.fetch_messages("test_channel", min_id=5, reverse=True)]
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_fetch_skips_non_message(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        mock_client = AsyncMock()

        non_msg = MagicMock()
        non_msg.id = 99
        msg = self._make_message(1, 100, "real")

        async def mock_iter(*args, **kwargs):
            yield non_msg
            yield msg

        mock_client.iter_messages = mock_iter
        crawler._client = mock_client

        results = [m async for m in crawler.fetch_messages("test_channel")]

        assert len(results) == 1
        assert results[0]["msg_id"] == 1

    @pytest.mark.asyncio
    async def test_fetch_empty_text_defaults(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        mock_client = AsyncMock()

        msg = Message(
            id=1,
            peer_id=PeerChannel(100),
            message="",
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        msg.message = None

        async def mock_iter(*args, **kwargs):
            yield msg

        mock_client.iter_messages = mock_iter
        crawler._client = mock_client

        results = [m async for m in crawler.fetch_messages("test_channel")]
        assert results[0]["text"] == ""


class TestFetchMessagesErrors:
    """Tests for error handling in fetch_messages."""

    @pytest.mark.asyncio
    async def test_flood_wait_retry(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        mock_client = AsyncMock()

        msg = _make_message(1, 100, "after flood")

        call_count = 0

        async def mock_iter(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                err = FloodWaitError(request=None)
                err.seconds = 1
                raise err
            yield msg

        mock_client.iter_messages = mock_iter
        crawler._client = mock_client

        with patch("asyncio.sleep", new_callable=AsyncMock):
            results = [m async for m in crawler.fetch_messages("test_channel")]

        assert call_count == 2
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_generic_error_raises(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        mock_client = AsyncMock()

        mock_client.iter_messages = MagicMock(side_effect=ValueError("boom"))
        crawler._client = mock_client

        with pytest.raises(ValueError, match="boom"):
            async for _ in crawler.fetch_messages("test_channel"):
                pass


class TestAddEventHandler:
    """Tests for add_event_handler."""

    def test_raises_when_not_connected(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        with pytest.raises(RuntimeError, match="Client not connected"):
            crawler.add_event_handler(lambda: None, "event")

    def test_delegates_to_client(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        mock_client = MagicMock()
        crawler._client = mock_client

        callback = MagicMock()
        crawler.add_event_handler(callback, "event")

        mock_client.add_event_handler.assert_called_once_with(callback, "event")


class TestRunUntilDisconnected:
    """Tests for run_until_disconnected."""

    @pytest.mark.asyncio
    async def test_raises_when_not_connected(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        with pytest.raises(RuntimeError, match="Client not connected"):
            await crawler.run_until_disconnected()

    @pytest.mark.asyncio
    async def test_delegates_to_client(self, config: TelegramConfig) -> None:
        crawler = TelethonCrawler(config)
        mock_client = AsyncMock()
        mock_client.run_until_disconnected = AsyncMock()
        crawler._client = mock_client

        await crawler.run_until_disconnected()

        mock_client.run_until_disconnected.assert_awaited_once()
