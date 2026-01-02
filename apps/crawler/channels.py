"""Channel management CLI."""

import argparse
from telegram_search.indexer.channel_registry import ChannelRegistry


def main():
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
    registry = ChannelRegistry()

    if args.cmd == "add":
        registry.add_channel(args.channel_id, args.username, args.title)
        print(f"Added: {args.channel_id}")
    elif args.cmd == "remove":
        registry.remove_channel(args.channel_id)
        print(f"Removed: {args.channel_id}")
    elif args.cmd == "list":
        for c in registry.list_channels():
            status = "✓" if c.enabled else "✗"
            print(f"[{status}] {c.channel_id} @{c.username} - {c.title}")


if __name__ == "__main__":
    main()
