"""ORM models for schedule types and student groups."""

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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.database import Base


class ScheduleTypeModel(Base):
    __tablename__ = "schedule_types"

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
    schedule_type: Mapped[str] = mapped_column(String(100), nullable=False)
    active_days: Mapped[list[int]] = mapped_column(JSONB, default=list)
    start_period: Mapped[int] = mapped_column(Integer, default=0)
    end_period: Mapped[int] = mapped_column(Integer, default=0)
    slot_duration_minutes: Mapped[int] = mapped_column(
        Integer, default=60
    )

    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "name",
            name="uq_schedule_types_institution_name",
        ),
        CheckConstraint(
            "start_period >= 0", name="ck_schedule_types_start_period"
        ),
        CheckConstraint(
            "end_period >= start_period",
            name="ck_schedule_types_end_period",
        ),
        CheckConstraint(
            "slot_duration_minutes > 0",
            name="ck_schedule_types_slot_duration",
        ),
    )


class GroupModel(Base):
    __tablename__ = "groups"

    id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    offering_line_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offering_lines.id"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id"),
        nullable=False,
        index=True,
    )
    group_number: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_enrollment: Mapped[int] = mapped_column(Integer, default=0)
    modality: Mapped[str] = mapped_column(String(50), default="")
    schedule_type_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schedule_types.id"),
        nullable=False,
        index=True,
    )
    priority: Mapped[int] = mapped_column(Integer, default=2)

    offering_line: Mapped["OfferingLineModel"] = relationship()
    subject: Mapped["SubjectModel"] = relationship()
    schedule_type: Mapped[ScheduleTypeModel] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "offering_line_id",
            "group_number",
            name="uq_groups_offering_line_number",
        ),
        CheckConstraint(
            "group_number >= 0", name="ck_groups_group_number"
        ),
        CheckConstraint(
            "expected_enrollment >= 0", name="ck_groups_enrollment"
        ),
        CheckConstraint(
            "priority >= 1 AND priority <= 5", name="ck_groups_priority"
        ),
    )
