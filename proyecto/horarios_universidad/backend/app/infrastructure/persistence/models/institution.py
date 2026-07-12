"""ORM models for institutions, campuses, and academic periods."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.database import Base


class InstitutionModel(Base):
    __tablename__ = "institutions"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str] = mapped_column(String(500), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    website: Mapped[str] = mapped_column(String(255), default="")
    logo_url: Mapped[str] = mapped_column(String(500), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict
    )

    campuses: Mapped[list[CampusModel]] = relationship(
        back_populates="institution"
    )
    academic_periods: Mapped[list[AcademicPeriodModel]] = relationship(
        back_populates="institution"
    )

    __table_args__ = (
        UniqueConstraint("abbreviation", name="uq_institutions_abbreviation"),
    )


class CampusModel(Base):
    __tablename__ = "campuses"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("institutions.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str] = mapped_column(String(500), default="")
    city: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    institution: Mapped[InstitutionModel] = relationship(
        back_populates="campuses"
    )
    buildings: Mapped[list["BuildingModel"]] = relationship(
        back_populates="campus"
    )

    __table_args__ = (
        UniqueConstraint(
            "institution_id", "code", name="uq_campuses_institution_code"
        ),
    )


class AcademicPeriodModel(Base):
    __tablename__ = "academic_periods"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("institutions.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="draft"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    institution: Mapped[InstitutionModel] = relationship(
        back_populates="academic_periods"
    )

    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "year",
            "period_number",
            name="uq_academic_periods_institution_year_period",
        ),
    )
