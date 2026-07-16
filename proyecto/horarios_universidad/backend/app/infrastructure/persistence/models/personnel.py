"""ORM models for instructors and related personnel data."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.database import Base


class InstructorModel(Base):
    __tablename__ = "instructors"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("institutions.id"),
        nullable=False,
        index=True,
    )
    area_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("academic_areas.id"),
        nullable=True,
        index=True,
    )
    employee_code: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    contracts: Mapped[list[InstructorContractModel]] = relationship(
        back_populates="instructor"
    )
    specialties: Mapped[list[InstructorSpecialtyModel]] = relationship(
        back_populates="instructor"
    )
    qualifications: Mapped[list[InstructorQualificationModel]] = relationship(
        back_populates="instructor"
    )
    availabilities: Mapped[list[InstructorAvailabilityModel]] = relationship(
        back_populates="instructor"
    )
    preferences: Mapped[list[InstructorPreferenceModel]] = relationship(
        back_populates="instructor"
    )

    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "employee_code",
            name="uq_instructors_institution_employee_code",
        ),
    )


class InstructorContractModel(Base):
    __tablename__ = "instructor_contracts"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    instructor_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("instructors.id"),
        nullable=False,
        index=True,
    )
    contract_type: Mapped[str] = mapped_column(String(100), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    max_daily_periods: Mapped[int] = mapped_column(Integer, default=0)
    max_weekly_periods: Mapped[int] = mapped_column(Integer, default=0)
    min_weekly_periods: Mapped[int] = mapped_column(Integer, default=0)
    max_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    instructor: Mapped[InstructorModel] = relationship(
        back_populates="contracts"
    )


class InstructorSpecialtyModel(Base):
    __tablename__ = "instructor_specialties"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    instructor_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("instructors.id"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("subjects.id"),
        nullable=False,
        index=True,
    )
    proficiency_level: Mapped[int] = mapped_column(Integer, default=5)

    instructor: Mapped[InstructorModel] = relationship(
        back_populates="specialties"
    )

    __table_args__ = (
        UniqueConstraint(
            "instructor_id",
            "subject_id",
            name="uq_instructor_specialties_instructor_subject",
        ),
        CheckConstraint(
            "proficiency_level >= 1 AND proficiency_level <= 10",
            name="ck_instructor_specialties_proficiency",
        ),
    )


class InstructorQualificationModel(Base):
    __tablename__ = "instructor_qualifications"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    instructor_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("instructors.id"),
        nullable=False,
        index=True,
    )
    qualification_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_name: Mapped[str] = mapped_column(String(255), default="")
    year_obtained: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    instructor: Mapped[InstructorModel] = relationship(
        back_populates="qualifications"
    )


class InstructorAvailabilityModel(Base):
    __tablename__ = "instructor_availabilities"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    instructor_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("instructors.id"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("academic_periods.id"),
        nullable=True,
        index=True,
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    instructor: Mapped[InstructorModel] = relationship(
        back_populates="availabilities"
    )

    __table_args__ = (
        UniqueConstraint(
            "instructor_id",
            "period_id",
            "day_of_week",
            "period",
            name="uq_instructor_availabilities_slot",
        ),
        CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6",
            name="ck_instructor_availabilities_day",
        ),
        CheckConstraint(
            "period >= 1",
            name="ck_instructor_availabilities_period",
        ),
    )


class InstructorPreferenceModel(Base):
    __tablename__ = "instructor_preferences"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    instructor_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("instructors.id"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("academic_periods.id"),
        nullable=True,
        index=True,
    )
    group_id: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("groups.id"),
        nullable=True,
        index=True,
    )
    subject_id: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("subjects.id"),
        nullable=True,
        index=True,
    )
    score: Mapped[int] = mapped_column(Integer, default=5)

    instructor: Mapped[InstructorModel] = relationship(
        back_populates="preferences"
    )

    __table_args__ = (
        CheckConstraint(
            "score >= 1 AND score <= 10",
            name="ck_instructor_preferences_score",
        ),
    )
