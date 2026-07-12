"""ORM models for authentication, authorization, and roles."""

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
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.database import Base


class RoleModel(Base):
    __tablename__ = "roles"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("institutions.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    permissions: Mapped[list[PermissionModel]] = relationship(
        back_populates="role"
    )

    __table_args__ = (
        UniqueConstraint(
            "institution_id", "name", name="uq_roles_institution_name"
        ),
    )


class PermissionModel(Base):
    __tablename__ = "permissions"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    role_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("roles.id"),
        nullable=False,
        index=True,
    )
    resource: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)

    role: Mapped[RoleModel] = relationship(back_populates="permissions")

    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "resource",
            "action",
            name="uq_permissions_role_resource_action",
        ),
    )


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("institutions.id"),
        nullable=True,
        index=True,
    )
    role_id: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("roles.id"),
        nullable=True,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    role: Mapped[RoleModel | None] = relationship()
    user_areas: Mapped[list[UserAreaModel]] = relationship(
        back_populates="user"
    )


class UserAreaModel(Base):
    __tablename__ = "user_areas"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    user_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    area_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("academic_areas.id"),
        nullable=False,
        index=True,
    )

    user: Mapped[UserModel] = relationship(back_populates="user_areas")

    __table_args__ = (
        UniqueConstraint(
            "user_id", "area_id", name="uq_user_areas_user_area"
        ),
    )
