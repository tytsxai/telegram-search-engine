"""Chinese text tokenizer using Jieba with HMM disabled."""

from __future__ import annotations

import jieba


def segment(text: str, use_hmm: bool = False) -> list[str]:
    """Segment Chinese text into tokens.

    Args:
        text: Input text to segment
        use_hmm: Whether to use HMM for unknown words (default False)

    Returns:
        List of tokens
    """
    if not text or not text.strip():
        return []

    return list(jieba.cut(text, HMM=use_hmm))


def segment_search(text: str, use_hmm: bool = False) -> list[str]:
    """Segment text for search with finer granularity.

    Args:
        text: Input text to segment
        use_hmm: Whether to use HMM (default False)

    Returns:
        List of tokens optimized for search
    """
    if not text or not text.strip():
        return []

    return list(jieba.cut_for_search(text, HMM=use_hmm))
