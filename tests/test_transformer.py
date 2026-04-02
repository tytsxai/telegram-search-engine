"""Tests for transformer module."""

from __future__ import annotations

from datetime import datetime, timezone

from telegram_search.pipeline.transformer import transform_message


def test_transform_message_basic():
    doc = transform_message(
        chat_id=123,
        msg_id=456,
        text="Hello World",
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        chat_title="Test Channel",
    )
    assert doc.id == "123_456"
    assert doc.chat_id == 123
    assert doc.msg_id == 456
    assert doc.text == "Hello World"
    assert doc.chat_title == "Test Channel"


def test_transform_message_generates_url():
    doc = transform_message(
        chat_id=1,
        msg_id=10,
        text="test",
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        chat_username="testchannel",
    )
    assert doc.url == "https://t.me/testchannel/10"


def test_transform_message_preserves_custom_url():
    doc = transform_message(
        chat_id=1,
        msg_id=10,
        text="test",
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        chat_username="testchannel",
        url="https://custom.url",
    )
    assert doc.url == "https://custom.url"


def test_transform_message_no_url_without_username():
    doc = transform_message(
        chat_id=1,
        msg_id=10,
        text="test",
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert doc.url is None


def test_transform_message_chinese():
    doc = transform_message(
        chat_id=1,
        msg_id=1,
        text="你好世界",
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert doc.text == "你好世界"
    assert doc.simp == "你好世界"
    assert doc.pinyin  # Should have pinyin representation
