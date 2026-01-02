"""Pytest fixtures and configuration."""

import pytest
from telegram_search.config import AppConfig


@pytest.fixture
def app_config() -> AppConfig:
    """Provide test configuration."""
    return AppConfig()
