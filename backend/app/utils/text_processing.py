"""
Text processing utilities for content normalization and keyword matching.

This module provides text normalization functions used across the application
for consistent keyword matching and content processing.
"""

import re


def normalize_text(text: str) -> list[str]:
    """
    Normalize text for keyword matching.

    Converts to lowercase, removes punctuation, splits into tokens.
    Used for consistent text processing across relevance scoring and
    keyword parsing.

    Args:
        text: Raw text to normalize

    Returns:
        List of normalized tokens (empty list if text is empty)

    Example:
        >>> normalize_text("Hello, World!")
        ['hello', 'world']
        >>> normalize_text("Machine Learning & AI")
        ['machine', 'learning', 'ai']
    """
    if not text:
        return []
    text_lower = text.lower()
    text_clean = re.sub(r"[^\w\s]", " ", text_lower)
    return [token for token in text_clean.split() if token]


def normalize_term_list(terms: list[str], max_terms: int = 50) -> list[str]:
    """
    Normalize a list of free-form terms for downstream processing.

    Cleans each term, removes duplicates while preserving order, and applies an
    optional limit on the number of returned terms.

    Args:
        terms: Raw terms to normalize
        max_terms: Maximum number of normalized terms to return

    Returns:
        Normalized list of unique terms trimmed to max_terms
    """
    if not terms:
        return []

    normalized_terms = []
    seen = set()

    for term in terms:
        tokens = normalize_text(term)
        if not tokens:
            continue

        normalized_term = " ".join(tokens)
        if normalized_term in seen:
            continue

        normalized_terms.append(normalized_term)
        seen.add(normalized_term)

    return normalized_terms[:max_terms]
