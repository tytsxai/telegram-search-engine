"""Near-duplicate detection using Simhash."""

from __future__ import annotations

from simhash import Simhash


def compute_simhash(text: str) -> str:
    """Compute simhash fingerprint for text.

    Args:
        text: Input text

    Returns:
        Hex string of simhash value
    """
    if not text or not text.strip():
        return "0"

    return hex(Simhash(text).value)


def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculate Hamming distance between two simhash values.

    Args:
        hash1: First simhash hex string
        hash2: Second simhash hex string

    Returns:
        Hamming distance (number of differing bits)
    """
    val1 = int(hash1, 16) if hash1 != "0" else 0
    val2 = int(hash2, 16) if hash2 != "0" else 0
    return bin(val1 ^ val2).count("1")


def is_duplicate(hash1: str, hash2: str, threshold: int = 3) -> bool:
    """Check if two texts are near-duplicates.

    Args:
        hash1: First simhash
        hash2: Second simhash
        threshold: Max Hamming distance for duplicates

    Returns:
        True if texts are near-duplicates
    """
    return hamming_distance(hash1, hash2) <= threshold
