"""Static data importer for JSON/CSV files."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterator


def import_json(path: Path) -> Iterator[dict]:
    """Import messages from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        yield from data


def import_csv(path: Path) -> Iterator[dict]:
    """Import messages from CSV file."""
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        yield from reader


def import_file(path: Path) -> Iterator[dict]:
    """Import from file based on extension."""
    if path.suffix == ".json":
        yield from import_json(path)
    elif path.suffix == ".csv":
        yield from import_csv(path)
