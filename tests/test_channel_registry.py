"""Tests for channel registry."""

import json
from datetime import datetime

import pytest

from telegram_search.indexer.channel_registry import Channel, ChannelRegistry


@pytest.fixture
def temp_config_path(tmp_path):
    """Create a temporary config file path."""
    return tmp_path / "channels.json"


def test_channel_model():
    """Test Channel model creation and serialization."""
    now = datetime.now()
    channel = Channel(
        channel_id=123,
        username="test_channel",
        title="Test Channel",
        added_at=now
    )
    
    assert channel.channel_id == 123
    assert channel.username == "test_channel"
    assert channel.title == "Test Channel"
    assert channel.enabled is True
    assert channel.added_at == now

    # Test serialization
    data = channel.model_dump_json_compatible()
    assert data["channel_id"] == 123
    assert isinstance(data["added_at"], str)

    # Test deserialization
    loaded = Channel.model_validate_json_compatible(data)
    assert loaded.channel_id == 123
    assert loaded.added_at == now


def test_registry_add_channel(temp_config_path):
    """Test adding channels to registry."""
    registry = ChannelRegistry(config_path=temp_config_path)
    
    channel = registry.add_channel(1, "chan1", "Channel 1")
    assert channel.channel_id == 1
    assert channel.username == "chan1"
    assert channel.title == "Channel 1"
    
    # Check if saved to file
    assert temp_config_path.exists()
    with open(temp_config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["channel_id"] == 1


def test_registry_update_channel(temp_config_path):
    """Test updating existing channel."""
    registry = ChannelRegistry(config_path=temp_config_path)
    
    # Add initial
    registry.add_channel(1, "chan1", "Channel 1")
    
    # Update
    updated = registry.add_channel(1, "chan1_new", "Channel 1 New")
    
    assert updated.channel_id == 1
    assert updated.username == "chan1_new"
    assert updated.title == "Channel 1 New"
    
    # Verify persistence
    registry2 = ChannelRegistry(config_path=temp_config_path)
    loaded = registry2.get_channel(1)
    assert loaded.username == "chan1_new"
    assert loaded.title == "Channel 1 New"


def test_registry_remove_channel(temp_config_path):
    """Test removing channels."""
    registry = ChannelRegistry(config_path=temp_config_path)
    registry.add_channel(1, "chan1", "Channel 1")
    
    assert registry.remove_channel(1) is True
    assert registry.get_channel(1) is None
    assert registry.remove_channel(1) is False
    
    # Verify file is empty list
    with open(temp_config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 0


def test_registry_list_channels(temp_config_path):
    """Test listing channels."""
    registry = ChannelRegistry(config_path=temp_config_path)
    registry.add_channel(1, "chan1", "Channel 1")
    registry.add_channel(2, "chan2", "Channel 2")
    
    channels = registry.list_channels()
    assert len(channels) == 2
    ids = {c.channel_id for c in channels}
    assert ids == {1, 2}


def test_registry_persistence(temp_config_path):
    """Test data persistence across registry instances."""
    # Create initial data
    registry1 = ChannelRegistry(config_path=temp_config_path)
    registry1.add_channel(1, "chan1", "Channel 1")
    
    # Load in new instance
    registry2 = ChannelRegistry(config_path=temp_config_path)
    channel = registry2.get_channel(1)
    
    assert channel is not None
    assert channel.username == "chan1"


def test_registry_invalid_channel_id(temp_config_path):
    """Test invalid channel ID handling."""
    registry = ChannelRegistry(config_path=temp_config_path)

    with pytest.raises(ValueError):
        registry.add_channel(0, "chan0", "Invalid")

    with pytest.raises(ValueError):
        registry.remove_channel(-1)

    with pytest.raises(ValueError):
        registry.get_channel(0)
