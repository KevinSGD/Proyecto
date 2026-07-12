"""ORM models for academic structure: areas and subjects."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.persistence.database import Base


class AcademicAreaModel(Base):
    __tablename__ = "academic_areas"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        Uuid,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint(
            "institution_id", "code", name="uq_academic_areas_institution_code"
        ),
    )


class SubjectModel(Base):
    __tablename__ = "subjects"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        Uuid,
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    credit_hours: Mapped[int] = mapped_column(Integer, default=0)
    weekly_hours: Mapped[int] = mapped_column(Integer, default=0)
    modality_default: Mapped[str] = mapped_column(
        String(50), default="presential"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint(
            "institution_id", "code", name="uq_subjects_institution_code"
        ),
    )
