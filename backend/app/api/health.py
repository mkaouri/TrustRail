import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.policy.opa_client import get_policy_evaluator

logger = logging.getLogger("trustrail.health")

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.version,
    )


@router.get("/health/ready")
async def readiness(session: Annotated[AsyncSession, Depends(get_session)]) -> JSONResponse:
    db_ok = True
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
        logger.warning("Readiness check failed: database unavailable.")

    opa_ok = await get_policy_evaluator().health_check()
    if not opa_ok:
        logger.warning("Readiness check failed: OPA unavailable.")

    if db_ok and opa_ok:
        return JSONResponse(status_code=200, content={"status": "ready"})
    # Report which dependency is down without leaking connection details.
    return JSONResponse(
        status_code=503,
        content={"status": "unavailable", "database": db_ok, "opa": opa_ok},
    )
