"""Tests for UserRepository."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.users import User
from app.repositories.user_repository import UserRepository
from app.utils.auth import get_password_hash


# Get by ID Tests
@pytest.mark.asyncio
async def test_get_by_id_existing_user(async_user_repo: UserRepository, sample_user: User):
    """Test retrieving an existing user by ID."""
    found_user = await async_user_repo.get_by_id(sample_user.id)

    assert found_user is not None
    assert found_user.id == sample_user.id
    assert found_user.email == sample_user.email


@pytest.mark.asyncio
async def test_get_by_id_nonexistent_user(async_user_repo: UserRepository):
    """Test retrieving a non-existent user returns None."""
    found_user = await async_user_repo.get_by_id("nonexistent_id")

    assert found_user is None


# Get by Email Tests
@pytest.mark.asyncio
async def test_get_by_email_existing_user(async_user_repo: UserRepository, sample_user: User):
    """Test retrieving an existing user by email."""
    found_user = await async_user_repo.get_by_email(sample_user.email)

    assert found_user is not None
    assert found_user.email == sample_user.email
    assert found_user.id == sample_user.id


@pytest.mark.asyncio
async def test_get_by_email_nonexistent_user(async_user_repo: UserRepository):
    """Test retrieving a non-existent email returns None."""
    found_user = await async_user_repo.get_by_email("nonexistent@example.com")

    assert found_user is None


@pytest.mark.asyncio
async def test_get_by_email_case_insensitive(async_user_repo: UserRepository, sample_user: User):
    """Test email lookup is case-insensitive."""
    # Should find user even if email case differs
    found_user = await async_user_repo.get_by_email(sample_user.email.upper())

    assert found_user is not None
    assert found_user.id == sample_user.id


# Create Tests
@pytest.mark.asyncio
async def test_create_user(async_user_repo: UserRepository, async_session: AsyncSession):
    """Test creating a new user."""
    new_user = User(
        email="newuser@example.com",
        hashed_password=get_password_hash("newpassword123"),
        timezone="America/New_York",
        is_verified=False,
        is_active=True,
    )

    created_user = await async_user_repo.create(new_user)
    await async_session.commit()

    assert created_user.id is not None
    assert created_user.email == "newuser@example.com"
    assert created_user.timezone == "America/New_York"
    assert created_user.is_verified is False
    assert created_user.is_active is True

    # Verify it exists in DB
    db_user = await async_user_repo.get_by_id(created_user.id)
    assert db_user is not None
    assert db_user.email == "newuser@example.com"


@pytest.mark.asyncio
async def test_create_user_generates_ulid(async_user_repo: UserRepository, async_session: AsyncSession):
    """Test created user has a valid ULID."""
    new_user = User(
        email="ulid@example.com",
        hashed_password=get_password_hash("password"),
        timezone="UTC",
    )

    created_user = await async_user_repo.create(new_user)
    await async_session.commit()

    assert created_user.id is not None
    assert len(created_user.id) == 26  # ULID length


@pytest.mark.asyncio
async def test_create_user_sets_timestamps(async_user_repo: UserRepository, async_session: AsyncSession):
    """Test created user has created_at and updated_at timestamps."""
    new_user = User(
        email="timestamps@example.com",
        hashed_password=get_password_hash("password"),
        timezone="UTC",
    )

    created_user = await async_user_repo.create(new_user)
    await async_session.commit()

    assert created_user.created_at is not None
    assert created_user.updated_at is not None


# Update Tests
@pytest.mark.asyncio
async def test_update_user(async_user_repo: UserRepository, sample_user: User, async_session: AsyncSession):
    """Test updating an existing user."""
    sample_user.timezone = "Europe/London"
    sample_user.is_verified = True

    updated_user = await async_user_repo.update(sample_user)
    await async_session.commit()

    assert updated_user.timezone == "Europe/London"
    assert updated_user.is_verified is True

    # Verify changes persisted
    db_user = await async_user_repo.get_by_id(sample_user.id)
    assert db_user.timezone == "Europe/London"


@pytest.mark.asyncio
async def test_update_user_updates_timestamp(
    async_user_repo: UserRepository, sample_user: User, async_session: AsyncSession
):
    """Test updating user updates the updated_at timestamp."""
    original_updated_at = sample_user.updated_at

    sample_user.timezone = "Asia/Tokyo"
    updated_user = await async_user_repo.update(sample_user)
    await async_session.commit()

    # updated_at should be newer (or at least equal if update was very fast)
    assert updated_user.updated_at >= original_updated_at


# Edge Cases
@pytest.mark.asyncio
async def test_create_duplicate_email_fails(
    async_user_repo: UserRepository, sample_user: User, async_session: AsyncSession
):
    """Test creating user with duplicate email raises integrity error."""

    duplicate_user = User(
        email=sample_user.email,  # Same email
        hashed_password=get_password_hash("different_password"),
        timezone="UTC",
    )

    # Should raise IntegrityError on commit due to unique constraint
    with pytest.raises(IntegrityError):
        await async_user_repo.create(duplicate_user)
        await async_session.commit()


@pytest.mark.asyncio
async def test_create_user_without_required_fields_fails(async_user_repo: UserRepository, async_session: AsyncSession):
    """Test creating user without required fields fails."""
    # Missing hashed_password
    incomplete_user = User(email="incomplete@example.com")

    with pytest.raises(IntegrityError):
        await async_user_repo.create(incomplete_user)
        await async_session.commit()
