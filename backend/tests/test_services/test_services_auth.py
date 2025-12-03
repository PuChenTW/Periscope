"""Unit tests for AuthService."""

from datetime import time

import pytest
from fastapi import HTTPException
from sqlmodel import select

from app.dtos.auth import LoginRequest, RegisterUserRequest
from app.models.users import DigestConfiguration, InterestProfile, User
from app.services.auth_service import AuthService
from app.utils.auth import get_password_hash, verify_password


@pytest.mark.asyncio
async def test_register_user_success(async_session):
    """Test successful user registration with default config."""
    service = AuthService(async_session)
    register_dto = RegisterUserRequest(
        email="newuser@example.com",
        password="password123",
        timezone="America/New_York",
    )

    user_dto = await service.register_user(register_dto)

    assert user_dto.email == "newuser@example.com"
    assert user_dto.timezone == "America/New_York"
    assert user_dto.is_verified is False
    assert user_dto.is_active is True

    # Verify actual user in database has hashed password
    stmt = select(User).where(User.id == user_dto.id)
    result = await async_session.exec(stmt)
    db_user = result.one()
    assert verify_password("password123", db_user.hashed_password)


@pytest.mark.asyncio
async def test_register_user_creates_default_config(async_session):
    """Test that registration creates default DigestConfiguration."""
    service = AuthService(async_session)
    register_dto = RegisterUserRequest(
        email="withconfig@example.com",
        password="password123",
        timezone="UTC",
    )

    user_dto = await service.register_user(register_dto)

    # Verify config was created
    stmt = select(DigestConfiguration).where(DigestConfiguration.user_id == user_dto.id)
    result = await async_session.exec(stmt)
    config = result.one()

    assert config.delivery_time == time(7, 0)
    assert config.summary_style == "brief"
    assert config.is_active is True


@pytest.mark.asyncio
async def test_register_user_creates_interest_profile(async_session):
    """Test that registration creates empty InterestProfile."""
    service = AuthService(async_session)
    register_dto = RegisterUserRequest(
        email="withprofile@example.com",
        password="password123",
        timezone="UTC",
    )

    user_dto = await service.register_user(register_dto)

    # Get config first
    config_stmt = select(DigestConfiguration).where(DigestConfiguration.user_id == user_dto.id)
    config_result = await async_session.exec(config_stmt)
    config = config_result.one()

    # Verify profile was created
    profile_stmt = select(InterestProfile).where(InterestProfile.config_id == config.id)
    profile_result = await async_session.exec(profile_stmt)
    profile = profile_result.one()

    assert profile.keywords == []
    assert profile.relevance_threshold == 40
    assert profile.boost_factor == 1.0


@pytest.mark.asyncio
async def test_register_user_email_lowercase(async_session):
    """Test that email is converted to lowercase."""
    service = AuthService(async_session)
    register_dto = RegisterUserRequest(
        email="UPPERCASE@EXAMPLE.COM",
        password="password123",
        timezone="UTC",
    )

    user_dto = await service.register_user(register_dto)

    assert user_dto.email == "uppercase@example.com"


@pytest.mark.asyncio
async def test_register_user_duplicate_email(async_session):
    """Test error when registering duplicate email."""
    service = AuthService(async_session)

    # Register first user
    register_dto1 = RegisterUserRequest(
        email="duplicate@example.com",
        password="password123",
        timezone="UTC",
    )
    await service.register_user(register_dto1)

    # Attempt to register with same email
    register_dto2 = RegisterUserRequest(
        email="duplicate@example.com",
        password="different",
        timezone="UTC",
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.register_user(register_dto2)

    assert exc_info.value.status_code == 409
    assert "already registered" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_register_user_duplicate_email_case_insensitive(async_session):
    """Test that duplicate check is case-insensitive."""
    service = AuthService(async_session)

    register_dto1 = RegisterUserRequest(
        email="case@example.com",
        password="password123",
        timezone="UTC",
    )
    await service.register_user(register_dto1)

    register_dto2 = RegisterUserRequest(
        email="CASE@EXAMPLE.COM",
        password="different",
        timezone="UTC",
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.register_user(register_dto2)

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_authenticate_user_success(async_session):
    """Test successful authentication."""
    # Create user directly
    user = User(
        email="auth@example.com",
        hashed_password=get_password_hash("correctpassword"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()

    service = AuthService(async_session)
    login_dto = LoginRequest(email="auth@example.com", password="correctpassword")
    user_dto, token_dto = await service.authenticate_user(login_dto)

    assert user_dto.id == user.id
    assert user_dto.email == "auth@example.com"
    assert token_dto.access_token is not None
    assert isinstance(token_dto.access_token, str)
    assert len(token_dto.access_token) > 0
    assert token_dto.token_type == "bearer"


@pytest.mark.asyncio
async def test_authenticate_user_email_case_insensitive(async_session):
    """Test that authentication is case-insensitive for email."""
    user = User(
        email="case@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()

    service = AuthService(async_session)
    login_dto = LoginRequest(email="CASE@EXAMPLE.COM", password="password123")
    user_dto, token_dto = await service.authenticate_user(login_dto)

    assert user_dto.email == "case@example.com"
    assert token_dto.access_token is not None


@pytest.mark.asyncio
async def test_authenticate_user_invalid_email(async_session):
    """Test error when email doesn't exist."""
    service = AuthService(async_session)
    login_dto = LoginRequest(email="nonexistent@example.com", password="anypassword")

    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate_user(login_dto)

    assert exc_info.value.status_code == 401
    assert "invalid email or password" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(async_session):
    """Test error when password is incorrect."""
    user = User(
        email="wrongpass@example.com",
        hashed_password=get_password_hash("correctpassword"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()

    service = AuthService(async_session)
    login_dto = LoginRequest(email="wrongpass@example.com", password="wrongpassword")

    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate_user(login_dto)

    assert exc_info.value.status_code == 401
    assert "invalid email or password" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_authenticate_user_inactive_account(async_session):
    """Test error when user account is inactive."""
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=False,  # Inactive
    )
    async_session.add(user)
    await async_session.commit()

    service = AuthService(async_session)
    login_dto = LoginRequest(email="inactive@example.com", password="password123")

    with pytest.raises(HTTPException) as exc_info:
        await service.authenticate_user(login_dto)

    assert exc_info.value.status_code == 401
    assert "inactive" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_register_user_atomic_transaction(async_session):
    """Test that registration is atomic - all or nothing."""
    service = AuthService(async_session)

    # This test verifies that if registration succeeds, all related records are created
    register_dto = RegisterUserRequest(
        email="atomic@example.com",
        password="password123",
        timezone="UTC",
    )
    user_dto = await service.register_user(register_dto)

    # Verify all entities exist
    config_stmt = select(DigestConfiguration).where(DigestConfiguration.user_id == user_dto.id)
    config_result = await async_session.exec(config_stmt)
    config = config_result.one()

    profile_stmt = select(InterestProfile).where(InterestProfile.config_id == config.id)
    profile_result = await async_session.exec(profile_stmt)
    profile = profile_result.one()

    assert user_dto is not None
    assert config is not None
    assert profile is not None
