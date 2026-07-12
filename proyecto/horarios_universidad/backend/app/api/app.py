"""FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.config.settings import get_settings
from app.api.middlewares.error_handler import register_exception_handlers
from app.api.middlewares.logging_middleware import RequestLoggingMiddleware


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    _configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    _add_middleware(app, settings)
    register_exception_handlers(app)
    _include_routers(app, settings.api_prefix)

    return app


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _add_middleware(app: FastAPI, settings) -> None:
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _include_routers(app: FastAPI, prefix: str) -> None:
    from app.api.routers.academic import router as academic_router
    from app.api.routers.auth import router as auth_router
    from app.api.routers.dashboard import router as dashboard_router
    from app.api.routers.health import router as health_router
    from app.api.routers.infrastructure import router as infrastructure_router
    from app.api.routers.institution import router as institution_router
    from app.api.routers.offering import router as offering_router
    from app.api.routers.personnel import router as personnel_router
    from app.api.routers.schedule import router as schedule_router

    app.include_router(health_router)
    app.include_router(auth_router, prefix=prefix)
    app.include_router(institution_router, prefix=prefix)
    app.include_router(academic_router, prefix=prefix)
    app.include_router(personnel_router, prefix=prefix)
    app.include_router(infrastructure_router, prefix=prefix)
    app.include_router(offering_router, prefix=prefix)
    app.include_router(schedule_router, prefix=prefix)
    app.include_router(dashboard_router, prefix=prefix)
