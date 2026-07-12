"""Database dependency injection for FastAPI routes."""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

from app.api.config.settings import get_settings
from app.infrastructure.persistence.database import DatabaseEngine
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from app.domain.interfaces.unit_of_work import UnitOfWork

_engine: DatabaseEngine | None = None


def _get_engine() -> DatabaseEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = DatabaseEngine(settings.database_url)
    return _engine


def get_uow() -> Generator[UnitOfWork, None, None]:
    """Yield a Unit of Work bound to a fresh SQLAlchemy session."""
    engine = _get_engine()
    uow = SqlAlchemyUnitOfWork(engine._session_factory)
    yield uow


def reset_engine() -> None:
    """Tear down the global engine (used in tests)."""
    global _engine
    _engine = None
