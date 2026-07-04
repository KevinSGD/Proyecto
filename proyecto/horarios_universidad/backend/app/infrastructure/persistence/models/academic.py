"""ORM models for academic structure: areas, departments, programs, subjects."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.database import Base


class AcademicAreaModel(Base):
    __tablename__ = "academic_areas"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    departments: Mapped[list[DepartmentModel]] = relationship(
        back_populates="area"
    )
    programs: Mapped[list[ProgramModel]] = relationship(
        back_populates="area"
    )

    __table_args__ = (
        UniqueConstraint(
            "institution_id", "code", name="uq_academic_areas_institution_code"
        ),
    )


class DepartmentModel(Base):
    __tablename__ = "departments"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    area_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_areas.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    head_instructor_id: Mapped[Any | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instructors.id"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    area: Mapped[AcademicAreaModel] = relationship(
        back_populates="departments"
    )

    __table_args__ = (
        UniqueConstraint(
            "area_id", "code", name="uq_departments_area_code"
        ),
    )


class ProgramModel(Base):
    __tablename__ = "programs"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    area_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_areas.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    total_semesters: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(String(1000), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    area: Mapped[AcademicAreaModel] = relationship(
        back_populates="programs"
    )
    study_plans: Mapped[list[StudyPlanModel]] = relationship(
        back_populates="program"
    )

    __table_args__ = (
        UniqueConstraint(
            "area_id", "code", name="uq_programs_area_code"
        ),
    )


class StudyPlanModel(Base):
    __tablename__ = "study_plans"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    program_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="")
    year: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    total_credits: Mapped[int] = mapped_column(Integer, default=0)

    program: Mapped[ProgramModel] = relationship(
        back_populates="study_plans"
    )
    plan_subjects: Mapped[list[PlanSubjectModel]] = relationship(
        back_populates="study_plan"
    )


class PlanSubjectModel(Base):
    __tablename__ = "plan_subjects"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    study_plan_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("study_plans.id"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id"),
        nullable=False,
        index=True,
    )
    semester: Mapped[int] = mapped_column(Integer, default=0)
    is_elective: Mapped[bool] = mapped_column(Boolean, default=False)

    study_plan: Mapped[StudyPlanModel] = relationship(
        back_populates="plan_subjects"
    )
    subject: Mapped["SubjectModel"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "study_plan_id",
            "subject_id",
            name="uq_plan_subjects_plan_subject",
        ),
        CheckConstraint("semester >= 0", name="ck_plan_subjects_semester"),
    )


class SubjectModel(Base):
    __tablename__ = "subjects"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id"),
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
    requires_lab: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    prerequisites: Mapped[list[SubjectPrerequisiteModel]] = relationship(
        back_populates="subject",
        foreign_keys="SubjectPrerequisiteModel.subject_id",
    )

    __table_args__ = (
        UniqueConstraint(
            "institution_id", "code", name="uq_subjects_institution_code"
        ),
    )


class SubjectPrerequisiteModel(Base):
    __tablename__ = "subject_prerequisites"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    subject_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id"),
        nullable=False,
        index=True,
    )
    prerequisite_subject_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id"),
        nullable=False,
        index=True,
    )
    prerequisite_type: Mapped[str] = mapped_column(
        String(50), default="required"
    )

    subject: Mapped[SubjectModel] = relationship(
        back_populates="prerequisites",
        foreign_keys=[subject_id],
    )
    prerequisite_subject: Mapped[SubjectModel] = relationship(
        foreign_keys=[prerequisite_subject_id],
    )

    __table_args__ = (
        UniqueConstraint(
            "subject_id",
            "prerequisite_subject_id",
            name="uq_subject_prerequisites_pair",
        ),
    )
