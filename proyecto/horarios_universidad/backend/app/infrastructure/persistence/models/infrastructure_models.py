"""ORM models for physical infrastructure: buildings, classrooms, equipment."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.database import Base


class BuildingModel(Base):
    __tablename__ = "buildings"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    campus_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campuses.id"), nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    floors: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    campus: Mapped["CampusModel"] = relationship(back_populates="buildings")
    classrooms: Mapped[list[ClassroomModel]] = relationship(back_populates="building")

    __table_args__ = (
        UniqueConstraint("campus_id", "code", name="uq_buildings_campus_code"),
        CheckConstraint("floors >= 1", name="ck_buildings_floors"),
    )


class ClassroomTypeModel(Base):
    __tablename__ = "classroom_types"

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

    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "code",
            name="uq_classroom_types_institution_code",
        ),
    )


class ClassroomModel(Base):
    __tablename__ = "classrooms"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id"),
        nullable=False,
        index=True,
    )
    building_id: Mapped[Any | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id"),
        nullable=True,
        index=True,
    )
    classroom_type_id: Mapped[Any | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classroom_types.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=0)
    floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_virtual: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    building: Mapped["BuildingModel | None"] = relationship(
        back_populates="classrooms"
    )
    classroom_type: Mapped["ClassroomTypeModel | None"] = relationship()
    availabilities: Mapped[list[ClassroomAvailabilityModel]] = relationship(
        back_populates="classroom"
    )
    equipment_links: Mapped[list[ClassroomEquipmentModel]] = relationship(
        back_populates="classroom"
    )

    __table_args__ = (
        UniqueConstraint(
            "institution_id", "code", name="uq_classrooms_institution_code"
        ),
        CheckConstraint("capacity >= 0", name="ck_classrooms_capacity"),
    )


class ClassroomAvailabilityModel(Base):
    __tablename__ = "classroom_availabilities"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    classroom_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[Any | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_periods.id"),
        nullable=True,
        index=True,
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    classroom: Mapped[ClassroomModel] = relationship(
        back_populates="availabilities"
    )

    __table_args__ = (
        UniqueConstraint(
            "classroom_id",
            "period_id",
            "day_of_week",
            "period",
            name="uq_classroom_availabilities_slot",
        ),
        CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6",
            name="ck_classroom_availabilities_day",
        ),
        CheckConstraint(
            "period >= 1", name="ck_classroom_availabilities_period"
        ),
    )


class EquipmentModel(Base):
    __tablename__ = "equipment"

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

    __table_args__ = (
        UniqueConstraint(
            "institution_id", "code", name="uq_equipment_institution_code"
        ),
    )


class ClassroomEquipmentModel(Base):
    __tablename__ = "classroom_equipment"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    classroom_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id"),
        nullable=False,
        index=True,
    )
    equipment_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("equipment.id"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    classroom: Mapped[ClassroomModel] = relationship(
        back_populates="equipment_links"
    )
    equipment: Mapped[EquipmentModel] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "classroom_id",
            "equipment_id",
            name="uq_classroom_equipment_pair",
        ),
        CheckConstraint(
            "quantity >= 1", name="ck_classroom_equipment_quantity"
        ),
    )


class SubjectEquipmentRequirementModel(Base):
    __tablename__ = "subject_equipment_requirements"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    subject_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id"),
        nullable=False,
        index=True,
    )
    equipment_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("equipment.id"),
        nullable=False,
        index=True,
    )
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)

    subject: Mapped["SubjectModel"] = relationship()
    equipment: Mapped[EquipmentModel] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "subject_id",
            "equipment_id",
            name="uq_subject_equipment_requirements_pair",
        ),
    )
