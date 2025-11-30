"""Authentication utilities for JWT token handling and password hashing."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_async_session
from app.models.users import User
from app.repositories.user_repository import UserRepository

# HTTP Bearer token scheme
security = HTTPBearer()


def get_password_hash(password: str) -> str:
    """Hash a plain password using bcrypt."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(user_id: str, email: str) -> str:
    """
    Create a JWT access token for a user.

    Token includes:
    - sub: user_id (subject)
    - email: user email
    - exp: expiration timestamp
    - iat: issued at timestamp
    """
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.security.jwt_expire_minutes)

    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, settings.security.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Raises HTTPException with 401 status if token is invalid or expired.

    Returns:
        Decoded token payload containing user_id (sub) and email.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.security.secret_key, algorithms=["HS256"])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    """
    FastAPI dependency to get the current authenticated user from JWT token.

    Validates the token, extracts user_id, and fetches user from database.
    Raises 401 if token is invalid or user not found/inactive.
    """
    token = credentials.credentials
    payload = decode_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
