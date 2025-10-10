"""Tests for text processing utilities."""

from app.utils.text_processing import normalize_text


def test_normalize_text_basic():
    """Test basic text normalization."""
    result = normalize_text("Hello, World!")
    assert result == ["hello", "world"]


def test_normalize_text_punctuation():
    """Test normalization removes punctuation."""
    result = normalize_text("Machine Learning & AI")
    assert result == ["machine", "learning", "ai"]


def test_normalize_text_empty():
    """Test normalization with empty string."""
    result = normalize_text("")
    assert result == []


def test_normalize_text_none():
    """Test normalization with None."""
    result = normalize_text(None)
    assert result == []


def test_normalize_text_whitespace():
    """Test normalization handles extra whitespace."""
    result = normalize_text("  Python   programming  ")
    assert result == ["python", "programming"]


def test_normalize_text_lowercase():
    """Test normalization converts to lowercase."""
    result = normalize_text("PYTHON Programming")
    assert result == ["python", "programming"]


def test_normalize_text_special_chars():
    """Test normalization handles special characters."""
    result = normalize_text("user@example.com, test-data!")
    assert result == ["user", "example", "com", "test", "data"]
