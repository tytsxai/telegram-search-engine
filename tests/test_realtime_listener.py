"""Tests for realtime listener."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from telethon import events
from telethon.tl.types import Message

from telegram_search.indexer.telethon_client import TelethonCrawler
from telegram_search.indexer.realtime_listener import RealtimeListener
from telegram_search.config import TelegramConfig


@pytest.fixture
def mock_config():
    """Mock Telegram config."""
    return TelegramConfig(
        bot_token="bot_token",
        api_id="12345",
        api_hash="hash",
    )


@pytest.fixture
def mock_telethon_client():
    """Mock Telethon client inside crawler."""
    client = MagicMock()
    client.start = AsyncMock()
    client.disconnect = AsyncMock()
    client.run_until_disconnected = AsyncMock()
    client.add_event_handler = Mock()
    return client


class TestTelethonCrawler:
    """Tests for TelethonCrawler."""

    @pytest.mark.asyncio
    async def test_connect_start(self, mock_config):
        """Test connect and start."""
        crawler = TelethonCrawler(mock_config)
        with patch("telegram_search.indexer.telethon_client.TelegramClient") as mock_cls:
            mock_instance = mock_cls.return_value
            mock_instance.start = AsyncMock()
            
            await crawler.connect()
            mock_cls.assert_called_once()
            mock_instance.start.assert_awaited_once()
            
            # Test double connect (should not re-init)
            await crawler.connect()
            mock_cls.assert_called_once() # Still once

    @pytest.mark.asyncio
    async def test_add_event_handler(self, mock_config):
        """Test add_event_handler."""
        crawler = TelethonCrawler(mock_config)
        with patch("telegram_search.indexer.telethon_client.TelegramClient") as mock_cls:
            mock_instance = mock_cls.return_value
            mock_instance.start = AsyncMock()
            await crawler.connect()
            
            callback = Mock()
            event = Mock()
            crawler.add_event_handler(callback, event)
            mock_instance.add_event_handler.assert_called_with(callback, event)

    @pytest.mark.asyncio
    async def test_run_until_disconnected(self, mock_config):
        """Test run_until_disconnected."""
        crawler = TelethonCrawler(mock_config)
        with patch("telegram_search.indexer.telethon_client.TelegramClient") as mock_cls:
            mock_instance = mock_cls.return_value
            mock_instance.start = AsyncMock()
            mock_instance.run_until_disconnected = AsyncMock()
            await crawler.connect()
            
            await crawler.run_until_disconnected()
            mock_instance.run_until_disconnected.assert_awaited_once()


class TestRealtimeListener:
    """Tests for RealtimeListener."""

    @pytest.mark.asyncio
    async def test_start(self, mock_config):
        """Test start listening."""
        crawler = TelethonCrawler(mock_config)
        crawler.connect = AsyncMock()
        crawler.run_until_disconnected = AsyncMock()
        crawler.add_event_handler = Mock()
        
        callback = AsyncMock()
        listener = RealtimeListener(crawler, callback)
        
        channels = ["channel1", 123]
        await listener.start(channels)
        
        crawler.connect.assert_awaited_once()
        crawler.add_event_handler.assert_called_once()
        crawler.run_until_disconnected.assert_awaited_once()
        
        # Check if event handler was registered with correct filter
        call_args = crawler.add_event_handler.call_args
        assert call_args[0][0] == listener._handle_new_message
        assert isinstance(call_args[0][1], events.NewMessage)
        assert call_args[0][1].chats == channels

    @pytest.mark.asyncio
    async def test_handle_new_message_async(self, mock_config):
        """Test handling new message with async callback."""
        crawler = TelethonCrawler(mock_config)
        callback = AsyncMock()
        listener = RealtimeListener(crawler, callback)
        
        # Mock event
        event = MagicMock(spec=events.NewMessage.Event)
        message = MagicMock(spec=Message)
        message.text = "Hello"
        message.chat_id = 123
        message.id = 1
        message.date = datetime.now()
        event.message = message
        
        await listener._handle_new_message(event)
        
        callback.assert_awaited_once()
        call_args = callback.call_args[0][0]
        assert call_args["text"] == "Hello"
        assert call_args["chat_id"] == 123
        assert call_args["msg_id"] == 1

    @pytest.mark.asyncio
    async def test_handle_new_message_sync(self, mock_config):
        """Test handling new message with sync callback."""
        crawler = TelethonCrawler(mock_config)
        callback = Mock()
        listener = RealtimeListener(crawler, callback)
        
        # Mock event
        event = MagicMock(spec=events.NewMessage.Event)
        message = MagicMock(spec=Message)
        message.text = "Hello"
        message.chat_id = 123
        message.id = 1
        message.date = datetime.now()
        event.message = message
        
        await listener._handle_new_message(event)
        
        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert call_args["text"] == "Hello"

    @pytest.mark.asyncio
    async def test_handle_new_message_exception(self, mock_config):
        """Test handling new message with exception in callback."""
        crawler = TelethonCrawler(mock_config)
        callback = Mock(side_effect=Exception("Callback error"))
        listener = RealtimeListener(crawler, callback)
        
        # Mock event
        event = MagicMock(spec=events.NewMessage.Event)
        message = MagicMock(spec=Message)
        message.text = "Hello"
        message.chat_id = 123
        message.id = 1
        message.date = datetime.now()
        event.message = message
        
        # Should not raise exception, but log it
        await listener._handle_new_message(event)
        
        callback.assert_called_once()
