"""Text normalizer with Chinese support."""

from __future__ import annotations

import re
import unicodedata

from opencc import OpenCC
from pypinyin import lazy_pinyin, Style


# Initialize converters
_s2t = OpenCC("s2t")  # Simplified to Traditional
_t2s = OpenCC("t2s")  # Traditional to Simplified


def normalize_unicode(text: str) -> str:
    """Normalize Unicode characters to NFC form."""
    return unicodedata.normalize("NFC", text)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace characters."""
    return re.sub(r"\s+", " ", text).strip()


def to_simplified(text: str) -> str:
    """Convert Traditional Chinese to Simplified."""
    return _t2s.convert(text)


def to_traditional(text: str) -> str:
    """Convert Simplified Chinese to Traditional."""
    return _s2t.convert(text)


def to_pinyin(text: str) -> str:
    """Convert Chinese text to pinyin."""
    return " ".join(lazy_pinyin(text, style=Style.NORMAL))


def normalize(text: str) -> str:
    """Apply full normalization pipeline."""
    if not text:
        return ""
    text = normalize_unicode(text)
    text = normalize_whitespace(text)
    return text
