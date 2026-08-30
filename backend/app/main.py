import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.database import check_connection, dispose_engine
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.request_id import RequestIDMiddleware

logger = logging.getLogger("trustrail.lifespan")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Fail closed: refuse to start if the database is unreachable (never silently ignore).
    try:
        await check_connection()
    except Exception:
        logger.critical("Database connectivity check failed at startup.")
        raise
    try:
        yield
    finally:
        await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="TrustRail",
        version=settings.version,
        lifespan=lifespan,
    )

    app.add_middleware(RequestIDMiddleware)
    register_exception_handlers(app)
    app.include_router(health_router)

    return app


app = create_app()
