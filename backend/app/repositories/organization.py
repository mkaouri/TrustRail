from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization, OrganizationStatus


class OrganizationRepository:
    """Persistence for organizations. Contains no HTTP or business-policy logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, name: str, slug: str) -> Organization:
        organization = Organization(name=name, slug=slug)
        self._session.add(organization)
        await self._session.flush()
        return organization

    async def get_by_id(self, organization_id: UUID) -> Organization | None:
        return await self._session.get(Organization, organization_id)

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self._session.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list(
        self, *, status: OrganizationStatus | None = None, limit: int = 50
    ) -> Sequence[Organization]:
        stmt = select(Organization).order_by(Organization.created_at, Organization.id)
        if status is not None:
            stmt = stmt.where(Organization.status == status)
        result = await self._session.execute(stmt.limit(limit))
        return result.scalars().all()

    async def apply_update(
        self,
        organization: Organization,
        *,
        name: str | None = None,
        status: OrganizationStatus | None = None,
    ) -> Organization:
        if name is not None:
            organization.name = name
        if status is not None:
            organization.status = status
        await self._session.flush()
        return organization
