"""ORM models for optimization runs, assignments, and session blocks."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.database import Base


class OptimizationConfigModel(Base):
    __tablename__ = "optimization_configs"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("institutions.id"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("academic_periods.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    config_data: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )
    is_default: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=True,
    )


class ScheduleRunModel(Base):
    __tablename__ = "schedule_runs"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    institution_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("institutions.id"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("academic_periods.id"),
        nullable=False,
        index=True,
    )
    config_id: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("optimization_configs.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, default=""
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    solver_config: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )
    statistics: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=dict
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    objective_value: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    gap: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_by: Mapped[Any | None] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=True,
    )

    assignments: Mapped[list[AssignmentModel]] = relationship(
        back_populates="schedule_run"
    )
    execution_logs: Mapped[list[ExecutionLogModel]] = relationship(
        back_populates="schedule_run"
    )


class AssignmentModel(Base):
    __tablename__ = "assignments"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    schedule_run_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("schedule_runs.id"),
        nullable=False,
        index=True,
    )
    group_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("groups.id"),
        nullable=False,
        index=True,
    )
    instructor_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("instructors.id"),
        nullable=False,
        index=True,
    )

    schedule_run: Mapped[ScheduleRunModel] = relationship(
        back_populates="assignments"
    )
    group: Mapped["GroupModel"] = relationship()
    instructor: Mapped["InstructorModel"] = relationship()
    session_blocks: Mapped[list[SessionBlockModel]] = relationship(
        back_populates="assignment"
    )

    __table_args__ = (
        UniqueConstraint(
            "schedule_run_id",
            "group_id",
            name="uq_assignments_run_group",
        ),
    )


class SessionBlockModel(Base):
    __tablename__ = "session_blocks"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    assignment_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("assignments.id"),
        nullable=False,
        index=True,
    )
    block_index: Mapped[int] = mapped_column(Integer, default=0)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_period: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    classroom_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("classrooms.id"),
        nullable=False,
        index=True,
    )

    assignment: Mapped[AssignmentModel] = relationship(
        back_populates="session_blocks"
    )
    classroom: Mapped["ClassroomModel"] = relationship()

    __table_args__ = (
        CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6",
            name="ck_session_blocks_day",
        ),
        CheckConstraint(
            "start_period >= 1", name="ck_session_blocks_start_period"
        ),
        CheckConstraint(
            "duration >= 1", name="ck_session_blocks_duration"
        ),
    )


class ExecutionLogModel(Base):
    __tablename__ = "execution_logs"

    id: Mapped[Any] = mapped_column(
        Uuid, primary_key=True, default=uuid4
    )
    schedule_run_id: Mapped[Any] = mapped_column(
        Uuid,
        ForeignKey("schedule_runs.id"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(String(2000), default="")
    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict
    )

    schedule_run: Mapped[ScheduleRunModel] = relationship(
        back_populates="execution_logs"
    )
