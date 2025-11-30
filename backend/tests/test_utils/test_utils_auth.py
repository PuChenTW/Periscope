"""Tests for authentication utilities."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from app.config import get_settings
from app.utils.auth import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)


# Password Hashing Tests
def test_password_hashing():
    """Test password is properly hashed and cannot be reversed."""
    plain_password = "mysecurepassword123"
    hashed = get_password_hash(plain_password)

    assert hashed != plain_password
    assert len(hashed) > 20
    assert hashed.startswith("$2b$")  # bcrypt prefix


def test_password_hashing_different_each_time():
    """Test same password produces different hashes (salt varies)."""
    password = "samepassword"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    assert hash1 != hash2


def test_verify_password_correct():
    """Test password verification succeeds with correct password."""
    plain_password = "correctpassword"
    hashed = get_password_hash(plain_password)

    assert verify_password(plain_password, hashed) is True


def test_verify_password_incorrect():
    """Test password verification fails with wrong password."""
    plain_password = "correctpassword"
    hashed = get_password_hash(plain_password)

    assert verify_password("wrongpassword", hashed) is False


def test_verify_password_empty():
    """Test password verification handles empty passwords."""
    hashed = get_password_hash("password")

    assert verify_password("", hashed) is False


# JWT Token Tests
def test_create_access_token():
    """Test JWT token creation includes required claims."""
    settings = get_settings()
    user_id = "user_123"
    email = "test@example.com"

    token = create_access_token(user_id, email)

    assert isinstance(token, str)
    assert len(token) > 20

    # Decode without verification to inspect payload
    payload = jwt.decode(token, settings.security.secret_key, algorithms=["HS256"])
    assert payload["sub"] == user_id
    assert payload["email"] == email
    assert "exp" in payload
    assert "iat" in payload


def test_create_access_token_expiration():
    """Test JWT token has correct expiration time."""
    settings = get_settings()
    token = create_access_token("user_123", "test@example.com")

    payload = jwt.decode(token, settings.security.secret_key, algorithms=["HS256"])

    exp_timestamp = payload["exp"]
    iat_timestamp = payload["iat"]

    exp_time = datetime.fromtimestamp(exp_timestamp, tz=UTC)
    iat_time = datetime.fromtimestamp(iat_timestamp, tz=UTC)

    time_diff = exp_time - iat_time

    # Should match configured JWT expiration (convert to seconds for comparison)
    expected_seconds = settings.security.jwt_expire_minutes * 60
    assert abs(time_diff.total_seconds() - expected_seconds) < 5


def test_decode_token_valid():
    """Test decoding a valid JWT token."""
    user_id = "user_456"
    email = "decode@example.com"
    token = create_access_token(user_id, email)

    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["email"] == email


def test_decode_token_invalid():
    """Test decoding an invalid token raises HTTPException."""
    invalid_token = "invalid.token.here"

    with pytest.raises(HTTPException) as exc_info:
        decode_token(invalid_token)

    assert exc_info.value.status_code == 401
    assert "invalid" in exc_info.value.detail.lower()


def test_decode_token_expired():
    """Test decoding an expired token raises HTTPException."""
    settings = get_settings()
    # Create token with past expiration
    now = datetime.now(UTC)
    expired_time = now - timedelta(hours=1)

    payload = {
        "sub": "user_789",
        "email": "expired@example.com",
        "exp": expired_time,
        "iat": now - timedelta(hours=2),
    }

    expired_token = jwt.encode(payload, settings.security.secret_key, algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        decode_token(expired_token)

    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_decode_token_wrong_secret():
    """Test decoding token with wrong secret key raises HTTPException."""
    # Create token with different secret
    payload = {
        "sub": "user_999",
        "email": "test@example.com",
        "exp": datetime.now(UTC) + timedelta(minutes=30),
        "iat": datetime.now(UTC),
    }

    wrong_token = jwt.encode(payload, "wrong_secret_key_here", algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        decode_token(wrong_token)

    assert exc_info.value.status_code == 401


def test_decode_token_missing_claims():
    """Test decoding token without required claims."""
    settings = get_settings()
    # Token without 'sub' claim
    payload = {
        "email": "noclaims@example.com",
        "exp": datetime.now(UTC) + timedelta(minutes=30),
        "iat": datetime.now(UTC),
    }

    token = jwt.encode(payload, settings.security.secret_key, algorithm="HS256")

    # decode_token should succeed but missing 'sub' will cause issues in get_current_user
    result = decode_token(token)
    assert result.get("sub") is None
    assert result["email"] == "noclaims@example.com"


def test_token_round_trip():
    """Test creating and decoding token preserves data."""
    user_id = "round_trip_user"
    email = "roundtrip@example.com"

    token = create_access_token(user_id, email)
    payload = decode_token(token)

    assert payload["sub"] == user_id
    assert payload["email"] == email
