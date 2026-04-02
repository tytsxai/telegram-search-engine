"""Pytest fixtures and configuration."""

from pathlib import Path
import sys

import pytest
from telegram_search.config import AppConfig

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def app_config() -> AppConfig:
    """Provide test configuration."""
    return AppConfig()
