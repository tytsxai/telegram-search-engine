"""State management for incremental indexing."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


class StateStore:
    """Persist synchronization state for channels."""

    def __init__(
        self,
        file_path: str | Path = "state.json",
        flush_interval: float = 0.0,
    ) -> None:
        """Initialize state store.

        Args:
            file_path: Path to the JSON state file.
            flush_interval: Minimum seconds between disk writes. 0 means immediate.
        """
        self.file_path = Path(file_path)
        self.flush_interval = max(flush_interval, 0.0)
        self._state: dict[str, Any] = {}
        self._dirty = False
        self._last_flush = 0.0
        self._load()

    def _load(self) -> None:
        """Load state from file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._state = json.load(f)
            except json.JSONDecodeError:
                self._state = {}
                # Preserve corrupted file for inspection
                corrupt_path = self.file_path.with_suffix(self.file_path.suffix + ".corrupt")
                try:
                    os.replace(self.file_path, corrupt_path)
                except OSError:
                    pass
        else:
            self._state = {}
        self._last_flush = time.monotonic()

    def _save(self) -> None:
        """Save state to file."""
        # Ensure directory exists
        if self.file_path.parent != Path("."):
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = self.file_path.with_suffix(self.file_path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2)
        os.replace(tmp_path, self.file_path)
        self._last_flush = time.monotonic()
        self._dirty = False

    def get_state(self, channel_id: str | int) -> int:
        """Get last synchronized message ID for a channel.

        Args:
            channel_id: Channel identifier.

        Returns:
            Last message ID or 0 if not found.
        """
        key = str(channel_id)
        return self._state.get(key, {}).get("last_msg_id", 0)

    def set_state(self, channel_id: str | int, msg_id: int) -> None:
        """Set last synchronized message ID for a channel.

        Args:
            channel_id: Channel identifier.
            msg_id: Last message ID.
        """
        key = str(channel_id)
        if key not in self._state:
            self._state[key] = {}
        
        # Only update if new ID is greater than existing
        current_id = self._state[key].get("last_msg_id", 0)
        if msg_id > current_id:
            self._state[key]["last_msg_id"] = msg_id
            self._dirty = True
            if self.flush_interval <= 0:
                self._save()
            else:
                now = time.monotonic()
                if now - self._last_flush >= self.flush_interval:
                    self._save()

    def flush(self) -> None:
        """Force persist state to disk."""
        if self._dirty:
            self._save()
