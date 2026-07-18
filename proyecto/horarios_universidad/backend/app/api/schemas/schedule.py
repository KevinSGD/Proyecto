"""Request/response schemas for schedule generation and solver results."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.api.schemas.base import CamelModel


# ── Requests ────────────────────────────────────────────────────────────────


class ScheduleGenerateRequest(CamelModel):
    """Trigger a new schedule generation run."""

    institution_id: UUID
    period_id: UUID
    max_time_seconds: int | None = Field(
        default=None, ge=10, le=3600,
        description="Solver time limit in seconds",
    )
    num_workers: int | None = Field(
        default=None, ge=1, le=16,
        description="Number of parallel solver workers",
    )
    created_by: UUID | None = None


class ScheduleValidateRequest(CamelModel):
    """Validate domain data before running the solver."""

    institution_id: UUID
    period_id: UUID
    run_id: UUID | None = None


class SchedulePublishRequest(CamelModel):
    """Mark a schedule run as published."""

    schedule_run_id: UUID


class ScheduleBlockRequest(CamelModel):
    """Mark a schedule run as blocked."""

    schedule_run_id: UUID


class SessionBlockUpdateRequest(CamelModel):
    """Update a session block (manual schedule edit)."""

    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_period: int | None = Field(default=None, ge=1)
    duration: int | None = Field(default=None, ge=1)
    classroom_id: UUID | None = None
    instructor_id: UUID | None = None


# ── Responses ───────────────────────────────────────────────────────────────


class ScheduleRunOut(CamelModel):
    """Summary of a solver execution."""

    id: UUID
    institution_id: UUID
    period_id: UUID
    name: str = ""
    status: str
    solver_config: dict[str, Any] = Field(default_factory=dict)
    statistics: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    objective_value: float | None = None
    gap: float | None = None
    created_by: UUID | None = None


class AssignmentOut(CamelModel):
    """Group-to-instructor mapping within a schedule run."""

    id: UUID
    schedule_run_id: UUID
    group_id: UUID
    instructor_id: UUID


class SessionBlockOut(CamelModel):
    """A concrete time-and-room slot for an assignment."""

    id: UUID
    assignment_id: UUID
    block_index: int
    day_of_week: int
    start_period: int
    duration: int
    classroom_id: UUID


class AssignmentDetailOut(CamelModel):
    """Assignment together with its session blocks."""

    id: UUID
    schedule_run_id: UUID
    group_id: UUID
    instructor_id: UUID
    sessions: list[SessionBlockOut] = Field(default_factory=list)


class ExecutionLogOut(CamelModel):
    """A single execution event log entry."""

    id: UUID
    schedule_run_id: UUID
    event_type: str
    message: str
    timestamp: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScheduleRunDetailOut(CamelModel):
    """Full schedule run including all assignments, sessions, and execution logs."""

    id: UUID
    institution_id: UUID
    period_id: UUID
    name: str = ""
    status: str
    solver_config: dict[str, Any] = Field(default_factory=dict)
    statistics: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    objective_value: float | None = None
    gap: float | None = None
    created_by: UUID | None = None
    assignments: list[AssignmentDetailOut] = Field(default_factory=list)
    execution_logs: list[ExecutionLogOut] = Field(default_factory=list)


class ValidationReportOut(CamelModel):
    """Result of a pre-solver validation run."""

    id: UUID
    institution_id: UUID
    period_id: UUID | None = None
    report_type: str
    status: str
    errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
