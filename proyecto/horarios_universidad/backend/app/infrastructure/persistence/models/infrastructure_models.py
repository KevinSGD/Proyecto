"""ORM models for physical infrastructure: buildings, classrooms, resources."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import (
    Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint, Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.database import Base


class BuildingModel(Base):
    __tablename__ = "buildings"

    id: Mapped[Any] = mapped_column(Uuid, primary_key=True, default=uuid4)
    campus_id: Mapped[Any] = mapped_column(
        Uuid, ForeignKey("campuses.id"), nullable=False, index=True,
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


class ClassroomModel(Base):
    __tablename__ = "classrooms"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("institutions.id"),
        nullable=False,
        index=True,
    )
    building_id: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("buildings.id"),
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
    availabilities: Mapped[list[ClassroomAvailabilityModel]] = relationship(
        back_populates="classroom"
    )
    resource_links: Mapped[list[RoomResourceModel]] = relationship(
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
        Uuid, primary_key=True, default=uuid4
    )
    classroom_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("classrooms.id"),
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


class ResourceModel(Base):
    __tablename__ = "resources"

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
    description: Mapped[str] = mapped_column(String(1000), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint(
            "institution_id", "code", name="uq_resources_institution_code"
        ),
    )


class RoomResourceModel(Base):
    __tablename__ = "room_resources"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    classroom_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("classrooms.id"),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("resources.id"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    classroom: Mapped[ClassroomModel] = relationship(
        back_populates="resource_links"
    )
    resource: Mapped[ResourceModel] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "classroom_id",
            "resource_id",
            name="uq_room_resources_pair",
        ),
        CheckConstraint(
            "quantity >= 1", name="ck_room_resources_quantity"
        ),
    )


class SubjectResourceRequirementModel(Base):
    __tablename__ = "subject_resource_requirements"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    subject_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("subjects.id"),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("resources.id"),
        nullable=False,
        index=True,
    )
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)

    subject: Mapped["SubjectModel"] = relationship()
    resource: Mapped[ResourceModel] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "subject_id",
            "resource_id",
            name="uq_subject_resource_requirements_pair",
        ),
    )
