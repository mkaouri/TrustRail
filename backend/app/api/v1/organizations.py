from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_organization_service
from app.models.organization import OrganizationStatus
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationListResponse,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.services.organization import OrganizationService

router = APIRouter(prefix="/v1/organizations", tags=["organizations"])

ServiceDep = Annotated[OrganizationService, Depends(get_organization_service)]


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate, service: ServiceDep
) -> OrganizationResponse:
    organization = await service.create_organization(data)
    return OrganizationResponse.model_validate(organization)


@router.get("", response_model=OrganizationListResponse)
async def list_organizations(
    service: ServiceDep,
    status_filter: Annotated[OrganizationStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> OrganizationListResponse:
    organizations = await service.list_organizations(status=status_filter, limit=limit)
    return OrganizationListResponse(
        items=[OrganizationResponse.model_validate(org) for org in organizations]
    )


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(organization_id: UUID, service: ServiceDep) -> OrganizationResponse:
    organization = await service.get_organization(organization_id)
    return OrganizationResponse.model_validate(organization)


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: UUID, data: OrganizationUpdate, service: ServiceDep
) -> OrganizationResponse:
    organization = await service.update_organization(organization_id, data)
    return OrganizationResponse.model_validate(organization)
