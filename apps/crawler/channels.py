"""Channel management CLI."""

import argparse
import logging

from telegram_search.config import load_config
from telegram_search.indexer.channel_registry import Channel, ChannelRegistry

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Channel Manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # add
    add_p = sub.add_parser("add", help="Add channel")
    add_p.add_argument("channel_id", type=int)
    add_p.add_argument("--username", default="")
    add_p.add_argument("--title", default="")

    # remove
    rm_p = sub.add_parser("remove", help="Remove channel")
    rm_p.add_argument("channel_id", type=int)

    # list
    sub.add_parser("list", help="List channels")

    args = parser.parse_args()
    config = load_config()
    registry = ChannelRegistry(config.indexer.channels_path)

    if args.cmd == "add":
        registry.add_channel(args.channel_id, args.username, args.title)
        logger.info("Added: %s", args.channel_id)
    elif args.cmd == "remove":
        registry.remove_channel(args.channel_id)
        logger.info("Removed: %s", args.channel_id)
    elif args.cmd == "list":
        channels: list[Channel] = registry.list_channels()
        for c in channels:
            status = "enabled" if c.enabled else "disabled"
            logger.info("[%s] %s @%s - %s", status, c.channel_id, c.username, c.title)


if __name__ == "__main__":
    main()
