"""Channel registry management."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from telegram_search.logging import get_logger, safe_error

logger = get_logger(__name__)

class Channel(BaseModel):
    """Channel model."""

    channel_id: int = Field(..., description="Telegram channel ID")
    username: str = Field(..., description="Channel username")
    title: str = Field(..., description="Channel title")
    enabled: bool = Field(default=True, description="Whether channel is enabled")
    added_at: datetime = Field(default_factory=datetime.now, description="Date added")

    def model_dump_json_compatible(self) -> dict:
        """Dump model to JSON compatible dictionary."""
        data = self.model_dump()
        data["added_at"] = self.added_at.isoformat()
        return data

    @classmethod
    def model_validate_json_compatible(cls, data: dict) -> Channel:
        """Validate from JSON compatible dictionary."""
        if isinstance(data.get("added_at"), str):
            data["added_at"] = datetime.fromisoformat(data["added_at"])
        return cls.model_validate(data)


class ChannelRegistry:
    """Registry for managing monitored channels."""

    def __init__(self, config_path: str | Path = "configs/channels.json"):
        """Initialize registry with config path."""
        self.config_path = Path(config_path)
        self._channels: dict[int, Channel] = {}
        self._load()

    def _load(self) -> None:
        """Load channels from config file."""
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    channel = Channel.model_validate_json_compatible(item)
                    self._channels[channel.channel_id] = channel
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("channel_registry_load_failed", **safe_error(e))

    def _save(self) -> None:
        """Save channels to config file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = [c.model_dump_json_compatible() for c in self._channels.values()]
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_channel(self, channel_id: int, username: str, title: str) -> Channel:
        """Add a new channel to registry.
        
        Args:
            channel_id: Telegram channel ID
            username: Channel username
            title: Channel title
            
        Returns:
            Created Channel object
        """
        if channel_id <= 0:
            raise ValueError("channel_id must be a positive integer")

        if channel_id in self._channels:
            # Update existing channel details but keep other fields
            existing = self._channels[channel_id]
            existing.username = username
            existing.title = title
            self._save()
            return existing

        channel = Channel(
            channel_id=channel_id,
            username=username,
            title=title
        )
        self._channels[channel_id] = channel
        self._save()
        return channel

    def remove_channel(self, channel_id: int) -> bool:
        """Remove a channel from registry.
        
        Args:
            channel_id: Channel ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if channel_id <= 0:
            raise ValueError("channel_id must be a positive integer")

        if channel_id in self._channels:
            del self._channels[channel_id]
            self._save()
            return True
        return False

    def list_channels(self) -> List[Channel]:
        """List all registered channels.
        
        Returns:
            List of Channel objects
        """
        return list(self._channels.values())

    def get_channel(self, channel_id: int) -> Optional[Channel]:
        """Get channel details.
        
        Args:
            channel_id: Channel ID
            
        Returns:
            Channel object or None if not found
        """
        if channel_id <= 0:
            raise ValueError("channel_id must be a positive integer")
        return self._channels.get(channel_id)
