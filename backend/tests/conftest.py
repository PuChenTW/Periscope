import copy
import os
import subprocess
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fakeredis import FakeAsyncRedis
from fastapi.testclient import TestClient
from loguru import logger
from pytest_mock_resources import PostgresConfig, create_postgres_fixture
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_async_sessionmaker, get_engine
from app.main import create_app
from app.temporal.client import get_temporal_client
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
    app = create_app()
    temporal_client = MagicMock()
    temporal_client.service_client = MagicMock()
    temporal_client.service_client.check_health = AsyncMock()
    temporal_client.service_client.check_health.return_value = True

    app.dependency_overrides[get_redis_client] = lambda: redis_client
    app.dependency_overrides[get_temporal_client] = lambda: temporal_client
    with TestClient(app) as c:
        yield c
