"""Tests for StateStore."""

import json
from pathlib import Path
from telegram_search.indexer.state_store import StateStore


def test_state_store_init(tmp_path: Path) -> None:
    """Test initialization with empty state."""
    f = tmp_path / "state.json"
    store = StateStore(f, flush_interval=0)
    assert store.get_state("test_channel") == 0


def test_state_store_set_get(tmp_path: Path) -> None:
    """Test setting and getting state."""
    f = tmp_path / "state.json"
    store = StateStore(f, flush_interval=0)
    store.set_state("ch1", 100)
    assert store.get_state("ch1") == 100

    # Should persist
    with open(f, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    assert data["ch1"]["last_msg_id"] == 100


def test_state_store_load(tmp_path: Path) -> None:
    """Test loading existing state."""
    f = tmp_path / "state.json"
    data = {"ch1": {"last_msg_id": 50}}
    with open(f, "w", encoding="utf-8") as fp:
        json.dump(data, fp)

    store = StateStore(f, flush_interval=0)
    assert store.get_state("ch1") == 50


def test_state_store_incremental_only(tmp_path: Path) -> None:
    """Test that state only increases."""
    f = tmp_path / "state.json"
    store = StateStore(f, flush_interval=0)
    store.set_state("ch1", 100)
    store.set_state("ch1", 50)  # Should be ignored
    assert store.get_state("ch1") == 100
