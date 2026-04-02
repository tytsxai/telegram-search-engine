"""Tests for runtime readiness helpers."""

from __future__ import annotations

import json

import pytest

from telegram_search.config import AppConfig
from telegram_search.runtime import check_writable_path, load_meili_settings, validate_runtime_config


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
