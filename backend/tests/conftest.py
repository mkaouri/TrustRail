import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.database import get_session
from app.main import create_app

_BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def _ensure_test_schema() -> None:
    # Migrate the test database to head once so integration tests see the schema.
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        return
    config = Config(str(_BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")


@pytest.fixture
def app():
    return create_app()


@pytest.fixture(autouse=True)
def _reset_opa_client_singleton():
    # The shared OPA client is bound to an event loop; pytest-asyncio uses a fresh
    # loop per test, so reset the singleton around each test to avoid cross-loop reuse.
    import app.policy.opa_client as opa_client

    opa_client._client = None
    yield
    opa_client._client = None


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


def _test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set; skipping database test.")
    return url


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Transactional session against the test database; rolled back for isolation."""

    engine = create_async_engine(_test_database_url(), pool_pre_ping=True)
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def db_client(app, db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """HTTP client whose get_session dependency uses the transactional test session."""

    async def _override() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_session, None)
