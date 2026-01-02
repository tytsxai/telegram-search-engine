"""Transform raw messages to indexed documents."""

from __future__ import annotations

from datetime import datetime

from telegram_search.models.message import MessageDoc
from telegram_search.pipeline import normalizer, deduper


def transform_message(
    chat_id: int,
    msg_id: int,
    text: str,
    date: datetime,
    chat_title: str = "",
    chat_username: str = "",
    url: str | None = None,
    media_type: str | None = None,
) -> MessageDoc:
    """Transform raw message to MessageDoc."""
    text_norm = normalizer.normalize(text)
    simp = normalizer.to_simplified(text_norm)
    trad = normalizer.to_traditional(text_norm)
    pinyin = normalizer.to_pinyin(simp)
    simhash = deduper.compute_simhash(text_norm)

    # Generate permalink if username available
    if not url and chat_username:
        url = f"https://t.me/{chat_username}/{msg_id}"

    return MessageDoc(
        id=f"{chat_id}_{msg_id}",
        chat_id=chat_id,
        chat_title=chat_title,
        chat_username=chat_username,
        msg_id=msg_id,
        date=date,
        text=text,
        text_norm=text_norm,
        pinyin=pinyin,
        trad=trad,
        simp=simp,
        simhash=simhash,
        url=url,
        media_type=media_type,
    )
