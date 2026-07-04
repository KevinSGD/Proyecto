"""ORM models for academic offerings."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.database import Base


class AcademicOfferingModel(Base):
    __tablename__ = "academic_offerings"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_periods.id"),
        nullable=False,
        index=True,
    )
    area_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_areas.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="draft"
    )
    created_by: Mapped[Any | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    lines: Mapped[list[OfferingLineModel]] = relationship(
        back_populates="offering"
    )

    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "period_id",
            "area_id",
            name="uq_academic_offerings_institution_period_area",
        ),
    )


class OfferingLineModel(Base):
    __tablename__ = "offering_lines"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    offering_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_offerings.id"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id"),
        nullable=False,
        index=True,
    )
    num_groups: Mapped[int] = mapped_column(Integer, default=0)
    expected_enrollment_per_group: Mapped[int] = mapped_column(
        Integer, default=0
    )
    modality: Mapped[str] = mapped_column(
        String(50), default="presential"
    )
    schedule_type_id: Mapped[Any | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schedule_types.id"),
        nullable=True,
        index=True,
    )

    offering: Mapped[AcademicOfferingModel] = relationship(
        back_populates="lines"
    )
    subject: Mapped["SubjectModel"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "offering_id",
            "subject_id",
            name="uq_offering_lines_offering_subject",
        ),
        CheckConstraint(
            "num_groups >= 0", name="ck_offering_lines_num_groups"
        ),
        CheckConstraint(
            "expected_enrollment_per_group >= 0",
            name="ck_offering_lines_enrollment",
        ),
    )
