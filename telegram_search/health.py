"""CLI health checks for production readiness."""

from __future__ import annotations

import argparse
import sys

from telegram_search.config import load_config
from telegram_search.logging import get_logger, safe_error, setup_logging
from telegram_search.runtime import (
    check_optional_redis,
    validate_channels_config,
    check_writable_path,
    create_search_backend,
    validate_runtime_config,
)

logger = get_logger(__name__)


def run_healthcheck(component: str) -> int:
    """Run a health check for the given component."""
    config = load_config()
    setup_logging(config.debug)

    try:
        validate_runtime_config(config, component=component)
        create_search_backend(config).health()
        if component == "bot":
            check_optional_redis(config)
        if component == "crawler":
            validate_channels_config(config.indexer.channels_path)
            check_writable_path(config.telegram.session_path)
            check_writable_path(config.indexer.state_path)
            check_writable_path(config.indexer.channels_path)
    except Exception as e:
        logger.error("healthcheck_failed", component=component, **safe_error(e))
        return 1

    logger.info("healthcheck_ok", component=component)
    return 0


def main() -> None:
    """Run the health check CLI."""
    parser = argparse.ArgumentParser(description="Telegram Search health check")
    parser.add_argument("--component", choices=["bot", "crawler"], required=True)
    args = parser.parse_args()
    sys.exit(run_healthcheck(args.component))


if __name__ == "__main__":
    main()
