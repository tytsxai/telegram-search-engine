"""Tests for ingest service."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from telegram_search.indexer.ingest_service import IngestService, IngestResult
from telegram_search.pipeline.filters import MessageFilter
from telegram_search.search.meili_client import MeiliClient


@pytest.fixture
def mock_meili_client():
    return Mock(spec=MeiliClient)


@pytest.fixture
def message_filter():
    return MessageFilter()


@pytest.fixture
def ingest_service(mock_meili_client, message_filter):
    return IngestService(mock_meili_client, message_filter, dedup_window_size=10)


def test_ingest_message_success(ingest_service, mock_meili_client):
    """Test successful ingestion of a single message."""
    msg_data = {
        "chat_id": 123,
        "msg_id": 1,
        "text": "Unique message content here",
        "date": datetime.now(),
    }

    result = ingest_service.ingest_message(msg_data)

    assert result == IngestResult.INDEXED
    mock_meili_client.add_documents.assert_called_once()
    args, _ = mock_meili_client.add_documents.call_args
    assert len(args[0]) == 1
    assert args[0][0]["text"] == "Unique message content here"


def test_ingest_message_duplicate(ingest_service, mock_meili_client):
    """Test deduplication of messages."""
    msg_data = {
        "chat_id": 123,
        "msg_id": 1,
        "text": "Duplicate message content",
        "date": datetime.now(),
    }

    # First ingestion
    assert ingest_service.ingest_message(msg_data) == IngestResult.INDEXED
    mock_meili_client.add_documents.assert_called_once()
    mock_meili_client.add_documents.reset_mock()

    # Second ingestion (exact duplicate text -> same simhash)
    msg_data_2 = msg_data.copy()
    msg_data_2["msg_id"] = 2 # Different ID but same content
    
    assert ingest_service.ingest_message(msg_data_2) == IngestResult.SKIPPED
    mock_meili_client.add_documents.assert_not_called()


def test_ingest_message_filtered(ingest_service, mock_meili_client):
    """Test that messages are filtered."""
    msg_data = {
        "chat_id": 123,
        "msg_id": 1,
        "text": "Hi", # Too short (default min_len=5)
        "date": datetime.now(),
    }

    assert ingest_service.ingest_message(msg_data) == IngestResult.SKIPPED
    mock_meili_client.add_documents.assert_not_called()


def test_ingest_batch(ingest_service, mock_meili_client):
    """Test batch ingestion with duplicates."""
    msgs_data = [
        {
            "chat_id": 123, 
            "msg_id": 1, 
            "text": "First unique message", 
            "date": datetime.now()
        },
        {
            "chat_id": 123, 
            "msg_id": 2, 
            "text": "First unique message", # Duplicate in batch
            "date": datetime.now()
        },
        {
            "chat_id": 123, 
            "msg_id": 3, 
            "text": "Second unique message", 
            "date": datetime.now()
        },
        {
            "chat_id": 123, 
            "msg_id": 4, 
            "text": "Hi", # Filtered (short)
            "date": datetime.now()
        },
    ]

    count = ingest_service.ingest_batch(msgs_data)

    assert count == 2 # 1st and 3rd are valid and unique
    mock_meili_client.add_documents.assert_called_once()
    args, _ = mock_meili_client.add_documents.call_args
    docs = args[0]
    assert len(docs) == 2
    assert docs[0]["msg_id"] == 1
    assert docs[1]["msg_id"] == 3


def test_ingest_batch_dedup_against_history(ingest_service, mock_meili_client):
    """Test batch ingestion checks against previously ingested messages."""
    # Pre-populate history
    ingest_service.ingest_message({
        "chat_id": 123, 
        "msg_id": 0, 
        "text": "Old message content", 
        "date": datetime.now()
    })
    mock_meili_client.add_documents.reset_mock()

    msgs_data = [
        {
            "chat_id": 123, 
            "msg_id": 1, 
            "text": "Old message content", # Duplicate of history
            "date": datetime.now()
        },
        {
            "chat_id": 123, 
            "msg_id": 2, 
            "text": "New message content", 
            "date": datetime.now()
        },
    ]

    count = ingest_service.ingest_batch(msgs_data)

    assert count == 1
    mock_meili_client.add_documents.assert_called_once()
    assert len(mock_meili_client.add_documents.call_args[0][0]) == 1
    assert mock_meili_client.add_documents.call_args[0][0][0]["text"] == "New message content"


def test_ingest_batch_no_dedup_on_failure(ingest_service, mock_meili_client):
    """Ensure failed batch doesn't advance dedup window."""
    msgs_data = [
        {
            "chat_id": 123,
            "msg_id": 1,
            "text": "First unique message content",
            "date": datetime.now(),
        },
        {
            "chat_id": 123,
            "msg_id": 2,
            "text": "Second unique message content",
            "date": datetime.now(),
        },
    ]

    mock_meili_client.add_documents.side_effect = Exception("Fail")
    count = ingest_service.ingest_batch(msgs_data)
    assert count == 0

    # Retry should still attempt to index the same messages
    mock_meili_client.add_documents.reset_mock()
    mock_meili_client.add_documents.side_effect = None
    count = ingest_service.ingest_batch(msgs_data)
    assert count == 2
    mock_meili_client.add_documents.assert_called_once()


def test_ingest_batch_raise_on_error(ingest_service, mock_meili_client):
    """Test ingest_batch raises when configured to."""
    msgs_data = [
        {
            "chat_id": 123,
            "msg_id": 1,
            "text": "Unique content",
            "date": datetime.now(),
        }
    ]

    mock_meili_client.add_documents.side_effect = Exception("Fail")
    with pytest.raises(Exception):
        ingest_service.ingest_batch(msgs_data, raise_on_error=True)


def test_ingest_batch_empty_text_filtered(ingest_service, mock_meili_client):
    """Test that messages with empty or whitespace-only text are filtered."""
    msgs_data = [
        {"chat_id": 123, "msg_id": 1, "text": "", "date": datetime.now()},
        {"chat_id": 123, "msg_id": 2, "text": "   ", "date": datetime.now()},
        {"chat_id": 123, "msg_id": 3, "text": None, "date": datetime.now()},
        {"chat_id": 123, "msg_id": 4, "text": "Valid message content", "date": datetime.now()},
    ]

    count = ingest_service.ingest_batch(msgs_data)

    assert count == 1
    mock_meili_client.add_documents.assert_called_once()
    docs = mock_meili_client.add_documents.call_args[0][0]
    assert len(docs) == 1
    assert docs[0]["msg_id"] == 4


def test_ingest_message_empty_text(ingest_service, mock_meili_client):
    """Test single message with empty text is skipped."""
    assert ingest_service.ingest_message(
        {"chat_id": 123, "msg_id": 1, "text": "", "date": datetime.now()}
    ) == IngestResult.SKIPPED

    assert ingest_service.ingest_message(
        {"chat_id": 123, "msg_id": 2, "text": "   ", "date": datetime.now()}
    ) == IngestResult.SKIPPED

    mock_meili_client.add_documents.assert_not_called()
