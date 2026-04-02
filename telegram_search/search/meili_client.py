"""Meilisearch client wrapper."""

from __future__ import annotations

import functools
import time
from collections.abc import Mapping
from typing import Any, Callable, TypeVar

import meilisearch
from meilisearch.errors import MeilisearchApiError
from telegram_search.config import MeilisearchConfig
from telegram_search.logging import get_logger, safe_error

logger = get_logger(__name__)

T = TypeVar("T")


def with_retry(func: Callable[..., T]) -> Callable[..., T]:
    """Retry decorator with exponential backoff (async-compatible)."""

    @functools.wraps(func)
    def wrapper(self: MeiliClient, *args: Any, **kwargs: Any) -> T:
        retries = 0
        while True:
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if retries >= self._max_retries:
                    logger.error(
                        "meili_request_failed",
                        method=func.__name__,
                        **safe_error(e),
                        retries=retries,
                    )
                    raise

                wait_time = (2**retries) * 0.1
                logger.warning(
                    "meili_retry_attempt",
                    method=func.__name__,
                    attempt=retries + 1,
                    wait_time=wait_time,
                    **safe_error(e),
                )
                time.sleep(wait_time)
                retries += 1

    return wrapper


class MeiliClient:
    """Wrapper for Meilisearch operations."""

    def __init__(self, config: MeilisearchConfig) -> None:
        """Initialize client with config."""
        self._client = meilisearch.Client(
            config.host,
            config.api_key,
            timeout=config.timeout,
        )
        self._index_name = config.index_name
        self._index = self._client.index(self._index_name)
        self._max_retries = config.max_retries

    def _wait_for_task(self, task: Any) -> None:
        """Wait for an async Meilisearch task when task info is available."""
        wait_for_task = getattr(self._client, "wait_for_task", None)
        if not callable(wait_for_task):
            return

        task_uid: Any = None
        if isinstance(task, Mapping):
            task_uid = task.get("taskUid") or task.get("uid")
        else:
            task_uid = getattr(task, "task_uid", None) or getattr(task, "uid", None)

        if task_uid is not None:
            wait_for_task(task_uid)

    def create_index(self) -> None:
        """Create index if not exists."""
        try:
            task = self._client.create_index(self._index_name, {"primaryKey": "id"})
            self._wait_for_task(task)
        except MeilisearchApiError as e:
            if "index_already_exists" not in str(e).lower():
                raise
            logger.info("meili_index_already_exists", index=self._index_name)

    @with_retry
    def configure_index(self, settings: dict[str, Any]) -> None:
        """Update index settings."""
        task = self._index.update_settings(settings)
        self._wait_for_task(task)

    @with_retry
    def health(self) -> None:
        """Validate Meilisearch connectivity."""
        health_check = getattr(self._client, "health", None)
        if callable(health_check):
            health_check()
            return
        self._client.get_version()

    def ensure_index(self, settings: dict[str, Any] | None = None) -> None:
        """Ensure index exists and baseline settings are applied."""
        self.health()
        self.create_index()
        if settings:
            self.configure_index(settings)

    @with_retry
    def add_documents(self, docs: list[dict[str, Any]]) -> None:
        """Add documents to index."""
        if docs:
            self._index.add_documents(docs)

    @with_retry
    def search(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        filters: str | list[str] | None = None,
        sort: list[str] | None = None,
    ) -> dict[str, Any]:
        """Search documents."""
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }
        if filters:
            params["filter"] = filters
        if sort:
            params["sort"] = sort
        return self._index.search(query, params)
