"""Message filtering logic."""

from __future__ import annotations

from telegram_search.models.message import MessageDoc


class MessageFilter:
    """Filter messages based on content and metadata."""

    def filter_empty(self, message: MessageDoc) -> bool:
        """Filter out empty messages.
        
        Args:
            message: Message to check.
            
        Returns:
            True if message is not empty.
        """
        if not message.text:
            return False
        return bool(message.text.strip())

    def filter_service_messages(self, message: MessageDoc) -> bool:
        """Filter out service messages.
        
        Args:
            message: Message to check.
            
        Returns:
            True if message is not a service message.
        """
        # Service messages typically have empty text or specific media types
        # Since we receive a MessageDoc, we check available fields.
        # Telethon usually filters service messages without text before here.
        # We add this check for robustness.
        if message.media_type == "service":
            return False
            
        # If text is present, we assume it's a valid message for now.
        # Future: Check for specific service message patterns if needed.
        return True

    def filter_by_length(self, message: MessageDoc, min_len: int = 5) -> bool:
        """Filter out messages that are too short.
        
        Args:
            message: Message to check.
            min_len: Minimum text length.
            
        Returns:
            True if message satisfies length requirement.
        """
        if not message.text:
            return False
        return len(message.text.strip()) >= min_len

    def apply_all(self, message: MessageDoc, min_len: int = 5) -> bool:
        """Apply all filters.
        
        Args:
            message: Message to check.
            min_len: Minimum text length for length filter.
            
        Returns:
            True if message passes all filters.
        """
        return (
            self.filter_empty(message)
            and self.filter_service_messages(message)
            and self.filter_by_length(message, min_len=min_len)
        )
