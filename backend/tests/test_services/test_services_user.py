"""Unit tests for UserService."""

import pytest
from sqlmodel import select

from app.dtos.user import UpdateTimezoneDTO
from app.models.users import User
from app.services.user_service import UserService
from app.utils.auth import get_password_hash


@pytest.mark.asyncio
async def test_update_timezone_success(async_session):
    """Test updating user timezone successfully."""
    user = User(
        email="user@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)

    service = UserService(async_session)
    update_dto = UpdateTimezoneDTO(timezone="America/New_York")
    user_dto = await service.update_timezone(user, update_dto)

    assert user_dto.timezone == "America/New_York"
    assert user_dto.id == user.id
    assert user_dto.email == user.email


@pytest.mark.asyncio
async def test_update_timezone_persists(async_session):
    """Test that timezone update is persisted to database."""
    user = User(
        email="persist@example.com",
        hashed_password=get_password_hash("password123"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    user_id = user.id

    service = UserService(async_session)
    update_dto = UpdateTimezoneDTO(timezone="Europe/London")
    await service.update_timezone(user, update_dto)

    # Verify persistence by fetching fresh instance

    stmt = select(User).where(User.id == user_id)
    result = await async_session.exec(stmt)
    fetched_user = result.one()

    assert fetched_user.timezone == "Europe/London"
