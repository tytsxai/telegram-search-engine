"""Tests for runtime readiness helpers."""

from __future__ import annotations

import json

import pytest

from telegram_search.config import AppConfig
from telegram_search.runtime import (
    check_writable_path,
    load_meili_settings,
    validate_channels_config,
    validate_runtime_config,
)


def test_load_meili_settings(tmp_path) -> None:
    path = tmp_path / "meili.json"
    path.write_text(json.dumps({"filterableAttributes": ["chat_username"]}), encoding="utf-8")

    settings = load_meili_settings(path)

    assert settings["filterableAttributes"] == ["chat_username"]


def test_check_writable_path_creates_parent(tmp_path) -> None:
    target = tmp_path / "nested" / "state.json"

    check_writable_path(target)

    assert target.parent.exists()


def test_validate_runtime_config_requires_production_secrets() -> None:
    config = AppConfig(
        environment="production",
        telegram={"bot_token": "token", "api_id": 1, "api_hash": "hash"},
    )

    with pytest.raises(ValueError, match="MEILI_MASTER_KEY"):
        validate_runtime_config(config, component="bot")


def test_validate_runtime_config_for_crawler_requires_api_credentials() -> None:
    config = AppConfig()

    with pytest.raises(ValueError, match="TELEGRAM_API_ID"):
        validate_runtime_config(config, component="crawler")


def test_validate_channels_config_requires_at_least_one_channel(tmp_path) -> None:
    path = tmp_path / "channels.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="No channels configured"):
        validate_channels_config(path)


def test_validate_channels_config_requires_enabled_channel(tmp_path) -> None:
    path = tmp_path / "channels.json"
    path.write_text(
        json.dumps(
            [
                {
                    "channel_id": -1001,
                    "username": "disabled",
                    "title": "Disabled",
                    "enabled": False,
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="No enabled channels"):
        validate_channels_config(path)
