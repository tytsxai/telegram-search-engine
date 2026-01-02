"""Ingest service for Telegram messages."""

from __future__ import annotations

from collections import deque
from enum import Enum
from typing import Any, Deque, List

import structlog

from telegram_search.pipeline import deduper, transformer
from telegram_search.pipeline.filters import MessageFilter
from telegram_search.search.meili_client import MeiliClient
from telegram_search.logging import safe_error

logger = structlog.get_logger()


class IngestResult(str, Enum):
    """Result status for ingest_message."""

    INDEXED = "indexed"
    SKIPPED = "skipped"
    ERROR = "error"


class IngestService:
    """Service for ingesting messages into search index."""

    def __init__(
        self,
        meili_client: MeiliClient,
        message_filter: MessageFilter,
        dedup_window_size: int = 1000,
    ) -> None:
        """Initialize ingest service.

        Args:
            meili_client: Client for search index.
            message_filter: Filter for messages.
            dedup_window_size: Number of recent hashes to keep for deduplication.
        """
        self._client = meili_client
        self._filter = message_filter
        self._seen_hashes: Deque[str] = deque(maxlen=dedup_window_size)

    def _is_duplicate(self, simhash: str) -> bool:
        """Check if simhash is a near-duplicate of recently seen messages."""
        # Linear scan is acceptable for small window sizes (e.g. 1000).
        # For larger scales, a specialized index would be needed.
        for seen_hash in self._seen_hashes:
            if deduper.is_duplicate(simhash, seen_hash):
                return True
        return False

    def ingest_message(self, msg_data: dict[str, Any]) -> IngestResult:
        """Ingest a single message.

        Args:
            msg_data: Raw message dictionary.

        Returns:
            IngestResult indicating indexed, skipped, or error.
        """
        text = msg_data.get("text")
        if not isinstance(text, str) or not text.strip():
            return IngestResult.SKIPPED

        try:
            doc = transformer.transform_message(**msg_data)
        except Exception as e:
            logger.error("transform_error", msg_id=msg_data.get("msg_id"), **safe_error(e))
            return IngestResult.ERROR

        if not self._filter.apply_all(doc):
            return IngestResult.SKIPPED

        if self._is_duplicate(doc.simhash):
            logger.debug("duplicate_message_skipped", msg_id=doc.id)
            return IngestResult.SKIPPED

        try:
            self._client.add_documents([doc.to_index_dict()])
            self._seen_hashes.append(doc.simhash)
            return IngestResult.INDEXED
        except Exception as e:
            logger.error("index_error", msg_id=doc.id, **safe_error(e))
            return IngestResult.ERROR

    def ingest_batch(
        self,
        msgs_data: List[dict[str, Any]],
        *,
        raise_on_error: bool = False,
    ) -> int:
        """Ingest a batch of messages.

        Args:
            msgs_data: List of raw message dictionaries.
            raise_on_error: Whether to raise on indexing failures.

        Returns:
            Number of messages successfully indexed.
        """
        docs_to_index: List[dict[str, Any]] = []
        batch_hashes: List[str] = []

        for msg_data in msgs_data:
            text = msg_data.get("text")
            if not isinstance(text, str) or not text.strip():
                continue

            try:
                doc = transformer.transform_message(**msg_data)
            except Exception as e:
                logger.error("transform_error", msg_id=msg_data.get("msg_id"), **safe_error(e))
                continue

            if not self._filter.apply_all(doc):
                continue

            if self._is_duplicate(doc.simhash):
                logger.debug("duplicate_message_skipped", msg_id=doc.id)
                continue

            # Check duplicates within current batch
            is_batch_dup = any(
                deduper.is_duplicate(doc.simhash, seen_hash)
                for seen_hash in batch_hashes
            )
            if is_batch_dup:
                logger.debug("duplicate_message_skipped", msg_id=doc.id)
                continue

            # Add to list and update batch state immediately to dedupe within batch
            docs_to_index.append(doc.to_index_dict())
            batch_hashes.append(doc.simhash)

        if not docs_to_index:
            return 0

        try:
            self._client.add_documents(docs_to_index)
            # Update local state only after successful indexing
            for simhash in batch_hashes:
                self._seen_hashes.append(simhash)
            return len(docs_to_index)
        except Exception as e:
            logger.error("batch_index_error", count=len(docs_to_index), **safe_error(e))
            if raise_on_error:
                raise
            return 0
