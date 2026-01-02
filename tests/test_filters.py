"""Tests for message filtering."""

from datetime import datetime

import pytest

from telegram_search.models.message import MessageDoc
from telegram_search.pipeline.filters import MessageFilter


@pytest.fixture
def filter_service() -> MessageFilter:
    return MessageFilter()


@pytest.fixture
def sample_message() -> MessageDoc:
    return MessageDoc(
        id="123_456",
        chat_id=123,
        msg_id=456,
        date=datetime.now(),
        text="Hello world",
        text_norm="hello world",
        pinyin="hello world",
        simhash="abc",
    )


def test_filter_empty(filter_service: MessageFilter, sample_message: MessageDoc):
    """Test filtering of empty messages."""
    assert filter_service.filter_empty(sample_message) is True

    sample_message.text = ""
    assert filter_service.filter_empty(sample_message) is False

    sample_message.text = "   "
    assert filter_service.filter_empty(sample_message) is False
    
    sample_message.text = None # type: ignore
    assert filter_service.filter_empty(sample_message) is False


def test_filter_service_messages(filter_service: MessageFilter, sample_message: MessageDoc):
    """Test filtering of service messages."""
    assert filter_service.filter_service_messages(sample_message) is True

    sample_message.media_type = "service"
    assert filter_service.filter_service_messages(sample_message) is False


def test_filter_by_length(filter_service: MessageFilter, sample_message: MessageDoc):
    """Test filtering by length."""
    sample_message.text = "Hi"
    assert filter_service.filter_by_length(sample_message, min_len=5) is False

    sample_message.text = "Hello"
    assert filter_service.filter_by_length(sample_message, min_len=5) is True
    
    sample_message.text = ""
    assert filter_service.filter_by_length(sample_message, min_len=5) is False


def test_apply_all(filter_service: MessageFilter, sample_message: MessageDoc):
    """Test applying all filters."""
    # Valid message
    assert filter_service.apply_all(sample_message) is True

    # Too short
    sample_message.text = "Hi"
    assert filter_service.apply_all(sample_message) is False

    # Empty
    sample_message.text = ""
    assert filter_service.apply_all(sample_message) is False
    
    # Service message
    sample_message.text = "Valid text"
    sample_message.media_type = "service"
    assert filter_service.apply_all(sample_message) is False
