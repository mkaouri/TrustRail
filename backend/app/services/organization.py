from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization, OrganizationStatus
from app.repositories.organization import OrganizationRepository
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.services.errors import (
    OrganizationNotFoundError,
    OrganizationSlugConflictError,
)


class OrganizationService:
    """Business logic for organizations. Owns the unit of work (commit/rollback)."""

    def __init__(self, repository: OrganizationRepository, session: AsyncSession) -> None:
        self._repository = repository
        self._session = session

    async def create_organization(self, data: OrganizationCreate) -> Organization:
        try:
            organization = await self._repository.create(name=data.name, slug=data.slug)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            # Unique slug constraint is the authoritative duplicate guard (race-safe).
            raise OrganizationSlugConflictError(data.slug) from exc
        return organization

    async def get_organization(self, organization_id: UUID) -> Organization:
        organization = await self._repository.get_by_id(organization_id)
        if organization is None:
            raise OrganizationNotFoundError(str(organization_id))
        return organization

    async def list_organizations(
        self, *, status: OrganizationStatus | None = None, limit: int = 50
    ) -> Sequence[Organization]:
        return await self._repository.list(status=status, limit=limit)

    async def update_organization(
        self, organization_id: UUID, data: OrganizationUpdate
    ) -> Organization:
        organization = await self.get_organization(organization_id)
        await self._repository.apply_update(
            organization, name=data.name, status=data.status
        )
        await self._session.commit()
        return organization
