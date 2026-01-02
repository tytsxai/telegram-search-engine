"""Tests for HistoricalSync."""

import pytest
from unittest.mock import MagicMock
from telegram_search.indexer.historical_sync import HistoricalSync
from telegram_search.indexer.state_store import StateStore
from telegram_search.indexer.telethon_client import TelethonCrawler


@pytest.mark.asyncio
async def test_sync_channel() -> None:
    """Test normal sync flow."""
    mock_crawler = MagicMock(spec=TelethonCrawler)
    mock_state = MagicMock(spec=StateStore)

    # Setup mocks
    mock_state.get_state.return_value = 100

    # Mock fetch_messages to yield items
    messages = [
        {"msg_id": 101, "text": "msg1"},
        {"msg_id": 102, "text": "msg2"},
    ]

    async def async_gen(*args, **kwargs):
        for msg in messages:
            yield msg

    mock_crawler.fetch_messages.side_effect = async_gen

    sync = HistoricalSync(mock_crawler, mock_state)

    processed = []
    async for msg in sync.sync_channel("ch1", limit=10):
        processed.append(msg)

    assert len(processed) == 2
    assert processed[0]["msg_id"] == 101

    # Check calls
    mock_state.get_state.assert_called_with("ch1")
    mock_crawler.fetch_messages.assert_called_with(
        "ch1", limit=10, min_id=100, reverse=True
    )
    mock_state.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_sync_channel_no_new_messages() -> None:
    """Test sync when no new messages."""
    mock_crawler = MagicMock(spec=TelethonCrawler)
    mock_state = MagicMock(spec=StateStore)
    mock_state.get_state.return_value = 100

    async def async_gen(*args, **kwargs):
        if False:
            yield

    mock_crawler.fetch_messages.side_effect = async_gen

    sync = HistoricalSync(mock_crawler, mock_state)
    async for _ in sync.sync_channel("ch1"):
        pass

    mock_state.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_sync_channel_progress_callback() -> None:
    """Test progress callback."""
    mock_crawler = MagicMock(spec=TelethonCrawler)
    mock_state = MagicMock(spec=StateStore)
    mock_state.get_state.return_value = 0

    messages = [{"msg_id": 1}, {"msg_id": 2}]

    async def async_gen(*args, **kwargs):
        for m in messages:
            yield m

    mock_crawler.fetch_messages.side_effect = async_gen

    callback = MagicMock()
    sync = HistoricalSync(mock_crawler, mock_state)

    async for _ in sync.sync_channel("ch1", progress_callback=callback):
        pass

    assert callback.call_count == 2
    callback.assert_any_call(1)
    callback.assert_any_call(2)
