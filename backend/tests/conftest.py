import copy
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fakeredis import FakeAsyncRedis
from fastapi.testclient import TestClient
from pytest_mock_resources import PostgresConfig, create_postgres_fixture
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import create_engine_and_session
from app.main import create_app
from app.utils.redis_client import get_redis_client

postgress = create_postgres_fixture(scope="session")


@pytest.fixture(scope="session")
def pmr_postgres_config(worker_id):
    return PostgresConfig(
        image="pgvector/pgvector:pg17",
        host="localhost",
        port=6432 + (0 if worker_id == "master" else int(worker_id[2:])),
        username="root",
        password="password",
        root_database=f"periscope_{worker_id}",
        drivername="postgresql+psycopg",
    )


@pytest.fixture(scope="session")
def database_url(pmr_postgres_config):
    database_url = "{0.drivername}://{0.username}:{0.password}@{0.host}:{0.port}/{0.root_database}"
    return database_url.format(pmr_postgres_config)


@pytest.fixture(scope="session", autouse=True)
def override_environment(database_url):
    original_environ = copy.deepcopy(os.environ)

    os.environ["DEBUG"] = "true"
    os.environ["DATABASE_URL"] = database_url
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["GEMINI_API_KEY"] = "test-api-key"
    os.environ["OPENAI_API_KEY"] = "test-api-key"

    yield

    os.environ.clear()
    os.environ.update(original_environ)


@pytest_asyncio.fixture
async def session(postgress, override_environment) -> AsyncGenerator[AsyncSession]:
    """
    The test session that will be used in the tests.
    """

    engine, async_session = create_engine_and_session()

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

        async with async_session() as session_:
            try:
                yield session_
            except Exception:
                await session_.rollback()
                raise
            finally:
                await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def redis_client():
    client = FakeAsyncRedis(decode_responses=True)
    yield client
    await client.aclose()


@pytest.fixture
def client(session, redis_client):
    app = create_app()
    app.dependency_overrides[get_redis_client] = lambda: redis_client
    with TestClient(app) as c:
        yield c
