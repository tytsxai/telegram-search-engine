"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def setup_logging(debug: bool = False) -> None:
    """Configure structured logging."""
    level = logging.DEBUG if debug else logging.INFO

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
            if debug
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance."""
    return structlog.get_logger(name)


def safe_error(err: Exception) -> dict[str, Any]:
    """Return a minimal, non-sensitive error payload for logging."""
    payload: dict[str, Any] = {"error_type": type(err).__name__}
    for attr in ("status_code", "code", "errno"):
        value = getattr(err, attr, None)
        if value is not None:
            payload[attr] = value
    return payload
