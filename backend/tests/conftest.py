import copy
import os
import subprocess
from datetime import time
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fakeredis import FakeAsyncRedis
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from loguru import logger
from pytest_mock_resources import PostgresConfig, create_postgres_fixture
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_async_sessionmaker, get_engine
from app.main import create_app
from app.models.users import ContentSource, DigestConfiguration, InterestProfile, User
from app.repositories.user_repository import UserRepository
from app.temporal.client import get_temporal_client
from app.utils.auth import create_access_token, get_password_hash
from app.utils.redis_client import get_redis_client


@pytest.fixture(scope="session", autouse=True)
def cleanup_docker_containers():
    """
    Clean up stale Docker containers before test session starts.

    Removes any leftover containers from previous test runs that may cause
    port conflicts or database connection issues.
    """
    try:
        # List all containers with names containing 'periscope' or 'pmr_postgres'
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=periscope", "--filter", "name=pmr_postgres", "-q"],
            capture_output=True,
            text=True,
            check=False,
        )

        container_ids = result.stdout.strip().split("\n")
        container_ids = [cid for cid in container_ids if cid]

        if container_ids:
            logger.info(f"Cleaning up {len(container_ids)} stale Docker containers")
            subprocess.run(
                ["docker", "rm", "-f", *container_ids],
                capture_output=True,
                check=False,
            )
            logger.info("Docker cleanup completed")
        else:
            logger.debug("No stale Docker containers found")

    except FileNotFoundError:
        logger.warning("Docker CLI not found - skipping container cleanup")
    except Exception as e:
        logger.warning(f"Failed to clean up Docker containers: {e}")

    yield


postgress = create_postgres_fixture(scope="session", async_=True)


@pytest.fixture(scope="session")
def pmr_postgres_config(worker_id):
    return PostgresConfig(
        image="pgvector/pgvector:pg17",
        host="localhost",
        port=6432 + (0 if worker_id == "master" else int(worker_id[2:])),
        username="root",
        password="password",
        root_database=f"periscope_{worker_id}",
        drivername="postgresql+asyncpg",
    )


@pytest.fixture(scope="session")
def database_url(pmr_postgres_config):
    database_url = "{0.drivername}://{0.username}:{0.password}@{0.host}:{0.port}/{0.root_database}"
    return database_url.format(pmr_postgres_config)


@pytest.fixture(scope="session", autouse=True)
def override_environment(database_url):
    original_environ = copy.deepcopy(os.environ)

    # Application settings
    os.environ["DEBUG"] = "true"
    os.environ["TEST_MODE"] = "true"

    # Nested configuration using __ delimiter
    os.environ["DATABASE__URL"] = database_url
    os.environ["SECURITY__SECRET_KEY"] = "test-secret-key"
    os.environ["AI__GEMINI_API_KEY"] = "test-api-key"
    os.environ["AI__OPENAI_API_KEY"] = "test-api-key"

    yield

    os.environ.clear()
    os.environ.update(original_environ)


@pytest.fixture(autouse=True)
def setup_database(override_environment, postgress):
    """
    Ensures that the database schema is created before any tests run
    and dropped after all tests complete.
    """
    # Clear cache first to ensure fresh engine for each test session
    engine = create_engine(
        os.environ["DATABASE__URL"].replace("asyncpg", "psycopg"),
        echo=False,
        future=True,
    )

    try:
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        yield
    finally:
        SQLModel.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def session(setup_database, override_environment):
    engine = create_engine(
        os.environ["DATABASE__URL"].replace("asyncpg", "psycopg"),
        echo=False,
        future=True,
    )
    with Session(engine) as session_:
        try:
            yield session_
        except Exception:
            session_.rollback()
            raise
        finally:
            session_.close()


@pytest.fixture
def clear_async_db_cache():
    """
    Clear cached async database engine and sessionmaker between tests.

    Use this fixture explicitly in tests that call Temporal activities or other
    async code that creates its own database sessions via get_async_sessionmaker().
    This prevents connection pool conflicts between sync test fixtures and async
    activity code.

    DO NOT use autouse=True - only apply where needed to avoid breaking parallel tests.
    """
    # Clear the cache before test
    get_engine.cache_clear()
    get_async_sessionmaker.cache_clear()

    yield

    # Clear again after test to ensure cleanup
    get_engine.cache_clear()
    get_async_sessionmaker.cache_clear()


@pytest_asyncio.fixture
async def redis_client():
    """Provides a fresh FakeAsyncRedis client for each test."""
    client = FakeAsyncRedis(decode_responses=True)
    try:
        yield client
    finally:
        # Ensure clean state between tests
        await client.flushall()
        await client.aclose()


