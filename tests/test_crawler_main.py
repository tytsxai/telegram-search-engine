"""Tests for crawler entrypoint helpers."""

from __future__ import annotations

from apps.crawler.main import enrich_message_with_channel
from telegram_search.indexer.channel_registry import Channel


def test_enrich_message_with_channel_fills_missing_metadata() -> None:
    msg = {"chat_id": -1001, "msg_id": 1, "text": "hello"}
    channel = Channel(channel_id=-1001, username="testchannel", title="Test Channel")

    enriched = enrich_message_with_channel(msg, channel)

    assert enriched["chat_title"] == "Test Channel"
    assert enriched["chat_username"] == "testchannel"


def test_enrich_message_with_channel_preserves_existing_metadata() -> None:
    msg = {
        "chat_id": -1001,
        "msg_id": 1,
        "text": "hello",
        "chat_title": "From Telethon",
        "chat_username": "telethonname",
    }
    channel = Channel(channel_id=-1001, username="registryname", title="Registry Title")

    enriched = enrich_message_with_channel(msg, channel)

    assert enriched["chat_title"] == "From Telethon"
    assert enriched["chat_username"] == "telethonname"
