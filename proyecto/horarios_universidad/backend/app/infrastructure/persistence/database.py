"""SQLAlchemy 2.x engine, session factory, and declarative base."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


class DatabaseEngine:
    """Thin wrapper around SQLAlchemy engine and session factory.

    Supports both PostgreSQL and SQLite transparently.
    """

    def __init__(
        self,
        database_url: str,
        *,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        **engine_kwargs: Any,
    ) -> None:
        kwargs: dict[str, Any] = {"echo": echo, **engine_kwargs}

        if _is_sqlite(database_url):
            kwargs["connect_args"] = {"check_same_thread": False}
            kwargs["pool_pre_ping"] = False
        else:
            kwargs["pool_size"] = pool_size
            kwargs["max_overflow"] = max_overflow
            kwargs["pool_pre_ping"] = True

        self._engine = create_engine(database_url, **kwargs)

        if _is_sqlite(database_url):
            @event.listens_for(self._engine, "connect")
            def _set_sqlite_pragma(dbapi_conn, _connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        self._session_factory = sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )

    @property
    def engine(self):
        return self._engine

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Yield a transactional session that auto-commits on success."""
        session: Session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_all(self) -> None:
        """Create all tables registered on *Base* (useful for tests)."""
        Base.metadata.create_all(self._engine)

    def drop_all(self) -> None:
        """Drop all tables registered on *Base* (useful for tests)."""
        Base.metadata.drop_all(self._engine)