@pytest.fixture
def client(redis_client):
    """
    Sync HTTP client for testing API endpoints.

    Use this fixture when:
    - Test does NOT use database fixtures (like test_user, session)
    - OR endpoint does validation only without database access
    - OR test creates data through API calls (not fixtures)

    Examples:
    - test_register_user_success (creates user via API)
    - test_register_user_short_password (validation only)
    - test_get_user_profile_unauthenticated (no database query)

    If your test uses database fixtures AND makes API calls that access the database,
    use async_client instead to avoid connection pool conflicts.
    """
    app = create_app()
    temporal_client = MagicMock()
    temporal_client.service_client = MagicMock()
    temporal_client.service_client.check_health = AsyncMock()
    temporal_client.service_client.check_health.return_value = True

    app.dependency_overrides[get_redis_client] = lambda: redis_client
    app.dependency_overrides[get_temporal_client] = lambda: temporal_client
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client(redis_client):
    """
    Async HTTP client for testing API endpoints with database access.

    Use this fixture when:
    - Test uses database fixtures (like test_user, session) to create test data
    - AND API endpoint accesses the database (queries, updates)
    - MUST combine with clear_async_db_cache fixture

    Examples:
    - test_login_success (uses test_user fixture + queries database)
    - test_update_user_profile_timezone (uses test_user + updates database)
    - test_get_digest_config_success (uses test_user + queries config)

    Why this is needed:
    - Sync fixtures (via session) and async endpoints share connection pools
    - Without clear_async_db_cache, get "another operation is in progress" errors
    - async_client forces async pattern throughout the test

    Pattern:
    @pytest.mark.asyncio
    async def test_something(async_client, clear_async_db_cache, test_user):
        response = await async_client.post("/endpoint", json={...})
        assert response.status_code == 200
    """
    app = create_app()
    temporal_client = MagicMock()
    temporal_client.service_client = MagicMock()
    temporal_client.service_client.check_health = AsyncMock()
    temporal_client.service_client.check_health.return_value = True

    app.dependency_overrides[get_redis_client] = lambda: redis_client
    app.dependency_overrides[get_temporal_client] = lambda: temporal_client

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def async_session(clear_async_db_cache, override_environment):
    """
    Async database session for repository tests.

    Use this fixture when testing repository methods that require AsyncSession.
    Automatically handles rollback on errors and cleanup.
    """
    sessionmaker = get_async_sessionmaker()
    async with sessionmaker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def async_user_repo(async_session):
    """Create UserRepository with async session for testing."""

    return UserRepository(async_session)


@pytest_asyncio.fixture
async def sample_user(async_session):
    """Create a sample user in the database using async session."""

    user = User(
        email="sample@example.com",
        hashed_password=get_password_hash("samplepassword"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_token(async_client, clear_async_db_cache):
    """
    Registers and logs in a test user, returning a valid JWT access token.
    Use this fixture for tests requiring authentication.
    """
    email = "auth_token_user@example.com"
    password = "password123"
    await async_client.post("/auth/register", json={"email": email, "password": password, "timezone": "UTC"})
    response = await async_client.post("/auth/login", json={"email": email, "password": password})
    return response.json()["access_token"]


@pytest.fixture
def test_user(session: Session) -> User:
    """Create a test user with hashed password."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        timezone="UTC",
        is_verified=True,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def test_user_with_config(session: Session, test_user: User) -> tuple[User, DigestConfiguration]:
    """Create a test user with complete digest configuration."""
    config = DigestConfiguration(
        user_id=test_user.id,
        delivery_time=time(7, 0),
        summary_style="brief",
        is_active=True,
    )
    session.add(config)
    session.commit()
    session.refresh(config)

    # Add interest profile
    profile = InterestProfile(
        config_id=config.id,
        keywords=["technology", "programming", "AI"],
        relevance_threshold=40,
        boost_factor=1.0,
    )
    session.add(profile)

    # Add a content source
    source = ContentSource(
        config_id=config.id,
        source_type="rss",
        source_url="https://example.com/feed.xml",
        source_name="Example Feed",
        is_active=True,
    )
    session.add(source)

    session.commit()
    session.refresh(config)

    return test_user, config


@pytest.fixture
def jwt_token(test_user: User) -> str:
    """Create a valid JWT token for the test user."""
    return create_access_token(user_id=test_user.id, email=test_user.email)


@pytest.fixture
def auth_headers(jwt_token: str) -> dict:
    """Create authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {jwt_token}"}
