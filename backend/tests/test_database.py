import asyncio
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

_BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.mark.db
async def test_database_connectivity(db_session: AsyncSession) -> None:
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar_one() == 1


@pytest.mark.db
@pytest.mark.opa
async def test_readiness_endpoint_ok(db_client: AsyncClient) -> None:
    if not os.environ.get("OPA_URL"):
        pytest.skip("OPA_URL not set; readiness requires OPA.")
    response = await db_client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def _alembic_config(url: str) -> Config:
    config = Config(str(_BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND_DIR / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    return config


async def _current_version(url: str) -> str | None:
    engine = create_async_engine(url)
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT version_num FROM alembic_version"))
            row = result.first()
            return row[0] if row is not None else None
    finally:
        await engine.dispose()


@pytest.mark.db
def test_migration_upgrade_head_and_downgrade() -> None:
    # Sync test: env.py calls asyncio.run(), so no event loop may be running.
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set; skipping migration smoke test.")

    config = _alembic_config(url)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    assert asyncio.run(_current_version(url)) == "0001_initial"

    command.downgrade(config, "base")
    assert asyncio.run(_current_version(url)) is None
