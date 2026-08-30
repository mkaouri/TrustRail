from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.repositories.organization import OrganizationRepository
from app.services.organization import OrganizationService


def get_organization_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OrganizationService:
    return OrganizationService(OrganizationRepository(session), session)
