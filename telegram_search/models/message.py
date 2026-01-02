"""Message document model for search indexing."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MessageDoc(BaseModel):
    """Document model for indexed Telegram messages."""

    id: str = Field(..., description="Unique document ID")
    chat_id: int = Field(..., description="Telegram chat ID")
    chat_title: str = Field(default="", description="Chat title")
    chat_username: str = Field(default="", description="Chat username")
    msg_id: int = Field(..., description="Message ID in chat")
    date: datetime = Field(..., description="Message timestamp")
    text: str = Field(default="", description="Original text")
    text_norm: str = Field(default="", description="Normalized text")
    pinyin: str = Field(default="", description="Pinyin representation")
    trad: str = Field(default="", description="Traditional Chinese")
    simp: str = Field(default="", description="Simplified Chinese")
    simhash: str = Field(default="", description="Simhash fingerprint")
    url: Optional[str] = Field(default=None, description="Message URL")
    media_type: Optional[str] = Field(default=None)

    def to_index_dict(self) -> dict:
        """Convert to dictionary for Meilisearch indexing."""
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "chat_title": self.chat_title,
            "chat_username": self.chat_username,
            "msg_id": self.msg_id,
            "date": int(self.date.timestamp()),
            "text": self.text,
            "text_norm": self.text_norm,
            "pinyin": self.pinyin,
            "trad": self.trad,
            "simp": self.simp,
            "simhash": self.simhash,
            "url": self.url,
            "media_type": self.media_type,
        }
