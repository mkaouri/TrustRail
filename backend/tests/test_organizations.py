import os
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_session
from app.models.organization import OrganizationStatus
from app.repositories.organization import OrganizationRepository
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.services.errors import OrganizationSlugConflictError
from app.services.organization import OrganizationService


def _require_db() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set; skipping organization DB test.")
    return url


async def _truncate(engine: object) -> None:
    async with engine.begin() as conn:  # type: ignore[attr-defined]
        await conn.execute(text("TRUNCATE TABLE organizations"))


@pytest_asyncio.fixture
async def org_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(_require_db())
    factory = async_sessionmaker(engine, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        await session.close()
        await _truncate(engine)
        await engine.dispose()


@pytest_asyncio.fixture
async def org_client(app) -> AsyncIterator[AsyncClient]:
    engine = create_async_engine(_require_db())
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_session] = _override
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
    finally:
        app.dependency_overrides.pop(get_session, None)
        await _truncate(engine)
        await engine.dispose()


# --------------------------------------------------------------------------- #
# Schema validation (no database)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("slug", ["acme", "acme-corp", "trustrail-demo", "company123"])
def test_valid_slugs(slug: str) -> None:
    model = OrganizationCreate(name="Acme Corp", slug=slug)
    assert model.slug == slug


@pytest.mark.parametrize(
    "slug",
    ["Acme Corp", "acme_corp", "-acme", "acme-", "acme corp", "a", "", "acme--corp", "ACME"],
)
def test_invalid_slugs_rejected(slug: str) -> None:
    with pytest.raises(ValueError):
        OrganizationCreate(name="Acme Corp", slug=slug)


def test_name_required_and_bounded() -> None:
    with pytest.raises(ValueError):
        OrganizationCreate(name="", slug="acme")
    with pytest.raises(ValueError):
        OrganizationCreate(name="x" * 201, slug="acme")


def test_create_rejects_status_field() -> None:
    with pytest.raises(ValueError):
        OrganizationCreate.model_validate({"name": "Acme", "slug": "acme", "status": "ACTIVE"})


def test_update_rejects_slug_field() -> None:
    with pytest.raises(ValueError):
        OrganizationUpdate.model_validate({"slug": "new-slug"})


def test_update_rejects_invalid_status() -> None:
    with pytest.raises(ValueError):
        OrganizationUpdate.model_validate({"status": "BOGUS"})


# --------------------------------------------------------------------------- #
# Repository / service (database)
# --------------------------------------------------------------------------- #


@pytest.mark.db
async def test_repo_create_and_get_by_id(org_session: AsyncSession) -> None:
    repo = OrganizationRepository(org_session)
    created = await repo.create(name="Acme", slug="acme")
    await org_session.commit()
    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.slug == "acme"
    assert fetched.status is OrganizationStatus.ACTIVE


@pytest.mark.db
async def test_repo_get_by_slug(org_session: AsyncSession) -> None:
    repo = OrganizationRepository(org_session)
    await repo.create(name="Acme", slug="acme")
    await org_session.commit()
    assert (await repo.get_by_slug("acme")) is not None
    assert (await repo.get_by_slug("missing")) is None


@pytest.mark.db
async def test_service_duplicate_slug_raises(org_session: AsyncSession) -> None:
    service = OrganizationService(OrganizationRepository(org_session), org_session)
    await service.create_organization(OrganizationCreate(name="Acme", slug="acme"))
    with pytest.raises(OrganizationSlugConflictError):
        await service.create_organization(OrganizationCreate(name="Other", slug="acme"))


@pytest.mark.db
async def test_service_update_name_and_disable(org_session: AsyncSession) -> None:
    service = OrganizationService(OrganizationRepository(org_session), org_session)
    org = await service.create_organization(OrganizationCreate(name="Acme", slug="acme"))
    updated = await service.update_organization(
        org.id, OrganizationUpdate(name="Acme Renamed", status=OrganizationStatus.DISABLED)
    )
    assert updated.name == "Acme Renamed"
    assert updated.status is OrganizationStatus.DISABLED


