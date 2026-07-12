"""ORM models for import/export sessions, logs, templates, and reports."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.database import Base


class ImportSessionModel(Base):
    __tablename__ = "import_sessions"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("institutions.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(500), default="")
    entity_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    processed_rows: Mapped[int] = mapped_column(Integer, default=0)
    error_rows: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rollback_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )

    log_entries: Mapped[list[ImportLogEntryModel]] = relationship(
        back_populates="import_session"
    )

    __table_args__ = (
        CheckConstraint(
            "total_rows >= 0", name="ck_import_sessions_total_rows"
        ),
        CheckConstraint(
            "processed_rows >= 0",
            name="ck_import_sessions_processed_rows",
        ),
        CheckConstraint(
            "error_rows >= 0", name="ck_import_sessions_error_rows"
        ),
    )


class ImportLogEntryModel(Base):
    __tablename__ = "import_log_entries"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    import_session_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("import_sessions.id"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    entity_id: Mapped[Any | None] = mapped_column(
        Uuid, nullable=True
    )
    error_message: Mapped[str] = mapped_column(String(2000), default="")
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    import_session: Mapped[ImportSessionModel] = relationship(
        back_populates="log_entries"
    )


class ImportTemplateModel(Base):
    __tablename__ = "import_templates"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("institutions.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    column_mappings: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list
    )
    transformation_rules: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list
    )
    validation_rules: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "name",
            "entity_type",
            name="uq_import_templates_institution_name_type",
        ),
    )


class ValidationReportModel(Base):
    __tablename__ = "validation_reports"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("institutions.id"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("academic_periods.id"),
        nullable=True,
        index=True,
    )
    report_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    errors: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list
    )
    warnings: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, default=list
    )
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
    )
    created_by: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=True,
    )
