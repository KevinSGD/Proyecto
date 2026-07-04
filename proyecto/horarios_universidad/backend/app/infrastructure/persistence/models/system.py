"""ORM models for audit logs, system parameters, and notifications."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[Any | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    entity_id: Mapped[Any | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    old_values: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict
    )
    new_values: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True
    )
    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
        index=True,
    )


class SystemParameterModel(Base):
    __tablename__ = "system_parameters"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id"),
        nullable=True,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(2000), default="")
    value_type: Mapped[str] = mapped_column(
        String(50), default="string"
    )
    description: Mapped[str] = mapped_column(String(1000), default="")
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "key",
            name="uq_system_parameters_institution_key",
        ),
    )


class NotificationModel(Base):
    __tablename__ = "notifications"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(2000), default="")
    notification_type: Mapped[str] = mapped_column(
        String(50), default="info"
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        server_default=func.now(),
    )
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict
    )