@pytest.mark.db
async def test_repo_list(org_session: AsyncSession) -> None:
    repo = OrganizationRepository(org_session)
    await repo.create(name="A", slug="a-org")
    await repo.create(name="B", slug="b-org")
    await org_session.commit()
    orgs = await repo.list()
    assert len(orgs) == 2


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #


@pytest.mark.db
async def test_api_create_returns_201_active(org_client: AsyncClient) -> None:
    response = await org_client.post(
        "/v1/organizations", json={"name": "Acme Corp", "slug": "acme"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Acme Corp"
    assert body["slug"] == "acme"
    assert body["status"] == "ACTIVE"
    assert body["created_at"] and body["updated_at"]
    assert uuid.UUID(body["id"])  # valid UUID


@pytest.mark.db
async def test_api_duplicate_slug_conflict(org_client: AsyncClient) -> None:
    await org_client.post("/v1/organizations", json={"name": "Acme", "slug": "acme"})
    response = await org_client.post("/v1/organizations", json={"name": "Other", "slug": "acme"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ORGANIZATION_SLUG_CONFLICT"


@pytest.mark.db
async def test_api_invalid_slug_422(org_client: AsyncClient) -> None:
    response = await org_client.post(
        "/v1/organizations", json={"name": "Acme", "slug": "Acme Corp"}
    )
    assert response.status_code == 422


@pytest.mark.db
async def test_api_get_existing(org_client: AsyncClient) -> None:
    created = await org_client.post("/v1/organizations", json={"name": "Acme", "slug": "acme"})
    org_id = created.json()["id"]
    response = await org_client.get(f"/v1/organizations/{org_id}")
    assert response.status_code == 200
    assert response.json()["id"] == org_id


@pytest.mark.db
async def test_api_get_missing_404(org_client: AsyncClient) -> None:
    response = await org_client.get(f"/v1/organizations/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ORGANIZATION_NOT_FOUND"


@pytest.mark.db
async def test_api_malformed_uuid_422(org_client: AsyncClient) -> None:
    response = await org_client.get("/v1/organizations/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.db
async def test_api_list(org_client: AsyncClient) -> None:
    await org_client.post("/v1/organizations", json={"name": "A", "slug": "a-org"})
    await org_client.post("/v1/organizations", json={"name": "B", "slug": "b-org"})
    response = await org_client.get("/v1/organizations")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


@pytest.mark.db
async def test_api_update_name(org_client: AsyncClient) -> None:
    created = await org_client.post("/v1/organizations", json={"name": "Acme", "slug": "acme"})
    org_id = created.json()["id"]
    response = await org_client.patch(f"/v1/organizations/{org_id}", json={"name": "Renamed"})
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"
    assert response.json()["slug"] == "acme"


@pytest.mark.db
async def test_api_update_status_disable(org_client: AsyncClient) -> None:
    created = await org_client.post("/v1/organizations", json={"name": "Acme", "slug": "acme"})
    org_id = created.json()["id"]
    response = await org_client.patch(f"/v1/organizations/{org_id}", json={"status": "DISABLED"})
    assert response.status_code == 200
    assert response.json()["status"] == "DISABLED"


@pytest.mark.db
async def test_api_reject_slug_mutation(org_client: AsyncClient) -> None:
    created = await org_client.post("/v1/organizations", json={"name": "Acme", "slug": "acme"})
    org_id = created.json()["id"]
    response = await org_client.patch(f"/v1/organizations/{org_id}", json={"slug": "new-slug"})
    assert response.status_code == 422


@pytest.mark.db
async def test_api_reject_invalid_status(org_client: AsyncClient) -> None:
    created = await org_client.post("/v1/organizations", json={"name": "Acme", "slug": "acme"})
    org_id = created.json()["id"]
    response = await org_client.patch(f"/v1/organizations/{org_id}", json={"status": "BOGUS"})
    assert response.status_code == 422


@pytest.mark.db
async def test_api_delete_not_allowed(org_client: AsyncClient) -> None:
    created = await org_client.post("/v1/organizations", json={"name": "Acme", "slug": "acme"})
    org_id = created.json()["id"]
    response = await org_client.delete(f"/v1/organizations/{org_id}")
    assert response.status_code == 405
